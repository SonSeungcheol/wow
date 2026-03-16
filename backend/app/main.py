from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.api.routes import router
from app.core.security import get_password_hash
from app.db.session import engine, SessionLocal
from app.models.base import Base
from app.models.models import Role, User

app = FastAPI(title="KR Closing & Corporate Tax Assistant")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()
    try:
        admin_role = db.query(Role).filter(Role.name == "admin").first()
        if not admin_role:
            admin_role = Role(name="admin", created_by="system")
            db.add(admin_role)
            db.flush()
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            db.add(User(username="admin", password_hash=get_password_hash("admin1234"), role_id=admin_role.id, created_by="system"))
        db.commit()
    finally:
        db.close()


app.include_router(router)


@app.get("/")
def health():
    return {"status": "ok"}
