"""Configuration manager for RainSense Farmer backend."""
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env if present
load_dotenv(BASE_DIR / ".env")

# Server Config
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8000))
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
DEBUG = os.getenv("DEBUG", "true").lower() in ("true", "1", "yes")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")

# Database Config
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'rainsense.db'}")
DB_PATH = Path(os.getenv("DB_PATH", str(BASE_DIR / "rainsense.db")))

# API Configuration (Documented / configurable)
# Open-Meteo does not require an API key for normal non-commercial usage.
# Optional keys for higher quota or custom providers:
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY", "")
RAINFALL_API_KEY = os.getenv("RAINFALL_API_KEY", "")
SOIL_API_KEY = os.getenv("SOIL_API_KEY", "")
MAP_API_KEY = os.getenv("MAP_API_KEY", "")

# Cache & Threshold Settings
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", 600))  # 10 minutes cache
RAIN_DETECTED_THRESHOLD_MM = float(os.getenv("RAIN_DETECTED_THRESHOLD_MM", 0.1))
MAX_SAVED_LOCATIONS = 5

# ML Model Paths
ML_DIR = BASE_DIR / "ml"
MODEL_CLASSIFIER_PATH = ML_DIR / "models" / "rain_classifier.joblib"
MODEL_REGRESSOR_PATH = ML_DIR / "models" / "rain_regressor.joblib"
MODEL_METADATA_PATH = ML_DIR / "models" / "model_metadata.json"
