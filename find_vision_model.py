import os
import requests
from dotenv import load_dotenv

def find_vision_model():
    print("--- FINDING BEST VISION MODEL ---")
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
            vision_models = [m for m in models if 'generateContent' in m['supportedGenerationMethods']]
            print("Vision/Content Models available:")
            for m in vision_models:
                print(f"- {m['name']}")
        else:
            print(f"[FAIL] Error: {response.status_code}")
    except Exception as e:
        print(f"[FAIL] Exception: {e}")

if __name__ == "__main__":
    find_vision_model()
