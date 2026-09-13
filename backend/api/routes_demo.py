"""API endpoint for Demo Mode scenario (Guntur Farm)."""
from fastapi import APIRouter
from backend.services.demo_service import get_demo_dashboard_data

router = APIRouter(prefix="/api", tags=["demo"])

@router.get("/demo")
def get_demo_scenario():
    """Returns the controlled demo presentation scenario."""
    return get_demo_dashboard_data()
