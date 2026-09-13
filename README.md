# RainSense Farmer 🌧🌾
> **“Know Where It Rains. Know Your Soil. Make Better Farming Decisions.”**

An intelligent, map-based rain monitoring and soil moisture intelligence platform built specifically for farmers across India.

---

## 📋 Production Readiness & Inspection Summary

| Category | Technical Specification |
|---|---|
| **Frontend Framework** | Semantic HTML5, Vanilla CSS3 (Design Tokens, Glassmorphism, Responsive Grid/Flexbox), Vanilla ES6+ Modular JavaScript, Leaflet.js 1.9.4 (Interactive Maps), Chart.js 4.4.1 (Analytics). Zero heavy build steps; high performance on mobile devices. |
| **Backend Framework** | Python 3.10+ with FastAPI, Starlette, Uvicorn, and Pydantic v2. Clean modular REST API structure with lifespan context management. |
| **ML Architecture** | Scikit-Learn Random Forest Classifier (`rain_classifier.joblib`) for rain occurrence (0/1) and Gradient Boosting Regressor (`rain_regressor.joblib`) for rainfall amount (mm). Strictly backward-looking time lag features (`rainfall_1h`, `rainfall_3h`, `rainfall_6h`, `rainfall_12h`, `rainfall_24h`, `rainfall_72h`, temperature, humidity, pressure, wind, surface/root soil moisture). Accompanied by `model_metadata.json` for transparent feature importance explainability. Models are packaged in Git (<4 MB) and auto-train if absent. |
| **Database Requirements** | SQLite by default (`./rainsense.db`, auto-migrated via `backend/database/schema.sql` on startup). Fully PostgreSQL-compatible by setting `DATABASE_URL=postgresql://...` (compatible with Render PostgreSQL, Supabase, Neon, AWS RDS). |
| **API Dependencies** | Open-Meteo Weather Forecast API (free, open, no API key required), Open-Meteo Geocoding API, ERA5-Land & GPM/IMERG hydrology models. Optional API keys supported for private or commercial tiers. |
| **Environment Variables** | Centralized in `backend/config.py` and documented in `.env.example`. Supports `PORT`, `HOST`, `ENVIRONMENT`, `DEBUG`, `CORS_ORIGINS`, `DATABASE_URL`, `DB_PATH`, `NEXT_PUBLIC_API_URL`, `VITE_API_URL`. |
| **Deployment Target** | **Frontend**: Vercel (static edge deployment with `vercel.json`). **Backend + ML**: Render (Python Web Service with `render.yaml` Blueprint). |

---

## 🌾 Core Features

1. **Interactive Rain Map with 15 km Radius Monitoring Zone**
   - Click or tap anywhere in India to place an animated farm pin.
   - Automatically renders a **15 km Rain Monitoring Zone** with translucent radius styling and dynamic tooltips.
   - Displays real-time precipitation intensity cells (0 mm/hr, Light, Moderate, Heavy, Very Heavy).
   - Strict geodesic distance calculations (Haversine formula).

2. **15 km Spatial Rain Telemetry**
   - Detects if rain is occurring at the selected farm.
   - Calculates distance to nearest rainfall activity (e.g. *"Rain detected 4.8 km northeast"*).
   - Calculates rain coverage percentage within the 15 km perimeter.
   - Estimates cloud movement direction (Approaching farm, Moving away, Stationary).
   - Zone-by-zone concentric breakdown (At Farm, Within 5 km, Within 10 km, Within 15 km).

3. **Multi-Source Data Fusion & Transparent Badging**
   - Explicitly differentiates data provenance using visual badges:
     - `LIVE / OBSERVED`: Real-time sensor and satellite observations.
     - `FORECAST`: Atmospheric numerical weather model predictions.
     - `AI PREDICTION`: Machine learning model inferences.
     - `DEMO DATA`: Controlled presentation scenario.
   - Data staleness alerts: displays *"Last updated X minutes ago"* and warnings when data is delayed.

4. **Soil Moisture Intelligence (0–9 cm Depth)**
   - Surface soil moisture (0–3 cm) and Root-zone moisture (3–9 cm) saturation percentages.
   - Status classifications: *Dry*, *Moderate*, *Moist*, *Very Wet*.
   - Dynamic waterlogging risk assessment (*Low*, *Moderate*, *High*, *Critical*).
   - Labeled transparently as *"Estimated soil moisture (Hydrology model)"*.

