# list_models.py
from google import genai
import os
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

print("\nAvailable models:")
for model in client.models.list():
    print(f"  - {model.name}")