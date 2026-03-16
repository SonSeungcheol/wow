from collections import defaultdict
from sqlalchemy.orm import Session

from app.models.models import TaxAdjustment, TaxAdjustmentLine


class TaxAdjustmentService:
    @staticmethod
    def create(db: Session, payload: dict):
        ta = TaxAdjustment(
            company_id=payload["company_id"],
            fiscal_year_id=payload["fiscal_year_id"],
            category=payload["category"],
            reserve_type=payload["reserve_type"],
            description=payload["description"],
        )
        db.add(ta)
        db.flush()
        db.add(TaxAdjustmentLine(tax_adjustment_id=ta.id, amount=payload["amount"]))
        db.commit()
        return ta

    @staticmethod
    def summary(db: Session, company_id: int, fiscal_year_id: int):
        rows = (
            db.query(TaxAdjustment, TaxAdjustmentLine)
            .join(TaxAdjustmentLine, TaxAdjustment.id == TaxAdjustmentLine.tax_adjustment_id)
            .filter(TaxAdjustment.company_id == company_id, TaxAdjustment.fiscal_year_id == fiscal_year_id)
            .all()
        )
        agg = defaultdict(float)
        for ta, line in rows:
            agg[f"{ta.category}:{ta.reserve_type}"] += line.amount
        return dict(agg)
