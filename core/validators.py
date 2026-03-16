"""Validation rules for transactions and journal entries."""
from __future__ import annotations


def validate_transaction_payload(payload: dict) -> list[str]:
    errors: list[str] = []
    required = ["date", "vendor", "description", "amount", "payment_method"]
    for field in required:
        if payload.get(field) in (None, ""):
            errors.append(f"필수값 누락: {field}")

    amount = payload.get("amount", 0)
    if isinstance(amount, (int, float)):
        if amount <= 0:
            errors.append("금액은 0보다 커야 합니다.")
    else:
        errors.append("금액 형식이 올바르지 않습니다.")
    return errors


def validate_journal_balance(debit_amount: float, credit_amount: float) -> None:
    if round(float(debit_amount), 2) != round(float(credit_amount), 2):
        raise ValueError("차변/대변 금액이 일치하지 않습니다.")
