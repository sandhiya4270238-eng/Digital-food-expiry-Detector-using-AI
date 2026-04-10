import os
import io

import base64
import uuid
import datetime
from flask import Flask, render_template, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit
from dotenv import load_dotenv
from PIL import Image
import numpy as np
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Import your detection logic
from predict import predict_freshness_gemini

load_dotenv(override=True)
if os.getenv('GEMINI_API_KEY'):
    key = os.getenv('GEMINI_API_KEY')
    logger.info(f"Loaded GEMINI_API_KEY: {key[:4]}...{key[-4:]}")
else:
    logger.warning("No GEMINI_API_KEY found in environment or .env file.")

app = Flask(__name__)

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'food-crystal-secret-123')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///food_inventory.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize Extensions
db = SQLAlchemy(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')


# --- Database Models ---
class FoodItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), nullable=False, index=True)
    product_name = db.Column(db.String(100), nullable=False)
    source = db.Column(db.String(50), default='Unknown')
    label = db.Column(db.String(50), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    expiry_estimate = db.Column(db.String(100), nullable=False)
    days_to_expiry = db.Column(db.Integer, default=7) # New Field: Days until expiry
    confidence = db.Column(db.Float, default=1.0)
    recommendation = db.Column(db.Text)
    image_base64 = db.Column(db.Text)  # Store thumbnail if needed
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def __init__(self, **kwargs):
        super(FoodItem, self).__init__(**kwargs)

# Create Database
with app.app_context():
    db.create_all()

# --- Helper Functions ---
def get_user_id():
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())
    return session['user_id']

def calc_stats(user_id):
    items = FoodItem.query.filter_by(user_id=user_id).all()
    total = len(items)
    # Refined logic: Expired if negative days OR label says rotten (with safety check)
    expired = len([i for i in items if (i.days_to_expiry is not None and i.days_to_expiry < 0) or 'Rotten' in (i.label or '')])
    # 1-day warning: if binary days is 0 or 1
    soon = len([i for i in items if i.days_to_expiry is not None and 0 <= i.days_to_expiry <= 1 and 'Rotten' not in (i.label or '')])
    fresh = total - expired - soon
    return total, expired, soon, fresh

@app.route('/')
def dashboard():
    uid = get_user_id()
    items = FoodItem.query.filter_by(user_id=uid).order_by(FoodItem.created_at.desc()).all()
    
    # Convert DB items to the format index.html expects
    history = []
    for item in items:
        history.append({
            'product': item.product_name,
            'source': item.source,
            'label': item.label,
            'expiry': item.expiry_estimate,
            'days_left': item.days_to_expiry, # New Field
            'quantity': item.quantity,
            'image': item.image_base64 or '',
            'id': item.id
        })
    
    total, expired, soon, fresh = calc_stats(uid)
    
    return render_template('index.html', 
                           total_items=total, 
                           expired_count=expired, 
                           expiring_soon_count=soon, 
                           safe_count=fresh, 
                           history=history)

@app.route('/add_manual', methods=['POST'])
def add_manual():
    uid = get_user_id()
    name = request.form.get('product_name')
    qty = int(request.form.get('quantity', 1))
    status = request.form.get('status', 'Fresh')
    expiry = request.form.get('expiry_date')

    new_item = FoodItem(
        user_id=uid,
        product_name=name,
        source='Manual Entry',
        label=status,
        quantity=qty,
        expiry_estimate=expiry
    )
    db.session.add(new_item)
    db.session.commit()
    
    socketio.emit('inventory_updated', {'user_id': uid}, room=None) # room handling could be better for true private real-time
    return jsonify({"status": "success"}) if request.is_json else dashboard()

@app.route('/scan', methods=['GET', 'POST'])
def scan_food():
    if request.method == 'GET':
        return dashboard()
    uid = get_user_id()
    if 'file' not in request.files:
        return dashboard()
    
    file = request.files['file']
    if file.filename == '':
        return dashboard()

    # Read image
    img_bytes = file.read()
    img_b64 = base64.b64encode(img_bytes).decode('utf-8')
    
    # --- REAL AI LOGIC ---
    try:
        # load_dotenv() removed from here (called at top level for speed)
        api_key = os.getenv('GEMINI_API_KEY')
        if api_key:
            result = predict_freshness_gemini(api_key, img_bytes)
            logger.debug(f"AI sync successful: {result.get('product_name')}")
        else:
            logger.warning("No Gemini API key found.")
            filename = os.path.splitext(file.filename)[0].capitalize().replace('_', ' ')
            result = {
                "product_name": filename,
                "label": "Unknown",
                "expiry_estimate": "N/A",
                "confidence": 0.0,
                "recommendation": "Mock result: Please add a valid GEMINI_API_KEY to your .env file."
            }
    except Exception as e:
        import traceback
        print("DEBUG: Error during AI detection")
        traceback.print_exc()
        # Fallback in case of API failure
        filename = os.path.splitext(file.filename)[0].capitalize().replace('_', ' ')
        result = {
            "product_name": filename,
            "label": "Analysis Error",
            "expiry_estimate": "Error",
            "days_to_expiry": 7, # Default for error cases
            "confidence": 0.0,
            "recommendation": f"Technical bottleneck: {str(e)}"
        }
    # ------------------------------------------------------------

    new_item = FoodItem(
        user_id=uid,
        product_name=result.get('product_name', 'Unknown Item'),
        source='AI Scanner',
        label=result.get('label', 'Unknown'),
        expiry_estimate=result.get('expiry_estimate', 'N/A'),
        days_to_expiry=int(result.get('days_to_expiry', 7)), # Store numeric value
        confidence=float(result.get('confidence', 0.0)),
        recommendation=result.get('recommendation', 'No recommendation available.'),
        image_base64=img_b64
    )
    db.session.add(new_item)
    db.session.commit()
    
    socketio.emit('inventory_updated', {'user_id': uid})
    
    # We return the overview but with the result highlighted
    # For real-time, we could just return JSON and let frontend update
    return render_template('index.html', result=result, image_data=img_b64, **dashboard_data(uid))

def dashboard_data(uid):
    items = FoodItem.query.filter_by(user_id=uid).order_by(FoodItem.created_at.desc()).all()
    history = [{
        'product': item.product_name,
        'source': item.source,
        'label': item.label,
        'expiry': item.expiry_estimate,
        'days_left': item.days_to_expiry, # New Field
        'quantity': item.quantity,
        'image': item.image_base64 or '',
        'id': item.id
    } for item in items]
    total, expired, soon, fresh = calc_stats(uid)
    return {
        'total_items': total,
        'expired_count': expired,
        'expiring_soon_count': soon,
        'safe_count': fresh,
        'history': history
    }

@app.route('/delete_history', methods=['POST'])
def delete_history():
    uid = get_user_id()
    item_id = request.form.get('id') # Using ID now instead of list index
    if not item_id:
        return dashboard()
    
    item = FoodItem.query.filter_by(id=item_id, user_id=uid).first()
    if item:
        db.session.delete(item)
        db.session.commit()
        socketio.emit('inventory_updated', {'user_id': uid})
        
    return dashboard()

@app.route('/api/stats')
def api_stats():
    uid = get_user_id()
    return jsonify(dashboard_data(uid))

if __name__ == '__main__':
    socketio.run(app, debug=True, port=5000)
