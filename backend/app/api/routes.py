from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.security import create_access_token, verify_password
from app.db.session import get_db
from app.models.models import Account, AuditLog, ClosingEntry, Company, FiscalYear, JournalEntry, JournalEntryLine, TaxAdjustment, Transaction, User
from app.schemas.schemas import (
    AccountCreate,
    ClosingCreate,
    CompanyCreate,
    FiscalYearCreate,
    JournalApproveRequest,
    LoginRequest,
    TaxAdjustmentCreate,
    TokenResponse,
    TransactionCreate,
)
from app.services.closing_service import ClosingService
from app.services.export_service import build_excel
from app.services.journal_service import JournalService
from app.services.ledger_service import LedgerService
from app.services.rule_engine_service import RuleEngineService
from app.services.statement_service import StatementService
from app.services.tax_adjustment_service import TaxAdjustmentService
from app.services.transaction_service import TransactionService

router = APIRouter(prefix="/api")
rule_engine = RuleEngineService("app/rules/account_rules.json")


def add_audit(db: Session, user_id: int | None, action: str, detail: str):
    db.add(AuditLog(user_id=user_id, action=action, detail=detail))
    db.commit()


@router.post("/auth/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == req.username).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    add_audit(db, user.id, "login", "관리자 로그인")
    return TokenResponse(access_token=create_access_token(user.username))


@router.get("/dashboard")
def dashboard(company_id: int, fiscal_year_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    tx_count = db.query(Transaction).filter(Transaction.company_id == company_id, Transaction.fiscal_year_id == fiscal_year_id).count()
    pending = db.query(Transaction).filter(Transaction.company_id == company_id, Transaction.fiscal_year_id == fiscal_year_id, Transaction.status.in_(["new", "suggested", "review_needed"])).count()
    journals = db.query(JournalEntry).filter(JournalEntry.company_id == company_id, JournalEntry.fiscal_year_id == fiscal_year_id, JournalEntry.approved.is_(True)).count()
    return {"transaction_count": tx_count, "pending_review": pending, "approved_journals": journals}


@router.post("/companies")
def create_company(payload: CompanyCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    entity = Company(**payload.model_dump(), created_by=user.username)
    db.add(entity)
    db.commit()
    db.refresh(entity)
    add_audit(db, user.id, "company.create", f"company_id={entity.id}")
    return entity


@router.get("/companies")
def list_companies(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return db.query(Company).all()


@router.post("/fiscal-years")
def create_fiscal(payload: FiscalYearCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    entity = FiscalYear(**payload.model_dump(), created_by=user.username)
    db.add(entity)
    db.commit()
    db.refresh(entity)
    add_audit(db, user.id, "fiscal_year.create", f"fy_id={entity.id}")
    return entity


@router.get("/fiscal-years")
def list_fiscal_years(company_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return db.query(FiscalYear).filter(FiscalYear.company_id == company_id).all()


@router.post("/accounts")
def create_account(payload: AccountCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    entity = Account(**payload.model_dump(), active=True, created_by=user.username)
    db.add(entity)
    db.commit()
    db.refresh(entity)
    return entity


@router.get("/accounts")
def list_accounts(company_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return db.query(Account).filter(Account.company_id == company_id, Account.active.is_(True)).all()


@router.post("/transactions")
def create_transaction(payload: TransactionCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    entity = TransactionService.create_transaction_and_suggest(db, payload.model_dump(), rule_engine, user.username)
    add_audit(db, user.id, "transaction.create", f"tx_id={entity.id}")
    return entity


@router.get("/transactions")
def list_transactions(company_id: int, fiscal_year_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return db.query(Transaction).filter(Transaction.company_id == company_id, Transaction.fiscal_year_id == fiscal_year_id).order_by(Transaction.date.desc()).all()


@router.get("/journals/review")
def journals_for_review(company_id: int, fiscal_year_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    journals = db.query(JournalEntry).filter(JournalEntry.company_id == company_id, JournalEntry.fiscal_year_id == fiscal_year_id, JournalEntry.approved.is_(False)).all()
    result = []
    for je in journals:
        lines = db.query(JournalEntryLine).filter(JournalEntryLine.journal_entry_id == je.id).all()
        result.append({"entry": je, "lines": lines})
    return result


@router.post("/journals/approve")
def approve_journal(payload: JournalApproveRequest, db: Session = Depends(get_db), user=Depends(get_current_user)):
    JournalService.approve_entry(db, payload.journal_entry_id, [x.model_dump() for x in payload.lines])
    add_audit(db, user.id, "journal.approve", f"journal_entry_id={payload.journal_entry_id}")
    return {"ok": True}


@router.get("/ledgers/journal")
def get_journal(company_id: int, fiscal_year_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return LedgerService.journal(db, company_id, fiscal_year_id)


@router.get("/ledgers/general-ledger")
def get_general_ledger(company_id: int, fiscal_year_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return LedgerService.general_ledger(db, company_id, fiscal_year_id)


@router.get("/ledgers/trial-balance")
def get_trial_balance(company_id: int, fiscal_year_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return LedgerService.trial_balance(db, company_id, fiscal_year_id)


@router.post("/closing-entries")
def create_closing(payload: ClosingCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    entity = ClosingService.apply_adjustment(db, payload.model_dump(), user.username)
    add_audit(db, user.id, "closing.create", f"closing_id={entity.id}")
    return entity


@router.get("/closing-entries")
def list_closing(company_id: int, fiscal_year_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return db.query(ClosingEntry).filter(ClosingEntry.company_id == company_id, ClosingEntry.fiscal_year_id == fiscal_year_id).all()


@router.get("/statements")
def get_statements(company_id: int, fiscal_year_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return StatementService.statements(db, company_id, fiscal_year_id)


@router.post("/tax-adjustments")
def create_tax_adjustment(payload: TaxAdjustmentCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    entity = TaxAdjustmentService.create(db, payload.model_dump())
    add_audit(db, user.id, "tax_adjustment.create", f"tax_adjustment_id={entity.id}")
    return entity


@router.get("/tax-adjustments")
def list_tax_adjustments(company_id: int, fiscal_year_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return db.query(TaxAdjustment).filter(TaxAdjustment.company_id == company_id, TaxAdjustment.fiscal_year_id == fiscal_year_id).all()


@router.get("/tax-adjustments/summary")
def tax_summary(company_id: int, fiscal_year_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return TaxAdjustmentService.summary(db, company_id, fiscal_year_id)


@router.get("/rules")
def rules_meta():
    return {
        "account_rules": "app/rules/account_rules.json",
        "account_rules_versions": ["app/rules/account_rules_v1.json"],
        "tax_rules": "app/rules/tax_rules.json",
        "tax_rules_versions": ["app/rules/tax_rules_v1.json"],
        "vat_rules": "app/rules/vat_rules.json",
        "vat_rules_versions": ["app/rules/vat_rules_v1.json"],
    }


@router.get("/audit-logs")
def audit_logs(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return db.query(AuditLog).order_by(AuditLog.id.desc()).limit(200).all()


@router.get("/exports/excel")
def export_excel(company_id: int, fiscal_year_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    payload = StatementService.statements(db, company_id, fiscal_year_id)
    journal_rows = LedgerService.journal(db, company_id, fiscal_year_id)
    general_ledger = LedgerService.general_ledger(db, company_id, fiscal_year_id)
    closing_rows = [r for r in journal_rows if r.get("source") == "closing"]
    tax = TaxAdjustmentService.summary(db, company_id, fiscal_year_id)
    data = build_excel(payload, journal_rows, general_ledger, closing_rows, tax)
    return StreamingResponse(
        BytesIO(data),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=corporate_tax_support.xlsx"},
    )
