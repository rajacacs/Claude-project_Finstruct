"""Per-client SQLite project database — schema, CRUD, migrations."""

from __future__ import annotations
import sqlite3
import json
import logging
from pathlib import Path
from datetime import datetime
from contextlib import contextmanager
from typing import Any

from data.encryption import encrypt, decrypt

log = logging.getLogger(__name__)

SCHEMA_VERSION = 3

PII_KEYS = {
    "pan", "cin", "llpin", "address", "reg_addr", "pan_no", "cin_no", "llpin_no",
    "dir1_din", "dir2_din", "dir1_name", "dir2_name", "dir1_pan", "dir2_pan",
    "cfo_name", "cs_name", "prop_name", "partner1_name", "partner2_name",
    "partner1_pan", "partner2_pan", "partner1_din", "partner2_din",
    "prop_pan", "prop_addr", "din", "reg_no", "audit_partner", "auditor_partner",
    "president_name", "secretary_name", "treasurer_name",
}


class ProjectDB:
    def __init__(self, path: Path):
        self.path = path
        self._conn: sqlite3.Connection | None = None

    def connect(self):
        self._conn = sqlite3.connect(self.path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._init_schema()

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None

    @contextmanager
    def _tx(self):
        try:
            yield self._conn
            self._conn.commit()
        except Exception:
            self._conn.rollback()
            raise

    def _init_schema(self):
        c = self._conn
        c.executescript("""
        CREATE TABLE IF NOT EXISTS project_meta (
            key TEXT PRIMARY KEY, value TEXT
        );
        CREATE TABLE IF NOT EXISTS entity_master (
            key TEXT PRIMARY KEY, value TEXT
        );
        CREATE TABLE IF NOT EXISTS raw_tb (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ledger_name TEXT NOT NULL,
            group_name TEXT,
            cy_debit REAL DEFAULT 0,
            cy_credit REAL DEFAULT 0,
            cy_net REAL DEFAULT 0,
            py_net REAL DEFAULT 0,
            source TEXT DEFAULT 'MANUAL'
        );
        CREATE TABLE IF NOT EXISTS wtb (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            raw_tb_id INTEGER UNIQUE REFERENCES raw_tb(id) ON DELETE CASCADE,
            mapping_code TEXT,
            confidence REAL DEFAULT 0,
            confidence_source TEXT DEFAULT 'MANUAL',
            cy_net REAL DEFAULT 0,
            py_net REAL DEFAULT 0,
            is_confirmed INTEGER DEFAULT 0
        );
        -- Cleanup duplicates if any exist from previous bug
        DELETE FROM wtb WHERE id NOT IN (SELECT MIN(id) FROM wtb GROUP BY raw_tb_id);
        CREATE UNIQUE INDEX IF NOT EXISTS idx_wtb_raw_id ON wtb(raw_tb_id);
        CREATE TABLE IF NOT EXISTS adjustments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            adj_id TEXT UNIQUE,
            ledger_name TEXT,
            mapping_code TEXT,
            dr_amount REAL DEFAULT 0,
            cr_amount REAL DEFAULT 0,
            narration TEXT,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        );
        CREATE TABLE IF NOT EXISTS ppe (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            asset_name TEXT NOT NULL,
            category TEXT,
            method TEXT DEFAULT 'SLM',
            useful_life_yrs INTEGER DEFAULT 10,
            gross_op REAL DEFAULT 0,
            additions REAL DEFAULT 0,
            disposals REAL DEFAULT 0,
            dep_op REAL DEFAULT 0,
            dep_charge REAL DEFAULT 0,
            dep_disposal REAL DEFAULT 0,
            nbv_py REAL DEFAULT 0,
            it_wdv_op REAL DEFAULT 0,
            it_rate REAL DEFAULT 15,
            it_dep REAL DEFAULT 0,
            it_wdv_cl REAL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS fs_overrides (
            section TEXT, line_code TEXT, cy_value REAL, py_value REAL,
            override_reason TEXT,
            PRIMARY KEY (section, line_code)
        );
        CREATE TABLE IF NOT EXISTS note_data (
            note_no INTEGER, sequence INTEGER, label TEXT,
            cy_value REAL DEFAULT 0, py_value REAL DEFAULT 0,
            row_type TEXT DEFAULT 'DATA',
            PRIMARY KEY (note_no, sequence)
        );
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT DEFAULT (datetime('now','localtime')),
            action TEXT, detail TEXT
        );
        CREATE TABLE IF NOT EXISTS directors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            designation TEXT DEFAULT 'Director',
            din TEXT DEFAULT '',
            pan TEXT DEFAULT '',
            is_signing_auth INTEGER DEFAULT 1,
            sort_order INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS annexure_rows (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            annexure_code TEXT NOT NULL,
            label TEXT NOT NULL,
            cy_value REAL DEFAULT 0,
            py_value REAL DEFAULT 0,
            sort_order INTEGER DEFAULT 0,
            UNIQUE(annexure_code, label)
        );
        """)
        c.commit()
        if not self.get_meta("schema_version"):
            self.set_meta("schema_version", str(SCHEMA_VERSION))
            self.set_meta("created_at", datetime.now().isoformat())
        ver = int(self.get_meta("schema_version") or "1")
        if ver < 2:
            self._migrate_v2()
        if ver < 3:
            self._migrate_v3()
        self.migrate_legacy_directors()

    def _migrate_v2(self):
        """Add UNIQUE(raw_tb_id) to wtb by recreating the table."""
        try:
            self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS wtb_v2 (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                raw_tb_id INTEGER UNIQUE REFERENCES raw_tb(id) ON DELETE CASCADE,
                mapping_code TEXT,
                confidence REAL DEFAULT 0,
                confidence_source TEXT DEFAULT 'MANUAL',
                cy_net REAL DEFAULT 0,
                py_net REAL DEFAULT 0,
                is_confirmed INTEGER DEFAULT 0
            );
            INSERT OR IGNORE INTO wtb_v2(
                raw_tb_id, mapping_code, confidence,
                confidence_source, cy_net, py_net, is_confirmed)
            SELECT raw_tb_id, mapping_code, confidence,
                confidence_source, cy_net, py_net, is_confirmed
            FROM wtb;
            DROP TABLE wtb;
            ALTER TABLE wtb_v2 RENAME TO wtb;
            """)
            self._conn.commit()
            self.set_meta("schema_version", "2")
            log.info("DB migrated to v2: wtb.raw_tb_id is now UNIQUE")
        except Exception as e:
            log.error("Migration v2 failed: %s", e)

    def _migrate_v3(self):
        """Add annexure_rows table (no destructive change)."""
        try:
            self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS annexure_rows (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                annexure_code TEXT NOT NULL,
                label TEXT NOT NULL,
                cy_value REAL DEFAULT 0,
                py_value REAL DEFAULT 0,
                sort_order INTEGER DEFAULT 0,
                UNIQUE(annexure_code, label)
            );
            """)
            self._conn.commit()
            self.set_meta("schema_version", "3")
            log.info("DB migrated to v3: annexure_rows table added")
        except Exception as e:
            log.error("Migration v3 failed: %s", e)

    # ── Annexures ────────────────────────────────────────────────────────
    def get_annexure_rows(self, annexure_code: str) -> list:
        return self._conn.execute(
            "SELECT label,cy_value,py_value FROM annexure_rows "
            "WHERE annexure_code=? ORDER BY sort_order, id",
            (annexure_code,)
        ).fetchall()

    def save_annexure_rows(self, annexure_code: str, rows: list[dict]):
        with self._tx():
            self._conn.execute(
                "DELETE FROM annexure_rows WHERE annexure_code=?", (annexure_code,)
            )
            for i, r in enumerate(rows):
                self._conn.execute(
                    "INSERT INTO annexure_rows(annexure_code,label,cy_value,py_value,sort_order) "
                    "VALUES(?,?,?,?,?)",
                    (annexure_code, r["label"],
                     float(r.get("cy_value") or 0),
                     float(r.get("py_value") or 0),
                     i)
                )

    def get_all_annexure_codes(self) -> list[str]:
        rows = self._conn.execute(
            "SELECT DISTINCT annexure_code FROM annexure_rows"
        ).fetchall()
        return [r[0] for r in rows]

    # ── Meta ─────────────────────────────────────────────────────────────
    def get_meta(self, key: str) -> str | None:
        row = self._conn.execute("SELECT value FROM project_meta WHERE key=?", (key,)).fetchone()
        return row[0] if row else None

    def set_meta(self, key: str, value: str):
        with self._tx():
            self._conn.execute(
                "INSERT OR REPLACE INTO project_meta(key,value) VALUES(?,?)", (key, value)
            )

    def get_all_meta(self) -> dict[str, str]:
        rows = self._conn.execute("SELECT key,value FROM project_meta").fetchall()
        return {r[0]: r[1] for r in rows}

    # ── Entity Master ────────────────────────────────────────────────────
    def get_entity(self, key: str) -> str:
        row = self._conn.execute("SELECT value FROM entity_master WHERE key=?", (key,)).fetchone()
        if not row:
            return ""
        val = row[0]
        if key.lower() in PII_KEYS:
            val = decrypt(val)
        return val or ""

    def set_entity(self, key: str, value: str):
        stored = encrypt(value) if key.lower() in PII_KEYS else value
        with self._tx():
            self._conn.execute(
                "INSERT OR REPLACE INTO entity_master(key,value) VALUES(?,?)", (key, stored)
            )

    def get_all_entity(self) -> dict[str, str]:
        rows = self._conn.execute("SELECT key,value FROM entity_master").fetchall()
        out = {}
        for k, v in rows:
            out[k] = decrypt(v) if k.lower() in PII_KEYS else (v or "")
        return out

    def save_entity_batch(self, data: dict[str, str]):
        with self._tx():
            for k, v in data.items():
                stored = encrypt(v) if k.lower() in PII_KEYS else v
                self._conn.execute(
                    "INSERT OR REPLACE INTO entity_master(key,value) VALUES(?,?)", (k, stored)
                )

    def get_directors(self) -> list[dict]:
        rows = self._conn.execute(
            "SELECT * FROM directors ORDER BY sort_order, id"
        ).fetchall()
        out = []
        for r in rows:
            d = dict(r)
            d["din"] = decrypt(d.get("din", ""))
            d["pan"] = decrypt(d.get("pan", ""))
            out.append(d)
        return out

    def upsert_director(self, d: dict) -> int:
        with self._tx():
            din = encrypt(d.get("din", ""))
            pan = encrypt(d.get("pan", ""))
            if d.get("id"):
                self._conn.execute(
                    "UPDATE directors SET name=?,designation=?,din=?,pan=?,is_signing_auth=?,sort_order=? WHERE id=?",
                    (d["name"], d.get("designation","Director"), din, pan,
                     int(d.get("is_signing_auth",1)), int(d.get("sort_order",0)), d["id"])
                )
                return d["id"]
            else:
                cur = self._conn.execute(
                    "INSERT INTO directors(name,designation,din,pan,is_signing_auth,sort_order) VALUES(?,?,?,?,?,?)",
                    (d["name"], d.get("designation","Director"), din, pan,
                     int(d.get("is_signing_auth",1)), int(d.get("sort_order",0)))
                )
                return cur.lastrowid

    def delete_director(self, dir_id: int):
        with self._tx():
            self._conn.execute("DELETE FROM directors WHERE id=?", (dir_id,))

    def migrate_legacy_directors(self):
        """Migrate dir1_name/dir2_name from entity_master to directors table (run once)."""
        if self._conn.execute("SELECT COUNT(*) FROM directors").fetchone()[0] > 0:
            return  # already migrated
        em = self.get_all_entity()
        for i in (1, 2):
            name = em.get(f"dir{i}_name", "").strip()
            if name:
                self.upsert_director({
                    "name": name,
                    "designation": em.get(f"dir{i}_desig", "Director"),
                    "din": em.get(f"dir{i}_din", ""),
                    "is_signing_auth": 1,
                    "sort_order": i - 1,
                })

    # ── Raw TB ───────────────────────────────────────────────────────────
    def clear_raw_tb(self):
        with self._tx():
            self._conn.execute("DELETE FROM raw_tb")
            self._conn.execute("DELETE FROM wtb")

    def insert_raw_tb_batch(self, rows: list[dict]):
        with self._tx():
            self._conn.executemany(
                "INSERT INTO raw_tb(ledger_name,group_name,cy_debit,cy_credit,cy_net,py_net,source) "
                "VALUES(:ledger_name,:group_name,:cy_debit,:cy_credit,:cy_net,:py_net,:source)",
                rows,
            )

    def get_raw_tb(self) -> list[sqlite3.Row]:
        return self._conn.execute("SELECT * FROM raw_tb ORDER BY id").fetchall()

    # ── WTB ──────────────────────────────────────────────────────────────
    def upsert_wtb(self, raw_tb_id: int, mapping_code: str, confidence: float,
                   source: str, cy_net: float, py_net: float, confirmed: int = 0):
        with self._tx():
            self._conn.execute(
                "INSERT INTO wtb(raw_tb_id,mapping_code,confidence,confidence_source,"
                "cy_net,py_net,is_confirmed) VALUES(?,?,?,?,?,?,?) "
                "ON CONFLICT(raw_tb_id) DO UPDATE SET "
                "mapping_code=excluded.mapping_code,"
                "confidence=excluded.confidence,"
                "confidence_source=excluded.confidence_source,"
                "cy_net=excluded.cy_net,py_net=excluded.py_net,"
                "is_confirmed=excluded.is_confirmed",
                (raw_tb_id, mapping_code, confidence, source, cy_net, py_net, confirmed)
            )

    def confirm_mapping(self, raw_tb_id: int, mapping_code: str):
        with self._tx():
            self._conn.execute(
                "UPDATE wtb SET mapping_code=?,is_confirmed=1 WHERE raw_tb_id=?",
                (mapping_code, raw_tb_id)
            )

    def get_wtb(self) -> list[sqlite3.Row]:
        return self._conn.execute("""
            SELECT w.*, r.ledger_name, r.group_name
            FROM wtb w JOIN raw_tb r ON r.id = w.raw_tb_id
            ORDER BY w.mapping_code, r.ledger_name
        """).fetchall()

    def sum_by_code(self) -> dict[str, tuple[float, float]]:
        """Return {mapping_code: (cy_net, py_net)} summed across all ledgers."""
        rows = self._conn.execute(
            "SELECT mapping_code, SUM(cy_net), SUM(py_net) FROM wtb "
            "WHERE mapping_code IS NOT NULL GROUP BY mapping_code"
        ).fetchall()
        return {r[0]: (r[1] or 0.0, r[2] or 0.0) for r in rows}

    def unconfirmed_count(self) -> int:
        row = self._conn.execute(
            "SELECT COUNT(*) FROM wtb WHERE is_confirmed=0 OR mapping_code IS NULL"
        ).fetchone()
        return row[0]

    # ── Adjustments ──────────────────────────────────────────────────────
    def add_adjustment(self, adj_id: str, ledger: str, code: str,
                       dr: float, cr: float, narration: str):
        with self._tx():
            self._conn.execute(
                "INSERT INTO adjustments(adj_id,ledger_name,mapping_code,dr_amount,cr_amount,narration) "
                "VALUES(?,?,?,?,?,?)",
                (adj_id, ledger, code, dr, cr, narration)
            )

    def get_adjustments(self) -> list[sqlite3.Row]:
        return self._conn.execute("SELECT * FROM adjustments ORDER BY id").fetchall()

    def delete_dep_adjustments(self):
        """Idempotent: remove all prior depreciation auto-post entries."""
        with self._tx():
            self._conn.execute(
                "DELETE FROM adjustments WHERE adj_id LIKE 'DEP-%'"
            )

    # ── PPE ──────────────────────────────────────────────────────────────
    def upsert_ppe(self, asset: dict):
        with self._tx():
            if asset.get("id"):
                self._conn.execute("""
                    UPDATE ppe SET asset_name=?,category=?,method=?,useful_life_yrs=?,
                    gross_op=?,additions=?,disposals=?,dep_op=?,dep_charge=?,dep_disposal=?,
                    nbv_py=?,it_wdv_op=?,it_rate=?,it_dep=?,it_wdv_cl=?
                    WHERE id=?
                """, (asset["asset_name"], asset.get("category",""), asset.get("method","SLM"),
                      asset.get("useful_life_yrs",10), asset.get("gross_op",0),
                      asset.get("additions",0), asset.get("disposals",0),
                      asset.get("dep_op",0), asset.get("dep_charge",0),
                      asset.get("dep_disposal",0), asset.get("nbv_py",0),
                      asset.get("it_wdv_op",0), asset.get("it_rate",15),
                      asset.get("it_dep",0), asset.get("it_wdv_cl",0), asset["id"]))
            else:
                self._conn.execute("""
                    INSERT INTO ppe(asset_name,category,method,useful_life_yrs,
                    gross_op,additions,disposals,dep_op,dep_charge,dep_disposal,
                    nbv_py,it_wdv_op,it_rate,it_dep,it_wdv_cl)
                    VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """, (asset["asset_name"], asset.get("category",""), asset.get("method","SLM"),
                      asset.get("useful_life_yrs",10), asset.get("gross_op",0),
                      asset.get("additions",0), asset.get("disposals",0),
                      asset.get("dep_op",0), asset.get("dep_charge",0),
                      asset.get("dep_disposal",0), asset.get("nbv_py",0),
                      asset.get("it_wdv_op",0), asset.get("it_rate",15),
                      asset.get("it_dep",0), asset.get("it_wdv_cl",0)))

    def delete_ppe(self, asset_id: int):
        with self._tx():
            self._conn.execute("DELETE FROM ppe WHERE id=?", (asset_id,))

    def get_ppe(self) -> list[sqlite3.Row]:
        return self._conn.execute("SELECT * FROM ppe ORDER BY category, asset_name").fetchall()

    # ── FS Overrides ─────────────────────────────────────────────────────
    def set_override(self, section: str, line_code: str, cy: float, py: float, reason: str = ""):
        with self._tx():
            self._conn.execute(
                "INSERT OR REPLACE INTO fs_overrides(section,line_code,cy_value,py_value,override_reason)"
                " VALUES(?,?,?,?,?)", (section, line_code, cy, py, reason)
            )

    def get_overrides(self, section: str) -> dict[str, tuple[float, float]]:
        rows = self._conn.execute(
            "SELECT line_code,cy_value,py_value FROM fs_overrides WHERE section=?", (section,)
        ).fetchall()
        return {r[0]: (r[1], r[2]) for r in rows}

    # ── Audit Log ────────────────────────────────────────────────────────
    def log(self, action: str, detail: str = ""):
        with self._tx():
            self._conn.execute(
                "INSERT INTO audit_log(action,detail) VALUES(?,?)", (action, detail)
            )

    def get_audit_log(self, limit: int = 200) -> list[sqlite3.Row]:
        return self._conn.execute(
            "SELECT * FROM audit_log ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
