"""Historical weather and rainfall dataset generator for Indian agricultural regions.
Generates realistic multi-season meteorological data with lag features.
"""
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

DATA_DIR = Path(__file__).resolve().parent

# Representative Indian farming locations: (name, lat, lon, state)
FARM_REGIONS = [
    ("Guntur", 16.3067, 80.4365, "Andhra Pradesh"),
    ("Nizamabad", 18.6725, 78.0941, "Telangana"),
    ("Ludhiana", 30.9010, 75.8573, "Punjab"),
    ("Nashik", 19.9975, 73.7898, "Maharashtra"),
    ("Dharwad", 15.4589, 75.0078, "Karnataka"),
    ("Varanasi", 25.3176, 82.9739, "Uttar Pradesh")
]

def generate_agricultural_weather_dataset(n_samples_per_region: int = 2000, random_seed: int = 42) -> pd.DataFrame:
    """Generates synthetic hourly historical time-series weather dataset without data leakage."""
    np.random.seed(random_seed)
    all_dfs = []
    
    base_date = datetime(2025, 1, 1, 0, 0)
    
    for name, lat, lon, state in FARM_REGIONS:
        timestamps = [base_date + timedelta(hours=i) for i in range(n_samples_per_region)]
        
        months = np.array([dt.month for dt in timestamps])
        hours = np.array([dt.hour for dt in timestamps])
        days_of_year = np.array([dt.timetuple().tm_yday for dt in timestamps])
        
        # Indian Monsoon effect (June to September: months 6, 7, 8, 9)
        is_monsoon = np.isin(months, [6, 7, 8, 9]).astype(float)
        
        # Base temperature with diurnal cycle and monsoon cooling
        base_temp = 32.0 - 4.0 * is_monsoon + 6.0 * np.sin(2 * np.pi * (hours - 9) / 24) + np.random.normal(0, 2.5, n_samples_per_region)
        temp = np.clip(base_temp, 14.0, 44.0)
        
        # Relative humidity: high in monsoon and early mornings, low in dry afternoons
        base_humidity = 50.0 + 32.0 * is_monsoon - 18.0 * np.sin(2 * np.pi * (hours - 9) / 24) + np.random.normal(0, 7.0, n_samples_per_region)
        humidity = np.clip(base_humidity, 20.0, 98.0)
        
        # Surface pressure (hPa)
        base_pressure = 1012.0 - 6.0 * is_monsoon + np.random.normal(0, 3.0, n_samples_per_region)
        pressure = np.clip(base_pressure, 995.0, 1025.0)
        
        # Wind speed (km/h)
        wind_speed = np.clip(8.0 + 6.0 * is_monsoon + np.random.exponential(4.0, n_samples_per_region), 1.0, 45.0)
        
        # Generate raw rainfall series with convective clustering
        # Rain probability driven by humidity, pressure drop, and monsoon
        rain_prob = 0.05 + 0.35 * is_monsoon + 0.40 * (humidity > 75.0) - 0.15 * (pressure > 1012.0)
        rain_prob = np.clip(rain_prob, 0.02, 0.85)
        
        raw_rain = np.zeros(n_samples_per_region)
        for i in range(n_samples_per_region):
            if np.random.rand() < rain_prob[i]:
                # Pareto / Gamma distributed rainfall intensity in mm
                amount = np.random.gamma(shape=1.5, scale=4.0)
                raw_rain[i] = round(amount, 2)
                
        # Generate strictly backward-looking lag features (NO future leakage!)
        rain_1h = np.roll(raw_rain, 1)
        rain_1h[0] = 0.0
        
        rain_3h = np.zeros(n_samples_per_region)
        rain_6h = np.zeros(n_samples_per_region)
        rain_12h = np.zeros(n_samples_per_region)
        rain_24h = np.zeros(n_samples_per_region)
        rain_72h = np.zeros(n_samples_per_region)
        
        for i in range(n_samples_per_region):
            # Sum up strictly prior hours
            rain_3h[i] = np.sum(raw_rain[max(0, i-3):i])
            rain_6h[i] = np.sum(raw_rain[max(0, i-6):i])
            rain_12h[i] = np.sum(raw_rain[max(0, i-12):i])
            rain_24h[i] = np.sum(raw_rain[max(0, i-24):i])
            rain_72h[i] = np.sum(raw_rain[max(0, i-72):i])
            
        # Soil moisture derived from cumulative antecedent rainfall and evaporation
        soil_surf = np.clip(25.0 + 0.8 * rain_24h + 0.3 * rain_72h + 10.0 * is_monsoon + np.random.normal(0, 3.0, n_samples_per_region), 10.0, 95.0)
        soil_root = np.clip(30.0 + 0.4 * rain_24h + 0.5 * rain_72h + 8.0 * is_monsoon + np.random.normal(0, 2.5, n_samples_per_region), 15.0, 92.0)
        
        # Targets for model
        # Target 1: Rain occurrence (current hour rain >= 0.1 mm)
        rain_occurrence = (raw_rain >= 0.1).astype(int)
        # Target 2: Rainfall amount (mm)
        rainfall_amount = raw_rain
        
        region_df = pd.DataFrame({
            "timestamp": timestamps,
            "region": name,
            "state": state,
            "latitude": lat,
            "longitude": lon,
            "month": months,
            "day": [dt.day for dt in timestamps],
            "hour": hours,
            "day_of_year": days_of_year,
            "temperature": np.round(temp, 1),
            "humidity": np.round(humidity, 1),
            "pressure": np.round(pressure, 1),
            "wind_speed": np.round(wind_speed, 1),
            "rainfall_1h": np.round(rain_1h, 2),
            "rainfall_3h": np.round(rain_3h, 2),
            "rainfall_6h": np.round(rain_6h, 2),
            "rainfall_12h": np.round(rain_12h, 2),
            "rainfall_24h": np.round(rain_24h, 2),
            "rainfall_72h": np.round(rain_72h, 2),
            "soil_moisture_surface": np.round(soil_surf, 1),
            "soil_moisture_root": np.round(soil_root, 1),
            "rain_occurrence": rain_occurrence,
            "rainfall_amount": rainfall_amount
        })
        all_dfs.append(region_df)
        
    final_df = pd.concat(all_dfs, ignore_index=True)
    return final_df

if __name__ == "__main__":
    df = generate_agricultural_weather_dataset(n_samples_per_region=2000)
    out_csv = DATA_DIR / "indian_weather_rain_dataset.csv"
    df.to_csv(out_csv, index=False)
    print(f"Generated {len(df)} records saved to {out_csv}")
    print(f"Rain occurrence distribution:\n{df['rain_occurrence'].value_counts(normalize=True)}")
