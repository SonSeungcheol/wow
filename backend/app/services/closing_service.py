from datetime import date

from sqlalchemy.orm import Session

from app.models.models import Account, ClosingEntry, ClosingEntryLine, JournalEntry, JournalEntryLine, Transaction


CLOSING_MAP = {
    "감가상각": ("감가상각비", "감가상각누계액"),
    "선급비용": ("선급비용", "지급수수료"),
    "미지급비용": ("지급수수료", "미지급금"),
    "선수수익": ("매출", "선수수익"),
    "미수수익": ("미수수익", "매출"),
    "재고조정": ("매출원가", "원재료"),
    "가수금정리": ("가수금", "보통예금"),
    "가지급금정리": ("보통예금", "가지급금"),
}


class ClosingService:
    @staticmethod
    def apply_adjustment(db: Session, payload: dict, created_by: str):
        ce = ClosingEntry(**payload, created_by=created_by)
        db.add(ce)
        db.flush()

        debit_name, credit_name = CLOSING_MAP.get(payload["adjustment_type"], ("검토필요", "검토필요"))
        debit_acc = db.query(Account).filter(Account.company_id == payload["company_id"], Account.name == debit_name).first()
        credit_acc = db.query(Account).filter(Account.company_id == payload["company_id"], Account.name == credit_name).first()

        if debit_acc and credit_acc:
            db.add_all([
                ClosingEntryLine(closing_entry_id=ce.id, account_id=debit_acc.id, debit=payload["amount"], credit=0, created_by=created_by),
                ClosingEntryLine(closing_entry_id=ce.id, account_id=credit_acc.id, debit=0, credit=payload["amount"], created_by=created_by),
            ])
            je = JournalEntry(
                company_id=payload["company_id"],
                fiscal_year_id=payload["fiscal_year_id"],
                date=date.fromisoformat(f"{date.today().year}-12-31"),
                description=payload["description"],
                explanation=f"결산조정: {payload['adjustment_type']}",
                review_points="결산근거 검토",
                confidence=1.0,
                approved=True,
                source="closing",
                created_by=created_by,
            )
            db.add(je)
            db.flush()
            db.add_all([
                JournalEntryLine(journal_entry_id=je.id, account_id=debit_acc.id, debit=payload["amount"], credit=0, created_by=created_by),
                JournalEntryLine(journal_entry_id=je.id, account_id=credit_acc.id, debit=0, credit=payload["amount"], created_by=created_by),
            ])
        db.query(Transaction).filter(
            Transaction.company_id == payload["company_id"],
            Transaction.fiscal_year_id == payload["fiscal_year_id"],
            Transaction.status == "approved",
        ).update({"status": "closing_reflected"}, synchronize_session=False)
        db.commit()
        return ce
