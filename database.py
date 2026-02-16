# database.py
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Use SQLite (simple, local database)
DATABASE_URL = "sqlite:///ai_monitor.db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class ApiCheck(Base):
    """Store API check results"""
    __tablename__ = "api_checks"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Provider info
    provider = Column(String, index=True)  # 'google', 'anthropic', 'openai'
    model = Column(String)
    
    # Performance
    latency_ms = Column(Float)
    success = Column(Boolean)
    
    # Error tracking
    error_message = Column(String, nullable=True)

def init_db():
    """Create database tables"""
    Base.metadata.create_all(bind=engine)
    print("✅ Database initialized: ai_monitor.db")

if __name__ == "__main__":
    init_db()