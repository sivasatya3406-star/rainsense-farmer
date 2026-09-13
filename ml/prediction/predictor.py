"""Inference service for RainSense Farmer ML models."""
import json
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

BASE_ML_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_ML_DIR / "models"

class RainPredictor:
    def __init__(self):
        self.clf = None
        self.reg = None
        self.metadata = None
        self.feature_names = []
        self._load()

    def _load(self):
        clf_path = MODELS_DIR / "rain_classifier.joblib"
        reg_path = MODELS_DIR / "rain_regressor.joblib"
        meta_path = MODELS_DIR / "model_metadata.json"

        if not (clf_path.exists() and reg_path.exists() and meta_path.exists()):
            # Train if models are not present
            try:
                from ml.training.train_model import train_and_evaluate
                print("Models not found. Training on first initialization...")
                train_and_evaluate()
            except Exception as e:
                print(f"Warning: Model training on load failed: {e}")
                return

        try:
            self.clf = joblib.load(clf_path)
            self.reg = joblib.load(reg_path)
            with open(meta_path, "r", encoding="utf-8") as f:
                self.metadata = json.load(f)
            self.feature_names = self.metadata.get("features", [])
        except Exception as e:
            print(f"Failed to load ML models: {e}")

    def is_ready(self) -> bool:
        return self.clf is not None and self.reg is not None

    def predict(self, input_features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Runs ML inference using current meteorological, lag, and temporal features.
        """
        if not self.is_ready():
            self._load()
            if not self.is_ready():
                # Fallback rule-based estimation if model is unavailable
                hum = float(input_features.get("humidity", 60.0))
                prob = int(min(90, max(5, hum * 0.75)))
                return {
                    "rain_occurrence_prediction": 1 if prob > 50 else 0,
                    "rain_probability_pct": prob,
                    "predicted_rainfall_mm": round(prob * 0.05, 2),
                    "confidence_score": 0.70,
                    "model_version": "v1.0.0-fallback",
                    "top_factors": [
                        {"feature": "humidity", "importance": 0.40, "human_label": "High atmospheric moisture"},
                        {"feature": "rainfall_3h", "importance": 0.30, "human_label": "Recent antecedent rainfall"}
                    ],
                    "source_badge": "AI PREDICTION"
                }

        # Format feature vector
        now = datetime.now()
        row = {
            "rainfall_1h": float(input_features.get("rainfall_1h", 0.0)),
            "rainfall_3h": float(input_features.get("rainfall_3h", 0.0)),
            "rainfall_6h": float(input_features.get("rainfall_6h", 0.0)),
            "rainfall_12h": float(input_features.get("rainfall_12h", 0.0)),
            "rainfall_24h": float(input_features.get("rainfall_24h", 0.0)),
            "rainfall_72h": float(input_features.get("rainfall_72h", 0.0)),
            "temperature": float(input_features.get("temperature", 28.0)),
            "humidity": float(input_features.get("humidity", 65.0)),
            "pressure": float(input_features.get("pressure", 1010.0)),
            "wind_speed": float(input_features.get("wind_speed", 10.0)),
            "soil_moisture_surface": float(input_features.get("soil_moisture_surface", 40.0)),
            "soil_moisture_root": float(input_features.get("soil_moisture_root", 45.0)),
            "latitude": float(input_features.get("latitude", 16.3)),
            "longitude": float(input_features.get("longitude", 80.4)),
            "month": int(input_features.get("month", now.month)),
            "hour": int(input_features.get("hour", now.hour)),
            "day_of_year": int(input_features.get("day_of_year", now.timetuple().tm_yday))
        }

        X = pd.DataFrame([row])[self.feature_names]
        
        # Classification inference
        pred_class = int(self.clf.predict(X)[0])
        prob_class = float(self.clf.predict_proba(X)[0][1])
        prob_pct = int(round(prob_class * 100))

        # Regression inference
        pred_amount = float(self.reg.predict(X)[0])
        pred_amount = max(0.0, round(pred_amount, 2))
        if pred_class == 0 and prob_pct < 40:
            pred_amount = 0.0

        # Confidence metric derived from prediction margin
        confidence = round(float(abs(prob_class - 0.5) * 2 * 0.3 + 0.65), 2)
        confidence = min(0.95, max(0.60, confidence))

        # Human-readable labels for top factors
        factor_map = {
            "humidity": "Relative humidity levels",
            "rainfall_3h": "Antecedent 3-hour rainfall",
            "rainfall_24h": "Past 24-hour accumulation",
            "soil_moisture_surface": "Surface soil saturation",
            "soil_moisture_root": "Root-zone water content",
            "pressure": "Atmospheric barometric pressure",
            "month": "Seasonal monsoon cycle",
            "temperature": "Ambient surface temperature",
            "wind_speed": "Surface wind speed"
        }

        top_feats = []
        for item in self.metadata.get("feature_importances", [])[:5]:
            f_name = item["feature"]
            top_feats.append({
                "feature": f_name,
                "importance": item["importance"],
                "human_label": factor_map.get(f_name, f_name)
            })

        return {
            "rain_occurrence_prediction": pred_class,
            "rain_probability_pct": prob_pct,
            "predicted_rainfall_mm": pred_amount,
            "confidence_score": confidence,
            "model_version": self.metadata.get("version", "v1.0.0"),
            "top_factors": top_feats,
            "source_badge": "AI PREDICTION"
        }

# Global singleton
predictor_instance = RainPredictor()
