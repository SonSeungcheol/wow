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
    def journal(db: Session, company_id: int, fiscal_year_id: int):
        rows = []
        for line, je, account in LedgerService.approved_lines(db, company_id, fiscal_year_id):
            rows.append({
                "date": str(je.date),
                "entry_id": je.id,
                "description": je.description,
                "account": account.name,
                "debit": line.debit,
                "credit": line.credit,
                "source": je.source,
            })
        return rows

    @staticmethod
    def general_ledger(db: Session, company_id: int, fiscal_year_id: int):
        ledger = defaultdict(list)
        balance = defaultdict(float)
        for row in sorted(LedgerService.journal(db, company_id, fiscal_year_id), key=lambda x: (x["account"], x["date"], x["entry_id"])):
            balance[row["account"]] += row["debit"] - row["credit"]
            row["balance"] = round(balance[row["account"]], 2)
            ledger[row["account"]].append(row)
        return dict(ledger)

    @staticmethod
    def trial_balance(db: Session, company_id: int, fiscal_year_id: int):
        agg = defaultdict(lambda: {"debit": 0.0, "credit": 0.0, "type": ""})
        for line, _, account in LedgerService.approved_lines(db, company_id, fiscal_year_id):
            agg[account.name]["debit"] += line.debit
            agg[account.name]["credit"] += line.credit
            agg[account.name]["type"] = account.type
        return dict(agg)
