import os
import sys
import requests
from dotenv import load_dotenv

import socket

def test_environment():
    print("--- ENVIRONMENT DIAGNOSTICS ---")
    print(f"Python Version: {sys.version}")
    
    dependencies = [
        "flask", "flask_sqlalchemy", "flask_socketio", "dotenv", "PIL", "numpy", "tensorflow", "cv2", "requests"
    ]
    
    for dep in dependencies:
        try:
            if dep == "cv2":
                import cv2
            elif dep == "PIL":
                from PIL import Image
            elif dep == "dotenv":
                import dotenv
            else:
                __import__(dep)
            print(f"[OK] {dep} is correctly installed.")
        except ImportError:
            print(f"[FAIL] {dep} is NOT installed correctly.")

def check_dns(host):
    try:
        ip = socket.gethostbyname(host)
        return True, ip
    except socket.gaierror:
        return False, None

def test_api_connectivity():
    print("\n--- API CONNECTIVITY DIAGNOSTICS ---")
    load_dotenv()
    api_key = os.getenv('GEMINI_API_KEY')
    print(f"GEMINI_API_KEY found: {bool(api_key)}")
    
    # 1. Check DNS resolution for Gemini
    gemini_host = "generativelanguage.googleapis.com"
    print(f"Checking DNS for {gemini_host}...")
    dns_ok, ip = check_dns(gemini_host)
    if dns_ok:
        print(f"[OK] DNS resolved {gemini_host} to {ip}")
    else:
        print(f"[FAIL] DNS failed to resolve {gemini_host}. This is likely why you're seeing 'NameResolutionError'.")
        print("      Suggestions: Check your internet connection, try a different DNS server (like 8.8.8.8), or check if your ISP/Firewall is blocking Google APIs.")

    # 2. Check general internet connectivity
    print("Checking general internet connectivity...")
    google_ok, _ = check_dns("google.com")
    if google_ok:
        print("[OK] able to resolve google.com. Internet is likely working.")
    else:
        print("[FAIL] DNS failed to resolve google.com. Your internet connection might be down or DNS is completely broken.")

    if api_key:
        # 3. Simple API request (Try a few models)
        models_to_try = [
            "gemini-1.5-flash",
            "gemini-pro",
            "gemini-1.5-pro-latest"
        ]
        
        # Check proxies
        proxies = {
            'http': os.environ.get('HTTP_PROXY'),
            'https': os.environ.get('HTTPS_PROXY'),
        }
        if any(proxies.values()):
            print(f"Proxies detected: {proxies}")
        else:
            print("No system proxies detected.")

        print("Testing simple GET request to Google...")
        try:
            r = requests.get("https://www.google.com", timeout=5)
            print(f"[OK] GET www.google.com returned {r.status_code}")
        except Exception as e:
            print(f"[FAIL] GET www.google.com failed: {e}")

        versions_and_models = [
            ("v1beta", "gemini-1.5-flash"),
            ("v1", "gemini-1.5-flash"),
            ("v1beta", "gemini-pro"),
            ("v1", "gemini-pro")
        ]
        
        for version, model in versions_and_models:
            url = f"https://{gemini_host}/{version}/models/{model}:generateContent?key={api_key}"
            print(f"Testing {version} for model: {model}...")
            try:
                payload = {
                    "contents": [{"parts": [{"text": "Say ok"}]}]
                }
                response = requests.post(url, json=payload, timeout=10)
                if response.status_code == 200:
                    print(f"[OK] Successfully connected to {model} via {version}.")
                    return # Exit after first success
                else:
                    print(f"[FAIL] {model} ({version}) returned {response.status_code}: {response.text[:100]}")
            except Exception as e:
                print(f"[FAIL] Error connecting to {model} ({version}): {e}")

    else:
        print("[SKIP] Skipping API request test (Key missing).")


def test_file_structure():
    print("\n--- FILE STRUCTURE DIAGNOSTICS ---")
    files = [
        "app.py", "predict.py", "utils/preprocessing.py", "utils/model_utils.py",
        "templates/index.html", "requirements.txt", ".env"
    ]
    for f in files:
        if os.path.exists(f):
            print(f"[OK] {f} exists.")
        else:
            print(f"[FAIL] {f} is missing.")

if __name__ == "__main__":
    test_environment()
    test_api_connectivity()
    test_file_structure()

