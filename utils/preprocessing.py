import cv2
import numpy as np
import io

def validate_image_bytes(image_bytes):
    """
    Validates if the provided bytes correspond to a valid image format.
    Raises ValueError if invalid.
    """
    if not image_bytes:
        raise ValueError("Image data is empty.")
        
    # Check magic numbers for common image formats
    if image_bytes.startswith(b'\xff\xd8\xff'): # JPEG
        return True
    elif image_bytes.startswith(b'\x89PNG\r\n\x1a\n'): # PNG
        return True
        
    raise ValueError("Invalid image format. Please upload a JPG or PNG.")

def load_image(path):
    img = cv2.imread(path)
    if img is None:
        raise ValueError(f"Could not load image from {path}. The file may be corrupted.")
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    return img

def resize_image(img, size=(224, 224)):
    # Use INTER_AREA interpolation which is better for shrinking images
    return cv2.resize(img, size, interpolation=cv2.INTER_AREA)

def normalize(img):
    # Vectorized fast normalization
    return img.astype(np.float32) / 255.0

def preprocess_image(path, size=(224, 224)):
    img = load_image(path)
    img = resize_image(img, size)
    img = normalize(img)
    return np.expand_dims(img, axis=0)

def preprocess_image_from_bytes(image_bytes, size=(224, 224)):
    # Validate first
    validate_image_bytes(image_bytes)
    
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if img is None:
         raise ValueError("Failed to decode image. File might be corrupted.")
         
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = resize_image(img, size)
    img = normalize(img)
    return np.expand_dims(img, axis=0)
