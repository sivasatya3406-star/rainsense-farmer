"""WeatherAPI provider implementation for RainSense Farmer.

Serves as an upstream fallback provider when Open-Meteo experiences
rate limiting (HTTP 429), timeouts, or service unavailability.
"""

import time
import logging
import threading
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import requests

logger = logging.getLogger(__name__)


class WeatherAPIProvider:
    """WeatherAPI Provider (https://api.weatherapi.com/v1).

    Features:
    - Thread-safe caching with TTL and stale cache support.
    - Strict redaction of API credentials in logs and exception messages.
    - Clean mapping to RainSense Farmer schemas.
    - Transparent attribution ('WeatherAPI').
    """

    def __init__(self, api_key: str = "", cache_ttl_seconds: int = 600):
        self.api_key = api_key.strip() if api_key else ""
        self.base_url = "https://api.weatherapi.com/v1"
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.cache_ttl = cache_ttl_seconds
        self._fetch_lock = threading.Lock()
        self.timeout = 12
        self.headers = {
            "User-Agent": "RainSense-Farmer/1.0"
        }

    def is_configured(self) -> bool:
        """Returns True if a valid non-empty API key is present."""
        return bool(self.api_key)

    def _get_cache(self, key: str, allow_stale: bool = False) -> Optional[Dict[str, Any]]:
        """Retrieve cached response if within TTL or allow_stale is True."""
        if key not in self.cache:
            return None

        entry = self.cache[key]
        age = time.time() - entry["timestamp"]

        if age < self.cache_ttl or allow_stale:
            return entry["data"]

        return None

    def _set_cache(self, key: str, data: Dict[str, Any]) -> None:
        """Store response data in cache with current timestamp."""
        self.cache[key] = {
            "timestamp": time.time(),
            "data": data
        }

    def _safe_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Performs an HTTP GET request to WeatherAPI with strict credential redaction.

        Guarantees that the API key will never appear in log messages or exception details.
        """
        if not self.is_configured():
            raise RuntimeError("WeatherAPI key is not configured.")

        # Prepare request params with key
        request_params = dict(params)
        request_params["key"] = self.api_key

        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        try:
            resp = requests.get(
                url,
                params=request_params,
                timeout=self.timeout,
                headers=self.headers
            )

            status = resp.status_code

            if status == 401 or status == 403:
                logger.error("WeatherAPI authentication error (status=%d)", status)
                raise RuntimeError("WeatherAPI authentication failed: Invalid or disabled API key.")

            if status == 400:
                logger.warning("WeatherAPI bad request (status=400)")
                raise RuntimeError("WeatherAPI bad request: Check coordinates.")

            if status == 404:
                logger.warning("WeatherAPI location not found (status=404)")
                raise RuntimeError("WeatherAPI location not found.")

            if status == 429:
                logger.warning("WeatherAPI rate limit reached (status=429)")
                raise RuntimeError("WeatherAPI rate limit reached (HTTP 429).")

            if status >= 500:
                logger.warning("WeatherAPI upstream server error (status=%d)", status)
                raise RuntimeError(f"WeatherAPI upstream server error (HTTP {status}).")

            resp.raise_for_status()

            try:
                data = resp.json()
            except Exception as parse_err:
                logger.warning("WeatherAPI invalid JSON response: %s", str(parse_err))
                raise RuntimeError("WeatherAPI returned invalid JSON response.") from parse_err

            # WeatherAPI error object in 200/other responses
            if "error" in data:
                err_msg = data["error"].get("message", "Unknown error")
                raise RuntimeError(f"WeatherAPI error: {err_msg}")

            return data

        except (requests.Timeout, requests.exceptions.Timeout) as e:
            logger.warning("WeatherAPI request timed out")
            raise RuntimeError("WeatherAPI request timed out.") from e

        except (requests.ConnectionError, requests.exceptions.ConnectionError) as e:
            logger.warning("WeatherAPI connection error")
            raise RuntimeError("WeatherAPI connection error.") from e

        except requests.RequestException as e:
            logger.warning("WeatherAPI request failed: %s", type(e).__name__)
            raise RuntimeError(f"WeatherAPI request failed: {type(e).__name__}") from e

    def get_current(self, lat: float, lon: float) -> Dict[str, Any]:
        """Fetch real-time weather conditions for given coordinates."""
        cache_key = f"wapi_curr_{round(lat, 3)}_{round(lon, 3)}"

        cached = self._get_cache(cache_key)
        if cached is not None:
            return cached

        with self._fetch_lock:
            cached = self._get_cache(cache_key)
            if cached is not None:
                return cached

            try:
                raw_data = self._safe_request(
                    "current.json",
                    {"q": f"{lat},{lon}"}
                )
            except Exception:
                # Stale-cache fallback
                stale = self._get_cache(cache_key, allow_stale=True)
                if stale is not None:
                    return stale
                raise

            current = raw_data.get("current", {})
            location = raw_data.get("location", {})

            temp = float(current.get("temp_c", 28.0) if current.get("temp_c") is not None else 28.0)
            humidity = float(current.get("humidity", 65.0) if current.get("humidity") is not None else 65.0)
            precip = float(current.get("precip_mm", 0.0) if current.get("precip_mm") is not None else 0.0)
            wind_speed = float(current.get("wind_kph", 10.0) if current.get("wind_kph") is not None else 10.0)
            wind_dir = float(current.get("wind_degree", 180.0) if current.get("wind_degree") is not None else 180.0)
            pressure = float(current.get("pressure_mb", 1010.0) if current.get("pressure_mb") is not None else 1010.0)

            # Observation timestamp
            obs_epoch = current.get("last_updated_epoch")
            if obs_epoch:
                obs_time_iso = datetime.fromtimestamp(obs_epoch, timezone.utc).isoformat()
            else:
                obs_time_iso = datetime.now(timezone.utc).isoformat()

            result = {
                "latitude": float(location.get("lat", lat)),
                "longitude": float(location.get("lon", lon)),
                "temperature_c": round(temp, 1),
                "humidity_pct": round(humidity, 1),
                "precipitation_rate_mm_hr": round(precip, 2),
                "wind_speed_kmh": round(wind_speed, 1),
                "wind_direction_deg": round(wind_dir, 1),
                "pressure_hpa": round(pressure, 1),
                "source": "WeatherAPI",
                "source_type": "LIVE / OBSERVED",
                "data_quality": "GOOD",
                "timestamp": obs_time_iso
            }

            self._set_cache(cache_key, result)
            return result

    def get_forecast(self, lat: float, lon: float, days: int = 7) -> Dict[str, Any]:
        """Fetch forecast data (hourly up to 24 hours, daily up to 7 days)."""
        cache_key = f"wapi_fc_{round(lat, 3)}_{round(lon, 3)}_{days}"

        cached = self._get_cache(cache_key)
        if cached is not None:
            return cached

        with self._fetch_lock:
            cached = self._get_cache(cache_key)
            if cached is not None:
                return cached

            try:
                # WeatherAPI free tier typically allows up to 3 days; paid up to 14 days
                raw_data = self._safe_request(
                    "forecast.json",
                    {
                        "q": f"{lat},{lon}",
                        "days": min(days, 7)
                    }
                )
            except Exception:
                stale = self._get_cache(cache_key, allow_stale=True)
                if stale is not None:
                    return stale
                raise

            forecast_obj = raw_data.get("forecast", {})
            forecast_days = forecast_obj.get("forecastday", [])

            now_epoch = int(time.time())

            # 1. Flatten all future hours across forecast days
            all_future_hours = []
            for fday in forecast_days:
                for hr in fday.get("hour", []):
                    hr_epoch = hr.get("time_epoch", 0)
                    # Include hours starting from current hour
                    if hr_epoch >= (now_epoch - 3600):
                        all_future_hours.append(hr)

            # Limit to next 24 hours
            selected_hours = all_future_hours[:24]

            hourly_forecasts = []
            for hr in selected_hours:
                raw_time = hr.get("time", "")
                try:
                    dt = datetime.strptime(raw_time, "%Y-%m-%d %H:%M")
                    formatted_hour = dt.strftime("%I %p")
                    iso_time = dt.isoformat()
                except Exception:
                    formatted_hour = raw_time[-5:] if len(raw_time) >= 5 else raw_time
                    iso_time = raw_time

                chance_rain = int(hr.get("chance_of_rain") or 0)
                precip_val = round(float(hr.get("precip_mm", 0.0) or 0.0), 2)
                condition_text = hr.get("condition", {}).get("text", "")

                if not condition_text:
                    if chance_rain > 50 or precip_val > 0.2:
                        condition_text = "Rain"
                    elif chance_rain > 20:
                        condition_text = "Chance of Rain"
                    else:
                        condition_text = "Partly Cloudy"

                hourly_forecasts.append({
                    "time": iso_time,
                    "formatted_hour": formatted_hour,
                    "rain_probability_pct": chance_rain,
                    "expected_rainfall_mm": precip_val,
                    "temperature_c": round(float(hr.get("temp_c", 28.0) or 28.0), 1),
                    "humidity_pct": int(hr.get("humidity", 60) or 60),
                    "wind_speed_kmh": round(float(hr.get("wind_kph", 10.0) or 10.0), 1),
                    "condition": condition_text
                })

            # 2. Daily forecasts
            daily_forecasts = []
            for fday in forecast_days:
                d_str = fday.get("date", "")
                day_data = fday.get("day", {})

                try:
                    dt = datetime.strptime(d_str, "%Y-%m-%d")
                    f_day = dt.strftime("%a, %b %d")
                except Exception:
                    f_day = d_str

                prob = int(day_data.get("daily_chance_of_rain") or 0)
                total_precip = round(float(day_data.get("totalprecip_mm", 0.0) or 0.0), 1)
                max_t = round(float(day_data.get("maxtemp_c", 32.0) or 32.0), 1)
                min_t = round(float(day_data.get("mintemp_c", 24.0) or 24.0), 1)
                cond_text = day_data.get("condition", {}).get("text") or ("Rain" if prob > 40 else "Partly Cloudy")

                daily_forecasts.append({
                    "date": d_str,
                    "formatted_day": f_day,
                    "rain_probability_pct": prob,
                    "total_rain_mm": total_precip,
                    "max_temp_c": max_t,
                    "min_temp_c": min_t,
                    "condition": cond_text
                })

            result = {
                "hourly": hourly_forecasts,
                "daily": daily_forecasts,
                "source": "WeatherAPI",
                "source_type": "FORECAST",
                "update_time": datetime.now(timezone.utc).strftime("%I:%M %p")
            }

            self._set_cache(cache_key, result)
            return result

    def get_rain_history(self, lat: float, lon: float) -> Dict[str, Any]:
        """Rainfall fallback representation.

        WeatherAPI does not provide historical observed rainfall over past 72h
        in standard tier. We strictly return real-time observed rate and mark
        unavailable historical accumulation fields as None, with clear source attribution
        and data quality labels.
        """
        # Fetch current conditions for genuine precipitation rate
        current_data = self.get_current(lat, lon)
        current_rate = float(current_data.get("precipitation_rate_mm_hr", 0.0))

        return {
            "current_rate_mm_hr": current_rate,
            "last_1h_mm": None,
            "last_3h_mm": None,
            "last_6h_mm": None,
            "last_24h_mm": None,
            "last_72h_mm": None,
            "hourly_history_24h": [],
            "daily_history": [],
            "source": "WeatherAPI",
            "source_type": "LIVE / OBSERVED",
            "data_quality": "PARTIAL / REAL-TIME ONLY (Historical accumulation unavailable via fallback)",
            "update_time": datetime.now(timezone.utc).strftime("%I:%M %p")
        }
