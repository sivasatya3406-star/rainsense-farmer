/**
 * RainSense Farmer - Main Application Orchestrator
 */

class RainSenseApp {
  constructor() {
    this.currentLat = 16.3067;
    this.currentLon = 80.4365;
    this.currentName = "Guntur Farm";
    this.searchDebounceTimer = null;
  }

  async init() {
    // 1. Initialize Localization
    const langSelect = document.getElementById("language-select");
    if (langSelect) {
      langSelect.value = window.i18n.currentLang;
      langSelect.addEventListener("change", (e) => {
        window.i18n.setLanguage(e.target.value);
        this.updateTexts();
      });
    }
    window.i18n.applyTranslations();

    // 2. Initialize Demo Mode
    window.demoManager.init();

    // 3. Initialize Map with callback
    window.rainSenseMap.init("leaflet-map", (lat, lon, name) => {
      this.onLocationChanged(lat, lon, name);
    });

    // 4. Initialize Location Search
    this.initSearch();

    // 5. Initialize Navigation
    this.initNavigation();

    // 6. Load Saved Locations
    await window.locationsManager.loadSavedLocations();

    // 7. Initial Data Fetch
    await this.refreshAllData();

    // 8. Auto refresh every 10 minutes
    setInterval(() => {
      this.refreshAllData(true);
    }, 600000);
  }

  initNavigation() {
    document.querySelectorAll(".nav-link").forEach(link => {
      link.addEventListener("click", (e) => {
        const targetSection = link.getAttribute("data-target");
        if (targetSection) {
          e.preventDefault();
          document.querySelectorAll(".nav-link").forEach(l => l.classList.remove("active"));
          link.classList.add("active");
          
          const sectionEl = document.getElementById(targetSection);
          if (sectionEl) {
            sectionEl.scrollIntoView({ behavior: 'smooth' });
          }
        }
      });
    });
  }

  initSearch() {
    const searchInput = document.getElementById("location-search-input");
    const dropdown = document.getElementById("search-dropdown-menu");
    const searchBtn = document.getElementById("location-search-btn");

    if (!searchInput || !dropdown) return;

    searchInput.addEventListener("input", (e) => {
      clearTimeout(this.searchDebounceTimer);
      const val = e.target.value.trim();
      if (val.length < 2) {
        dropdown.classList.remove("show");
        return;
      }

      this.searchDebounceTimer = setTimeout(async () => {
        try {
          const res = await window.api.searchLocations(val);
          const results = res.results || [];
          if (results.length === 0) {
            dropdown.innerHTML = `<div style="padding: 0.75rem 1rem; color: var(--text-muted); font-size: 0.85rem;">No Indian towns or villages found.</div>`;
          } else {
            dropdown.innerHTML = results.map(r => `
              <div class="search-item" onclick="window.app.selectSearchResult('${r.name.replace(/'/g, "\\'")}', ${r.latitude}, ${r.longitude}, '${(r.district || '').replace(/'/g, "\\'")}')">
                <div>
                  <div class="search-item-main">📍 ${r.name}</div>
                  <div class="search-item-sub">${r.district ? r.district + ', ' : ''}${r.state || 'India'}</div>
                </div>
                <span style="font-size: 0.75rem; color: var(--color-primary); font-weight: 600;">Select</span>
              </div>
            `).join('');
          }
          dropdown.classList.add("show");
        } catch (err) {
          console.warn("Search error:", err);
        }
      }, 250);
    });

    // Hide dropdown on outside click
    document.addEventListener("click", (e) => {
      if (!searchInput.contains(e.target) && !dropdown.contains(e.target)) {
        dropdown.classList.remove("show");
      }
    });

    if (searchBtn) {
      searchBtn.addEventListener("click", () => {
        const val = searchInput.value.trim();
        if (val) {
          window.api.searchLocations(val).then(res => {
            if (res.results && res.results.length > 0) {
              const top = res.results[0];
              this.selectSearchResult(top.name, top.latitude, top.longitude, top.district);
            }
          });
        }
      });
    }
  }

  selectSearchResult(name, lat, lon, district) {
    const input = document.getElementById("location-search-input");
    const dropdown = document.getElementById("search-dropdown-menu");
    if (input) input.value = `${name}${district ? ' (' + district + ')' : ''}`;
    if (dropdown) dropdown.classList.remove("show");

    this.currentLat = lat;
    this.currentLon = lon;
    this.currentName = name;

    window.rainSenseMap.setLocation(lat, lon, name, true);
  }

