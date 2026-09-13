"""Database connection and initialization module for RainSense Farmer."""
import sqlite3
import json
import uuid
from typing import List, Dict, Any, Optional
from pathlib import Path
from backend.config import DB_PATH, BASE_DIR

def get_db_connection() -> sqlite3.Connection:
    """Returns a SQLite connection with row factory enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes tables from schema.sql and seeds default data sources and demo farmer if empty."""
    schema_file = BASE_DIR / "backend" / "database" / "schema.sql"
    with open(schema_file, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    with get_db_connection() as conn:
        conn.executescript(schema_sql)
        
        # Seed default data sources if not present
        sources = [
            ("Open-Meteo Weather API", "ONLINE", "High-resolution hourly weather models & radar estimation"),
            ("Satellite Precipitation (IMERG/GPM)", "ONLINE", "Multi-satellite precipitation estimates for India"),
            ("Soil Moisture Model (ERA5-Land)", "ONLINE", "Volumetric soil water analysis 0-9cm depth"),
            ("RainSense ML Predictor v1.0", "ONLINE", "Random Forest + Gradient Boosting trained models")
        ]
        for name, status, details in sources:
            conn.execute(
                """INSERT OR IGNORE INTO data_sources (name, status, details) 
                   VALUES (?, ?, ?)""",
                (name, status, details)
            )

        # Seed demo user if none exists
        cursor = conn.execute("SELECT COUNT(*) as cnt FROM users")
        if cursor.fetchone()["cnt"] == 0:
            demo_user_id = "farmer_demo_default"
            conn.execute(
                """INSERT INTO users (id, email, password_hash, full_name, language)
                   VALUES (?, ?, ?, ?, ?)""",
                (demo_user_id, "farmer@rainsense.in", "demo_password_hash", "Ramesh Patel", "en")
            )
            # Seed 2 initial sample farming locations
            conn.execute(
                """INSERT INTO saved_locations (id, user_id, name, latitude, longitude, district, state, crop, notes)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                ("loc_guntur_1", demo_user_id, "My Farm (Guntur)", 16.3067, 80.4365, "Guntur", "Andhra Pradesh", "Chilli & Cotton", "Black cotton soil, prone to monsoon waterlogging")
            )
            conn.execute(
                """INSERT INTO saved_locations (id, user_id, name, latitude, longitude, district, state, crop, notes)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                ("loc_vijayawada_2", demo_user_id, "East Field (Vijayawada)", 16.5062, 80.6480, "Krishna", "Andhra Pradesh", "Paddy Rice", "Canal irrigated alluvial soil")
            )
            
            # Seed initial welcome alerts
            conn.execute(
                """INSERT INTO alerts (id, user_id, location_id, alert_type, message)
                   VALUES (?, ?, ?, ?, ?)""",
                (str(uuid.uuid4()), demo_user_id, "loc_guntur_1", "info", "Welcome to RainSense Farmer. Real-time 15 km rain monitoring is active for your fields.")
            )
        conn.commit()

def get_saved_locations(user_id: str = "farmer_demo_default") -> List[Dict[str, Any]]:
    """Retrieves all saved locations for a user (up to 5)."""
    with get_db_connection() as conn:
        cursor = conn.execute(
            "SELECT * FROM saved_locations WHERE user_id = ? ORDER BY created_at ASC LIMIT 5",
            (user_id,)
        )
        return [dict(row) for row in cursor.fetchall()]

def count_saved_locations(user_id: str = "farmer_demo_default") -> int:
    """Returns the count of saved locations for a user."""
    with get_db_connection() as conn:
        cursor = conn.execute(
            "SELECT COUNT(*) as cnt FROM saved_locations WHERE user_id = ?",
            (user_id,)
        )
        return cursor.fetchone()["cnt"]

def add_saved_location(
    name: str,
    latitude: float,
    longitude: float,
    district: Optional[str] = None,
    state: Optional[str] = None,
    crop: Optional[str] = None,
    notes: Optional[str] = None,
    user_id: str = "farmer_demo_default"
) -> Dict[str, Any]:
    """Adds a saved location if user has fewer than 5 locations."""
    current_count = count_saved_locations(user_id)
    if current_count >= 5:
        raise ValueError("You can save up to 5 farming locations.")

    loc_id = f"loc_{uuid.uuid4().hex[:8]}"
    with get_db_connection() as conn:
        conn.execute(
            """INSERT INTO saved_locations 
               (id, user_id, name, latitude, longitude, district, state, crop, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (loc_id, user_id, name, latitude, longitude, district, state, crop, notes)
        )
        conn.commit()
        cursor = conn.execute("SELECT * FROM saved_locations WHERE id = ?", (loc_id,))
        return dict(cursor.fetchone())

def update_saved_location(
    loc_id: str,
    name: str,
    crop: Optional[str] = None,
    notes: Optional[str] = None,
    user_id: str = "farmer_demo_default"
) -> Optional[Dict[str, Any]]:
    """Updates an existing saved location's editable attributes."""
    with get_db_connection() as conn:
        conn.execute(
            """UPDATE saved_locations 
               SET name = ?, crop = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
               WHERE id = ? AND user_id = ?""",
            (name, crop, notes, loc_id, user_id)
        )
        conn.commit()
        cursor = conn.execute("SELECT * FROM saved_locations WHERE id = ?", (loc_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def delete_saved_location(loc_id: str, user_id: str = "farmer_demo_default") -> bool:
    """Deletes a saved location."""
    with get_db_connection() as conn:
        cursor = conn.execute(
            "DELETE FROM saved_locations WHERE id = ? AND user_id = ?",
            (loc_id, user_id)
        )
        conn.commit()
        return cursor.rowcount > 0

def get_alerts(user_id: str = "farmer_demo_default") -> List[Dict[str, Any]]:
    """Returns alerts for user."""
    with get_db_connection() as conn:
        cursor = conn.execute(
            "SELECT * FROM alerts WHERE user_id = ? ORDER BY timestamp DESC LIMIT 20",
            (user_id,)
        )
        return [dict(row) for row in cursor.fetchall()]

def mark_alerts_read(user_id: str = "farmer_demo_default") -> bool:
    """Marks all alerts as read."""
    with get_db_connection() as conn:
        conn.execute("UPDATE alerts SET is_read = 1 WHERE user_id = ?", (user_id,))
        conn.commit()
        return True

def get_data_sources_status() -> List[Dict[str, Any]]:
    """Returns status of external data sources."""
    with get_db_connection() as conn:
        cursor = conn.execute("SELECT * FROM data_sources ORDER BY name ASC")
        return [dict(row) for row in cursor.fetchall()]
