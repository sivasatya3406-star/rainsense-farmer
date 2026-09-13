"""API endpoints for weather, rainfall accumulation, soil moisture, and forecast."""
from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from backend.services.weather_provider import provider
from backend.services.demo_service import get_demo_dashboard_data

router = APIRouter(prefix="/api", tags=["weather"])


@router.get("/weather")
def get_live_weather(
    lat: float = Query(..., ge=-90.0, le=90.0),
    lon: float = Query(..., ge=-180.0, le=180.0),
    demo: bool = Query(False)
):
    """Returns live/observed temperature, humidity, wind, pressure, and current precipitation rate."""
    if demo:
        demo_data = get_demo_dashboard_data()
        return demo_data["live_weather"]
    try:
        return provider.get_live_conditions(lat, lon)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Weather service temporarily unavailable: {str(e)}")

@router.get("/rainfall")
def get_rainfall_data(
    lat: float = Query(..., ge=-90.0, le=90.0),
    lon: float = Query(..., ge=-180.0, le=180.0),
    demo: bool = Query(False)
):
    """Returns rainfall accumulation: 1h, 3h, 6h, 24h, 72h and recent series."""
    if demo:
        demo_data = get_demo_dashboard_data()
        return demo_data["current_rain"]
    try:
        return provider.get_rain_history(lat, lon)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Rainfall history temporarily unavailable: {str(e)}")

@router.get("/soil-moisture")
def get_soil_moisture_data(
    lat: float = Query(..., ge=-90.0, le=90.0),
    lon: float = Query(..., ge=-180.0, le=180.0),
    demo: bool = Query(False)
):
    """Returns surface and root-zone soil moisture percentages, waterlogging risk, and trend."""
    if demo:
        demo_data = get_demo_dashboard_data()
        return demo_data["soil_moisture"]
    try:
        return provider.get_soil_moisture(lat, lon)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Soil moisture data temporarily unavailable: {str(e)}")

@router.get("/forecast")
def get_forecast_data(
    lat: float = Query(..., ge=-90.0, le=90.0),
    lon: float = Query(..., ge=-180.0, le=180.0),
    demo: bool = Query(False)
):
    """Returns short-term hourly forecast (24h) and daily forecast (7 days)."""
    if demo:
        demo_data = get_demo_dashboard_data()
        return demo_data["forecast"]
    try:
        return provider.get_forecast(lat, lon)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Forecast service temporarily unavailable: {str(e)}")
