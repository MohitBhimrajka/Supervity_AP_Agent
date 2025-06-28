# src/app/api/dependencies.py
from app.db.session import SessionLocal

def get_db():
    """
    FastAPI dependency that provides a database session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 