"""ML Mapping engine — TF-IDF + Sentence-BERT + Claude API fallback."""

from __future__ import annotations
import logging
from typing import TYPE_CHECKING

from .master_db import MASTER, MappingEntry

if TYPE_CHECKING:
    from ..data.settings_db import SettingsDB

log = logging.getLogger(__name__)

CONF_GREEN  = 0.85
CONF_YELLOW = 0.65


class MappingResult:
    __slots__ = ("code", "entry", "confidence", "source")

    def __init__(self, code: str, entry: MappingEntry | None,
                 confidence: float, source: str):
        self.code       = code
        self.entry      = entry
        self.confidence = confidence
        self.source     = source

    @property
    def status(self) -> str:
        if self.confidence >= CONF_GREEN:
            return "GREEN"
        if self.confidence >= CONF_YELLOW:
            return "YELLOW"
        return "RED"


class Mapper:
    def __init__(self, entity_type: str, settings_db: "SettingsDB"):
        self._etype    = entity_type
        self._sdb      = settings_db
        self._tfidf    = None
        self._sbert    = None
        self._corpus   = []     # lookup_name strings
        self._entries  = []     # MappingEntry objects aligned with corpus
        self._build_corpus()

    def _build_corpus(self):
        from .entity_types import MASTER_TAGS, EntityType
        try:
            et = EntityType(self._etype)
            tags = MASTER_TAGS.get(et, ["ALL"])
        except ValueError:
            tags = ["ALL"]
        tag_set = set(tags)
        self._entries = [m for m in MASTER if set(m.entity_types).intersection(tag_set)]
        self._corpus  = [m.lookup_name for m in self._entries]

    def _get_tfidf(self):
        if self._tfidf is None:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity
            self._tfidf_fn = cosine_similarity
            v = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4))
            self._tfidf_matrix = v.fit_transform(self._corpus)
            self._tfidf = v
        return self._tfidf

    def _get_sbert(self):
        if self._sbert is None:
            try:
                from sentence_transformers import SentenceTransformer
                from ..config import MODELS_DIR
                model_path = MODELS_DIR / "all-MiniLM-L6-v2"
                self._sbert = SentenceTransformer(str(model_path) if model_path.exists() else "all-MiniLM-L6-v2")
                self._sbert_corpus_emb = self._sbert.encode(self._corpus, convert_to_numpy=True)
            except Exception as e:
                log.warning("Sentence-transformer unavailable: %s", e)
                self._sbert = False
        return self._sbert or None

    def map_ledger(self, ledger_name: str) -> MappingResult:
        # 1. Learned mappings (global DB)
        code = self._sdb.lookup(ledger_name, self._etype)
        if code:
            entry = next((e for e in self._entries if e.code == code), None)
            return MappingResult(code, entry, 1.0, "LEARNED")

        # 2. Exact match on lookup_name
        ln = ledger_name.lower()
        for entry in self._entries:
            if entry.sub_heading.lower() == ln or entry.lookup_name.lower() == ln:
                return MappingResult(entry.code, entry, 1.0, "EXACT")

        # 3. TF-IDF
        best_code, best_conf, best_entry = self._tfidf_match(ledger_name)
        best_source = "TFIDF"

        # 4. Sentence-BERT (if TF-IDF not confident enough)
        if best_conf < CONF_GREEN:
            sb_code, sb_conf, sb_entry = self._sbert_match(ledger_name)
            if sb_conf > best_conf:
                best_code, best_conf, best_entry = sb_code, sb_conf, sb_entry
                best_source = "SBERT"

        return MappingResult(best_code or "", best_entry, best_conf, best_source)

    def _tfidf_match(self, ledger: str) -> tuple[str | None, float, MappingEntry | None]:
        try:
            from sklearn.metrics.pairwise import cosine_similarity
            v = self._get_tfidf()
            q  = v.transform([ledger])
            scores = cosine_similarity(q, self._tfidf_matrix)[0]
            idx = int(scores.argmax())
            score = float(scores[idx])
            if score > 0:
                e = self._entries[idx]
                return e.code, score, e
        except Exception as e:
            log.debug("TF-IDF error: %s", e)
        return None, 0.0, None

    def _sbert_match(self, ledger: str) -> tuple[str | None, float, MappingEntry | None]:
        try:
            import numpy as np
            sb = self._get_sbert()
            if not sb:
                return None, 0.0, None
            q_emb  = sb.encode([ledger], convert_to_numpy=True)
            scores = np.dot(self._sbert_corpus_emb, q_emb.T).flatten()
            norms  = (np.linalg.norm(self._sbert_corpus_emb, axis=1) *
                      np.linalg.norm(q_emb))
            cos    = scores / (norms + 1e-9)
            idx    = int(cos.argmax())
            score  = float(cos[idx])
            if score > 0:
                e = self._entries[idx]
                return e.code, score, e
        except Exception as e:
            log.debug("SBERT error: %s", e)
        return None, 0.0, None

    def map_batch(self, ledger_names: list[str]) -> list[MappingResult]:
        return [self.map_ledger(n) for n in ledger_names]

    def map_via_claude(self, unresolved: list[str]) -> dict[str, str]:
        """Ask Claude API to resolve unresolved ledger names.
        Returns {ledger_name: mapping_code}.
        """
        api_key = self._sdb.get_api_key()
        if not api_key:
            return {}
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            corpus_sample = "\n".join(
                f"{m.code}: {m.lookup_name}" for m in self._entries[:80]
            )
            ledger_list = "\n".join(f"- {l}" for l in unresolved[:30])
            prompt = (
                f"You are a Chartered Accountant. Match each ledger name below to the best "
                f"Schedule III / ICAI code from the reference list. "
                f"Reply as JSON: {{\"ledger_name\": \"CODE\", ...}}\n\n"
                f"Reference codes:\n{corpus_sample}\n\n"
                f"Ledger names to map:\n{ledger_list}"
            )
            msg = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
            )
            import json, re
            text = msg.content[0].text
            m = re.search(r"\{.*\}", text, re.DOTALL)
            if m:
                return json.loads(m.group())
        except Exception as e:
            log.warning("Claude API mapping failed: %s", e)
        return {}

    def confirm_and_learn(self, ledger_name: str, code: str):
        """Save confirmed mapping to global learned_mappings."""
        self._sdb.learn(ledger_name, self._etype, code)
