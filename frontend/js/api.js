/**
 * RainSense Farmer - API Client & Mobile-Ready Offline Cache Layer
 * Works seamlessly across public HTTPS URLs, reverse proxies, and mobile browsers.
 */

// Determine API Base URL:
// 1. Check for runtime environment variables (window.NEXT_PUBLIC_API_URL, window.VITE_API_URL, window.__API_BASE__)
// 2. Check for meta tags (<meta name="next-public-api-url">, <meta name="vite-api-url">, <meta name="api-base-url">)
// 3. Check query parameter (?api=... or ?api_url=...) and persist in localStorage
// 4. Check localStorage
// 5. Default to relative '' (works when frontend & backend are served on same origin or reverse proxy)
function getApiBaseUrl() {
  if (typeof window !== "undefined") {
    // 1. Runtime window environment variables (Vite, Next.js, or script injected)
    if (window.NEXT_PUBLIC_API_URL) return window.NEXT_PUBLIC_API_URL.replace(/\/+$/, "");
    if (window.VITE_API_URL) return window.VITE_API_URL.replace(/\/+$/, "");
    if (window.__API_BASE__) return window.__API_BASE__.replace(/\/+$/, "");
    
    // 2. Meta tags
    const metaNext = document.querySelector('meta[name="next-public-api-url"]');
    if (metaNext && metaNext.content && metaNext.content.trim() !== "") return metaNext.content.trim().replace(/\/+$/, "");

    const metaVite = document.querySelector('meta[name="vite-api-url"]');
    if (metaVite && metaVite.content && metaVite.content.trim() !== "") return metaVite.content.trim().replace(/\/+$/, "");

    const metaBase = document.querySelector('meta[name="api-base-url"]');
    if (metaBase && metaBase.content && metaBase.content.trim() !== "") return metaBase.content.trim().replace(/\/+$/, "");

    // 3. Query parameter & local storage
    try {
      if (window.location && window.location.search) {
        const params = new URLSearchParams(window.location.search);
        const paramUrl = params.get("api") || params.get("api_url") || params.get("backend");
        if (paramUrl) {
          const clean = paramUrl.replace(/\/+$/, "");
          localStorage.setItem("rainsense_api_base", clean);
          return clean;
        }
      }
      const stored = localStorage.getItem("rainsense_api_base");
      if (stored && stored.trim() !== "") return stored.trim().replace(/\/+$/, "");
    } catch (e) {
      // Ignore storage errors on restricted webviews
    }
  }
  return ""; // Relative path ensures automatic HTTPS/HTTP, port, and host matching
}

const API_BASE = getApiBaseUrl();

class RainSenseAPI {
  constructor() {
    this.cachePrefix = "rainsense_cache_v2_";
  }

  _getCacheEntry(key) {
    try {
      const raw = localStorage.getItem(this.cachePrefix + key);
      if (!raw) return null;
      return JSON.parse(raw);
    } catch (e) {
      return null;
    }
  }

  _getCache(key, maxAgeSeconds = 600) {
    try {
      const entry = this._getCacheEntry(key);
      if (!entry) return null;
      if (Date.now() - entry.timestamp < maxAgeSeconds * 1000) {
        return entry.data;
      }
    } catch (e) {
      console.warn("Cache read error:", e);
    }
    return null;
  }

  _setCache(key, data) {
    try {
      localStorage.setItem(this.cachePrefix + key, JSON.stringify({
        timestamp: Date.now(),
        data: data
      }));
    } catch (e) {
      console.warn("Cache write error:", e);
    }
  }

  _buildUrl(endpoint, params = {}) {
    // If API_BASE is empty, use relative path with URLSearchParams
    const queryString = Object.keys(params)
      .filter(k => params[k] !== undefined && params[k] !== null)
      .map(k => `${encodeURIComponent(k)}=${encodeURIComponent(params[k])}`)
      .join("&");

    const base = API_BASE ? API_BASE : "";
    const cleanEndpoint = endpoint.startsWith("/") ? endpoint : `/${endpoint}`;
    return queryString ? `${base}${cleanEndpoint}?${queryString}` : `${base}${cleanEndpoint}`;
  }

