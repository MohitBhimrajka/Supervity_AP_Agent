# database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.models import Base

# The database URL for a local SQLite file
SQLALCHEMY_DATABASE_URL = "sqlite:///./ap_data.db"

# The engine is the main point of contact with the DB
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# A SessionLocal class to create DB sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_db_and_tables():
    # This function creates all the tables defined in models.py
    # This now includes the new Job and AuditLog tables
    print("Creating all database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully.") 