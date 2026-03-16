from collections import defaultdict
from sqlalchemy.orm import Session
from app.models.models import Account, JournalEntry, JournalEntryLine


class LedgerService:
    @staticmethod
    def approved_lines(db: Session, company_id: int, fiscal_year_id: int):
        return (
            db.query(JournalEntryLine, JournalEntry, Account)
            .join(JournalEntry, JournalEntry.id == JournalEntryLine.journal_entry_id)
            .join(Account, Account.id == JournalEntryLine.account_id)
            .filter(JournalEntry.company_id == company_id, JournalEntry.fiscal_year_id == fiscal_year_id, JournalEntry.approved.is_(True))
            .all()
        )

    @staticmethod
    def trial_balance(db: Session, company_id: int, fiscal_year_id: int):
        agg = defaultdict(lambda: {"debit": 0.0, "credit": 0.0, "type": ""})
        for line, _, account in LedgerService.approved_lines(db, company_id, fiscal_year_id):
            agg[account.name]["debit"] += line.debit
            agg[account.name]["credit"] += line.credit
            agg[account.name]["type"] = account.type
        return agg
