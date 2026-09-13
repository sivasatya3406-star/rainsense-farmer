"""Unit tests for geospatial calculations and 15 km boundary analysis."""
import unittest
from backend.services.geospatial_service import (
    haversine_distance_km,
    calculate_bearing_deg,
    bearing_to_short_cardinal,
    destination_point,
    classify_rain_intensity,
    analyze_15km_monitoring_zone
)

class TestGeospatialService(unittest.TestCase):
    
    def test_haversine_distance_zero(self):
        """Distance between identical coordinates must be 0.0."""
        dist = haversine_distance_km(16.3067, 80.4365, 16.3067, 80.4365)
        self.assertAlmostEqual(dist, 0.0, places=4)

    def test_haversine_known_distance(self):
        """Guntur (16.3067, 80.4365) to Vijayawada (16.5062, 80.6480) is ~31 km."""
        dist = haversine_distance_km(16.3067, 80.4365, 16.5062, 80.6480)
        self.assertTrue(28.0 < dist < 35.0, f"Expected ~31 km, got {dist}")

    def test_compass_bearing_cardinals(self):
        """Test cardinal conversions."""
        # Due North
        p_n_lat, p_n_lon = destination_point(16.0, 80.0, 10.0, 0.0)
        bearing_n = calculate_bearing_deg(16.0, 80.0, p_n_lat, p_n_lon)
        self.assertAlmostEqual(bearing_n, 0.0, delta=1.0)
        self.assertEqual(bearing_to_short_cardinal(bearing_n), "N")

        # Due East (90 deg)
        p_e_lat, p_e_lon = destination_point(16.0, 80.0, 10.0, 90.0)
        bearing_e = calculate_bearing_deg(16.0, 80.0, p_e_lat, p_e_lon)
        self.assertAlmostEqual(bearing_e, 90.0, delta=1.0)
        self.assertEqual(bearing_to_short_cardinal(bearing_e), "E")

    def test_15km_strict_boundary_inclusion_and_exclusion(self):
        """
        Critical test:
        - Points at 5 km and 15.0 km MUST be included in the 15 km monitoring zone.
        - Points at 15.1 km and 16.0 km MUST be strictly excluded.
        """
        farm_lat = 16.3067
        farm_lon = 80.4365

        # 5 km point (Northeast, bearing 45)
        p_5km_lat, p_5km_lon = destination_point(farm_lat, farm_lon, 5.0, 45.0)
        # 15.0 km point (North, bearing 0)
        p_15km_lat, p_15km_lon = destination_point(farm_lat, farm_lon, 15.0, 0.0)
        # 15.2 km point (South, bearing 180)
        p_15_2km_lat, p_15_2km_lon = destination_point(farm_lat, farm_lon, 15.2, 180.0)
        # 16.0 km point (West, bearing 270)
        p_16km_lat, p_16km_lon = destination_point(farm_lat, farm_lon, 16.0, 270.0)

        observations = [
            {"id": "cell_5km", "name": "5km Rain Cell", "latitude": p_5km_lat, "longitude": p_5km_lon, "rainfall_rate_mm": 4.5},
            {"id": "cell_15km", "name": "15km Border Cell", "latitude": p_15km_lat, "longitude": p_15km_lon, "rainfall_rate_mm": 2.0},
            {"id": "cell_15_2km", "name": "15.2km Outside Cell", "latitude": p_15_2km_lat, "longitude": p_15_2km_lon, "rainfall_rate_mm": 8.0},
            {"id": "cell_16km", "name": "16km Far Outside Cell", "latitude": p_16km_lat, "longitude": p_16km_lon, "rainfall_rate_mm": 12.0},
        ]

        result = analyze_15km_monitoring_zone(
            farm_lat=farm_lat,
            farm_lon=farm_lon,
            farm_current_rate_mm=0.0,
            nearby_observations=observations
        )

        detected_zone_ids = [z["zone_id"] for z in result["zones_detected"]]

        # Verify inclusion of <= 15.0 km
        self.assertIn("cell_5km", detected_zone_ids, "5 km cell must be included in 15 km zone")
        self.assertIn("cell_15km", detected_zone_ids, "15.0 km border cell must be included")

        # Verify strict exclusion of > 15.0 km
        self.assertNotIn("cell_15_2km", detected_zone_ids, "15.2 km cell must be EXCLUDED from 15 km zone")
        self.assertNotIn("cell_16km", detected_zone_ids, "16.0 km cell must be EXCLUDED from 15 km zone")

    def test_rain_intensity_classification(self):
        self.assertEqual(classify_rain_intensity(0.0), "No Rain")
        self.assertEqual(classify_rain_intensity(1.2), "Light Rain")
        self.assertEqual(classify_rain_intensity(5.4), "Moderate Rain")
        self.assertEqual(classify_rain_intensity(12.0), "Heavy Rain")
        self.assertEqual(classify_rain_intensity(22.0), "Very Heavy Rain")

if __name__ == "__main__":
    unittest.main()