5. **AI Farming Advisory Engine**
   - Pragmatic, farmer-friendly recommendations using cautious language (*"Consider"*, *"May"*, *"Check field conditions"*):
     - **💧 Irrigation Advice**: Delay pumping if recent 24h rain is high or rain cells are active nearby.
     - **🌿 Spraying & Chemical Advisory**: Postpone spraying if rain is likely within 4–6 hours to prevent chemical wash-off.
     - **🚜 Soil Drainage & Bunds**: Guidance on clearing bund trenches in low-lying plots when saturation is high.
   - Model confidence scoring (e.g. 84%) with top contributing explainable factors.

6. **5 Saved Locations Management & Comparison**
   - Farmers can save up to **5 farming locations** (enforced on both client and backend).
   - **Locations Comparison Table**: Side-by-side comparison highlighting:
     - 💧 **Wettest Location**
     - ☀️ **Driest Location**
     - 🌧 **Highest 24h Rainfall**
     - 📍 **Nearest Active Rain**

7. **Multilingual Localization**
   - Instant real-time language switching:
     - **English**
     - **Telugu (తెలుగు)**
     - **Hindi (हिंदी)**

8. **Section 54 Demo Presentation Mode**
   - One-click demo toggle loading the **Guntur, Andhra Pradesh (16.3067, 80.4365)** scenario with 6.4 km NE moderate rain cell, 54% soil moisture, 12.6 mm 24h rain, 68% rain chance, and AI guidance.

---

## 🚀 Production Deployment Guide

### 1. Push Project to GitHub

1. Initialize git repository if not already done:
   ```bash
   git init
   git add .
   git commit -m "feat: production ready RainSense Farmer application"
   ```
