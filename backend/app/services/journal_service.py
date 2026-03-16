from sqlalchemy.orm import Session

from app.models.models import Account, JournalEntry, JournalEntryLine, Transaction


class JournalService:
    @staticmethod
    def validate_lines(lines: list[dict]) -> None:
        debit = round(sum(float(l.get("debit", 0)) for l in lines), 2)
        credit = round(sum(float(l.get("credit", 0)) for l in lines), 2)
        if debit <= 0 or credit <= 0 or debit != credit:
            raise ValueError("차변 합계와 대변 합계가 일치해야 하며 0보다 커야 합니다")

    @staticmethod
    def create_suggestion_entry(db: Session, tx: Transaction, suggestion: dict):
        debit_acc = db.query(Account).filter(Account.company_id == tx.company_id, Account.name == suggestion["debit_account"]).first()
        credit_acc = db.query(Account).filter(Account.company_id == tx.company_id, Account.name == suggestion["credit_account"]).first()
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
            explanation=suggestion["explanation"],
            review_points=suggestion["review_points"],
            confidence=suggestion["confidence"],
            approved=False,
            source="transaction",
            created_by=tx.created_by,
        )
        db.add(entry)
        db.flush()
        db.add_all([
            JournalEntryLine(journal_entry_id=entry.id, account_id=debit_acc.id, debit=tx.amount, credit=0, created_by=tx.created_by),
            JournalEntryLine(journal_entry_id=entry.id, account_id=credit_acc.id, debit=0, credit=tx.amount, created_by=tx.created_by),
        ])
        tx.status = "suggested" if suggestion["confidence"] >= 0.7 else "review_needed"
        db.commit()
        return entry

    @staticmethod
    def approve_entry(db: Session, entry_id: int, lines: list[dict]):
        JournalService.validate_lines(lines)
        entry = db.query(JournalEntry).filter(JournalEntry.id == entry_id).first()
        if not entry:
            raise ValueError("분개가 존재하지 않습니다")
        db.query(JournalEntryLine).filter(JournalEntryLine.journal_entry_id == entry_id).delete()
        for line in lines:
            db.add(
                JournalEntryLine(
                    journal_entry_id=entry_id,
                    account_id=line["account_id"],
                    debit=float(line.get("debit", 0)),
                    credit=float(line.get("credit", 0)),
                    memo=line.get("memo", ""),
                )
            )
        entry.approved = True
        if entry.transaction_id:
            tx = db.query(Transaction).filter(Transaction.id == entry.transaction_id).first()
            if tx:
                tx.status = "approved"
        db.commit()
