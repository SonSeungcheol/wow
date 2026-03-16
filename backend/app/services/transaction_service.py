from sqlalchemy.orm import Session

from app.models.models import Transaction
from app.services.journal_service import JournalService
from app.services.rule_engine_service import RuleEngineService


class TransactionService:
    @staticmethod
    def create_transaction_and_suggest(db: Session, payload: dict, engine: RuleEngineService, created_by: str):
        tx = Transaction(**payload, status="new", created_by=created_by)
        db.add(tx)
        db.commit()
        db.refresh(tx)
        suggestion = engine.suggest(f"{tx.vendor} {tx.description} {tx.memo}", tx.payment_method, tx.date)
        JournalService.create_suggestion_entry(db, tx, suggestion)
        db.refresh(tx)
        return tx
