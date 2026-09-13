"""API endpoints for notifications, alerts, and user settings."""
from fastapi import APIRouter
from backend.database.db import get_alerts, mark_alerts_read

router = APIRouter(prefix="/api", tags=["alerts"])

@router.get("/alerts")
def list_user_alerts(user_id: str = "farmer_demo_default"):
    """Returns alerts and notifications for the farmer."""
    alerts = get_alerts(user_id)
    unread_count = len([a for a in alerts if not a.get("is_read")])
    return {
        "unread_count": unread_count,
        "alerts": alerts
    }

@router.post("/alerts/mark-read")
def mark_read(user_id: str = "farmer_demo_default"):
    """Marks all alerts as read."""
    mark_alerts_read(user_id)
    return {"success": True, "message": "All notifications marked as read."}
