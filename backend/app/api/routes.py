from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from io import BytesIO

from app.api.deps import get_current_user
from app.core.security import create_access_token, verify_password
from app.db.session import get_db
from app.models.models import Account, Company, FiscalYear, JournalEntry, Role, Transaction, User
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
from app.services.rule_engine_service import RuleEngineService
from app.services.statement_service import StatementService
from app.services.tax_adjustment_service import TaxAdjustmentService
from app.services.transaction_service import TransactionService

router = APIRouter(prefix="/api")
engine = RuleEngineService("app/rules/account_rules.json")


@router.post("/auth/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == req.username).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return TokenResponse(access_token=create_access_token(user.username))


@router.post("/companies")
def create_company(payload: CompanyCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    company = Company(**payload.model_dump(), created_by=user.username)
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


@router.post("/fiscal-years")
def create_fiscal(payload: FiscalYearCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    fy = FiscalYear(**payload.model_dump(), created_by=user.username)
    db.add(fy)
    db.commit()
    db.refresh(fy)
    return fy


@router.post("/accounts")
def create_account(payload: AccountCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    acc = Account(**payload.model_dump(), active=True, created_by=user.username)
    db.add(acc)
    db.commit()
    db.refresh(acc)
    return acc


@router.get("/accounts")
def list_accounts(company_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return db.query(Account).filter(Account.company_id == company_id, Account.active.is_(True)).all()


@router.post("/transactions")
def create_transaction(payload: TransactionCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    tx = TransactionService.create_transaction_and_suggest(db, payload.model_dump(), engine)
    return tx


@router.get("/transactions")
def list_transactions(company_id: int, fiscal_year_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return db.query(Transaction).filter(Transaction.company_id == company_id, Transaction.fiscal_year_id == fiscal_year_id).all()


@router.get("/journals")
def list_journals(company_id: int, fiscal_year_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return db.query(JournalEntry).filter(JournalEntry.company_id == company_id, JournalEntry.fiscal_year_id == fiscal_year_id).all()


@router.post("/journals/approve")
def approve_journal(payload: JournalApproveRequest, db: Session = Depends(get_db), user=Depends(get_current_user)):
    JournalService.approve_entry(db, payload.journal_entry_id, [x.model_dump() for x in payload.lines])
    return {"ok": True}


@router.get("/ledgers/trial-balance")
def get_trial_balance(company_id: int, fiscal_year_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return StatementService.statements(db, company_id, fiscal_year_id)["trial_balance"]


@router.post("/closing-entries")
def create_closing(payload: ClosingCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return ClosingService.apply_adjustment(db, payload.model_dump())


@router.get("/statements")
def get_statements(company_id: int, fiscal_year_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return StatementService.statements(db, company_id, fiscal_year_id)


@router.post("/tax-adjustments")
def create_tax_adj(payload: TaxAdjustmentCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return TaxAdjustmentService.create(db, payload.model_dump())


@router.get("/tax-adjustments/summary")
def tax_summary(company_id: int, fiscal_year_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return TaxAdjustmentService.summary(db, company_id, fiscal_year_id)


@router.get("/exports/excel")
def export_excel(company_id: int, fiscal_year_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    payload = StatementService.statements(db, company_id, fiscal_year_id)
    data = build_excel(payload)
    return StreamingResponse(
        BytesIO(data),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=filing_support.xlsx"},
    )
