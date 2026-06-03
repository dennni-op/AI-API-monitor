import os
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

monitor_type = os.getenv("MONITOR_TYPE", "main")

if monitor_type == "customer":
    DATABASE_URL = os.getenv("DATABASE_URL_CUSTOMER")
else:
    DATABASE_URL = os.getenv("DATABASE_URL")

# If DATABASE_URL is not set, fall back to SQLite
if not DATABASE_URL:
    DATABASE_URL = "sqlite:///./api_monitor.db"

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
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
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        raise

if __name__ == "__main__":
    init_db()