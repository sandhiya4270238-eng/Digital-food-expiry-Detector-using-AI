import os
import requests
from dotenv import load_dotenv

def list_all_models_no_trunc():
    load_dotenv()
    api_key = os.getenv('GEMINI_API_KEY')
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    try:
        response = requests.get(url, timeout=10)
        models = response.json().get('models', [])
        print(f"Total models found: {len(models)}")
        # Print first 20 characters of each name to avoid massive output but show all
        for m in models:
            print(f"{m['name']}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    list_all_models_no_trunc()
