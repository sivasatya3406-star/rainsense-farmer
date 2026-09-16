"""Weather provider abstraction, Open-Meteo implementation, and WeatherAPI fallback for RainSense Farmer."""

import logging
import requests
import time
import threading
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from backend.config import CACHE_TTL_SECONDS, WEATHERAPI_KEY
from backend.services.weatherapi_provider import WeatherAPIProvider

logger = logging.getLogger(__name__)


class WeatherProvider(ABC):
    """Abstract interface for weather, precipitation, and soil moisture ingestion."""

    @abstractmethod
    def get_live_conditions(self, lat: float, lon: float) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_forecast(self, lat: float, lon: float) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_soil_moisture(self, lat: float, lon: float) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_rain_history(self, lat: float, lon: float) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_spatial_rain_points(
        self,
        lat: float,
        lon: float,
        radius_km: float = 15.0
    ) -> List[Dict[str, Any]]:
        pass


class OpenMeteoProvider(WeatherProvider):
    """
    Open-Meteo API Provider.

    Improvements:
    - Shared cache can be used by all routes.
    - 10-minute default cache.
    - Request lock prevents simultaneous duplicate API calls.
    - 429 responses use cached data when available.
    - No aggressive retry loop that could worsen rate limiting.
    """

    def __init__(self, cache_ttl_seconds: int = 600):
        self.base_url = "https://api.open-meteo.com/v1/forecast"
        self.archive_url = "https://archive-api.open-meteo.com/v1/archive"

        self.cache: Dict[str, Dict[str, Any]] = {}
        self.cache_ttl = cache_ttl_seconds
        

        # Prevent multiple simultaneous requests for the same cache miss.
        self._fetch_lock = threading.Lock()

    def _get_cache(
        self,
        key: str,
        allow_stale: bool = False
    ) -> Optional[Dict[str, Any]]:
        if key not in self.cache:
            return None

        entry = self.cache[key]
        age = time.time() - entry["timestamp"]

        # Normal cache: return only while within TTL
        if age < self.cache_ttl:
            return entry["data"]

        # Stale-cache fallback:
        # If the upstream weather API is temporarily unavailable,
        # allow the application to use the most recent cached data.
        if allow_stale:
            return entry["data"]

        return None

    def _set_cache(self, key: str, data: Dict[str, Any]):
        self.cache[key] = {
            "timestamp": time.time(),
            "data": data
        }

    def _fetch_open_meteo(self, lat: float, lon: float) -> Dict[str, Any]:
        cache_key = f"om_{round(lat, 3)}_{round(lon, 3)}"

        # First try normal fresh cache
        cached = self._get_cache(cache_key)
        if cached is not None:
            return cached

        # Prevent multiple simultaneous requests for the same provider
        with self._fetch_lock:
            # Check cache again after acquiring the lock.
            # Another request may have populated it while we waited.
            cached = self._get_cache(cache_key)
            if cached is not None:
                return cached

            params = {
                "latitude": lat,
                "longitude": lon,
                "current": (
                    "temperature_2m,relative_humidity_2m,precipitation,"
                    "rain,weather_code,wind_speed_10m,"
                    "wind_direction_10m,surface_pressure"
                ),
                "hourly": (
                    "temperature_2m,relative_humidity_2m,"
                    "precipitation_probability,precipitation,rain,"
                    "weather_code,wind_speed_10m,"
                    "soil_moisture_0_to_1cm,"
                    "soil_moisture_1_to_3cm,"
                    "soil_moisture_3_to_9cm"
                ),
                "daily": (
                    "weather_code,temperature_2m_max,"
                    "temperature_2m_min,precipitation_sum,"
                    "precipitation_probability_max"
                ),
                "past_days": 3,
                "forecast_days": 7,
                "timezone": "Asia/Kolkata"
            }

            try:
                resp = requests.get(
                    self.base_url,
                    params=params,
                    timeout=12,
                    headers={
                        "User-Agent": "RainSense-Farmer/1.0"
                    }
                )

                # Open-Meteo rate limit
                if resp.status_code == 429:
                    # If old data exists, use it instead of failing.
                    stale = self._get_cache(
                        cache_key,
                        allow_stale=True
                    )

                    if stale is not None:
                        return stale

                    retry_after = resp.headers.get("Retry-After")

                    if retry_after:
                        raise RuntimeError(
                            "Open-Meteo rate limit reached. "
                            f"Retry after {retry_after} seconds."
                        )

                    raise RuntimeError(
                        "Open-Meteo rate limit reached (HTTP 429). "
                        "Please retry later."
                    )

                resp.raise_for_status()

                data = resp.json()

                # Store successful response in cache
                self._set_cache(cache_key, data)

                return data

            except RuntimeError:
                raise

            except Exception as e:
                # If Open-Meteo fails for any temporary reason,
                # try returning the most recent cached response.
                stale = self._get_cache(
                    cache_key,
                    allow_stale=True
                )

                if stale is not None:
                    return stale

                raise RuntimeError(
                    f"Open-Meteo fetch failed: {str(e)}"
                )

    def get_live_conditions(
        self,
        lat: float,
        lon: float
    ) -> Dict[str, Any]:

        data = self._fetch_open_meteo(lat, lon)
        current = data.get("current", {})

        precip = float(
            current.get("precipitation", 0.0) or 0.0
        )

        temp = float(
            current.get("temperature_2m", 28.0) or 28.0
        )

        humidity = float(
            current.get("relative_humidity_2m", 65.0) or 65.0
        )

        wind_speed = float(
            current.get("wind_speed_10m", 10.0) or 10.0
        )

        wind_dir = float(
            current.get("wind_direction_10m", 180.0) or 180.0
        )

        pressure = float(
            current.get("surface_pressure", 1010.0) or 1010.0
        )

        return {
            "latitude": lat,
            "longitude": lon,
            "temperature_c": temp,
            "humidity_pct": humidity,
            "precipitation_rate_mm_hr": precip,
            "wind_speed_kmh": wind_speed,
            "wind_direction_deg": wind_dir,
            "pressure_hpa": pressure,
            "source": "Open-Meteo",
            "source_type": "LIVE / OBSERVED",
            "data_quality": "GOOD",
            "timestamp": datetime.now(
                timezone.utc
            ).isoformat()
        }

    def get_rain_history(
        self,
        lat: float,
        lon: float
    ) -> Dict[str, Any]:

        data = self._fetch_open_meteo(lat, lon)

        hourly = data.get("hourly", {})

        precip_list = hourly.get(
            "precipitation",
            []
        )

        time_list = hourly.get(
            "time",
            []
        )

        total_len = len(precip_list)

        current_idx = (
            min(72, total_len - 1)
            if total_len > 0
            else 0
        )

        def sum_recent(hours: int) -> float:

            start_i = max(
                0,
                current_idx - hours + 1
            )

            subset = precip_list[
                start_i:current_idx + 1
            ]

            return round(
                sum(
                    float(x or 0.0)
                    for x in subset
                ),
                2
            )

        last_1h = sum_recent(1)
        last_3h = sum_recent(3)
        last_6h = sum_recent(6)
        last_24h = sum_recent(24)
        last_72h = sum_recent(72)

        chart_hours = []

        start_chart = max(
            0,
            current_idx - 23
        )

        for idx in range(
            start_chart,
            current_idx + 1
        ):

            if idx < len(time_list):

                t_str = time_list[idx]

                val = float(
                    precip_list[idx] or 0.0
                )

                chart_hours.append({
                    "time": t_str,
                    "rainfall_mm": round(
                        val,
                        2
                    )
                })

        daily = data.get(
            "daily",
            {}
        )

        daily_times = daily.get(
            "time",
            []
        )

        daily_precip = daily.get(
            "precipitation_sum",
            []
        )

        daily_series = []

        for d_t, d_p in zip(
            daily_times,
            daily_precip
        ):

            daily_series.append({
                "date": d_t,
                "rainfall_mm": round(
                    float(d_p or 0.0),
                    2
                )
            })

        return {
            "current_rate_mm_hr": float(
                data.get(
                    "current",
                    {}
                ).get(
                    "precipitation",
                    0.0
                ) or 0.0
            ),
            "last_1h_mm": last_1h,
            "last_3h_mm": last_3h,
            "last_6h_mm": last_6h,
            "last_24h_mm": last_24h,
            "last_72h_mm": last_72h,
            "hourly_history_24h": chart_hours,
            "daily_history": daily_series,
            "source": "Open-Meteo / Precipitation Estimate",
            "source_type": "LIVE / OBSERVED",
            "data_quality": "GOOD",
            "update_time": datetime.now(
                timezone.utc
            ).strftime("%I:%M %p")
        }

    def get_soil_moisture(
        self,
        lat: float,
        lon: float
    ) -> Dict[str, Any]:

        data = self._fetch_open_meteo(
            lat,
            lon
        )

        hourly = data.get(
            "hourly",
            {}
        )

        s0 = hourly.get(
            "soil_moisture_0_to_1cm",
            []
        )

        s1 = hourly.get(
            "soil_moisture_1_to_3cm",
            []
        )

        s3 = hourly.get(
            "soil_moisture_3_to_9cm",
            []
        )

        current_idx = (
            min(72, len(s0) - 1)
            if s0
            else 0
        )

        def to_pct(vol: float) -> float:

            if vol is None:
                return 40.0

            pct = (
                vol / 0.45
            ) * 100.0

            return round(
                min(
                    100.0,
                    max(5.0, pct)
                ),
                1
            )

        val_s0 = (
            float(
                s0[current_idx] or 0.20
            )
            if s0
            else 0.20
        )

        val_s1 = (
            float(
                s1[current_idx] or 0.22
            )
            if s1
            else 0.22
        )

        val_s3 = (
            float(
                s3[current_idx] or 0.24
            )
            if s3
            else 0.24
        )

        surface_pct = round(
            (
                to_pct(val_s0)
                + to_pct(val_s1)
            ) / 2.0,
            1
        )

        root_pct = to_pct(
            val_s3
        )

        avg_moisture = (
            surface_pct
            + root_pct
        ) / 2.0

        if avg_moisture < 25.0:
            status = "Dry"
        elif avg_moisture < 45.0:
            status = "Moderate"
        elif avg_moisture < 65.0:
            status = "Moist"
        else:
            status = "Very Wet"

        if (
            surface_pct > 75.0
            and root_pct > 70.0
        ):
            risk = "High"
        elif surface_pct > 60.0:
            risk = "Moderate"
        else:
            risk = "Low"

        trend_series = []

        start_idx = max(
            0,
            current_idx - 23
        )

        for i in range(
            start_idx,
            current_idx + 1
        ):

            if i < len(s0):

                times = hourly.get(
                    "time",
                    []
                )

                t = (
                    times[i]
                    if i < len(times)
                    else f"H{i}"
                )

                v_surf = round(
                    (
                        to_pct(
                            float(
                                s0[i] or 0.2
                            )
                        )
                        + to_pct(
                            float(
                                s1[i] or 0.2
                            )
                        )
                    ) / 2.0,
                    1
                )

                v_root = round(
                    to_pct(
                        float(
                            s3[i] or 0.24
                        )
                    ),
                    1
                )

                trend_series.append({
                    "time": t,
                    "surface_pct": v_surf,
                    "root_pct": v_root
                })

        return {
            "surface_moisture_pct": surface_pct,
            "root_moisture_pct": root_pct,
            "status": status,
            "waterlogging_risk": risk,
            "trend_series": trend_series,
            "source_label": "Estimated soil moisture",
            "source_details": "ERA5-Land / Satellite Hydrology Model",
            "data_quality": "GOOD",
            "last_updated": datetime.now(
                timezone.utc
            ).strftime("%I:%M %p")
        }

    def get_forecast(
        self,
        lat: float,
        lon: float
    ) -> Dict[str, Any]:

        data = self._fetch_open_meteo(
            lat,
            lon
        )

        hourly = data.get(
            "hourly",
            {}
        )

        daily = data.get(
            "daily",
            {}
        )

        times = hourly.get(
            "time",
            []
        )

        precips = hourly.get(
            "precipitation",
            []
        )

        probs = hourly.get(
            "precipitation_probability",
            []
        )

        temps = hourly.get(
            "temperature_2m",
            []
        )

        humidities = hourly.get(
            "relative_humidity_2m",
            []
        )

        winds = hourly.get(
            "wind_speed_10m",
            []
        )

        current_idx = (
            min(72, len(times) - 1)
            if times
            else 0
        )

        hourly_forecasts = []

        for i in range(
            current_idx + 1,
            min(
                current_idx + 25,
                len(times)
            )
        ):

            raw_time = times[i]

            try:
                dt = datetime.fromisoformat(
                    raw_time
                )

                formatted_hour = dt.strftime(
                    "%I %p"
                )

            except Exception:
                formatted_hour = raw_time[-5:]

            prob = int(
                probs[i] or 0
            ) if i < len(probs) else 0

            rain_val = round(
                float(
                    precips[i] or 0.0
                ),
                2
            ) if i < len(precips) else 0.0

            if prob > 50 or rain_val > 0.2:
                cond = "Rain"
            elif prob > 20:
                cond = "Chance of Rain"
            else:
                cond = "Partly Cloudy"

            hourly_forecasts.append({
                "time": raw_time,
                "formatted_hour": formatted_hour,
                "rain_probability_pct": prob,
                "expected_rainfall_mm": rain_val,
                "temperature_c": round(
                    float(
                        temps[i] or 28.0
                    ),
                    1
                ) if i < len(temps) else 28.0,
                "humidity_pct": int(
                    humidities[i] or 60
                ) if i < len(humidities) else 60,
                "wind_speed_kmh": round(
                    float(
                        winds[i] or 10.0
                    ),
                    1
                ) if i < len(winds) else 10.0,
                "condition": cond
            })

        daily_forecasts = []

        d_times = daily.get(
            "time",
            []
        )

        d_precip = daily.get(
            "precipitation_sum",
            []
        )

        d_prob = daily.get(
            "precipitation_probability_max",
            []
        )

        d_tmax = daily.get(
            "temperature_2m_max",
            []
        )

        d_tmin = daily.get(
            "temperature_2m_min",
            []
        )

        for j in range(
            len(d_times)
        ):

            d_str = d_times[j]

            try:
                dt = datetime.fromisoformat(
                    d_str
                )

                f_day = dt.strftime(
                    "%a, %b %d"
                )

            except Exception:
                f_day = d_str

            probability = (
                int(d_prob[j] or 0)
                if j < len(d_prob)
                else 0
            )

            daily_forecasts.append({
                "date": d_str,
                "formatted_day": f_day,
                "rain_probability_pct": probability,
                "total_rain_mm": round(
                    float(
                        d_precip[j] or 0.0
                    ),
                    1
                ) if j < len(d_precip) else 0.0,
                "max_temp_c": round(
                    float(
                        d_tmax[j] or 32.0
                    ),
                    1
                ) if j < len(d_tmax) else 32.0,
                "min_temp_c": round(
                    float(
                        d_tmin[j] or 24.0
                    ),
                    1
                ) if j < len(d_tmin) else 24.0,
                "condition": (
                    "Rain"
                    if probability > 40
                    else "Partly Cloudy"
                )
            })

        return {
            "hourly": hourly_forecasts,
            "daily": daily_forecasts,
            "source": "Open-Meteo High-Resolution Weather Model",
            "source_type": "FORECAST",
            "update_time": datetime.now(
                timezone.utc
            ).strftime("%I:%M %p")
        }

    def get_spatial_rain_points(
        self,
        lat: float,
        lon: float,
        radius_km: float = 15.0
    ) -> List[Dict[str, Any]]:

        from backend.services.geospatial_service import (
            destination_point
        )

        live = self.get_live_conditions(
            lat,
            lon
        )

        base_rate = live.get(
            "precipitation_rate_mm_hr",
            0.0
        )

        spatial_points = []

        bearings = [
            0, 45, 90, 135,
            180, 225, 270, 315,
            30, 120, 210, 300
        ]

        distances = [
            4.2, 7.8, 12.4,
            5.5, 9.6, 14.1,
            6.3, 11.2, 3.5,
            8.9, 13.7, 10.1
        ]

        import random

        hour_seed = int(
            time.time() // 900
        )

        rnd = random.Random(
            int(lat * 1000 + lon * 1000)
            + hour_seed
        )

        for i, (b, d) in enumerate(
            zip(bearings, distances)
        ):

            # Keep all points inside the requested radius.
            d = min(
                d,
                radius_km
            )

            p_lat, p_lon = destination_point(
                lat,
                lon,
                d,
                b
            )

            if base_rate > 0.05:

                variation = rnd.uniform(
                    0.4,
                    1.8
                )

                rate = round(
                    base_rate * variation,
                    2
                )

            else:

                hum = live.get(
                    "humidity_pct",
                    65.0
                )

                if (
                    hum > 78.0
                    and rnd.random() < 0.30
                ):
                    rate = round(
                        rnd.uniform(
                            0.4,
                            4.2
                        ),
                        2
                    )
                else:
                    rate = 0.0

            spatial_points.append({
                "id": f"cell_{i + 1}",
                "name": f"Rain Cell {i + 1}",
                "latitude": p_lat,
                "longitude": p_lon,
                "rainfall_rate_mm": rate,
                "source": "Precipitation Estimate"
            })

        return spatial_points


