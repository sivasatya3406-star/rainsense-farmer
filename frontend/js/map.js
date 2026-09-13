/**
 * RainSense Farmer - Leaflet Interactive Map Controller (Mobile & Touch Optimized)
 * Supports tap, pan, pinch-to-zoom, 15 km radius circle, and dynamic resize invalidation.
 */

class RainSenseMap {
  constructor() {
    this.map = null;
    this.farmMarker = null;
    this.radiusCircle15km = null;
    this.rainLayerGroup = null;
    this.soilLayerGroup = null;
    this.currentLat = 16.3067; // Default: Guntur, Andhra Pradesh
    this.currentLon = 80.4365;
    this.currentLocationName = "Guntur Farm";
    
    this.showRainLayer = true;
    this.show15kmZone = true;
    this.showSoilLayer = false;
    
    this.onLocationSelectedCallback = null;
  }

  init(containerId = "leaflet-map", onSelectCallback = null) {
    this.onLocationSelectedCallback = onSelectCallback;

    if (this.map) return; // already initialized

    // Check if Leaflet L is loaded; if not, retry gracefully
    if (typeof L === "undefined") {
      console.warn("Leaflet not loaded yet, retrying map initialization...");
      setTimeout(() => this.init(containerId, onSelectCallback), 200);
      return;
    }

    // Configure local icon paths to ensure zero 404s
    if (L.Icon && L.Icon.Default) {
      delete L.Icon.Default.prototype._getIconUrl;
      L.Icon.Default.mergeOptions({
        iconRetinaUrl: '/static/vendor/leaflet/images/marker-icon-2x.png',
        iconUrl: '/static/vendor/leaflet/images/marker-icon.png',
        shadowUrl: '/static/vendor/leaflet/images/marker-shadow.png',
      });
    }

    // Center on India or initial point
    // tap: false is CRITICAL for iOS Safari and mobile Chrome touch compatibility in Leaflet 1.9+
    this.map = L.map(containerId, {
      center: [this.currentLat, this.currentLon],
      zoom: 11,
      zoomControl: false, // custom position
      tap: false,         // Disable legacy simulated tap; fixes iOS & Android touch responsiveness
      touchZoom: true,
      dragging: true,
      bounceAtZoomLimits: true
    });

    // High quality OpenStreetMap / CartoDB tiles with HTTPS
    L.tileLayer("https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png", {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>',
      subdomains: "abcd",
      maxZoom: 19
    }).addTo(this.map);

    // Zoom control at bottom right (touch-friendly)
    L.control.zoom({ position: "bottomright" }).addTo(this.map);

    this.rainLayerGroup = L.layerGroup().addTo(this.map);
    this.soilLayerGroup = L.layerGroup();

    // Map click / tap event for mobile and desktop
    this.map.on("click", (e) => {
      this.setLocation(e.latlng.lat, e.latlng.lng, "Selected Field");
    });

    // Handle mobile orientation change & viewport resize (prevents gray/partial tiles)
    window.addEventListener("resize", () => {
      if (this.map) this.map.invalidateSize();
    });
    window.addEventListener("orientationchange", () => {
      setTimeout(() => { if (this.map) this.map.invalidateSize(); }, 350);
    });
    setTimeout(() => { if (this.map) this.map.invalidateSize(); }, 400);

    // Set initial farm
    this.setLocation(this.currentLat, this.currentLon, this.currentLocationName, false);
  }

