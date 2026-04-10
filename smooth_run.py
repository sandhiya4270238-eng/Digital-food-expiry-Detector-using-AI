import os
import subprocess
import sys
import time

def kill_process_on_port(port):
    print(f"Checking for processes on port {port}...")
    try:
        # Get the PID using netstat
        result = subprocess.check_output(f"netstat -ano | findstr :{port}", shell=True).decode()
        if result:
            lines = result.strip().split('\n')
            pids = set()
            for line in lines:
                parts = line.split()
                if len(parts) > 4:
                    pids.add(parts[-1])
            
            for pid in pids:
                print(f"Terminating PID {pid} using port {port}...")
                os.system(f"taskkill /F /PID {pid}")
            time.sleep(1)
    except subprocess.CalledProcessError:
        print(f"Port {port} is clear.")

def check_env():
    if not os.path.exists(".env"):
        print("WARNING: .env file missing. Creating a template...")
        with open(".env", "w") as f:
            f.write("GEMINI_API_KEY=YOUR_API_KEY_HERE\n")
    else:
        print("[OK] .env file found.")

def start_app():
    print("\n" + "="*40)
    print("🚀 DIGITAL FOOD EXPIRY DETECTOR STARTUP")
    print("="*40)
    
    kill_process_on_port(5000)
    check_env()
    
    print("\nInitializing Optical Sensor & AI Core...")
    try:
        # Using sys.executable to ensure we use the same python environment
        subprocess.run([sys.executable, "app.py"])
    except KeyboardInterrupt:
        print("\nSystem standby. Goodbye.")

if __name__ == "__main__":
    start_app()
