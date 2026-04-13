# Service Layer
# Business logic lives here (NOT in API)
# Service functions that operate on User using a SQLAlchemy Session and
# your settings if needed:
# src/myapp/services/user_service.py
import os
from typing import List, Optional

from sqlalchemy.orm import Session

from myapp.metrics import DB_ERRORS_TOTAL
from myapp.models import db_models
from myapp.models.schemas import UserCreate, UserRead

# DI: db is injected from FastAPI via Depends(get_db).
# settings is available if you need env‑specific behavior (e.g., feature flags,
# logging decisions).

APP_ENV = os.getenv("APP_ENV", "dev")


def get_user(db: Session, user_id: int) -> Optional[UserRead]:
    try:
        user = db.get(db_models.User, user_id)
        if not user:
            return None
        return UserRead.model_validate(user)
    except Exception:
        DB_ERRORS_TOTAL.labels(operation="get_user", app_env=APP_ENV).inc()
        raise


def list_users(db: Session, limit: int = 100) -> List[UserRead]:
    try:
        users = db.query(db_models.User).limit(limit).all()
        return [UserRead.model_validate(u) for u in users]
    except Exception:
        DB_ERRORS_TOTAL.labels(operation="list_users", app_env=APP_ENV).inc()
        raise


def create_user(db: Session, user_in: UserCreate) -> UserRead:
    try:
        user = db_models.User(email=user_in.email, name=user_in.name)
        db.add(user)
        db.commit()
        db.refresh(user)
        # You could log or branch behavior based on settings.app_env if needed
        # e.g., if settings.app_env == "staging": ...
        return UserRead.model_validate(user)
    except Exception:
        DB_ERRORS_TOTAL.labels(operation="create_user", app_env=APP_ENV).inc()
        raise
