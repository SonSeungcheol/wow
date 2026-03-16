import pytest

from core.validators import validate_journal_balance, validate_transaction_payload


def test_validate_transaction_payload_required_fields():
    payload = {
        "date": "2026-01-01",
        "vendor": "",
        "description": "",
        "amount": 0,
        "payment_method": "",
    }
    errors = validate_transaction_payload(payload)
    assert any("vendor" in e for e in errors)
    assert any("description" in e for e in errors)
    assert any("금액은 0보다 커야" in e for e in errors)


def test_validate_journal_balance_raises_on_mismatch():
    with pytest.raises(ValueError):
        validate_journal_balance(10000, 9000)
