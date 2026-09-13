"""Model training script for RainSense Farmer.
Trains Random Forest Classifier and Gradient Boosting Regressor with time-aware splitting.
"""
import json
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score, roc_auc_score,
    mean_absolute_error, mean_squared_error, r2_score
)

BASE_ML_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_ML_DIR / "data"
MODELS_DIR = BASE_ML_DIR / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

FEATURE_COLS = [
    "rainfall_1h", "rainfall_3h", "rainfall_6h", "rainfall_12h", "rainfall_24h", "rainfall_72h",
    "temperature", "humidity", "pressure", "wind_speed",
    "soil_moisture_surface", "soil_moisture_root",
    "latitude", "longitude", "month", "hour", "day_of_year"
]

def train_and_evaluate():
    csv_path = DATA_DIR / "indian_weather_rain_dataset.csv"
    if not csv_path.exists():
        from ml.data.generate_dataset import generate_agricultural_weather_dataset
        print("Dataset not found. Generating now...")
        df = generate_agricultural_weather_dataset(n_samples_per_region=2000)
        df.to_csv(csv_path, index=False)
    else:
        df = pd.read_csv(csv_path)

    # Sort strictly chronologically by timestamp to ensure time-aware split
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp").reset_index(drop=True)

    # Time-aware split: 80% train, 20% test (NO future data leakage!)
    split_idx = int(len(df) * 0.80)
    train_df = df.iloc[:split_idx]
    test_df = df.iloc[split_idx:]

    X_train = train_df[FEATURE_COLS]
    y_train_class = train_df["rain_occurrence"]
    y_train_reg = train_df["rainfall_amount"]

    X_test = test_df[FEATURE_COLS]
    y_test_class = test_df["rain_occurrence"]
    y_test_reg = test_df["rainfall_amount"]

    print(f"Training set: {len(X_train)} samples | Test set: {len(X_test)} samples")

    # 1. Train Classifier: Random Forest with balanced class weights
    print("Training Random Forest Rain Occurrence Classifier...")
    clf = RandomForestClassifier(
        n_estimators=100,
        max_depth=12,
        min_samples_split=6,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1
    )
    clf.fit(X_train, y_train_class)

    y_pred_class = clf.predict(X_test)
    y_prob_class = clf.predict_proba(X_test)[:, 1]

    clf_metrics = {
        "accuracy": round(float(accuracy_score(y_test_class, y_pred_class)), 4),
        "precision": round(float(precision_score(y_test_class, y_pred_class, zero_division=0)), 4),
        "recall": round(float(recall_score(y_test_class, y_pred_class)), 4),
        "f1_score": round(float(f1_score(y_test_class, y_pred_class)), 4),
        "roc_auc": round(float(roc_auc_score(y_test_class, y_prob_class)), 4)
    }
    print("Classification Metrics:", clf_metrics)

    # 2. Train Regressor: Gradient Boosting for Rainfall Amount (mm)
    print("Training Gradient Boosting Rainfall Regressor...")
    reg = GradientBoostingRegressor(
        n_estimators=100,
        max_depth=5,
        learning_rate=0.08,
        random_state=42
    )
    reg.fit(X_train, y_train_reg)

    y_pred_reg = np.clip(reg.predict(X_test), 0.0, None)

    reg_metrics = {
        "mae": round(float(mean_absolute_error(y_test_reg, y_pred_reg)), 4),
        "rmse": round(float(np.sqrt(mean_squared_error(y_test_reg, y_pred_reg))), 4),
        "r2_score": round(float(r2_score(y_test_reg, y_pred_reg)), 4)
    }
    print("Regression Metrics:", reg_metrics)

    # 3. Calculate Feature Importance for Model Explainability
    importances = clf.feature_importances_
    feat_importance_list = [
        {"feature": feat, "importance": round(float(imp), 4)}
        for feat, imp in sorted(zip(FEATURE_COLS, importances), key=lambda x: x[1], reverse=True)
    ]

    # Save models
    clf_path = MODELS_DIR / "rain_classifier.joblib"
    reg_path = MODELS_DIR / "rain_regressor.joblib"
    meta_path = MODELS_DIR / "model_metadata.json"

    joblib.dump(clf, clf_path)
    joblib.dump(reg, reg_path)

    metadata = {
        "version": "v1.0.0",
        "trained_date": "2026-09-11",
        "training_samples": len(X_train),
        "test_samples": len(X_test),
        "features": FEATURE_COLS,
        "classification_algorithm": "RandomForestClassifier",
        "classification_metrics": clf_metrics,
        "regression_algorithm": "GradientBoostingRegressor",
        "regression_metrics": reg_metrics,
        "feature_importances": feat_importance_list
    }

    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print(f"Models successfully saved to {MODELS_DIR}")
    return metadata

if __name__ == "__main__":
    train_and_evaluate()
