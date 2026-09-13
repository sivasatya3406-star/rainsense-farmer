/**
 * RainSense Farmer - Demo Mode Toggle & Presentation Scenario Controller
 */

class DemoModeManager {
  constructor() {
    this.isDemoActive = false;
  }

  init() {
    const toggle = document.getElementById("demo-mode-checkbox");
    if (toggle) {
      toggle.addEventListener("change", (e) => {
        this.setDemoMode(e.target.checked);
      });
    }
  }

  setDemoMode(active) {
    this.isDemoActive = active;
    const banner = document.getElementById("demo-mode-banner");
    if (banner) {
      banner.style.display = active ? "flex" : "none";
    }

    const toggle = document.getElementById("demo-mode-checkbox");
    if (toggle) toggle.checked = active;

    if (active) {
      window.app.showToast("⚡ DEMO MODE Activated: Loading Guntur Farm Presentation Scenario");
      // Set to Guntur coordinate
      window.rainSenseMap.setLocation(16.3067, 80.4365, "Guntur Farm (Demo)", true);
    } else {
      window.app.showToast("Switched to LIVE observational data.");
      window.app.refreshAllData();
    }
  }
}

window.demoManager = new DemoModeManager();