2. Create a new repository on [GitHub](https://github.com/new).
3. Link and push:
   ```bash
   git remote add origin https://github.com/<your-username>/rainsense-farmer.git
   git branch -M main
   git push -u origin main
   ```

---

### 2. Deploy Backend + ML to Render

You can deploy the backend in two ways: via the **Render Blueprint (`render.yaml`)** or as a **Manual Web Service**.

#### Option A: One-Click Render Blueprint (Recommended)
1. Log in to [Render](https://dashboard.render.com/).
2. Click **New +** $\to$ **Blueprint**.
3. Select your `rainsense-farmer` repository.
4. Render will automatically detect `render.yaml` and configure:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
   - **Health Check**: `/health`
5. Click **Apply**. Once deployed, copy your public backend URL:
   `https://rainsense-farmer-backend.onrender.com`

#### Option B: Manual Web Service
1. On Render Dashboard, click **New +** $\to$ **Web Service**.
2. Connect your GitHub repository.
3. Configure the following fields:
   - **Name**: `rainsense-farmer-backend`
   - **Region**: Oregon (or your preferred region)
   - **Branch**: `main`
   - **Root Directory**: Leave blank (repository root)
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
4. Under **Environment Variables**, add:
   - `HOST`: `0.0.0.0`
   - `ENVIRONMENT`: `production`
   - `DEBUG`: `false`
   - `CORS_ORIGINS`: `*` (or your Vercel URL e.g. `https://rainsense-farmer.vercel.app`)
5. Under **Health Check Path**, enter: `/health`
6. Click **Create Web Service**.

---

### 3. Deploy Frontend to Vercel

1. Log in to [Vercel](https://vercel.com/new).
2. Click **Add New...** $\to$ **Project** and import your `rainsense-farmer` GitHub repository.
3. Configure the project:
   - **Framework Preset**: Other
   - **Root Directory**: `./` (or click Edit and select `frontend`)
   - **Build Command**: Leave default (or `echo 'Static build ready'`)
   - **Output Directory**: `frontend` (if root directory is `./`) or `.` (if root directory is `frontend`)
4. Under **Environment Variables**, add:
   - `NEXT_PUBLIC_API_URL`: Your Render backend URL (e.g. `https://rainsense-farmer-backend.onrender.com`)
   - `VITE_API_URL`: Your Render backend URL (e.g. `https://rainsense-farmer-backend.onrender.com`)
5. Click **Deploy**.
6. Vercel will deploy your site in seconds and provide your public URL:
   `https://rainsense-farmer.vercel.app`

---

### 4. Custom Domains & HTTPS

- **Vercel**: Go to **Project Settings** $\to$ **Domains** $\to$ Add your custom domain (e.g. `rainsense.in`). Vercel automatically provisions free SSL/HTTPS certificates.
- **Render**: Go to **Settings** $\to$ **Custom Domains** $\to$ Add `api.rainsense.in` with a CNAME record. Render automatically provisions free Let's Encrypt SSL/HTTPS certificates.
- **CORS Update**: Once your custom domains are active, set `CORS_ORIGINS=https://rainsense.in,https://www.rainsense.in` in Render environment variables.

---

## 📱 Mobile Compatibility & Testing

The application is thoroughly optimized and tested for mobile devices:

- **Touch & Gesture Interactions**:
  - `tap: false` configured on Leaflet 1.9.4 to prevent tap event suppression on iOS Safari and mobile Chrome.
  - Native `pointerdown` and `pointerup` handlers for responsive marker placement.
  - Touch-friendly zoom buttons and touch panning.
  - Comfortable touch targets ($\ge 44\times 44\text{ px}$) across all buttons and dropdowns.
- **Responsive Layout Breakpoints**:
  - Mobile Small: $320\text{ px} - 375\text{ px}$ (iPhone SE, Galaxy A)
  - Mobile Standard: $390\text{ px} - 430\text{ px}$ (iPhone 14/15/16 Pro Max, Pixel 8, Galaxy S24)
  - Tablet: $768\text{ px} - 1024\text{ px}$ (iPad, Galaxy Tab)
  - Desktop: $1280\text{ px} - 1440\text{ px}+$
- **Viewport & Text Zoom**:
  - `<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0, viewport-fit=cover">`.
  - All form inputs styled with `16px` base font size to prevent automatic iOS Safari viewport zooming on focus.
- **Mobile Network Resilience**:
  - Offline/slow network caching with LocalStorage.
  - User-friendly error banners and retry prompts instead of technical stack traces.
  - Local vendor bundle for Leaflet and Chart.js with CDN fallback to protect against third-party CDN throttling on Indian cellular networks (Jio, Airtel, Vi).

---

## 🧪 Local Verification & Tests

Run the test suite locally:
```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

17 automated unit and integration tests verify:
- Exact Haversine geodesic calculations.
- Strict $15.0\text{ km}$ boundary filtering ($15.0\text{ km}$ included, $>15.0\text{ km}$ excluded).
- Rain intensity classification thresholds.
- ML model loading, feature validation, and prediction output ranges.
- Strict 5-saved-locations enforcement (rejection of 6th location with HTTP 400).
- FastAPI endpoints (`/health`, `/api/weather`, `/api/rainfall`, `/api/nearby-rain`, `/api/location/search`, `/api/admin/status`, `/api/predict`, `/api/demo`).

---

## 🛠 Deployment Checklist

- [x] All `localhost` and `127.0.0.1` references removed from client-side API requests.
- [x] Client uses relative `/api/...` or dynamically configured `NEXT_PUBLIC_API_URL` / `VITE_API_URL`.
- [x] Backend listens on `0.0.0.0` and reads `$PORT` environment variable.
- [x] CORS middleware configured to allow public frontend domains and Vercel preview URLs.
- [x] Production health check endpoint active at `GET /health`.
- [x] Machine learning models (`rain_classifier.joblib`, `rain_regressor.joblib`, `model_metadata.json`) tracked in repository with zero external file path dependencies.
- [x] Mobile touch responsiveness verified (iOS Safari, Android Chrome).
- [x] Leaflet and Chart.js bundled locally in `frontend/vendor/` with CDN fallback.
- [x] `requirements.txt`, `package.json`, `vercel.json`, `render.yaml`, `.gitignore`, and `.env.example` created and validated.

---

## ⚙️ Configuration Reference

| Parameter | Default | Production Recommendation |
|---|---|---|
| `HOST` | `0.0.0.0` | `0.0.0.0` |
| `PORT` | `8000` | Injected by Render via `$PORT` |
| `ENVIRONMENT` | `development` | `production` |
| `DEBUG` | `true` | `false` |
| `CORS_ORIGINS` | `*` | `*` or `https://your-app.vercel.app` |
| `DATABASE_URL` | `sqlite:///./rainsense.db` | PostgreSQL URI on Render for multi-instance |
| `CACHE_TTL_SECONDS` | `600` | `600` (10 minutes) |
| `NEXT_PUBLIC_API_URL` | `""` | `https://your-backend.onrender.com` (Vercel env) |
| `VITE_API_URL` | `""` | `https://your-backend.onrender.com` (Vercel env) |

---

## ⚠️ Known Limitations

1. **Satellite Precipitation Delay**: Satellite estimates (GPM/IMERG) typically update every 30 to 60 minutes. The UI automatically displays a *"Last updated X minutes ago"* indicator to maintain transparency.
2. **Soil Moisture Resolution**: Modeled volumetric water content (ERA5-Land) operates at a $0.1^\circ \times 0.1^\circ$ ($\sim 9\text{ km}$) spatial grid and should be used as agricultural decision support alongside ground field inspection.
3. **Browser Geolocation**: Mobile browsers require a secure HTTPS context to grant GPS location access. Ensure the public URL uses `https://`.
