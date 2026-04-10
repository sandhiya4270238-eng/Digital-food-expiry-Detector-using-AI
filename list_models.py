import os
import requests
import json
from dotenv import load_dotenv

def list_gemini_models():
    print("--- LISTING ALL GEMINI MODELS ---")
    load_dotenv()
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("[FAIL] Missing GEMINI_API_KEY")
        return

    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            models = response.json().get('models', [])
            # Filter and print only Gemini models
            for m in models:
                if "gemini" in m['name'].lower():
                    print(f"- {m['name']} (Supported: {m['supportedGenerationMethods']})")
        else:
            print(f"[FAIL] Error listing models: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"[FAIL] Exception during model listing: {e}")

if __name__ == "__main__":
    list_gemini_models()
