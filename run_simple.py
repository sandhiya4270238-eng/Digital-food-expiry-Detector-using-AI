import os
from dotenv import load_dotenv

# Load environment variables (Override system vars to ensure .env takes precedence)
load_dotenv(override=True)


# Set required environment variables for better Windows stability
os.environ['FLASK_DEBUG'] = '1'

if __name__ == "__main__":
    from app import app, socketio
    print("\n--- STARTING FOOD EXPIRY DETECTOR (SIMPLE MODE) ---")
    print("Dashboard: http://127.0.0.1:5000")
    print("Press Ctrl+C to stop.\n")
    
    # Run using socketio with threading mode (more stable on Windows)
    socketio.run(app, debug=True, port=5000, allow_unsafe_werkzeug=True)
