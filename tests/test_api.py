"""Integration tests for FastAPI endpoints."""
import unittest
from starlette.testclient import TestClient
from backend.main import app

class TestAPIEndpoints(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_health_check(self):
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["app"], "RainSense Farmer")

    def test_demo_endpoint(self):
        resp = self.client.get("/api/demo")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["is_demo_mode"])
        self.assertEqual(data["location"]["district"], "Guntur")
        self.assertEqual(data["fifteen_km_analysis"]["nearest_rain_distance_km"], 6.4)
        self.assertEqual(data["soil_moisture"]["average_moisture_pct"], 54.0)

    def test_weather_endpoint_with_demo_param(self):
        resp = self.client.get("/api/weather?lat=16.3067&lon=80.4365&demo=true")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("temperature_c", data)
        self.assertIn("humidity_pct", data)

    def test_rain_history_endpoint_with_demo_param(self):
        resp = self.client.get("/api/rainfall?lat=16.3067&lon=80.4365&demo=true")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["last_24h_mm"], 12.6)

    def test_nearby_rain_15km_endpoint_with_demo(self):
        resp = self.client.get("/api/nearby-rain?lat=16.3067&lon=80.4365&demo=true")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["rain_nearby"])
        self.assertEqual(data["nearest_rain_distance_km"], 6.4)
        self.assertEqual(data["nearest_rain_direction"], "NE")

    def test_location_search(self):
        resp = self.client.get("/api/location/search?q=Guntur")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(len(data["results"]) > 0)
        self.assertEqual(data["results"][0]["name"], "Guntur")

    def test_admin_status(self):
        resp = self.client.get("/api/admin/status")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["system_status"], "HEALTHY")

    def test_ml_predict_endpoint(self):
        payload = {
            "latitude": 16.3067,
            "longitude": 80.4365,
            "humidity": 75.0,
            "temperature": 28.0,
            "rainfall_3h": 3.2
        }
        resp = self.client.post("/api/predict", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("rain_probability_pct", data)
        self.assertIn("predicted_rainfall_mm", data)

if __name__ == "__main__":
    unittest.main()
