from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.config import BASE_DIR, DEBUG, CORS_ORIGINS
from backend.database.db import init_db

# Import API routers
from backend.api.routes_weather import router as weather_router
from backend.api.routes_map import router as map_router
from backend.api.routes_locations import router as locations_router
from backend.api.routes_ml import router as ml_router
from backend.api.routes_insights import router as insights_router
from backend.api.routes_alerts import router as alerts_router
from backend.api.routes_admin import router as admin_router
from backend.api.routes_demo import router as demo_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(
    title="RainSense Farmer API",
    description="Intelligent rain and soil moisture monitoring platform for Indian farmers.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Enable CORS for local development, mobile devices, and public cloud deployments
if CORS_ORIGINS == "*":
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=r"https?://.*",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"]
    )
else:
    allowed_list = [o.strip() for o in CORS_ORIGINS.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_list,
        allow_origin_regex=r"https://.*\.vercel\.app",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"]
    )

# Register API Routers
app.include_router(weather_router)
app.include_router(map_router)
app.include_router(locations_router)
app.include_router(ml_router)
app.include_router(insights_router)
app.include_router(alerts_router)
app.include_router(admin_router)
app.include_router(demo_router)

# Health endpoint
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "app": "RainSense Farmer",
        "tagline": "Know Where It Rains. Know Your Soil. Make Better Farming Decisions."
    }

# Mount Frontend static files
frontend_dir = BASE_DIR / "frontend"
if frontend_dir.exists():
    # Mount /static for standard static assets
    app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")

    # Also mount direct subdirectories for maximum flexibility across reverse proxies & CDNs
    css_dir = frontend_dir / "css"
    if css_dir.exists():
        app.mount("/css", StaticFiles(directory=str(css_dir)), name="css")
    js_dir = frontend_dir / "js"
    if js_dir.exists():
        app.mount("/js", StaticFiles(directory=str(js_dir)), name="js")
    vendor_dir = frontend_dir / "vendor"
    if vendor_dir.exists():
        app.mount("/vendor", StaticFiles(directory=str(vendor_dir)), name="vendor")

    @app.get("/")
    @app.get("/index.html")
    def serve_frontend():
        return FileResponse(frontend_dir / "index.html")

