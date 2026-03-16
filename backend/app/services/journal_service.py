from sqlalchemy.orm import Session

from app.models.models import Account, JournalEntry, JournalEntryLine, Transaction


def _check_balance(lines: list[dict]):
    debit = round(sum(l.get("debit", 0) for l in lines), 2)
    credit = round(sum(l.get("credit", 0) for l in lines), 2)
    if debit != credit:
        raise ValueError("차변 합계와 대변 합계가 일치하지 않습니다")


class JournalService:
    @staticmethod
    def create_suggestion_entry(db: Session, tx: Transaction, debit_name: str, credit_name: str):
        debit_acc = db.query(Account).filter(Account.company_id == tx.company_id, Account.name == debit_name).first()
        credit_acc = db.query(Account).filter(Account.company_id == tx.company_id, Account.name == credit_name).first()
        if not debit_acc or not credit_acc:
            tx.status = "review_needed"
            db.commit()
            return None
        entry = JournalEntry(
            transaction_id=tx.id,
            company_id=tx.company_id,
            fiscal_year_id=tx.fiscal_year_id,
            date=tx.date,
            description=tx.description,
            approved=False,
            source="transaction",
        )
        db.add(entry)
        db.flush()
        db.add_all([
            JournalEntryLine(journal_entry_id=entry.id, account_id=debit_acc.id, debit=tx.amount, credit=0),
            JournalEntryLine(journal_entry_id=entry.id, account_id=credit_acc.id, debit=0, credit=tx.amount),
        ])
        tx.status = "suggested"
        db.commit()
        return entry

    @staticmethod
    def approve_entry(db: Session, entry_id: int, lines: list[dict]):
        _check_balance(lines)
        entry = db.query(JournalEntry).filter(JournalEntry.id == entry_id).first()
        if not entry:
            raise ValueError("분개가 존재하지 않습니다")
        db.query(JournalEntryLine).filter(JournalEntryLine.journal_entry_id == entry_id).delete()
        for l in lines:
            db.add(JournalEntryLine(journal_entry_id=entry_id, account_id=l["account_id"], debit=l["debit"], credit=l["credit"], memo=l.get("memo", "")))
        entry.approved = True
        if entry.transaction_id:
            tx = db.query(Transaction).filter(Transaction.id == entry.transaction_id).first()
            tx.status = "approved"
        db.commit()