  async _fetch(endpoint, params = {}, useCache = true, cacheTTL = 300) {
    const url = this._buildUrl(endpoint, params);
    const cacheKey = endpoint + JSON.stringify(params);

    if (useCache) {
      const cached = this._getCache(cacheKey, cacheTTL);
      if (cached) return cached;
    }

    try {
      const controller = new AbortController();
      // Mobile networks can be slower; 15s timeout
      const timeoutId = setTimeout(() => controller.abort(), 15000);

      const resp = await fetch(url, {
        signal: controller.signal,
        headers: {
          "Accept": "application/json"
        }
      });
      clearTimeout(timeoutId);

      if (!resp.ok) {
        const errorData = await resp.json().catch(() => ({ detail: resp.statusText }));
        throw new Error(errorData.detail || `Server status: ${resp.status}`);
      }

      const data = await resp.json();
      if (useCache) {
        this._setCache(cacheKey, data);
      }
      return data;
    } catch (err) {
      console.warn(`Fetch error for ${url}:`, err.message);
      // If mobile network fails, return cached data if available (up to 48 hours)
      const entry = this._getCacheEntry(cacheKey);
      if (entry && entry.data) {
        const minsAgo = Math.max(1, Math.round((Date.now() - entry.timestamp) / 60000));
        const stale = entry.data;
        stale._is_stale = true;
        stale._last_updated_mins = minsAgo;
        stale._stale_warning = `Unable to update live rainfall right now. Last updated: ${minsAgo} minutes ago.`;
        return stale;
      }
      // Return a clean farmer-friendly error message
      throw new Error("We couldn't update rainfall information right now. Please check your connection.");
    }
  }

  async getLiveWeather(lat, lon, demo = false) {
    return this._fetch("/api/weather", { lat, lon, demo });
  }

  async getRainfallHistory(lat, lon, demo = false) {
    return this._fetch("/api/rainfall", { lat, lon, demo });
  }

  async getSoilMoisture(lat, lon, demo = false) {
    return this._fetch("/api/soil-moisture", { lat, lon, demo });
  }

  async getForecast(lat, lon, demo = false) {
    return this._fetch("/api/forecast", { lat, lon, demo });
  }

  async getNearbyRain(lat, lon, demo = false) {
    return this._fetch("/api/nearby-rain", { lat, lon, demo });
  }

  async getRainMap(lat, lon, demo = false) {
    return this._fetch("/api/rain-map", { lat, lon, demo });
  }

  async getAIInsights(lat, lon, crop = "General Crops", demo = false) {
    return this._fetch("/api/insights", { lat, lon, crop, demo });
  }

  async searchLocations(q) {
    return this._fetch("/api/location/search", { q }, false);
  }

  async getSavedLocations() {
    return this._fetch("/api/saved-locations", {}, false);
  }

  async saveLocation(payload) {
    const url = this._buildUrl("/api/saved-locations");
    const resp = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json", "Accept": "application/json" },
      body: JSON.stringify(payload)
    });
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({ detail: "Failed to save location." }));
      throw new Error(err.detail || "Failed to save location.");
    }
    return resp.json();
  }

  async deleteSavedLocation(locId) {
    const url = this._buildUrl(`/api/saved-locations/${locId}`);
    const resp = await fetch(url, {
      method: "DELETE",
      headers: { "Accept": "application/json" }
    });
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({ detail: "Failed to delete location." }));
      throw new Error(err.detail || "Failed to delete location.");
    }
    return resp.json();
  }

  async compareLocations() {
    return this._fetch("/api/compare", {}, false);
  }

  async getAlerts() {
    return this._fetch("/api/alerts", {}, false);
  }

  async markAlertsRead() {
    const url = this._buildUrl("/api/alerts/mark-read");
    return fetch(url, { method: "POST" });
  }

  async getAdminStatus() {
    return this._fetch("/api/admin/status", {}, false);
  }

  async predictML(features) {
    const url = this._buildUrl("/api/predict");
    const resp = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json", "Accept": "application/json" },
      body: JSON.stringify(features)
    });
    if (!resp.ok) {
      throw new Error("Prediction service error.");
    }
    return resp.json();
  }
}

window.api = new RainSenseAPI();
