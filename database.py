import os
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Get DATABASE_URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")

# Railway gives us postgres:// but SQLAlchemy needs postgresql://
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Fallback to SQLite for local development
if not DATABASE_URL:
    DATABASE_URL = "sqlite:///./ai_monitor.db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class ApiCheck(Base):
    """Store API check results"""
    __tablename__ = "api_checks"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Provider info
    provider = Column(String, index=True)
    model = Column(String)
    
    # Performance
    latency_ms = Column(Float)
    success = Column(Boolean)
    
    # Error tracking
    error_message = Column(Text, nullable=True)

def init_db():
    """Create database tables"""
    Base.metadata.create_all(bind=engine)
    print("✅ Database initialized")

if __name__ == "__main__":
    init_db()