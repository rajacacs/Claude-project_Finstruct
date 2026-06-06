"""AI Service — Abstraction for multiple LLM providers (Claude, OpenAI, Gemini)."""

from __future__ import annotations
import json
import re
import logging
from abc import ABC, abstractmethod

log = logging.getLogger(__name__)

class AIProvider(ABC):
    @abstractmethod
    def solve_mapping(self, unresolved: list[str], reference_sample: str, api_key: str) -> dict[str, str]:
        """Ask LLM to resolve unresolved ledger names.
        Returns {ledger_name: mapping_code}.
        """
        pass

class ClaudeProvider(AIProvider):
    def solve_mapping(self, unresolved: list[str], reference_sample: str, api_key: str) -> dict[str, str]:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            ledger_list = "\n".join(f"- {l}" for l in unresolved[:30])
            prompt = self._get_prompt(reference_sample, ledger_list)
            
            msg = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
            )
            return self._parse_json(msg.content[0].text)
        except Exception as e:
            log.warning("Claude API failed: %s", e)
        return {}

    def _get_prompt(self, reference, ledgers):
        return (
            f"You are a Chartered Accountant. Match each ledger name below to the best "
            f"Schedule III / ICAI code from the reference list. "
            f"Reply ONLY as JSON: {{\"ledger_name\": \"CODE\", ...}}\n\n"
            f"Reference codes:\n{reference}\n\n"
            f"Ledger names to map:\n{ledgers}"
        )

    def _parse_json(self, text: str) -> dict[str, str]:
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group())
            except json.JSONDecodeError:
                pass
        return {}

class OpenAIProvider(AIProvider):
    def solve_mapping(self, unresolved: list[str], reference_sample: str, api_key: str) -> dict[str, str]:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            ledger_list = "\n".join(f"- {l}" for l in unresolved[:30])
            prompt = self._get_prompt(reference_sample, ledger_list)
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            log.warning("OpenAI API failed: %s", e)
        return {}

    def _get_prompt(self, reference, ledgers):
        return (
            f"You are a Chartered Accountant. Match each ledger name below to the best "
            f"Schedule III / ICAI code from the reference list. "
            f"Return a JSON object where keys are ledger names and values are codes.\n\n"
            f"Reference codes:\n{reference}\n\n"
            f"Ledger names to map:\n{ledgers}"
        )

class GeminiProvider(AIProvider):
    def solve_mapping(self, unresolved: list[str], reference_sample: str, api_key: str) -> dict[str, str]:
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-1.5-flash")
            ledger_list = "\n".join(f"- {l}" for l in unresolved[:30])
            prompt = self._get_prompt(reference_sample, ledger_list)
            
            response = model.generate_content(prompt)
            return self._parse_json(response.text)
        except Exception as e:
            log.warning("Gemini API failed: %s", e)
        return {}

    def _get_prompt(self, reference, ledgers):
        return (
            f"You are a Chartered Accountant. Match each ledger name below to the best "
            f"Schedule III / ICAI code from the reference list. "
            f"Reply ONLY as JSON: {{\"ledger_name\": \"CODE\", ...}}\n\n"
            f"Reference codes:\n{reference}\n\n"
            f"Ledger names to map:\n{ledgers}"
        )

    def _parse_json(self, text: str) -> dict[str, str]:
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group())
            except json.JSONDecodeError:
                pass
        return {}

def get_ai_service(provider_name: str) -> AIProvider | None:
    providers = {
        "Claude": ClaudeProvider,
        "OpenAI": OpenAIProvider,
        "Gemini": GeminiProvider,
    }
    cls = providers.get(provider_name)
    return cls() if cls else None
