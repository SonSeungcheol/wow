from datetime import date
import pytest

from app.models.models import Account, JournalEntry, JournalEntryLine
from app.services.closing_service import ClosingService
from app.services.journal_service import JournalService
from app.services.rule_engine_service import RuleEngineService
from app.services.statement_service import StatementService
from app.services.tax_adjustment_service import TaxAdjustmentService
from app.services.transaction_service import TransactionService


def _base_tx():
    return {
        "company_id": 1, "fiscal_year_id": 1, "date": date(2026, 1, 2), "vendor": "메타", "description": "인스타 광고",
        "amount": 110000, "vat_included": True, "supply_amount": 100000, "vat_amount": 10000,
        "payment_method": "보통예금", "evidence_type": "세금계산서", "memo": ""
    }


def test_rule_engine_keyword_match():
    eng = RuleEngineService("app/rules/account_rules.json")
    debit, credit, version = eng.suggest_accounts("메타 광고 집행", "보통예금", date(2026, 1, 1))
    assert debit == "광고선전비" and credit == "보통예금" and version == "2026.1"


def test_rule_engine_unknown_goes_review():
    eng = RuleEngineService("app/rules/account_rules.json")
    debit, credit, _ = eng.suggest_accounts("분류불명 거래", "외상", date(2026, 1, 1))
    assert debit == "검토필요" and credit == "미지급금"


def test_transaction_creates_suggestion(db_session):
    eng = RuleEngineService("app/rules/account_rules.json")
    tx = TransactionService.create_transaction_and_suggest(db_session, _base_tx(), eng)
    assert tx.status == "suggested"


def test_journal_approve_balance_error(db_session):
    je = JournalEntry(company_id=1, fiscal_year_id=1, date=date(2026, 1, 2), description="x", approved=False)
    db_session.add(je); db_session.commit(); db_session.refresh(je)
    with pytest.raises(ValueError):
        JournalService.approve_entry(db_session, je.id, [{"account_id":1,"debit":1000,"credit":0},{"account_id":2,"debit":0,"credit":900}])


def test_journal_approve_success(db_session):
    je = JournalEntry(company_id=1, fiscal_year_id=1, date=date(2026, 1, 2), description="x", approved=False)
    db_session.add(je); db_session.commit(); db_session.refresh(je)
    JournalService.approve_entry(db_session, je.id, [{"account_id":1,"debit":1000,"credit":0},{"account_id":2,"debit":0,"credit":1000}])
    assert db_session.query(JournalEntry).get(je.id).approved is True


def test_trial_balance_generated(db_session):
    je = JournalEntry(company_id=1, fiscal_year_id=1, date=date(2026, 1, 2), description="x", approved=True)
    db_session.add(je); db_session.flush()
    db_session.add_all([JournalEntryLine(journal_entry_id=je.id, account_id=1, debit=1000, credit=0), JournalEntryLine(journal_entry_id=je.id, account_id=5, debit=0, credit=1000)])
    db_session.commit()
    tb = StatementService.statements(db_session, 1, 1)["trial_balance"]
    assert "보통예금" in tb


def test_income_statement_logic():
    tb = {"매출":{"debit":0,"credit":1000,"type":"수익"}, "광고선전비":{"debit":400,"credit":0,"type":"비용"}}
    pl = StatementService.income_statement(tb)
    assert pl["net_income"] == 600


def test_balance_sheet_equation():
    tb = {"보통예금":{"debit":1000,"credit":0,"type":"자산"}, "자본금":{"debit":0,"credit":800,"type":"자본"}, "미지급금":{"debit":0,"credit":100,"type":"부채"}}
    bs = StatementService.balance_sheet(tb, 100)
    assert bs["assets"] == bs["liabilities_and_equity"]


def test_closing_entry_creates_journal(db_session):
    ClosingService.apply_adjustment(db_session, {"company_id":1,"fiscal_year_id":1,"adjustment_type":"감가상각","amount":500,"description":"감가"})
    assert db_session.query(JournalEntry).filter(JournalEntry.source=="closing").count() == 1


def test_tax_adjustment_summary(db_session):
    TaxAdjustmentService.create(db_session, {"company_id":1,"fiscal_year_id":1,"category":"손금불산입","reserve_type":"유보","description":"접대비","amount":300})
    s = TaxAdjustmentService.summary(db_session,1,1)
    assert s["손금불산입:유보"] == 300
