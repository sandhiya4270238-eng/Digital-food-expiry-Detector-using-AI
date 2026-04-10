import os
import requests
from dotenv import load_dotenv

def test_final_model():
    print("--- FINAL MODEL VERIFICATION ---")
    load_dotenv()
    api_key = os.getenv('GEMINI_API_KEY')
    model = "gemini-flash-latest"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    
    payload = {
        "contents": [{"parts": [{"text": "Identify this: It is red and round and grows on a vine."}]}]
    }
    
    try:
        response = requests.post(url, json=payload, timeout=15)
        if response.status_code == 200:
            print(f"[OK] Model {model} is working.")
            print(f"Response: {response.json().get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', 'N/A')}")
        else:
            print(f"[FAIL] Model {model} returned {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"[FAIL] Exception: {e}")

if __name__ == "__main__":
    test_final_model()
