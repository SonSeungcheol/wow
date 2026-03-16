"""Dataclasses for transactions and journal suggestions."""
from dataclasses import dataclass


@dataclass
class TransactionInput:
    date: str
    vendor: str
    description: str
    amount: float
    payment_method: str
    vat_included: bool
    memo: str = ""


@dataclass
class JournalSuggestion:
    debit_account: str
    credit_account: str
    amount: float
    explanation: str
    review_points: str
    status: str
