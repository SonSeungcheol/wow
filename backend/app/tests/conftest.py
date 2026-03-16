import os
import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///./test.db"

from app.models.base import Base
from app.models.models import Account, Company, FiscalYear, Role, User
from app.core.security import get_password_hash


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    role = Role(name="admin", created_by="test")
    db.add(role)
    db.flush()
    db.add(User(username="admin", password_hash=get_password_hash("admin1234"), role_id=role.id, created_by="test"))
    c = Company(name="테스트", business_number="111-11-11111", created_by="test")
    db.add(c)
    db.flush()
    fy = FiscalYear(company_id=c.id, start_date="2026-01-01", end_date="2026-12-31", created_by="test")
    db.add(fy)
    db.flush()
    accounts = [
        ("101", "보통예금", "자산"), ("201", "미지급금", "부채"), ("202", "가수금", "부채"),
        ("401", "매출", "수익"), ("501", "광고선전비", "비용"), ("502", "운반비", "비용"),
        ("503", "지급수수료", "비용"), ("150", "원재료", "자산"), ("504", "복리후생비", "비용"),
        ("999", "검토필요", "비용"), ("505", "감가상각비", "비용"), ("109", "감가상각누계액", "자산"),
        ("110", "선급비용", "자산"), ("111", "미수수익", "자산"), ("210", "선수수익", "부채"), ("506", "매출원가", "비용")
    ]
    for code, name, typ in accounts:
        db.add(Account(company_id=c.id, code=code, name=name, type=typ, active=True, created_by="test"))
    db.commit()
    yield db
    db.close()
