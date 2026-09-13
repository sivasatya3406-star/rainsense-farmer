/**
 * RainSense Farmer - 5 Saved Locations Manager & Comparison Engine
 */

class LocationsManager {
  constructor() {
    this.locations = [];
    this.maxLocations = 5;
  }

  async loadSavedLocations() {
    try {
      const data = await window.api.getSavedLocations();
      this.locations = data.locations || [];
      this.renderSavedCards();
      this.renderCounter();
      return this.locations;
    } catch (e) {
      console.warn("Error loading saved locations:", e);
      return [];
    }
  }

  renderCounter() {
    const counterEl = document.getElementById("saved-locations-counter");
    if (counterEl) {
      counterEl.textContent = `${this.locations.length} / ${this.maxLocations} ${window.i18n.t("locations_saved_counter")}`;
      if (this.locations.length >= this.maxLocations) {
        counterEl.style.color = "#b91c1c";
      } else {
        counterEl.style.color = "var(--text-secondary)";
      }
    }
  }

  renderSavedCards() {
    const container = document.getElementById("saved-locations-grid");
    if (!container) return;

    if (this.locations.length === 0) {
      container.innerHTML = `
        <div style="grid-column: 1 / -1; padding: 2rem; text-align: center; background: #fff; border-radius: var(--radius-lg); border: 1px dashed var(--border-color);">
          <p style="color: var(--text-muted); font-size: 0.95rem;">No saved farming locations yet. Click any point on the map or search your village to save your farm.</p>
        </div>
      `;
      return;
    }

    container.innerHTML = this.locations.map(loc => `
      <div class="card" style="border-left: 4px solid var(--color-primary);">
        <div class="card-header" style="padding-bottom: 0.4rem; margin-bottom: 0.5rem;">
          <div>
            <h4 style="font-size: 1rem; font-weight: 700; color: var(--color-primary-dark);">🌾 ${loc.name}</h4>
            <span style="font-size: 0.75rem; color: var(--text-muted);">${loc.district || ''}, ${loc.state || ''}</span>
          </div>
          <button class="btn btn-danger btn-sm" onclick="window.locationsManager.deleteLocation('${loc.id}')" title="Delete Location">🗑</button>
        </div>
        <div style="display: flex; flex-direction: column; gap: 0.35rem; font-size: 0.85rem; margin-top: 0.4rem;">
          <div style="display: flex; justify-content: space-between;">
            <span style="color: var(--text-muted);">Coordinates:</span>
            <span style="font-weight: 600;">${loc.latitude.toFixed(3)}, ${loc.longitude.toFixed(3)}</span>
          </div>
          ${loc.crop ? `
          <div style="display: flex; justify-content: space-between;">
            <span style="color: var(--text-muted);">Crop:</span>
            <span style="font-weight: 600; color: var(--color-primary);">${loc.crop}</span>
          </div>` : ''}
          ${loc.notes ? `
          <p style="font-size: 0.78rem; color: var(--text-secondary); background: #f8fafc; padding: 0.3rem 0.5rem; border-radius: 4px; margin-top: 0.2rem;">
            ${loc.notes}
          </p>` : ''}
        </div>
        <div style="margin-top: 0.85rem; display: flex; gap: 0.5rem;">
          <button class="btn btn-primary btn-sm w-full" onclick="window.locationsManager.flyToLocation(${loc.latitude}, ${loc.longitude}, '${loc.name}')">
            📍 Open on Map
          </button>
        </div>
      </div>
    `).join('');
  }

  openSaveModal(defaultName = "", lat = null, lon = null) {
    if (this.locations.length >= this.maxLocations) {
      alert("You can save up to 5 farming locations. Please remove an existing location first.");
      return;
    }

    const modal = document.getElementById("save-location-modal");
    if (!modal) return;

    document.getElementById("modal-loc-name").value = defaultName || "My Farm";
    document.getElementById("modal-loc-lat").value = (lat !== null ? lat : window.rainSenseMap.currentLat).toFixed(4);
    document.getElementById("modal-loc-lon").value = (lon !== null ? lon : window.rainSenseMap.currentLon).toFixed(4);
    document.getElementById("modal-loc-district").value = "";
    document.getElementById("modal-loc-crop").value = "";
    document.getElementById("modal-loc-notes").value = "";

    modal.classList.add("active");
  }

  closeSaveModal() {
    const modal = document.getElementById("save-location-modal");
    if (modal) modal.classList.remove("active");
  }

