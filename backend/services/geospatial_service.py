"""Geospatial processing service for RainSense Farmer.
Implements exact Haversine distance, compass bearing, and 15 km zone analysis.
"""
import math
from typing import Tuple, List, Dict, Any, Optional

EARTH_RADIUS_KM = 6371.0088

def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates the great-circle distance between two points on the Earth in kilometers."""
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    
    a = (math.sin(d_lat / 2) ** 2 + 
         math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(d_lon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return EARTH_RADIUS_KM * c

def calculate_bearing_deg(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates the initial compass bearing in degrees from point 1 to point 2 (0 to 360)."""
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    d_lon = math.radians(lon2 - lon1)
    
    y = math.sin(d_lon) * math.cos(lat2_rad)
    x = (math.cos(lat1_rad) * math.sin(lat2_rad) - 
         math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(d_lon))
    
    initial_bearing = math.atan2(y, x)
    initial_bearing = math.degrees(initial_bearing)
    compass_bearing = (initial_bearing + 360) % 360
    return compass_bearing

def bearing_to_cardinal(bearing_deg: float) -> str:
    """Converts a bearing in degrees to 8-point cardinal direction string."""
    dirs = ["North", "Northeast", "East", "Southeast", "South", "Southwest", "West", "Northwest"]
    ix = int((bearing_deg + 22.5) / 45.0) % 8
    return dirs[ix]

def bearing_to_short_cardinal(bearing_deg: float) -> str:
    """Converts a bearing in degrees to short cardinal abbreviation."""
    dirs = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    ix = int((bearing_deg + 22.5) / 45.0) % 8
    return dirs[ix]

def destination_point(lat: float, lon: float, distance_km: float, bearing_deg: float) -> Tuple[float, float]:
    """Given a start point, distance, and bearing, returns the destination coordinate."""
    d_r = distance_km / EARTH_RADIUS_KM
    b_r = math.radians(bearing_deg)
    lat_r = math.radians(lat)
    lon_r = math.radians(lon)

    dest_lat = math.asin(
        math.sin(lat_r) * math.cos(d_r) + 
        math.cos(lat_r) * math.sin(d_r) * math.cos(b_r)
    )
    dest_lon = lon_r + math.atan2(
        math.sin(b_r) * math.sin(d_r) * math.cos(lat_r),
        math.cos(d_r) - math.sin(lat_r) * math.sin(dest_lat)
    )
    return math.degrees(dest_lat), (math.degrees(dest_lon) + 540) % 360 - 180

def classify_rain_intensity(rainfall_rate_mm: float) -> str:
    """Classifies rainfall rate according to standard meteorological thresholds."""
    if rainfall_rate_mm <= 0.05:
        return "No Rain"
    elif rainfall_rate_mm < 2.5:
        return "Light Rain"
    elif rainfall_rate_mm < 7.6:
        return "Moderate Rain"
    elif rainfall_rate_mm < 16.0:
        return "Heavy Rain"
    else:
        return "Very Heavy Rain"

def analyze_15km_monitoring_zone(
    farm_lat: float, 
    farm_lon: float, 
    farm_current_rate_mm: float,
    nearby_observations: List[Dict[str, Any]],
    wind_direction_deg: Optional[float] = None
) -> Dict[str, Any]:
    """
    Performs spatial analysis on all observations strictly within 15.0 km radius.
    Ensures that any observation > 15.0 km is filtered out.
    """
    farm_rain_status = classify_rain_intensity(farm_current_rate_mm)
    is_raining_at_farm = farm_current_rate_mm > 0.05
    
    valid_zones: List[Dict[str, Any]] = []
    zone_5km_rain = False
    zone_10km_rain = False
    zone_15km_rain = False
    
    for obs in nearby_observations:
        o_lat = obs["latitude"]
        o_lon = obs["longitude"]
        dist = haversine_distance_km(farm_lat, farm_lon, o_lat, o_lon)
        
        # Strict 15 km check
        if dist > 15.0001:
            continue
            
        rate = obs.get("rainfall_rate_mm", 0.0)
        if rate > 0.05:
            bearing = calculate_bearing_deg(farm_lat, farm_lon, o_lat, o_lon)
            cardinal = bearing_to_short_cardinal(bearing)
            intensity = classify_rain_intensity(rate)
            
            valid_zones.append({
                "zone_id": obs.get("id", f"zone_{len(valid_zones)+1}"),
                "name": obs.get("name", f"Rain Zone {len(valid_zones)+1}"),
                "distance_km": round(dist, 1),
                "bearing_deg": round(bearing, 1),
                "direction": cardinal,
                "intensity": intensity,
                "rainfall_rate_mm": round(rate, 1),
                "latitude": round(o_lat, 4),
                "longitude": round(o_lon, 4)
            })
            
            if dist <= 5.0:
                zone_5km_rain = True
            elif dist <= 10.0:
                zone_10km_rain = True
            elif dist <= 15.0:
                zone_15km_rain = True

    # Sort zones by nearest distance
    valid_zones.sort(key=lambda z: z["distance_km"])
    
    nearest_rain_dist = valid_zones[0]["distance_km"] if valid_zones else None
    nearest_rain_dir = valid_zones[0]["direction"] if valid_zones else None
    nearest_rain_intensity = valid_zones[0]["intensity"] if valid_zones else None
    
    # Coverage calculation across 15km zone
    # Base estimation: active rain points / total monitored sample points
    total_samples = max(len(nearby_observations), 1)
    rain_samples = len([z for z in valid_zones if z["rainfall_rate_mm"] > 0.05])
    coverage_pct = round(min(100.0, (rain_samples / total_samples) * 100), 1) if nearby_observations else 0.0
    if is_raining_at_farm and coverage_pct == 0.0:
        coverage_pct = 15.0
        
    # Movement vector estimation
    movement_desc = "Rain movement unavailable"
    movement_conf = None
    if valid_zones and wind_direction_deg is not None:
        # Check if wind blows the nearest rain cell towards the farm
        nearest_zone = valid_zones[0]
        bearing_to_cell = nearest_zone["bearing_deg"]
        # Wind blowing towards farm: wind direction aligns opposite to cell bearing
        wind_towards_farm = (wind_direction_deg + 180) % 360
        angle_diff = abs((wind_towards_farm - bearing_to_cell + 180) % 360 - 180)
        
        if angle_diff <= 45:
            movement_desc = "Rain activity may be moving toward your selected area."
            movement_conf = 0.68
        elif angle_diff >= 135:
            movement_desc = "Rain activity appears to be moving away from your area."
            movement_conf = 0.62
        else:
            movement_desc = "Rain activity appears relatively stationary or drifting tangentially."
            movement_conf = 0.55

    breakdown = {
        "at_farm": farm_rain_status,
        "within_5km": "Rain detected" if zone_5km_rain else "No rain detected",
        "within_10km": "Rain detected" if zone_10km_rain else "No rain detected",
        "within_15km": "Rain detected" if zone_15km_rain else "No rain detected"
    }

    return {
        "is_raining_at_farm": is_raining_at_farm,
        "farm_rain_rate_mm": round(farm_current_rate_mm, 1),
        "farm_rain_status": farm_rain_status,
        "rain_nearby": len(valid_zones) > 0,
        "nearest_rain_distance_km": nearest_rain_dist,
        "nearest_rain_direction": nearest_rain_dir,
        "nearest_rain_intensity": nearest_rain_intensity,
        "rain_coverage_pct": coverage_pct,
        "rain_movement": movement_desc,
        "rain_movement_confidence": movement_conf,
        "zones_detected": valid_zones,
        "zone_breakdown": breakdown
    }