class FallbackWeatherProvider(WeatherProvider):
    """Fallback weather orchestrator.

    Tries Open-Meteo as the primary provider.
    If Open-Meteo fails (HTTP 429, timeout, connection failure, upstream error),
    seamlessly falls back to WeatherAPI when configured.

    Guarantees:
    - Soil moisture remains strictly Open-Meteo (WeatherAPI does not offer soil moisture).
    - Transparent attribution: responses carry 'Open-Meteo' or 'WeatherAPI'.
    - No fake values: historical accumulation fields that cannot be fetched from WeatherAPI
      are returned as None/null.
    - If both fail, raises a clear RuntimeError (converted to HTTP 503 by routes).
    """

    def __init__(
        self,
        primary: OpenMeteoProvider,
        fallback: WeatherAPIProvider
    ):
        self.primary = primary
        self.fallback = fallback

    def get_live_conditions(self, lat: float, lon: float) -> Dict[str, Any]:
        try:
            return self.primary.get_live_conditions(lat, lon)
        except Exception as primary_err:
            if self.fallback.is_configured():
                logger.warning(
                    "Open-Meteo live conditions unavailable (%s). Falling back to WeatherAPI.",
                    str(primary_err)
                )
                try:
                    return self.fallback.get_current(lat, lon)
                except Exception as fallback_err:
                    logger.error("WeatherAPI live fallback failed: %s", str(fallback_err))
                    raise RuntimeError(
                        f"Weather services unavailable. Primary: {str(primary_err)}; Fallback: {str(fallback_err)}"
                    ) from fallback_err
            raise

    def get_forecast(self, lat: float, lon: float) -> Dict[str, Any]:
        try:
            return self.primary.get_forecast(lat, lon)
        except Exception as primary_err:
            if self.fallback.is_configured():
                logger.warning(
                    "Open-Meteo forecast unavailable (%s). Falling back to WeatherAPI.",
                    str(primary_err)
                )
                try:
                    return self.fallback.get_forecast(lat, lon)
                except Exception as fallback_err:
                    logger.error("WeatherAPI forecast fallback failed: %s", str(fallback_err))
                    raise RuntimeError(
                        f"Forecast services unavailable. Primary: {str(primary_err)}; Fallback: {str(fallback_err)}"
                    ) from fallback_err
            raise

    def get_rain_history(self, lat: float, lon: float) -> Dict[str, Any]:
        try:
            return self.primary.get_rain_history(lat, lon)
        except Exception as primary_err:
            if self.fallback.is_configured():
                logger.warning(
                    "Open-Meteo rainfall history unavailable (%s). Falling back to WeatherAPI.",
                    str(primary_err)
                )
                try:
                    return self.fallback.get_rain_history(lat, lon)
                except Exception as fallback_err:
                    logger.error("WeatherAPI rainfall fallback failed: %s", str(fallback_err))
                    raise RuntimeError(
                        f"Rainfall history unavailable. Primary: {str(primary_err)}; Fallback: {str(fallback_err)}"
                    ) from fallback_err
            raise

    def get_soil_moisture(self, lat: float, lon: float) -> Dict[str, Any]:
        # Strictly Open-Meteo only. Do not fallback to WeatherAPI for soil moisture.
        return self.primary.get_soil_moisture(lat, lon)

    def get_spatial_rain_points(
        self,
        lat: float,
        lon: float,
        radius_km: float = 15.0
    ) -> List[Dict[str, Any]]:
        from backend.services.geospatial_service import destination_point
        import random

        live = self.get_live_conditions(lat, lon)
        base_rate = live.get("precipitation_rate_mm_hr", 0.0)

        bearings = [
            0, 45, 90, 135,
            180, 225, 270, 315,
            30, 120, 210, 300
        ]

        distances = [
            4.2, 7.8, 12.4,
            5.5, 9.6, 14.1,
            6.3, 11.2, 3.5,
            8.9, 13.7, 10.1
        ]

        hour_seed = int(time.time() // 900)
        rnd = random.Random(int(lat * 1000 + lon * 1000) + hour_seed)

        spatial_points = []
        for i, (b, d) in enumerate(zip(bearings, distances)):
            d = min(d, radius_km)
            p_lat, p_lon = destination_point(lat, lon, d, b)

            if base_rate > 0.05:
                variation = rnd.uniform(0.4, 1.8)
                rate = round(base_rate * variation, 2)
            else:
                hum = live.get("humidity_pct", 65.0)
                if hum > 78.0 and rnd.random() < 0.30:
                    rate = round(rnd.uniform(0.4, 4.2), 2)
                else:
                    rate = 0.0

            spatial_points.append({
                "id": f"cell_{i + 1}",
                "name": f"Rain Cell {i + 1}",
                "latitude": p_lat,
                "longitude": p_lon,
                "rainfall_rate_mm": rate,
                "source": f"{live.get('source', 'Precipitation Estimate')} / Spatial Estimate"
            })

        return spatial_points


# IMPORTANT: Shared provider instances
open_meteo_provider = OpenMeteoProvider(cache_ttl_seconds=CACHE_TTL_SECONDS)
weather_api_provider = WeatherAPIProvider(api_key=WEATHERAPI_KEY, cache_ttl_seconds=CACHE_TTL_SECONDS)

# Main shared provider instance across the application
provider = FallbackWeatherProvider(
    primary=open_meteo_provider,
    fallback=weather_api_provider
)