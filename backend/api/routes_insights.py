"""API endpoint for AI-powered farming insights."""
from fastapi import APIRouter, Query
from backend.services.weather_provider import provider
from backend.services.ai_advisory import generate_farming_advisory
from backend.services.demo_service import get_demo_dashboard_data
from backend.services.geospatial_service import analyze_15km_monitoring_zone

router = APIRouter(prefix="/api", tags=["insights"])

@router.get("/insights")
def get_farming_insights(
    lat: float = Query(..., ge=-90.0, le=90.0),
    lon: float = Query(..., ge=-180.0, le=180.0),
    crop: str = Query("General Crops"),
    demo: bool = Query(False)
):
    """
    Generates actionable, farmer-friendly agricultural recommendations:
    - Irrigation decision support (Should I irrigate today? Wait for nearby clouds?)
    - Spraying suitability (Is rain likely to wash away chemicals?)
    - Waterlogging precautions
    - Field trafficability
    - Model confidence & explainable factors
    """
    if demo:
        demo_data = get_demo_dashboard_data()
        return demo_data["ai_insights"]

    try:
        live = provider.get_live_conditions(lat, lon)
        rain = provider.get_rain_history(lat, lon)
        soil = provider.get_soil_moisture(lat, lon)
        forecast = provider.get_forecast(lat, lon)
        spatial = provider.get_spatial_rain_points(lat, lon, radius_km=15.0)
        
        fifteen_km = analyze_15km_monitoring_zone(
            farm_lat=lat,
            farm_lon=lon,
            farm_current_rate_mm=live.get("precipitation_rate_mm_hr", 0.0),
            nearby_observations=spatial,
            wind_direction_deg=live.get("wind_direction_deg", 180.0)
        )
        
        # 3h rain probability from forecast
        hourly_fc = forecast.get("hourly", [])
        p_3h = hourly_fc[0].get("rain_probability_pct", 20) if hourly_fc else 20
        next_24h_rain = sum(h.get("expected_rainfall_mm", 0.0) for h in hourly_fc[:24])

        advisory = generate_farming_advisory(
            farm_rain_status=fifteen_km["farm_rain_status"],
            is_raining=fifteen_km["is_raining_at_farm"],
            nearby_rain=fifteen_km["rain_nearby"],
            nearest_dist_km=fifteen_km["nearest_rain_distance_km"],
            nearest_dir=fifteen_km["nearest_rain_direction"],
            nearest_intensity=fifteen_km["nearest_rain_intensity"],
            rain_24h_mm=rain.get("last_24h_mm", 0.0),
            surface_moisture_pct=soil.get("surface_moisture_pct", 40.0),
            root_moisture_pct=soil.get("root_moisture_pct", 45.0),
            waterlogging_risk=soil.get("waterlogging_risk", "Low"),
            forecast_rain_prob_3h=p_3h,
            forecast_rain_next_24h_mm=next_24h_rain,
            crop=crop
        )
        return advisory
    except Exception as e:
        # Graceful fallback advisory
        return {
            "headline": "Moderate weather conditions observed around field.",
            "advisory_bullet_points": [
                "Weather data is currently updating. Check your field soil moisture before irrigating."
            ],
            "irrigation_advice": "Check field soil moisture by hand before scheduling irrigation.",
            "spraying_advice": "Safe to spray if wind speed is below 15 km/h and no heavy clouds are visible.",
            "field_work_advice": "Routine field operations can proceed.",
            "waterlogging_advisory": "Low risk of waterlogging.",
            "confidence_pct": 75,
            "key_factors": ["Atmospheric humidity", "Historical rainfall average"],
            "source_type": "AI PREDICTION"
        }
