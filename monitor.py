# monitor.py
import time
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def monitor_openai():
    """Monitor OpenAI API"""
    try:
        import openai
        
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        print(f"\n🔍 Testing OpenAI at {datetime.now().strftime('%H:%M:%S')}")
        start = time.time()
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": "Say 'OK'"}],
            max_tokens=5
        )
        
        duration = (time.time() - start) * 1000  # Convert to milliseconds
        
        result = {
            'timestamp': datetime.now().isoformat(),
            'provider': 'openai',
            'model': 'gpt-4',
            'latency_ms': round(duration, 0),
            'success': True,
            'tokens': response.usage.total_tokens,
            'cost': (response.usage.prompt_tokens * 0.03 / 1000) + 
                   (response.usage.completion_tokens * 0.06 / 1000)
        }
        
        print(f"✅ Success: {result['latency_ms']}ms")
        print(f"   Tokens: {result['tokens']}")
        print(f"   Cost: ${result['cost']:.4f}")
        
        return result
        
    except Exception as e:
        result = {
            'timestamp': datetime.now().isoformat(),
            'provider': 'openai',
            'model': 'gpt-4',
            'success': False,
            'error': str(e)
        }
        print(f"❌ Failed: {e}")
        return result

def monitor_anthropic():
    """Monitor Anthropic API"""
    try:
        import anthropic
        
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        
        print(f"\n🔍 Testing Anthropic at {datetime.now().strftime('%H:%M:%S')}")
        start = time.time()
        
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=5,
            messages=[{"role": "user", "content": "Say 'OK'"}]
        )
        
        duration = (time.time() - start) * 1000
        
        result = {
            'timestamp': datetime.now().isoformat(),
            'provider': 'anthropic',
            'model': 'claude-sonnet-4',
            'latency_ms': round(duration, 0),
            'success': True,
            'tokens': response.usage.input_tokens + response.usage.output_tokens,
            'cost': (response.usage.input_tokens * 0.003 / 1000) + 
                   (response.usage.output_tokens * 0.015 / 1000)
        }
        
        print(f"✅ Success: {result['latency_ms']}ms")
        print(f"   Tokens: {result['tokens']}")
        print(f"   Cost: ${result['cost']:.4f}")
        
        return result
        
    except Exception as e:
        result = {
            'timestamp': datetime.now().isoformat(),
            'provider': 'anthropic',
            'model': 'claude-sonnet-4',
            'success': False,
            'error': str(e)
        }
        print(f"❌ Failed: {e}")
        return result

def monitor_google():
    """Monitor Google Gemini API"""
    try:
        import google.generativeai as genai
        
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        model = genai.GenerativeModel('gemini-pro')
        
        print(f"\n🔍 Testing Google at {datetime.now().strftime('%H:%M:%S')}")
        start = time.time()
        
        response = model.generate_content("Say 'OK'")
        
        duration = (time.time() - start) * 1000
        
        result = {
            'timestamp': datetime.now().isoformat(),
            'provider': 'google',
            'model': 'gemini-pro',
            'latency_ms': round(duration, 0),
            'success': True,
            'tokens': 20,  # Estimate
            'cost': 0.00002  # Very cheap
        }
        
        print(f"✅ Success: {result['latency_ms']}ms")
        print(f"   Response: {response.text}")
        
        return result
        
    except Exception as e:
        result = {
            'timestamp': datetime.now().isoformat(),
            'provider': 'google',
            'model': 'gemini-pro',
            'success': False,
            'error': str(e)
        }
        print(f"❌ Failed: {e}")
        return result

if __name__ == "__main__":
    print("\n" + "="*50)
    print("AI API MONITOR - Test Run")
    print("="*50)
    
    results = []
    
    # Test each provider
    results.append(monitor_openai())
    results.append(monitor_anthropic())
    results.append(monitor_google())
    
    # Summary
    print("\n" + "="*50)
    print("SUMMARY")
    print("="*50)
    
    for r in results:
        if r['success']:
            print(f"✅ {r['provider']:12s} {r['latency_ms']:6.0f}ms  ${r['cost']:.5f}")
        else:
            print(f"❌ {r['provider']:12s} FAILED")
    
    print("\n")