  async submitSaveLocation() {
    const name = document.getElementById("modal-loc-name").value.trim();
    const lat = parseFloat(document.getElementById("modal-loc-lat").value);
    const lon = parseFloat(document.getElementById("modal-loc-lon").value);
    const district = document.getElementById("modal-loc-district").value.trim();
    const crop = document.getElementById("modal-loc-crop").value.trim();
    const notes = document.getElementById("modal-loc-notes").value.trim();

    if (!name) {
      alert("Please provide a name for this farming location.");
      return;
    }

    try {
      await window.api.saveLocation({
        name,
        latitude: lat,
        longitude: lon,
        district: district || undefined,
        crop: crop || undefined,
        notes: notes || undefined
      });
      this.closeSaveModal();
      await this.loadSavedLocations();
      window.app.showToast(`🌾 Location "${name}" saved successfully!`);
    } catch (e) {
      alert(e.message || "Failed to save location.");
    }
  }

  async deleteLocation(locId) {
    if (!confirm("Are you sure you want to remove this saved farming location?")) return;
    try {
      await window.api.deleteSavedLocation(locId);
      await this.loadSavedLocations();
      window.app.showToast("Location removed.");
    } catch (e) {
      alert(e.message || "Could not delete location.");
    }
  }

  flyToLocation(lat, lon, name) {
    window.rainSenseMap.setLocation(lat, lon, name, true);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  async loadComparison() {
    const compContainer = document.getElementById("comparison-content");
    if (!compContainer) return;

    try {
      compContainer.innerHTML = `<p style="padding: 1rem; color: var(--text-muted);">Comparing your saved farming locations...</p>`;
      const res = await window.api.compareLocations();
      const items = res.comparison || [];
      const highlights = res.highlights || {};

      if (items.length === 0) {
        compContainer.innerHTML = `<p style="padding: 1.5rem; text-align: center; color: var(--text-muted);">Save at least 2 farming locations to compare rainfall and soil moisture.</p>`;
        return;
      }

      let highlightHtml = "";
      if (highlights.wettest_location) {
        highlightHtml = `
          <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 0.75rem; margin-bottom: 1rem;">
            <div style="background: #e0f2fe; padding: 0.75rem 1rem; border-radius: var(--radius-md); border-left: 4px solid #0284c7;">
              <span style="font-size: 0.75rem; color: #0369a1; font-weight: 700; text-transform: uppercase;">Wettest Location</span>
              <p style="font-size: 1rem; font-weight: 800; color: #0c4a6e;">💧 ${highlights.wettest_location}</p>
            </div>
            <div style="background: #fef3c7; padding: 0.75rem 1rem; border-radius: var(--radius-md); border-left: 4px solid #d97706;">
              <span style="font-size: 0.75rem; color: #b45309; font-weight: 700; text-transform: uppercase;">Driest Location</span>
              <p style="font-size: 1rem; font-weight: 800; color: #78350f;">☀️ ${highlights.driest_location}</p>
            </div>
            <div style="background: #dcfce7; padding: 0.75rem 1rem; border-radius: var(--radius-md); border-left: 4px solid #10b981;">
              <span style="font-size: 0.75rem; color: #15803d; font-weight: 700; text-transform: uppercase;">Highest 24h Rain</span>
              <p style="font-size: 1rem; font-weight: 800; color: #064e3b;">🌧 ${highlights.highest_rainfall}</p>
            </div>
            <div style="background: #f3e8ff; padding: 0.75rem 1rem; border-radius: var(--radius-md); border-left: 4px solid #8b5cf6;">
              <span style="font-size: 0.75rem; color: #6d28d9; font-weight: 700; text-transform: uppercase;">Active Rain Zone</span>
              <p style="font-size: 1rem; font-weight: 800; color: #4c1d95;">📍 ${highlights.nearest_active_rain}</p>
            </div>
          </div>
        `;
      }

      const rowsHtml = items.map(it => `
        <tr>
          <td style="font-weight: 700; color: var(--color-primary-dark);">${it.name}</td>
          <td>${it.current_rain_status === 'Raining' ? '🌧 ' + it.rain_rate_mm_hr + ' mm/hr' : '☀️ No Rain'}</td>
          <td>${it.has_nearby_rain ? '🌧 Detected in 15km' : '🟢 Clear'}</td>
          <td><span style="font-weight: 700; color: #d97706;">${it.soil_moisture_pct}%</span> (${it.soil_status})</td>
          <td style="font-weight: 700;">${it.rainfall_24h_mm} mm</td>
          <td>
            <button class="btn btn-outline btn-sm" onclick="window.locationsManager.flyToLocation(${it.latitude}, ${it.longitude}, '${it.name}')">
              View
            </button>
          </td>
        </tr>
      `).join('');

      compContainer.innerHTML = `
        ${highlightHtml}
        <div class="table-responsive">
          <table class="compare-table">
            <thead>
              <tr>
                <th>Location</th>
                <th>Current Rain</th>
                <th>Nearby 15km</th>
                <th>Soil Moisture</th>
                <th>24h Rain</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              ${rowsHtml}
            </tbody>
          </table>
        </div>
      `;
    } catch (e) {
      compContainer.innerHTML = `<p style="padding: 1rem; color: red;">Error comparing locations: ${e.message}</p>`;
    }
  }
}

window.locationsManager = new LocationsManager();