  async onLocationChanged(lat, lon, name) {
    this.currentLat = lat;
    this.currentLon = lon;
    this.currentName = name;

    // Update location header label
    const locLabel = document.getElementById("selected-farm-name");
    if (locLabel) locLabel.textContent = name;

    const locCoords = document.getElementById("selected-farm-coords");
    if (locCoords) locCoords.textContent = `${lat.toFixed(4)}° N, ${lon.toFixed(4)}° E`;

    await this.refreshAllData();
  }

  async refreshAllData(silent = false) {
    const isDemo = window.demoManager.isDemoActive;
    const lat = this.currentLat;
    const lon = this.currentLon;

    if (!silent) {
      this.setLoadingState(true);
    }

    try {
      // Parallel fetch of telemetry with resilient per-endpoint handling
      const results = await Promise.allSettled([
        window.api.getLiveWeather(lat, lon, isDemo),
        window.api.getRainfallHistory(lat, lon, isDemo),
        window.api.getSoilMoisture(lat, lon, isDemo),
        window.api.getForecast(lat, lon, isDemo),
        window.api.getNearbyRain(lat, lon, isDemo),
        window.api.getRainMap(lat, lon, isDemo),
        window.api.getAIInsights(lat, lon, "Crops", isDemo)
      ]);

      const liveWeather = results[0].status === "fulfilled" ? results[0].value : null;
      const rainHistory = results[1].status === "fulfilled" ? results[1].value : null;
      const soilMoisture = results[2].status === "fulfilled" ? results[2].value : null;
      const forecast = results[3].status === "fulfilled" ? results[3].value : null;
      const nearbyAnalysis = results[4].status === "fulfilled" ? results[4].value : null;
      const rainMap = results[5].status === "fulfilled" ? results[5].value : null;
      const insights = results[6].status === "fulfilled" ? results[6].value : null;

      // 1. Render Rain Cells on Map
      if (rainMap && rainMap.precipitation_cells) {
        window.rainSenseMap.renderRainCells(rainMap.precipitation_cells);
      } else if (nearbyAnalysis && nearbyAnalysis.zones_detected) {
        window.rainSenseMap.renderRainCells(nearbyAnalysis.zones_detected);
      }

      // 2. Update Current Rain Card
      if (liveWeather || nearbyAnalysis) {
        this.renderCurrentRainCard(liveWeather, rainHistory, nearbyAnalysis);
      }

      // 3. Update 15 km Monitoring Card
      if (nearbyAnalysis) {
        this.render15kmMonitoringCard(nearbyAnalysis);
      }

      // 4. Update Soil Moisture Card
      if (soilMoisture) {
        this.renderSoilMoistureCard(soilMoisture);
      }

      // 5. Update Forecast Section
      if (forecast) {
        this.renderForecastSection(forecast);
      }

      // 6. Update AI Advisory
      if (insights) {
        window.insightsRenderer.renderAdvisory("ai-insights-container", insights);
      }

      // 7. Update Charts
      if (rainHistory && rainHistory.hourly_history_24h) {
        window.rainCharts.renderRainHistoryChart("rain-history-chart", rainHistory.hourly_history_24h, rainHistory.daily_history);
      }
      if (soilMoisture && soilMoisture.trend_series) {
        window.rainCharts.renderSoilMoistureChart("soil-moisture-chart", soilMoisture.trend_series);
      }

      // Staleness warning check
      const staleBanner = document.getElementById("stale-warning-banner");
      if (staleBanner) {
        if (liveWeather && liveWeather._is_stale) {
          staleBanner.style.display = "block";
          staleBanner.textContent = "⚠️ " + liveWeather._stale_warning;
        } else {
          staleBanner.style.display = "none";
        }
      }

      // Update timestamp badges
      document.querySelectorAll(".live-timestamp-badge").forEach(el => {
        el.textContent = (liveWeather && liveWeather.timestamp)
          ? new Date(liveWeather.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
          : "Just now";
      });

    } catch (err) {
      console.error("Data refresh failed:", err);
      this.showToast("Notice: Live data connection delayed. Showing available estimates.");
    } finally {
      this.setLoadingState(false);
    }
  }

  renderCurrentRainCard(live = {}, history = {}, nearby = null) {
    // Farm rain condition must use authoritative fields from nearby-rain if available:
    // is_raining_at_farm, farm_rain_rate_mm, farm_rain_status
    let rate = 0;
    let isRaining = false;
    let farmStatus = null;

    if (nearby && (nearby.farm_rain_rate_mm !== undefined || nearby.farm_rain_status !== undefined || nearby.is_raining_at_farm !== undefined)) {
      rate = Number(nearby.farm_rain_rate_mm !== undefined && nearby.farm_rain_rate_mm !== null ? nearby.farm_rain_rate_mm : (live ? live.precipitation_rate_mm_hr || 0 : 0));
      isRaining = nearby.is_raining_at_farm !== undefined ? Boolean(nearby.is_raining_at_farm) : rate > 0.05;
      farmStatus = nearby.farm_rain_status || null;
    } else if (live) {
      rate = Number(live.precipitation_rate_mm_hr || 0);
      isRaining = rate > 0.05;
    }

    // Status Pill
    const pill = document.getElementById("current-rain-status-pill");
    if (pill) {
      if (farmStatus) {
        const lower = farmStatus.toLowerCase();
        if (lower.includes("heavy") || rate >= 10.0) {
          pill.className = "rain-status-pill status-heavy-rain";
          pill.innerHTML = `🔴 ${farmStatus}`;
        } else if (lower.includes("moderate") || rate >= 2.5) {
          pill.className = "rain-status-pill status-moderate-rain";
          pill.innerHTML = `🟠 ${farmStatus}`;
        } else if (isRaining || rate > 0.05 || lower.includes("light") || lower.includes("rain") || lower.includes("drizzle")) {
          pill.className = "rain-status-pill status-light-rain";
          pill.innerHTML = `🟡 ${farmStatus}`;
        } else {
          pill.className = "rain-status-pill status-no-rain";
          pill.innerHTML = `🟢 ${farmStatus}`;
        }
      } else {
        if (rate >= 10.0) {
          pill.className = "rain-status-pill status-heavy-rain";
          pill.innerHTML = "🔴 Heavy Rain";
        } else if (rate >= 2.5) {
          pill.className = "rain-status-pill status-moderate-rain";
          pill.innerHTML = "🟠 Moderate Rain";
        } else if (rate > 0.05) {
          pill.className = "rain-status-pill status-light-rain";
          pill.innerHTML = "🟡 Light Rain";
        } else {
          pill.className = "rain-status-pill status-no-rain";
          pill.innerHTML = "🟢 No Rain";
        }
      }
    }

    // Big rate display
    const rateEl = document.getElementById("current-rain-rate");
    if (rateEl) rateEl.textContent = rate.toFixed(1);

    // Accumulation stats
    const hist = history || {};
    const setVal = (id, val) => {
      const el = document.getElementById(id);
      if (el) el.textContent = (val || 0).toFixed(1) + " mm";
    };
    setVal("rain-acc-1h", hist.last_1h_mm);
    setVal("rain-acc-3h", hist.last_3h_mm);
    setVal("rain-acc-6h", hist.last_6h_mm);
    setVal("rain-acc-24h", hist.last_24h_mm);
    setVal("rain-acc-72h", hist.last_72h_mm);

    // Weather params
    const l = live || {};
    const tempEl = document.getElementById("current-temperature");
    if (tempEl) tempEl.textContent = Math.round(l.temperature_c || 28) + "°C";

    const humEl = document.getElementById("current-humidity");
    if (humEl) humEl.textContent = Math.round(l.humidity_pct || 65) + "%";

    const windEl = document.getElementById("current-wind");
    if (windEl) windEl.textContent = Math.round(l.wind_speed_kmh || 10) + " km/h";
  }

  render15kmMonitoringCard(analysis) {
    if (!analysis) return;

    const nearbySummaryEl = document.getElementById("nearby-rain-summary");
    const distEl = document.getElementById("nearest-rain-distance");
    const dirEl = document.getElementById("nearest-rain-direction");
    const covEl = document.getElementById("rain-zone-coverage");
    const movEl = document.getElementById("rain-movement-desc");
    const confEl = document.getElementById("rain-movement-confidence");
    const countEl = document.getElementById("active-rain-cells-count");
    const zonesListEl = document.getElementById("active-rain-cells-list");

    // 1. Nearest Rain Activity Distance
    if (distEl) {
      if (analysis.nearest_rain_distance_km !== null && analysis.nearest_rain_distance_km !== undefined) {
        distEl.textContent = `${analysis.nearest_rain_distance_km} km`;
      } else if (analysis.rain_nearby === false) {
        distEl.textContent = "No rain in 15 km";
      } else {
        distEl.textContent = "--";
      }
    }

    // 2. Nearest Rain Direction & Intensity
    if (dirEl) {
      if (analysis.nearest_rain_direction) {
        const intensity = analysis.nearest_rain_intensity || "Active";
        dirEl.textContent = `${analysis.nearest_rain_direction} (${intensity})`;
      } else if (analysis.rain_nearby === false) {
        dirEl.textContent = "None";
      } else {
        dirEl.textContent = "--";
      }
    }

    // 3. Rain Coverage (15 km Zone)
    if (covEl) {
      if (analysis.rain_coverage_pct !== null && analysis.rain_coverage_pct !== undefined) {
        const covPct = Number(analysis.rain_coverage_pct);
        covEl.textContent = `${Number.isInteger(covPct) ? covPct : covPct.toFixed(1)}% of 15 km zone`;
      } else {
        covEl.textContent = "--";
      }
    }

    // 4. Rain Movement Direction & Confidence
    if (movEl) {
      movEl.textContent = analysis.rain_movement || "Rain activity may be moving toward your selected area.";
    }
    if (confEl && analysis.rain_movement_confidence !== null && analysis.rain_movement_confidence !== undefined) {
      const confVal = Number(analysis.rain_movement_confidence);
      const confPct = Math.round(confVal <= 1.0 ? confVal * 100 : confVal);
      confEl.textContent = `(${confPct}% confidence)`;
    } else if (confEl) {
      confEl.textContent = "";
    }

    // 5. Active Rain Cells in 15 km Radius Count
    const zones = analysis.zones_detected || [];
    if (countEl) {
      countEl.textContent = zones.length;
    }

    // 6. Primary Nearby Rain Banner
    if (nearbySummaryEl) {
      if (analysis.nearest_rain_distance_km !== null && analysis.nearest_rain_distance_km !== undefined) {
        nearbySummaryEl.innerHTML = `
          <div style="background: #fff7ed; border-left: 4px solid #ea580c; padding: 0.65rem 0.85rem; border-radius: var(--radius-sm); font-size: 0.88rem; color: #9a3412; font-weight: 600;">
            🌧 Rain detected <strong>${analysis.nearest_rain_distance_km} km ${analysis.nearest_rain_direction || ''}</strong> from your selected location.
          </div>
        `;
      } else if (analysis.is_raining_at_farm) {
        nearbySummaryEl.innerHTML = `
          <div style="background: #eff6ff; border-left: 4px solid #0284c7; padding: 0.65rem 0.85rem; border-radius: var(--radius-sm); font-size: 0.88rem; color: #075985; font-weight: 600;">
            🌧 Rain currently occurring directly at your farm location (${analysis.farm_rain_rate_mm || 0} mm/hr).
          </div>
        `;
      } else {
        nearbySummaryEl.innerHTML = `
          <div style="background: #f0fdf4; border-left: 4px solid #16a34a; padding: 0.65rem 0.85rem; border-radius: var(--radius-sm); font-size: 0.88rem; color: #166534; font-weight: 600;">
            🟢 No precipitation detected anywhere inside your 15 km monitoring zone.
          </div>
        `;
      }
    }

    // 7. Active Rain Zones List
    if (zonesListEl) {
      if (zones.length === 0) {
        zonesListEl.innerHTML = `<p style="font-size: 0.8rem; color: var(--text-muted);">No rain cells active within 15 km radius.</p>`;
      } else {
        zonesListEl.innerHTML = zones.map(z => `
          <div style="display: flex; justify-content: space-between; align-items: center; padding: 0.45rem 0; border-bottom: 1px solid var(--border-color-subtle); font-size: 0.82rem;">
            <div>
              <span style="font-weight: 700; color: var(--text-primary);">${z.name || ('Rain Cell ' + (z.zone_id || ''))}</span>
              <span style="color: var(--text-muted); margin-left: 0.35rem;">(${z.distance_km} km ${z.direction})</span>
            </div>
            <div style="text-align: right;">
              <span style="font-weight: 700; color: ${z.rainfall_rate_mm >= 4.0 ? '#ea580c' : '#16a34a'};">${Number(z.rainfall_rate_mm || 0).toFixed(1)} mm/hr</span>
              <span style="font-size: 0.72rem; color: var(--text-muted); display: block;">${z.intensity || 'Rain'}</span>
            </div>
          </div>
        `).join('');
      }
    }
  }

  renderSoilMoistureCard(soil) {
    const surfEl = document.getElementById("soil-moisture-surface");
    const rootEl = document.getElementById("soil-moisture-root");
    const statusPill = document.getElementById("soil-status-pill");
    const riskEl = document.getElementById("soil-waterlog-risk");
    const barEl = document.getElementById("soil-moisture-bar");

    const surfaceVal = soil.surface_moisture_pct || 40;
    const rootVal = soil.root_moisture_pct || 45;
    const avgMoist = Math.round((surfaceVal + rootVal) / 2);

    if (surfEl) surfEl.textContent = `${surfaceVal.toFixed(1)}%`;
    if (rootEl) rootEl.textContent = `${rootVal.toFixed(1)}%`;
    if (riskEl) riskEl.textContent = soil.waterlogging_risk || "Low";

    if (statusPill) {
      statusPill.textContent = soil.status || "Moderate";
      if (soil.status === "Dry") {
        statusPill.style.background = "#fef3c7";
        statusPill.style.color = "#b45309";
      } else if (soil.status === "Very Wet") {
        statusPill.style.background = "#fee2e2";
        statusPill.style.color = "#991b1b";
      } else {
        statusPill.style.background = "#dcfce7";
        statusPill.style.color = "#15803d";
      }
    }

    if (barEl) {
      barEl.style.width = `${Math.min(100, Math.max(5, avgMoist))}%`;
    }
  }

  renderForecastSection(fc) {
    const hourlyContainer = document.getElementById("hourly-forecast-grid");
    if (!hourlyContainer) return;

    const hourly = fc.hourly || [];
    if (hourly.length === 0) {
      hourlyContainer.innerHTML = `<p style="color: var(--text-muted);">Forecast updating...</p>`;
      return;
    }

    // Render next 8 hours
    hourlyContainer.innerHTML = hourly.slice(0, 8).map(h => `
      <div style="background: #f8fafc; padding: 0.75rem 0.6rem; border-radius: var(--radius-md); text-align: center; border: 1px solid var(--border-color-subtle);">
        <div style="font-size: 0.75rem; font-weight: 700; color: var(--text-secondary);">${h.formatted_hour}</div>
        <div style="font-size: 1.25rem; margin: 0.2rem 0;">${h.rain_probability_pct > 40 ? '🌧' : (h.rain_probability_pct > 15 ? '🌦' : '☀️')}</div>
        <div style="font-size: 0.85rem; font-weight: 800; color: var(--color-primary);">${h.rain_probability_pct}%</div>
        <div style="font-size: 0.7rem; color: var(--text-muted);">${h.expected_rainfall_mm} mm</div>
      </div>
    `).join('');
  }

  setLoadingState(loading) {
    const spinner = document.getElementById("global-refresh-spinner");
    if (spinner) spinner.style.display = loading ? "inline-block" : "none";
  }

  showToast(message) {
    let container = document.querySelector(".toast-container");
    if (!container) {
      container = document.createElement("div");
      container.className = "toast-container";
      document.body.appendChild(container);
    }

    const toast = document.createElement("div");
    toast.className = "toast";
    toast.textContent = message;
    container.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = "0";
      toast.style.transition = "opacity 0.3s ease";
      setTimeout(() => toast.remove(), 300);
    }, 4000);
  }

  updateTexts() {
    window.i18n.applyTranslations();
    window.locationsManager.renderCounter();
  }
}

window.app = new RainSenseApp();

// Boot on DOM ready
document.addEventListener("DOMContentLoaded", () => {
  window.app.init();
});
