# scheduler.py
import schedule
import time
from datetime import datetime
from google import genai
import openai
import anthropic
import os
from dotenv import load_dotenv
from database import SessionLocal, ApiCheck, init_db

load_dotenv()
init_db()

# Configure APIs
openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
google_client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
anthropic_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def save_check(provider, model, latency, success, error=None):
    """Save check result to database"""
    db = SessionLocal()
    try:
        check = ApiCheck(
            provider=provider,
            model=model,
            latency_ms=latency,
            success=success,
            error_message=error
        )
        db.add(check)
        db.commit()
        print(f"   💾 Saved to database")
    except Exception as e:
        print(f"   ⚠️ Database error: {e}")
    finally:
        db.close()

def monitor_google():
    """Monitor Google Gemini"""
    print("🔍 Testing Google Gemini 2.5 Flash...")
    start = time.time()
    try:
        response = google_client.models.generate_content(
            model='gemini-2.5-flash',
            contents='Say "OK"'
        )
        latency = (time.time() - start) * 1000
        
        print(f"✅ Success: {latency:.0f}ms")
        save_check('google', 'gemini-2.5-flash', latency, True)
        return {'provider': 'google', 'latency': latency, 'success': True}
        
    except Exception as e:
        print(f"❌ Failed: {e}")
        save_check('google', 'gemini-2.5-flash', 0, False, str(e))
        return {'provider': 'google', 'latency': 0, 'success': False}   


def monitor_anthropic():
    """Monitor Anthropic Claude"""
    db = SessionLocal()
    print("🔍 Testing Anthropic Claude Opus 4.6...")
    start = time.time()
    try:
        response = anthropic_client.messages.create(
            model="claude-opus-4-6",
            max_tokens=5,
            messages=[{"role": "user", "content": "Say 'OK'"}]
        )
        latency = (time.time() - start) * 1000
        
        print(f"✅ Success: {latency:.0f}ms")
        save_check('anthropic', 'claude-opus-4-6', latency, True)
        return {'provider': 'anthropic', 'latency': latency, 'success': True}
        
    except Exception as e:
        print(f"❌ Failed: {e}")
        save_check('anthropic', 'claude-opus-4-6', 0, False, str(e))
        return {'provider': 'anthropic', 'latency': 0, 'success': False}

def monitor_openai():
    """Monitor OpenAI ChatGPT"""
    print ("🔍 Testing ChatGPT 4.1 mini ")
    start = time.time()
    try:
        response = openai_client.chat.completions.create(
            model = 'gpt-4.1-mini',
            messages = [{"role": "user", "content": "Say 'OK'"}]
        )
        duration = (time.time() - start) * 1000
        print(f"✅ Success: {duration:.0f}ms")
        print(f"   Response: {response.choices[0].message.content}")
        save_check('openai', 'gpt-4.1-mini', duration, True)
        return {'provider': 'openai', 'latency': duration, 'success': True}
    except Exception as e:
        print(f"❌ Failed: {e}")
        save_check('openai', 'gpt-4.1-mini', 0, False, str(e))
        return {'provider': 'openai', 'latency': 0, 'success': False}
        
def run_checks():
    """Run all monitoring checks"""
    print("\n" + "="*60)
    print(f"⏰ RUNNING CHECKS - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
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
    print(f"\nStarted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Checking every hour")
    print("Press Ctrl+C to stop\n")
    
    # Run immediately on start
    run_checks()
    
    # Schedule to run every hour
    schedule.every(1).hours.do(run_checks)
    
    # Keep running
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute if something needs to run