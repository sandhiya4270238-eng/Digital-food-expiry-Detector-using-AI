import io
import os
import json
import base64
import requests
import numpy as np

# Performance Optimization: Use a session for connection pooling
session = requests.Session()

import logging
logger = logging.getLogger(__name__)

# Only import TF if needed to save memory/speed if not using local model
try:
    import tensorflow as tf
    from utils.preprocessing import preprocess_image, preprocess_image_from_bytes
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False

# Define categories
CATEGORIES = ["Fresh", "Slightly Spoiled", "Rotten", "Unknown"]

# Recommendations based on category
RECOMMENDATIONS = {
    "Fresh": "Safe to consume or use.",
    "Slightly Spoiled": "Check carefully before consuming. Consume or use soon.",
    "Rotten": "Do not consume. Please discard.",
    "Unknown": "Could not determine freshness."
}

def load_trained_model(model_path="models/model.keras"):
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found at {model_path}. Please train the model first.")
    return tf.keras.models.load_model(model_path)

def predict_freshness_local(model, image_bytes):
    """
    Predicts the freshness of the given image bytes using the local CNN model.
    """
    img_tensor = preprocess_image_from_bytes(image_bytes)
        
    predictions = model.predict(img_tensor, verbose=0)[0]
    class_idx = np.argmax(predictions)
    confidence = predictions[class_idx]
    
    label = CATEGORIES[class_idx] if class_idx < len(CATEGORIES) else "Unknown"
    recommendation = RECOMMENDATIONS.get(label, "Check condition before use.")
    
    return {
        "product_name": "Unknown Local Item",
        "label": label,
        "confidence": float(confidence),
        "expiry_estimate": "N/A (Local Model used)",
        "recommendation": recommendation,
        "source": "Local CNN"
    }

def predict_freshness_gemini(api_key, image_bytes):
    """
    Predicts food/grocery freshness using Google Gemini API.
    """
    # Google Gemini Vision API endpoint (v1beta)
    # Recommended model for vision/content generation
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={api_key}"
    
    # Prepare image data
    base64_image = base64.b64encode(image_bytes).decode('utf-8')
    
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": "Analyze this food item. Return a clean JSON object with: 'product_name' (accurate name), 'label' (one of: 'Fresh', 'Slightly Spoiled', 'Rotten'), 'expiry_estimate' (string like '2 days'), 'recommendation' (concise advice), 'confidence' (float 0-1), and 'days_to_expiry' (number of days until it expires; use 0 for today, 1 for tomorrow, -1 if already rotten)."
                    },
                    {
                        "inline_data": {
                            "mime_type": "image/jpeg",
                            "data": base64_image
                        }
                    }
                ]
            }
        ]
    }
    
    headers = {"Content-Type": "application/json"}
    
    max_retries = 2
    for attempt in range(max_retries):
        try:
            # Increased timeout to 20s for more stability
            response = session.post(url, headers=headers, json=payload, timeout=20)
            break # Success!
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            error_msg = str(e)
            if "getaddrinfo failed" in error_msg or "NameResolutionError" in error_msg:
                advice = "DNS Resolution Failed. Please check your internet connection or DNS settings. The domain 'generativelanguage.googleapis.com' could not be found."
                logger.error(f"Network failure: {advice}")
                raise requests.exceptions.ConnectionError(advice) from e
                
            if attempt == max_retries - 1:
                logger.error(f"Final network failure after {max_retries} attempts: {e}")
                raise e
            import time
            time.sleep(1) # Small pause before retry
            logger.warning(f"Network jitter detected. Retrying AI sync (Attempt {attempt + 2})...")

    
    if response.status_code == 200:
        try:
            res_json = response.json()
            candidates = res_json.get('candidates', [])
            if not candidates:
                # Check for safety ratings or errors
                if 'promptFeedback' in res_json:
                    raise ValueError(f"Gemini Safety Filter blocked the request: {res_json['promptFeedback']}")
                raise ValueError(f"No candidates returned from Gemini. Response: {res_json}")
                
            text_result = candidates[0].get('content', {}).get('parts', [{}])[0].get('text', '')
            
            if not text_result:
                raise ValueError(f"Empty text result from Gemini. Response: {res_json}")
            
            # Clean up potential markdown formatting
            text_result = text_result.strip()
            if text_result.startswith("```"):
                # Handle ```json ... ``` or just ``` ... ```
                lines = text_result.split('\n')
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                text_result = '\n'.join(lines).strip()
            
            try:
                parsed = json.loads(text_result)
            except json.JSONDecodeError as e:
                # Try to find JSON block in case there's extra text
                import re
                match = re.search(r'\{.*\}', text_result, re.DOTALL)
                if match:
                    parsed = json.loads(match.group())
                else:
                    raise e
            
            label = parsed.get("label", "Unknown")
            # Ensure label matches expected categories exactly
            if "fresh" in label.lower() or "good" in label.lower(): label = "Fresh"
            elif "spoil" in label.lower() or "warning" in label.lower() or "near" in label.lower(): label = "Slightly Spoiled"
            elif "rot" in label.lower() or "expir" in label.lower() or "bad" in label.lower(): label = "Rotten"
            else: label = "Unknown"
                
            confidence_str = str(parsed.get("confidence", "85")).replace("%", "")
            confidence = float(confidence_str) / 100.0 if float(confidence_str) > 1 else float(confidence_str)
            product_name = parsed.get("product_name", "Unknown Grocery Item")
            
            return {
                "product_name": product_name,
                "label": label,
                "confidence": confidence,
                "expiry_estimate": parsed.get("expiry_estimate", "Unknown shelf life"),
                "recommendation": parsed.get("recommendation", RECOMMENDATIONS.get(label, "")),
                "source": "Google Gemini AI"
            }
            
        except Exception as e:
            raise ValueError(f"Failed to parse Gemini response: {e}. Raw response: {response.text}")
    else:
        raise ValueError(f"API Error {response.status_code}: {response.text}")
