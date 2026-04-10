import os
import requests
from dotenv import load_dotenv

def find_1_5_models():
    print("--- FINDING 1.5 MODELS ---")
    load_dotenv()
    api_key = os.getenv('GEMINI_API_KEY')
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    try:
        response = requests.get(url, timeout=10)
        models = response.json().get('models', [])
        for m in models:
            if "1.5" in m['name']:
                print(f"- {m['name']} (Methods: {m['supportedGenerationMethods']})")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    find_1_5_models()