  setLocation(lat, lon, name = "Selected Field", triggerCallback = true) {
    if (!this.map) return;
    this.currentLat = lat;
    this.currentLon = lon;
    this.currentLocationName = name;

    // Remove existing marker and circle
    if (this.farmMarker) this.map.removeLayer(this.farmMarker);
    if (this.radiusCircle15km) this.map.removeLayer(this.radiusCircle15km);

    // 1. Create 15 KM RADIUS CIRCLE
    if (this.show15kmZone) {
      this.radiusCircle15km = L.circle([lat, lon], {
        radius: 15000, // 15 km in meters
        color: "#0284c7", // Rain blue stroke
        weight: 2,
        dashArray: "6, 6",
        fillColor: "#38bdf8",
        fillOpacity: 0.09
      }).addTo(this.map);

      this.radiusCircle15km.bindTooltip("15 km Rain Monitoring Zone", {
        permanent: false,
        direction: "top",
        className: "radius-tooltip"
      });
    }

    // 2. Create Animated Farm Pin Marker with touch-friendly size
    const farmIcon = L.divIcon({
      className: "custom-farm-icon",
      html: `
        <div class="farmer-marker-pin" style="touch-action: manipulation;">
          <div class="farmer-marker-pulse"></div>
          🌱
        </div>
      `,
      iconSize: [32, 32],
      iconAnchor: [16, 16]
    });

    this.farmMarker = L.marker([lat, lon], { icon: farmIcon }).addTo(this.map);

    // Farm Marker Popup with mobile-friendly action buttons
    const escapedName = (name || "Selected Field").replace(/'/g, "\\'");
    const popupHtml = `
      <div class="popup-farm-header">
        <h4>📍 ${name}</h4>
      </div>
      <div class="popup-farm-body">
        <div class="popup-stat-row">
          <span class="popup-stat-label">Coordinates:</span>
          <span class="popup-stat-val">${lat.toFixed(4)}, ${lon.toFixed(4)}</span>
        </div>
        <div class="popup-stat-row">
          <span class="popup-stat-label">Monitoring:</span>
          <span class="popup-stat-val" style="color: var(--color-accent-rain);">15 km radius</span>
        </div>
        <button class="btn btn-primary btn-sm w-full" style="margin-top: 0.6rem; min-height: 40px;" onclick="window.locationsManager.openSaveModal('${escapedName}', ${lat}, ${lon})">
          🌾 Save Location
        </button>
      </div>
    `;
    this.farmMarker.bindPopup(popupHtml, { maxWidth: 280 });

    // Smooth pan
    this.map.panTo([lat, lon], { animate: true, duration: 0.6 });

    // Call update handler
    if (triggerCallback && typeof this.onLocationSelectedCallback === "function") {
      this.onLocationSelectedCallback(lat, lon, name);
    }
  }

  renderRainCells(cells = []) {
    if (!this.map || !this.rainLayerGroup) return;
    this.rainLayerGroup.clearLayers();
    if (!this.showRainLayer) return;

    cells.forEach((cell) => {
      const rate = cell.rainfall_rate_mm || 0;
      if (rate <= 0.05) return; // only render active rain cells

      let color = "#10b981"; // Light
      let radius = 1800;     // cell radius in meters
      let fillOpacity = 0.45;

      if (rate >= 10.0) {
        color = "#ef4444"; // Heavy
        radius = 2800;
        fillOpacity = 0.65;
      } else if (rate >= 4.0) {
        color = "#f97316"; // Moderate
        radius = 2200;
        fillOpacity = 0.55;
      } else if (rate >= 1.5) {
        color = "#eab308"; // Light
        radius = 1800;
        fillOpacity = 0.50;
      }

      // Draw precipitation cell circle
      const cellCircle = L.circle([cell.latitude, cell.longitude], {
        radius: radius,
        color: color,
        weight: 1,
        fillColor: color,
        fillOpacity: fillOpacity
      });

      const tooltipContent = `
        <div style="font-size: 0.85rem; line-height: 1.3;">
          <strong>${cell.name || 'Rain Cell'}</strong><br/>
          Rainfall Rate: <strong>${rate.toFixed(1)} mm/hr</strong><br/>
          Intensity: <strong>${cell.intensity || 'Active'}</strong><br/>
          ${cell.distance_km ? `Distance: <strong>${cell.distance_km} km ${cell.direction || ''}</strong>` : ''}
        </div>
      `;
      cellCircle.bindPopup(tooltipContent);
      this.rainLayerGroup.addLayer(cellCircle);

      // Add center cloud icon with touch-friendly dimensions
      const cellPin = L.divIcon({
        className: "radar-cell-pin",
        html: `<div style="background:${color}; width:24px; height:24px; border-radius:50%; display:flex; align-items:center; justify-content:center; color:#fff; font-size:12px; box-shadow: 0 2px 6px rgba(0,0,0,0.35);">🌧</div>`,
        iconSize: [24, 24],
        iconAnchor: [12, 12]
      });
      const cellMarker = L.marker([cell.latitude, cell.longitude], { icon: cellPin });
      cellMarker.bindPopup(tooltipContent);
      this.rainLayerGroup.addLayer(cellMarker);
    });
  }

  toggleRainLayer(enable) {
    this.showRainLayer = enable;
    if (!this.map) return;
    if (enable) {
      if (!this.map.hasLayer(this.rainLayerGroup)) {
        this.map.addLayer(this.rainLayerGroup);
      }
    } else {
      if (this.map.hasLayer(this.rainLayerGroup)) {
        this.map.removeLayer(this.rainLayerGroup);
      }
    }
  }

  toggle15kmZone(enable) {
    this.show15kmZone = enable;
    if (!this.map || !this.radiusCircle15km) return;
    if (enable) {
      this.map.addLayer(this.radiusCircle15km);
    } else {
      this.map.removeLayer(this.radiusCircle15km);
    }
  }

  locateUser() {
    if (!navigator.geolocation) {
      if (window.app && window.app.showToast) {
        window.app.showToast("Location access is unavailable. Search or select your farm on the map.");
      } else {
        alert("Location access is unavailable. Search or select your farm on the map.");
      }
      return;
    }

    if (window.app && window.app.showToast) {
      window.app.showToast("Detecting your GPS location...");
    }

    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const lat = pos.coords.latitude;
        const lon = pos.coords.longitude;
        this.setLocation(lat, lon, "My Current Location", true);
        if (window.app && window.app.showToast) {
          window.app.showToast("📍 Field location updated from GPS.");
        }
      },
      (err) => {
        console.warn("Geolocation error:", err.message);
        // Farmer-friendly message matching Section 12 requirements:
        if (window.app && window.app.showToast) {
          window.app.showToast("Location access is unavailable. Search or select your farm on the map.");
        }
      },
      { timeout: 10000, enableHighAccuracy: true, maximumAge: 60000 }
    );
  }
}

window.rainSenseMap = new RainSenseMap();
