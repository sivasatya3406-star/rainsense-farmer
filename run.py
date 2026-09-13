import sys
import os

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import uvicorn
from pathlib import Path
from backend.config import HOST, PORT, DEBUG, BASE_DIR
from backend.database.db import init_db
from ml.prediction.predictor import predictor_instance

def main():
    print("=" * 70)
    print("  [RainSense Farmer]")
    print("  'Know Where It Rains. Know Your Soil. Make Better Farming Decisions.'")
    print("=" * 70)
    
    # 1. Initialize Database
    print("[1/3] Initializing SQLite database and default farming regions...")
    init_db()
    print("      ✓ Database ready.")

    # 2. Check ML Models
    print("[2/3] Checking machine learning models (Random Forest + Gradient Boosting)...")
    if predictor_instance.is_ready():
        print(f"      ✓ ML Predictor ready (Version: {predictor_instance.metadata.get('version', 'v1.0')}).")
    else:
        print("      * Training ML models on historical agricultural dataset...")
        from ml.training.train_model import train_and_evaluate
        train_and_evaluate()
        predictor_instance._load()
        print("      ✓ Models trained and loaded successfully.")

    # 3. Start Web Server
    import socket
    def get_lan_ip():
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"
    
    lan_ip = get_lan_ip()
    print(f"[3/3] Starting RainSense web server on {HOST}:{PORT} ...")
    print(f"      • Desktop / Local:   http://localhost:{PORT}")
    print(f"      • Mobile / Network:  http://{lan_ip}:{PORT}")
    print(f"      • Interactive Docs:  http://localhost:{PORT}/docs")
    print(f"      • Admin Status:      http://localhost:{PORT}/api/admin/status")
    print("=" * 70)

    uvicorn.run(
        "backend.main:app",
        host=HOST,
        port=PORT,
        reload=DEBUG,
        log_level="info"
    )

if __name__ == "__main__":
    main()
