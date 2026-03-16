from datetime import date
from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class CompanyCreate(BaseModel):
    name: str
    business_number: str


class FiscalYearCreate(BaseModel):
    company_id: int
    start_date: date
    end_date: date


class AccountCreate(BaseModel):
    company_id: int
    code: str
    name: str
    type: str


class TransactionCreate(BaseModel):
    company_id: int
    fiscal_year_id: int
    date: date
    vendor: str
    description: str
    amount: float
    vat_included: bool
    supply_amount: float
    vat_amount: float
    payment_method: str
    evidence_type: str
    memo: str = ""


class JournalLineInput(BaseModel):
    account_id: int
    debit: float = 0
    credit: float = 0
    memo: str = ""


class JournalApproveRequest(BaseModel):
    journal_entry_id: int
    lines: list[JournalLineInput]


class ClosingCreate(BaseModel):
    company_id: int
    fiscal_year_id: int
    adjustment_type: str
    amount: float
    description: str


class TaxAdjustmentCreate(BaseModel):
    company_id: int
    fiscal_year_id: int
    category: str
    reserve_type: str
    description: str
    amount: float
