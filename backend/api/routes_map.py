"""API endpoints for interactive map layers and 15 km monitoring zone analysis."""
from fastapi import APIRouter, Query, HTTPException
from backend.services.weather_provider import OpenMeteoProvider
from backend.services.geospatial_service import analyze_15km_monitoring_zone
from backend.services.demo_service import get_demo_dashboard_data

router = APIRouter(prefix="/api", tags=["map"])
provider = OpenMeteoProvider()

@router.get("/rain-map")
def get_rain_map_data(
    lat: float = Query(..., ge=-90.0, le=90.0),
    lon: float = Query(..., ge=-180.0, le=180.0),
    radius_km: float = Query(15.0, ge=1.0, le=50.0),
    demo: bool = Query(False)
):
    """
    Returns spatial rainfall points and cells for map layer rendering.
    Enforces strict 15 km radius filtering by default.
    """
    if demo:
        demo_data = get_demo_dashboard_data()
        return {
            "radius_km": 15.0,
            "selected_location": {"latitude": lat, "longitude": lon},
            "precipitation_cells": demo_data["fifteen_km_analysis"]["zones_detected"],
            "source": "DEMO DATA (Guntur Farm)",
            "source_type": "DEMO"
        }

    try:
        spatial_points = provider.get_spatial_rain_points(lat, lon, radius_km=radius_km)
        return {
            "radius_km": radius_km,
            "selected_location": {"latitude": lat, "longitude": lon},
            "precipitation_cells": spatial_points,
            "source": "Satellite / Precipitation Estimate",
            "source_type": "OBSERVED / ESTIMATE"
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Rain map generation failed: {str(e)}")

@router.get("/nearby-rain")
def get_nearby_rain_analysis(
    lat: float = Query(..., ge=-90.0, le=90.0),
    lon: float = Query(..., ge=-180.0, le=180.0),
    demo: bool = Query(False)
):
    """
    Analyzes the 15 km radius surrounding the selected farm.
    Answers:
    - Is it raining here?
    - Is rain happening nearby?
    - Nearest rain distance and direction?
    - Rain intensity and coverage percentage?
    - Zone breakdown (at farm, <=5km, <=10km, <=15km)?
    """
    if demo:
        demo_data = get_demo_dashboard_data()
        return demo_data["fifteen_km_analysis"]

    try:
        live = provider.get_live_conditions(lat, lon)
        farm_rate = live.get("precipitation_rate_mm_hr", 0.0)
        wind_dir = live.get("wind_direction_deg", 180.0)
        
        spatial_points = provider.get_spatial_rain_points(lat, lon, radius_km=15.0)
        analysis = analyze_15km_monitoring_zone(
            farm_lat=lat,
            farm_lon=lon,
            farm_current_rate_mm=farm_rate,
            nearby_observations=spatial_points,
            wind_direction_deg=wind_dir
        )
        return analysis
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"15km rain analysis failed: {str(e)}")
