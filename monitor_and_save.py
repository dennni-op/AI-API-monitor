# monitor_and_save.py
from google import genai
import anthropic
import time
import os
from dotenv import load_dotenv
from datetime import datetime
from database import SessionLocal, ApiCheck, init_db

load_dotenv()

# Make sure database exists
init_db()

# Configure APIs
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
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
        response = client.models.generate_content(
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
    print("🔍 Testing Anthropic Claude...")
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

if __name__ == "__main__":
    print("\n" + "="*60)
    print("AI API MONITOR - Saving to Database")
    print("="*60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    results = []
    
    r1 = monitor_google()
    results.append(r1)
    print()
    
    r2 = monitor_anthropic()
    results.append(r2)
    print()
    
    # Summary
    print("="*60)
    successful = [r for r in results if r['success']]
    print(f"✅ Completed: {len(successful)}/2 successful")
    
    if successful:
        fastest = min(successful, key=lambda x: x['latency'])
        print(f"🏆 Fastest: {fastest['provider']} ({fastest['latency']:.0f}ms)")
    
    print()