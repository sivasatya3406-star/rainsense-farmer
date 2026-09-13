"""API endpoints for machine learning prediction and model explainability."""
from fastapi import APIRouter, HTTPException
from backend.config import MODEL_METADATA_PATH
from backend.schemas.models import MLPredictRequest, MLPredictResponse
from ml.prediction.predictor import predictor_instance
from pathlib import Path
import json

router = APIRouter(prefix="/api", tags=["ml"])

@router.post("/predict", response_model=MLPredictResponse)
def predict_rain(request: MLPredictRequest):
    """
    ML prediction endpoint.
    Uses Random Forest Classifier and Gradient Boosting Regressor to estimate:
    - Rain occurrence (0 or 1)
    - Rain probability %
    - Estimated rainfall amount (mm)
    - Confidence metric
    - Top contributing factors for explainability
    """
    try:
        res = predictor_instance.predict(request.model_dump())
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ML prediction error: {str(e)}")

@router.get("/ml-explainability")
def get_ml_explainability():
    """
    Returns feature importance rankings and model evaluation metrics for transparency.
    """
    if MODEL_METADATA_PATH.exists():
        with open(MODEL_METADATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "version": "v1.0.0-default",
        "features": [
            "humidity", "rainfall_3h", "rainfall_24h", "soil_moisture_surface",
            "soil_moisture_root", "pressure", "temperature", "month"
        ],
        "feature_importances": [
            {"feature": "humidity", "importance": 0.28},
            {"feature": "rainfall_3h", "importance": 0.22},
            {"feature": "soil_moisture_surface", "importance": 0.16},
            {"feature": "pressure", "importance": 0.12},
            {"feature": "rainfall_24h", "importance": 0.10},
            {"feature": "month", "importance": 0.07},
            {"feature": "temperature", "importance": 0.05}
        ]
    }
