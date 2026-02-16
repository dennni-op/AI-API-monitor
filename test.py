# test.py
import openai
import time
import os
from dotenv import load_dotenv
from datetime import datetime

# Load API keys from .env
load_dotenv()

# Initialize OpenAI client
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

print("\n" + "="*50)
print("AI API Monitor - Test Run")
print("="*50)
print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

print("Testing OpenAI GPT-3.5...")
start = time.time()

try:
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Say 'OK'"}],
        max_tokens=5
    )
    
    duration = (time.time() - start) * 1000
    
    print(f"✅ Success!")
    print(f"   Latency: {duration:.0f}ms")
    print(f"   Response: {response.choices[0].message.content}")
    print(f"   Tokens: {response.usage.total_tokens}")
    print(f"   Cost: ${(response.usage.total_tokens * 0.0005 / 1000):.6f}")
    
except Exception as e:
    print(f"❌ Error: {e}")

print()