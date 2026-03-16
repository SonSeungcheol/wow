from datetime import date

import pytest

from app.models.models import JournalEntry, JournalEntryLine
from app.services.closing_service import ClosingService
from app.services.export_service import build_excel
from app.services.journal_service import JournalService
from app.services.ledger_service import LedgerService
from app.services.rule_engine_service import RuleEngineService
from app.services.statement_service import StatementService
from app.services.tax_adjustment_service import TaxAdjustmentService
from app.services.transaction_service import TransactionService


def tx_payload(desc: str = "인스타 광고"):
    return {
        "company_id": 1,
        "fiscal_year_id": 1,
        "date": date(2026, 1, 2),
        "vendor": "메타",
        "description": desc,
        "amount": 110000,
        "vat_included": True,
        "supply_amount": 100000,
        "vat_amount": 10000,
        "payment_method": "보통예금",
        "evidence_type": "세금계산서",
        "memo": "",
    }


def test_rule_match():
    s = RuleEngineService("app/rules/account_rules.json").suggest("메타 광고", "보통예금", date(2026, 1, 1))
    assert s["debit_account"] == "광고선전비"


def test_rule_fallback_review_needed():
    s = RuleEngineService("app/rules/account_rules.json").suggest("불명확", "외상", date(2026, 1, 1))
    assert s["debit_account"] == "검토필요" and s["credit_account"] == "미지급금"


def test_create_transaction_and_suggestion(db_session):
    engine = RuleEngineService("app/rules/account_rules.json")
    tx = TransactionService.create_transaction_and_suggest(db_session, tx_payload(), engine, "admin")
    assert tx.status in ("suggested", "review_needed")


def test_journal_balance_error(db_session):
    je = JournalEntry(company_id=1, fiscal_year_id=1, date=date(2026, 1, 2), description="x", approved=False)
    db_session.add(je)
    db_session.commit()
    with pytest.raises(ValueError):
        JournalService.approve_entry(db_session, je.id, [{"account_id": 1, "debit": 1000, "credit": 0}, {"account_id": 2, "debit": 0, "credit": 900}])


def test_journal_approve_success(db_session):
    je = JournalEntry(company_id=1, fiscal_year_id=1, date=date(2026, 1, 2), description="x", approved=False)
    db_session.add(je)
    db_session.commit()
    JournalService.approve_entry(db_session, je.id, [{"account_id": 1, "debit": 1000, "credit": 0}, {"account_id": 2, "debit": 0, "credit": 1000}])
    refreshed = db_session.query(JournalEntry).filter(JournalEntry.id == je.id).first()
    assert refreshed and refreshed.approved is True


def test_trial_balance(db_session):
    je = JournalEntry(company_id=1, fiscal_year_id=1, date=date(2026, 1, 2), description="x", approved=True)
    db_session.add(je)
    db_session.flush()
    db_session.add_all([
        JournalEntryLine(journal_entry_id=je.id, account_id=1, debit=1000, credit=0),
        JournalEntryLine(journal_entry_id=je.id, account_id=11, debit=0, credit=1000),
    ])
    db_session.commit()
    tb = LedgerService.trial_balance(db_session, 1, 1)
    assert tb["보통예금"]["debit"] == 1000


def test_income_statement():
    tb = {"매출": {"debit": 0, "credit": 1000, "type": "수익"}, "광고선전비": {"debit": 300, "credit": 0, "type": "비용"}}
    pl = StatementService.income_statement(tb)
    assert pl["net_income"] == 700


def test_balance_sheet_equation():
    tb = {"보통예금": {"debit": 1000, "credit": 0, "type": "자산"}, "자본금": {"debit": 0, "credit": 900, "type": "자본"}, "미지급금": {"debit": 0, "credit": 100, "type": "부채"}}
    bs = StatementService.balance_sheet(tb, 0)
    assert bs["assets"] == bs["liabilities_and_equity"]


def test_closing_creates_entry(db_session):
    ClosingService.apply_adjustment(db_session, {"company_id": 1, "fiscal_year_id": 1, "adjustment_type": "감가상각", "amount": 500, "description": "감가"}, "admin")
    assert db_session.query(JournalEntry).filter(JournalEntry.source == "closing").count() == 1


def test_tax_adjustment_summary(db_session):
    TaxAdjustmentService.create(db_session, {"company_id": 1, "fiscal_year_id": 1, "category": "손금불산입", "reserve_type": "유보", "description": "접대비", "amount": 300})
    summary = TaxAdjustmentService.summary(db_session, 1, 1)
    assert summary["손금불산입:유보"] == 300


def test_export_build_bytes():
    content = build_excel(
        {"trial_balance": {}, "income_statement": {}, "balance_sheet": {}, "retained_earnings": {}, "cashflow": {}},
        [],
        {},
        [],
        {},
    )
    assert isinstance(content, bytes)
