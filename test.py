# test.py
import google.generativeai as genai
import time
import os
from dotenv import load_dotenv
from datetime import datetime

# Load API keys from .env
load_dotenv()

# Configure Google
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

print("\n" + "="*50)
print("AI API MONITOR - Test Run")
print("="*50)
print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

print("🔍 Testing Google Gemini...")
start = time.time()

try:
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content("Say 'OK'")
    
    duration = (time.time() - start) * 1000
    
    print(f"✅ Success!")
    print(f"   Latency: {duration:.0f}ms")
    print(f"   Response: {response.text}")
    
except Exception as e:
    print(f"❌ Failed: {e}")

print()