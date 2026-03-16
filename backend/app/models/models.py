from datetime import datetime

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by: Mapped[str | None] = mapped_column(String(100), nullable=True)


class Role(Base, TimestampMixin):
    __tablename__ = "roles"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)


class User(Base, TimestampMixin):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(100), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"))
    role = relationship("Role")


class Company(Base, TimestampMixin):
    __tablename__ = "companies"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    business_number: Mapped[str] = mapped_column(String(30), unique=True)


class FiscalYear(Base, TimestampMixin):
    __tablename__ = "fiscal_years"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))
    start_date: Mapped[datetime] = mapped_column(Date)
    end_date: Mapped[datetime] = mapped_column(Date)
    is_closed: Mapped[bool] = mapped_column(Boolean, default=False)


class Account(Base, TimestampMixin):
    __tablename__ = "accounts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))
    code: Mapped[str] = mapped_column(String(20))
    name: Mapped[str] = mapped_column(String(100))
    type: Mapped[str] = mapped_column(String(20))
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class Transaction(Base, TimestampMixin):
    __tablename__ = "transactions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))
    fiscal_year_id: Mapped[int] = mapped_column(ForeignKey("fiscal_years.id"))
    date: Mapped[datetime] = mapped_column(Date)
    vendor: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(String(300))
    amount: Mapped[float] = mapped_column(Float)
    vat_included: Mapped[bool] = mapped_column(Boolean, default=True)
    supply_amount: Mapped[float] = mapped_column(Float, default=0)
    vat_amount: Mapped[float] = mapped_column(Float, default=0)
    payment_method: Mapped[str] = mapped_column(String(50))
    evidence_type: Mapped[str] = mapped_column(String(50))
    memo: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(30), default="new")


class JournalEntry(Base, TimestampMixin):
    __tablename__ = "journal_entries"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    transaction_id: Mapped[int | None] = mapped_column(ForeignKey("transactions.id"), nullable=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))
    fiscal_year_id: Mapped[int] = mapped_column(ForeignKey("fiscal_years.id"))
    date: Mapped[datetime] = mapped_column(Date)
    description: Mapped[str] = mapped_column(String(300))
    approved: Mapped[bool] = mapped_column(Boolean, default=False)
    source: Mapped[str] = mapped_column(String(30), default="transaction")
    lines = relationship("JournalEntryLine", cascade="all, delete-orphan", back_populates="entry")


class JournalEntryLine(Base, TimestampMixin):
    __tablename__ = "journal_entry_lines"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    journal_entry_id: Mapped[int] = mapped_column(ForeignKey("journal_entries.id"))
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"))
    debit: Mapped[float] = mapped_column(Float, default=0)
    credit: Mapped[float] = mapped_column(Float, default=0)
    memo: Mapped[str] = mapped_column(String(200), default="")
    entry = relationship("JournalEntry", back_populates="lines")
    account = relationship("Account")


class ClosingEntry(Base, TimestampMixin):
    __tablename__ = "closing_entries"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))
    fiscal_year_id: Mapped[int] = mapped_column(ForeignKey("fiscal_years.id"))
    adjustment_type: Mapped[str] = mapped_column(String(50))
    amount: Mapped[float] = mapped_column(Float)
    description: Mapped[str] = mapped_column(String(300))


class FinancialStatement(Base, TimestampMixin):
    __tablename__ = "financial_statements"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))
    fiscal_year_id: Mapped[int] = mapped_column(ForeignKey("fiscal_years.id"))
    statement_type: Mapped[str] = mapped_column(String(50))
    payload_json: Mapped[str] = mapped_column(Text)


class TaxAdjustment(Base, TimestampMixin):
    __tablename__ = "tax_adjustments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))
    fiscal_year_id: Mapped[int] = mapped_column(ForeignKey("fiscal_years.id"))
    category: Mapped[str] = mapped_column(String(30))
    reserve_type: Mapped[str] = mapped_column(String(20))
    description: Mapped[str] = mapped_column(String(300))


class TaxAdjustmentLine(Base, TimestampMixin):
    __tablename__ = "tax_adjustment_lines"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tax_adjustment_id: Mapped[int] = mapped_column(ForeignKey("tax_adjustments.id"))
    amount: Mapped[float] = mapped_column(Float)


class ExportJob(Base, TimestampMixin):
    __tablename__ = "export_jobs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))
    fiscal_year_id: Mapped[int] = mapped_column(ForeignKey("fiscal_years.id"))
    file_path: Mapped[str] = mapped_column(String(400))


class AuditLog(Base, TimestampMixin):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(100))
    detail: Mapped[str] = mapped_column(Text)
