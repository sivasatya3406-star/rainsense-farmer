"""Demo Mode service for RainSense Farmer.
Provides controlled, realistic presentation data specifically for Guntur, Andhra Pradesh (Section 54).
"""
from typing import Dict, Any, List
from backend.services.geospatial_service import destination_point

def get_demo_dashboard_data() -> Dict[str, Any]:
    """Returns the exact demonstration scenario for Guntur, Andhra Pradesh."""
    guntur_lat = 16.3067
    guntur_lon = 80.4365
    
    # 6.4 km Northeast cell (bearing 45 degrees)
    cell_lat, cell_lon = destination_point(guntur_lat, guntur_lon, 6.4, 45.0)
    
    # 9.8 km Southwest cell (bearing 225 degrees)
    sw_lat, sw_lon = destination_point(guntur_lat, guntur_lon, 9.8, 225.0)
    
    # 13.2 km East cell (bearing 90 degrees)
    e_lat, e_lon = destination_point(guntur_lat, guntur_lon, 13.2, 90.0)

    demo_zones = [
        {
            "zone_id": "demo_zone_1",
            "name": "Northeast Rain Cell",
            "distance_km": 6.4,
            "bearing_deg": 45.0,
            "direction": "NE",
            "intensity": "Moderate",
            "rainfall_rate_mm": 8.4,
            "latitude": round(cell_lat, 4),
            "longitude": round(cell_lon, 4)
        },
        {
            "zone_id": "demo_zone_2",
            "name": "Southwest Light Cell",
            "distance_km": 9.8,
            "bearing_deg": 225.0,
            "direction": "SW",
            "intensity": "Light",
            "rainfall_rate_mm": 1.9,
            "latitude": round(sw_lat, 4),
            "longitude": round(sw_lon, 4)
        },
        {
            "zone_id": "demo_zone_3",
            "name": "East Peripheral Shower",
            "distance_km": 13.2,
            "bearing_deg": 90.0,
            "direction": "E",
            "intensity": "Light",
            "rainfall_rate_mm": 0.8,
            "latitude": round(e_lat, 4),
            "longitude": round(e_lon, 4)
        }
    ]

    return {
        "is_demo_mode": True,
        "mode_badge": "DEMO MODE (Guntur Farm Scenario)",
        "location": {
            "name": "Guntur Farm (Sample Farm)",
            "latitude": guntur_lat,
            "longitude": guntur_lon,
            "district": "Guntur",
            "state": "Andhra Pradesh",
            "crop": "Chilli & Cotton"
        },
        "live_weather": {
            "temperature_c": 27.5,
            "humidity_pct": 78,
            "wind_speed_kmh": 14.2,
            "wind_direction_deg": 225.0,
            "pressure_hpa": 1008.2,
            "source": "DEMO SCENARIO",
            "source_type": "DEMO DATA",
            "data_quality": "DEMO"
        },
        "current_rain": {
            "farm_rain_status": "Light Rain",
            "rainfall_rate_mm_hr": 1.4,
            "last_1h_mm": 1.2,
            "last_3h_mm": 3.8,
            "last_6h_mm": 6.1,
            "last_24h_mm": 12.6,
            "last_72h_mm": 24.8,
            "rain_probability_pct": 68,
            "source_type": "DEMO DATA",
            "update_time": "Just now (Demo)"
        },
        "fifteen_km_analysis": {
            "is_raining_at_farm": True,
            "farm_rain_rate_mm": 1.4,
            "farm_rain_status": "Light Rain",
            "rain_nearby": True,
            "nearest_rain_distance_km": 6.4,
            "nearest_rain_direction": "NE",
            "nearest_rain_intensity": "Moderate",
            "rain_coverage_pct": 34.0,
            "rain_movement": "Rain activity may be moving toward your selected area.",
            "rain_movement_confidence": 0.68,
            "zones_detected": demo_zones,
            "zone_breakdown": {
                "at_farm": "Light Rain (1.4 mm/hr)",
                "within_5km": "Light Rain spreading",
                "within_10km": "Moderate Rain cell at 6.4 km NE",
                "within_15km": "Multiple rain showers active"
            }
        },
        "soil_moisture": {
            "surface_moisture_pct": 48.0,
            "root_moisture_pct": 58.0,
            "average_moisture_pct": 54.0,
            "status": "Moderate",
            "waterlogging_risk": "Moderate",
            "source_label": "Estimated soil moisture (Demo)",
            "last_updated": "Just now"
        },
        "forecast": {
            "next_3h": [
                {"hour": "10:00 PM", "prob": 68, "rain_mm": 1.2, "temp": 27.2},
                {"hour": "11:00 PM", "prob": 74, "rain_mm": 2.6, "temp": 26.8},
                {"hour": "12:00 AM", "prob": 82, "rain_mm": 4.1, "temp": 26.2}
            ],
            "next_24h_summary": "Scattered moderate showers expected over next 6-12 hours.",
            "source_type": "FORECAST (Demo)"
        },
        "ai_insights": {
            "headline": "Active rain cell nearby; delay pesticide spraying and irrigation.",
            "summary": "Rainfall is currently detected near the selected farm. Soil moisture is moderate (54%). Additional rainfall may increase soil moisture.",
            "recommendations": [
                "Do NOT irrigate today: 12.6 mm received in the last 24h and moderate rain is active 6.4 km away.",
                "Delay chemical spraying: High risk of wash-off with 68% rain chance over the next 3 hours.",
                "Check drainage channels in low-lying Chilli plots to prevent water pooling if rain intensifies.",
                "Field soil moisture is currently optimal for root development."
            ],
            "confidence_pct": 82,
            "key_factors": [
                "Moderate rain cell 6.4 km NE moving toward farm",
                "24-hour rainfall accumulation is 12.6 mm",
                "Soil moisture at 54% (Moist)",
                "Relative humidity is 78%"
            ],
            "source_type": "AI PREDICTION (Demo)"
        }
    }
