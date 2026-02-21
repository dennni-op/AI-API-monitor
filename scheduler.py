import schedule
import time
from datetime import datetime
import os
from dotenv import load_dotenv

# Import your monitoring functions
from google import genai
import anthropic
import openai

from database import SessionLocal, ApiCheck, init_db

load_dotenv()

# PRINT DATABASE INFO (for debugging)
db_url = os.getenv("DATABASE_URL", "Not set")
if db_url.startswith("postgresql://"):
    print("✅ Using PostgreSQL database")
elif db_url.startswith("sqlite"):
    print("⚠️ Using SQLite database")
else:
    print(f"❓ Unknown database: {db_url[:50]}")

# Initialize database
print("Initializing database...")
init_db()

# Configure APIs
google_client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
anthropic_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def monitor_google():
    """Monitor Google Gemini"""
    db = SessionLocal()
    print(f"\n🔍 [{datetime.utcnow().strftime('%H:%M:%S')}] Testing Google Gemini...")
    start = time.time()
    
    try:
        response = google_client.models.generate_content(
            model='gemini-2.5-flash',
            contents='Say "OK"'
        )
        latency = (time.time() - start) * 1000
        
        check = ApiCheck(
            timestamp=datetime.utcnow(),
            provider='google',
            model='gemini-2.5-flash',
            latency_ms=latency,
            success=True
        )
        db.add(check)
        db.commit()
        
        print(f"   ✅ {latency:.0f}ms - Saved to database (ID: {check.id})")
        
    except Exception as e:
        check = ApiCheck(
            timestamp=datetime.utcnow(),
            provider='google',
            model='gemini-2.5-flash',
            latency_ms=0,
            success=False,
            error_message=str(e)
        )
        db.add(check)
        db.commit()
        print(f"   ❌ Failed: {e}")
        
    finally:
        db.close()

def monitor_anthropic():
    """Monitor Anthropic Claude"""
    db = SessionLocal()
    print(f"🔍 [{datetime.utcnow().strftime('%H:%M:%S')}] Testing Anthropic Claude...")
    start = time.time()
    
    try:
        response = anthropic_client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=5,
            messages=[{"role": "user", "content": "Say 'OK'"}]
        )
        latency = (time.time() - start) * 1000
        
        check = ApiCheck(
            timestamp=datetime.utcnow(),
            provider='anthropic',
            model='claude-3.5-haiku',
            latency_ms=latency,
            success=True
        )
        db.add(check)
        db.commit()
        
        print(f"   ✅ {latency:.0f}ms - Saved to database (ID: {check.id})")
        
    except Exception as e:
        check = ApiCheck(
            timestamp=datetime.utcnow(),
            provider='anthropic',
            model='claude-3.5-haiku',
            latency_ms=0,
            success=False,
            error_message=str(e)
        )
        db.add(check)
        db.commit()
        print(f"   ❌ Failed: {e}")
        
    finally:
        db.close()

def monitor_openai():
    """Monitor OpenAI"""
    db = SessionLocal()
    print(f"🔍 [{datetime.utcnow().strftime('%H:%M:%S')}] Testing OpenAI...")
    start = time.time()
    
    try:
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Say 'OK'"}],
            max_tokens=5
        )
        latency = (time.time() - start) * 1000
        
        check = ApiCheck(
            timestamp=datetime.utcnow(),
            provider='openai',
            model='gpt-3.5-turbo',
            latency_ms=latency,
            success=True
        )
        db.add(check)
        db.commit()
        
        print(f"   ✅ {latency:.0f}ms - Saved to database (ID: {check.id})")
        
    except Exception as e:
        check = ApiCheck(
            timestamp=datetime.utcnow(),
            provider='openai',
            model='gpt-3.5-turbo',
            latency_ms=0,
            success=False,
            error_message=str(e)
        )
        db.add(check)
        db.commit()
        print(f"   ❌ Failed: {e}")
        
    finally:
        db.close()

def run_checks():
    """Run all monitoring checks"""
    print("\n" + "="*60)
    print(f"⏰ RUNNING CHECKS - {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print("="*60)
    
    monitor_google()
    monitor_anthropic()
    monitor_openai()
    
    print("="*60)
    print("✅ Check complete. Next check in 1 hour.")
    print("="*60)

if __name__ == "__main__":
    print("\n" + "🚀 "*20)
    print("AI API MONITOR - SCHEDULER STARTED")
    print("🚀 "*20)
    print(f"\nStarted at: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    
    # Run immediately on startup
    print("\nRunning initial check immediately...")
    run_checks()
    
    # Schedule hourly checks
    print("\nScheduling hourly checks...")
    schedule.every(1).hours.do(run_checks)
    
    print("Scheduler is now running. Press Ctrl+C to stop\n")
    
    # Keep running
    while True:
        schedule.run_pending()
        time.sleep(60)