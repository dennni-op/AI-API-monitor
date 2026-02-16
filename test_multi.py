# test_multi.py
from google import genai
import anthropic
import time
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

# Configure APIs
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
anthropic_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

print("\n" + "="*60)
print("AI API MONITOR - Multi-Provider Comparison")
print("="*60)
print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

results = []

# Test Google

print("🔍 Testing Google Gemini 2.5 Flash...")
start = time.time()
try:
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents='Say "OK"'
    )
    duration = (time.time() - start) * 1000
    print(f"✅ Success: {duration:.0f}ms")
    print(f"   Response: {response.text}")
    results.append({'provider': 'Google', 'latency': duration, 'success': True})
except Exception as e:
    print(f"❌ Failed: {e}")
    results.append({'provider': 'Google', 'latency': 0, 'success': False})

print()

# Test Anthropic
print("🔍 Testing Anthropic Claude Opus 4.6...")
start = time.time()
try:
    response = anthropic_client.messages.create(
        model="claude-opus-4-6",
        max_tokens=5,
        messages=[{"role": "user", "content": "Say 'OK'"}]
    )
    duration = (time.time() - start) * 1000
    print(f"✅ Success: {duration:.0f}ms")
    print(f"   Response: {response.content[0].text}")
    results.append({'provider': 'Anthropic', 'latency': duration, 'success': True})
except Exception as e:
    print(f"❌ Failed: {e}")
    results.append({'provider': 'Anthropic', 'latency': 0, 'success': False})

print()
print("="*60)
print("📊 COMPARISON")
print("="*60)

successful = [r for r in results if r['success']]
if len(successful) >= 2:
    fastest = min(successful, key=lambda x: x['latency'])
    
    print(f"\n🏆 Winner: {fastest['provider']} ({fastest['latency']:.0f}ms)\n")
    
    for r in sorted(successful, key=lambda x: x['latency']):
        if r['provider'] == fastest['provider']:
            print(f"   {r['provider']:12s} {r['latency']:6.0f}ms  ⭐ Fastest")
        else:
            slower_pct = ((r['latency'] / fastest['latency'] - 1) * 100)
            print(f"   {r['provider']:12s} {r['latency']:6.0f}ms  ({slower_pct:+.0f}% slower)")

elif len(successful) == 1:
    print(f"\n✅ Only {successful[0]['provider']} succeeded")
else:
    print("\n❌ All providers failed")

print()