from sqlalchemy.orm import Session

from app.models.models import Transaction
from app.services.journal_service import JournalService
from app.services.rule_engine_service import RuleEngineService


class TransactionService:
    @staticmethod
    def create_transaction_and_suggest(db: Session, payload: dict, engine: RuleEngineService):
        tx = Transaction(**payload, status="new")
        db.add(tx)
        db.commit()
        db.refresh(tx)
        d, c, _ = engine.suggest_accounts(f"{tx.vendor} {tx.description} {tx.memo}", tx.payment_method, tx.date)
        JournalService.create_suggestion_entry(db, tx, d, c)
        db.refresh(tx)
        return tx
