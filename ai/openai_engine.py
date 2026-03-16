"""OpenAI-backed journal engine placeholder implementation."""
from __future__ import annotations

from ai.ai_engine import BaseJournalEngine


class OpenAIJournalEngine(BaseJournalEngine):
    def suggest(self, transaction: dict) -> dict:
        raise NotImplementedError("OpenAI 엔진은 API 키 연동 후 사용하세요.")
