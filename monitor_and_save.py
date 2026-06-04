# monitor_and_save.py
from google import genai
import anthropic
import time
import os
import openai
from dotenv import load_dotenv
from datetime import datetime
from database import SessionLocal, ApiCheck, init_db

load_dotenv()

# Make sure database exists
init_db()

# Configure APIs
openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
google_client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
anthropic_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
MAX_SUCCESS_LATENCY_MS = float(os.getenv("MAX_SUCCESS_LATENCY_MS", "30000"))


def classify_result(latency_ms, response_text):
    """Only count a check as success if it returned useful output within SLA."""
    if not response_text or not response_text.strip():
        return False, "empty response"
    if latency_ms > MAX_SUCCESS_LATENCY_MS:
        return False, f"latency exceeded threshold ({latency_ms:.0f}ms > {MAX_SUCCESS_LATENCY_MS:.0f}ms)"
    return True, None

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
        response_text = response.choices[0].message.content or ""
        is_success, error = classify_result(duration, response_text)
        if not is_success:
            print(f"❌ Failed: {error}")
            save_check('openai', 'gpt-4.1-mini', None, False, error)
            return {'provider': 'openai', 'latency': None, 'success': False}
        print(f"✅ Success: {duration:.0f}ms")
        print(f"   Response: {response_text}")
        save_check('openai', 'gpt-4.1-mini', duration, True)
        return {'provider': 'openai', 'latency': duration, 'success': True}
    except Exception as e:
        print(f"❌ Failed: {e}")
        save_check('openai', 'gpt-4.1-mini', None, False, str(e))
        return {'provider': 'openai', 'latency': None, 'success': False}

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
        response_text = getattr(response, "text", None) or ""
        is_success, error = classify_result(latency, response_text)
        if not is_success:
            print(f"❌ Failed: {error}")
            save_check('google', 'gemini-2.5-flash', None, False, error)
            return {'provider': 'google', 'latency': None, 'success': False}
        print(f"✅ Success: {latency:.0f}ms")
        save_check('google', 'gemini-2.5-flash', latency, True)
        return {'provider': 'google', 'latency': latency, 'success': True}
        
    except Exception as e:
        print(f"❌ Failed: {e}")
        save_check('google', 'gemini-2.5-flash', None, False, str(e))
        return {'provider': 'google', 'latency': None, 'success': False}

def monitor_anthropic():
    """Monitor Anthropic Claude"""
    print("🔍 Testing Anthropic Claude Opus 4.6...")
    start = time.time()
    try:
        response = anthropic_client.messages.create(
            model="claude-opus-4-6",
            max_tokens=5,
            messages=[{"role": "user", "content": "Say 'OK'"}]
        )
        latency = (time.time() - start) * 1000
        response_text = " ".join(
            block.text for block in response.content if hasattr(block, "text") and block.text
        )
        is_success, error = classify_result(latency, response_text)
        if not is_success:
            print(f"❌ Failed: {error}")
            save_check('anthropic', 'claude-opus-4-6', None, False, error)
            return {'provider': 'anthropic', 'latency': None, 'success': False}
        print(f"✅ Success: {latency:.0f}ms")
        save_check('anthropic', 'claude-opus-4-6', latency, True)
        return {'provider': 'anthropic', 'latency': latency, 'success': True}
        
    except Exception as e:
        print(f"❌ Failed: {e}")
        save_check('anthropic', 'claude-opus-4-6', None, False, str(e))
        return {'provider': 'anthropic', 'latency': None, 'success': False}

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
    
    
    r3 = monitor_openai()
    results.append(r3)
    print()
    
    # Summary
    print("="*60)
    successful = [r for r in results if r['success']]
    print(f"✅ Completed: {len(successful)}/3 successful")
    
    if successful:
        fastest = min(successful, key=lambda x: x['latency'])
        print(f"🏆 Fastest: {fastest['provider']} ({fastest['latency']:.0f}ms)")
    
    print()