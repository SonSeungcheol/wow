from sqlalchemy.orm import Session
from app.models.models import ClosingEntry, JournalEntry, JournalEntryLine, Account


CLOSING_MAP = {
    "감가상각": ("감가상각비", "감가상각누계액"),
    "선급비용": ("선급비용", "비용"),
    "미지급비용": ("비용", "미지급금"),
    "선수수익": ("수익", "선수수익"),
    "미수수익": ("미수수익", "수익"),
    "재고조정": ("매출원가", "원재료"),
    "가수금정리": ("가수금", "보통예금"),
}


class ClosingService:
    @staticmethod
    def apply_adjustment(db: Session, payload: dict):
        ce = ClosingEntry(**payload)
        db.add(ce)
        debit_name, credit_name = CLOSING_MAP.get(payload["adjustment_type"], ("검토필요", "검토필요"))
        debit_acc = db.query(Account).filter(Account.company_id == payload["company_id"], Account.name == debit_name).first()
        credit_acc = db.query(Account).filter(Account.company_id == payload["company_id"], Account.name == credit_name).first()
        if debit_acc and credit_acc:
            je = JournalEntry(company_id=payload["company_id"], fiscal_year_id=payload["fiscal_year_id"], date="2026-12-31", description=payload["description"], approved=True, source="closing")
            db.add(je)
            db.flush()
            db.add_all([
                JournalEntryLine(journal_entry_id=je.id, account_id=debit_acc.id, debit=payload["amount"], credit=0),
                JournalEntryLine(journal_entry_id=je.id, account_id=credit_acc.id, debit=0, credit=payload["amount"]),
            ])
        db.commit()
        return ce
