"""Pydantic request and response schemas for RainSense Farmer."""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class SavedLocationCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    district: Optional[str] = None
    state: Optional[str] = None
    crop: Optional[str] = None
    notes: Optional[str] = None

class SavedLocationUpdate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    crop: Optional[str] = None
    notes: Optional[str] = None

class SavedLocationResponse(BaseModel):
    id: str
    user_id: str
    name: str
    latitude: float
    longitude: float
    district: Optional[str] = None
    state: Optional[str] = None
    crop: Optional[str] = None
    notes: Optional[str] = None
    rain_alert: int = 1
    nearby_alert: int = 1
    heavy_rain_alert: int = 1
    soil_alert: int = 1
    alert_distance_km: float = 15.0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class RainZone(BaseModel):
    zone_id: str
    name: str
    distance_km: float
    bearing_deg: float
    direction: str  # e.g. "NE", "SW"
    intensity: str  # "Light", "Moderate", "Heavy", "Very Heavy"
    rainfall_rate_mm: float
    latitude: float
    longitude: float

class FifteenKmAnalysis(BaseModel):
    is_raining_at_farm: bool
    farm_rain_rate_mm: float
    farm_rain_status: str  # "No Rain", "Light Rain", "Moderate Rain", "Heavy Rain"
    rain_nearby: bool
    nearest_rain_distance_km: Optional[float] = None
    nearest_rain_direction: Optional[str] = None
    nearest_rain_intensity: Optional[str] = None
    rain_coverage_pct: float
    rain_movement: str  # "Moving toward farm", "Moving away", "Stationary", "Rain movement unavailable"
    rain_movement_confidence: Optional[float] = None
    zones_detected: List[RainZone]
    zone_breakdown: Dict[str, str]  # at_farm, within_5km, within_10km, within_15km

class SoilMoistureData(BaseModel):
    surface_moisture_pct: float
    root_moisture_pct: float
    status: str  # "Dry", "Moderate", "Moist", "Very Wet"
    waterlogging_risk: str  # "Low", "Moderate", "High", "Critical"
    source_label: str = "Estimated soil moisture"
    data_quality: str = "GOOD"
    last_updated: str

class RainfallHistoryAccumulation(BaseModel):
    current_rate_mm_hr: float
    last_1h_mm: Optional[float] = None
    last_3h_mm: Optional[float] = None
    last_6h_mm: Optional[float] = None
    last_24h_mm: Optional[float] = None
    last_72h_mm: Optional[float] = None
    rain_probability_pct: Optional[int] = None
    data_quality: str = "GOOD"
    source_label: str = "Open-Meteo / Satellite Estimate"
    update_time: str

class HourlyForecastItem(BaseModel):
    time: str
    formatted_hour: str
    rain_probability_pct: int
    expected_rainfall_mm: float
    temperature_c: float
    humidity_pct: int
    wind_speed_kmh: float
    condition: str

class DailyForecastItem(BaseModel):
    date: str
    formatted_day: str
    rain_probability_pct: int
    total_rain_mm: float
    max_temp_c: float
    min_temp_c: float
    condition: str

class AIInsightResponse(BaseModel):
    headline: str
    advisory_bullet_points: List[str]
    irrigation_advice: str
    spraying_advice: str
    field_work_advice: str
    waterlogging_advisory: str
    confidence_pct: int
    key_factors: List[str]
    source_type: str = "AI PREDICTION"

class MLPredictRequest(BaseModel):
    latitude: float
    longitude: float
    rainfall_1h: Optional[float] = 0.0
    rainfall_3h: Optional[float] = 0.0
    rainfall_6h: Optional[float] = 0.0
    rainfall_24h: Optional[float] = 0.0
    rainfall_72h: Optional[float] = 0.0
    temperature: Optional[float] = 28.0
    humidity: Optional[float] = 70.0
    pressure: Optional[float] = 1010.0
    wind_speed: Optional[float] = 12.0
    soil_moisture_surface: Optional[float] = 45.0
    soil_moisture_root: Optional[float] = 50.0

class MLPredictResponse(BaseModel):
    rain_occurrence_prediction: int  # 0 or 1
    rain_probability_pct: int
    predicted_rainfall_mm: float
    confidence_score: float
    model_version: str
    top_factors: List[Dict[str, Any]]
    source_badge: str = "AI PREDICTION"
