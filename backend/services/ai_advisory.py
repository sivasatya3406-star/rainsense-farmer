"""AI Farming Advisory Engine for RainSense Farmer.
Generates farmer-friendly agricultural recommendations using cautious, practical language.
"""
from typing import Dict, Any, List

def generate_farming_advisory(
    farm_rain_status: str,
    is_raining: bool,
    nearby_rain: bool,
    nearest_dist_km: float = None,
    nearest_dir: str = None,
    nearest_intensity: str = None,
    rain_24h_mm: float = 0.0,
    surface_moisture_pct: float = 40.0,
    root_moisture_pct: float = 45.0,
    waterlogging_risk: str = "Low",
    forecast_rain_prob_3h: int = 20,
    forecast_rain_next_24h_mm: float = 0.0,
    crop: str = "Crops"
) -> Dict[str, Any]:
    """Generates context-aware, humble farming advisories."""
    avg_soil = (surface_moisture_pct + root_moisture_pct) / 2.0
    advisories: List[str] = []
    factors: List[str] = []
    
    # 1. Headline logic
    if is_raining:
        headline = f"Rainfall occurring at your field. Pause field operations."
        advisories.append("Rain is currently observed at your field. Field activities like sowing, spraying, and weeding should be paused.")
        factors.append(f"Observed rainfall at farm ({farm_rain_status})")
    elif nearby_rain and nearest_dist_km is not None and nearest_dist_km <= 8.0:
        headline = f"{nearest_intensity or 'Active'} rain detected {nearest_dist_km} km {nearest_dir or ''}. Rain may reach your field."
        advisories.append(f"A {nearest_intensity or 'rain'} cell is active {nearest_dist_km} km away in the {nearest_dir or 'nearby'} direction. Keep an eye on incoming clouds.")
        factors.append(f"Nearby rain {nearest_dist_km} km {nearest_dir}")
    elif forecast_rain_prob_3h >= 60:
        headline = f"High chance of rain ({forecast_rain_prob_3h}%) in the next 3 hours."
        advisories.append(f"Atmospheric conditions indicate a {forecast_rain_prob_3h}% chance of precipitation soon. Plan indoor or covered tasks.")
        factors.append(f"3-hour rain probability: {forecast_rain_prob_3h}%")
    elif avg_soil < 25.0 and forecast_rain_prob_3h < 30 and forecast_rain_next_24h_mm < 2.0:
        headline = "Dry soil conditions and low chance of rain."
        advisories.append("Soil moisture is low across both surface and root zones, and no significant rain is detected nearby.")
        factors.append(f"Low soil moisture ({round(avg_soil, 1)}%)")
    else:
        headline = "Stable conditions with moderate soil moisture."
        advisories.append("Current weather is calm. Soil moisture levels are within normal seasonal range for crop maintenance.")

    # 2. Irrigation Advice
    if rain_24h_mm >= 15.0 or avg_soil >= 65.0:
        irrigation_advice = "Irrigation is not needed at this time. The field has received adequate rainfall recently and soil moisture is abundant."
        factors.append(f"Recent 24h rainfall: {round(rain_24h_mm, 1)} mm")
    elif (nearby_rain and nearest_dist_km and nearest_dist_km <= 10.0) or forecast_rain_prob_3h >= 50:
        irrigation_advice = "Consider waiting before turning on irrigation pumps. Nearby rainfall or upcoming clouds may provide natural watering."
        factors.append(f"Upcoming rain potential")
    elif avg_soil < 30.0 and rain_24h_mm < 3.0:
        irrigation_advice = "Consider checking soil moisture with a probe or hand-feel before irrigating. If soil is dry below 5 cm, light irrigation is advisable."
        factors.append(f"Dry root zone ({round(root_moisture_pct, 1)}%)")
    else:
        irrigation_advice = "Soil moisture is currently moderate. Monitor field conditions before scheduling the next irrigation cycle."

    # 3. Spraying & Chemical Application Advice
    if is_raining or (nearby_rain and nearest_dist_km and nearest_dist_km <= 8.0) or forecast_rain_prob_3h >= 45:
        spraying_advice = "Postpone pesticide, fungicide, or foliar fertilizer spraying. Rain occurring or approaching nearby can wash away chemicals, wasting money."
        factors.append(f"Rain wash-off risk")
    elif rain_24h_mm > 0 and surface_moisture_pct > 70:
        spraying_advice = "Allow wet foliage to dry before applying sprays to ensure proper chemical adherence and prevent fungal spread."
    else:
        spraying_advice = "Weather conditions are suitable for spraying if wind speed remains below 15 km/h."

    # 4. Drainage & Waterlogging Advice
    if waterlogging_risk in ("High", "Critical") or (avg_soil > 70 and forecast_rain_next_24h_mm > 15.0):
        waterlogging_advisory = "High waterlogging risk. Check field bunds and drainage outlets to ensure excess water can drain quickly, especially for sensitive crops."
        factors.append("Soil saturation above 70%")
    elif waterlogging_risk == "Moderate":
        waterlogging_advisory = "Moderate moisture accumulation. Ensure drainage trenches are free of weeds and silt."
    else:
        waterlogging_advisory = "Low risk of waterlogging. Soil has good infiltration capacity under current conditions."

    # Field operations
    if is_raining or rain_24h_mm >= 25.0:
        field_work = "Avoid heavy tractor operations or tilling on water-saturated fields to prevent soil compaction."
    else:
        field_work = "Favorable conditions for routine weeding, manual hoeing, and crop inspection."

    # Confidence calculation (between 70% and 92%)
    base_conf = 78
    if is_raining or nearby_rain:
        base_conf += 8
    if rain_24h_mm > 10:
        base_conf += 4
    confidence_pct = min(94, base_conf)

    return {
        "headline": headline,
        "advisory_bullet_points": advisories,
        "irrigation_advice": irrigation_advice,
        "spraying_advice": spraying_advice,
        "field_work_advice": field_work,
        "waterlogging_advisory": waterlogging_advisory,
        "confidence_pct": confidence_pct,
        "key_factors": factors[:4],
        "source_type": "AI PREDICTION"
    }
