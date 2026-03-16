"""AI engine interface for journal suggestions."""
from __future__ import annotations

from abc import ABC, abstractmethod


class BaseJournalEngine(ABC):
    @abstractmethod
    def suggest(self, transaction: dict) -> dict:
        """Return debit/credit suggestion for a transaction."""
