"""Unit tests for ML prediction pipeline and feature bounds."""
import unittest
from ml.prediction.predictor import RainPredictor

class TestMLPredictor(unittest.TestCase):

    def setUp(self):
        self.predictor = RainPredictor()

    def test_predictor_loaded(self):
        """Ensure models are loaded and ready."""
        self.assertTrue(self.predictor.is_ready(), "Predictor models should be loaded and ready.")

    def test_prediction_output_ranges(self):
        """Check valid probabilities, rainfall amount, and confidence scores."""
        sample_features = {
            "rainfall_1h": 0.5,
            "rainfall_3h": 2.1,
            "rainfall_6h": 4.5,
            "rainfall_12h": 8.0,
            "rainfall_24h": 12.5,
            "rainfall_72h": 20.0,
            "temperature": 27.5,
            "humidity": 82.0,
            "pressure": 1008.0,
            "wind_speed": 14.0,
            "soil_moisture_surface": 52.0,
            "soil_moisture_root": 58.0,
            "latitude": 16.3067,
            "longitude": 80.4365
        }

        res = self.predictor.predict(sample_features)

        self.assertIn(res["rain_occurrence_prediction"], [0, 1])
        self.assertTrue(0 <= res["rain_probability_pct"] <= 100)
        self.assertTrue(res["predicted_rainfall_mm"] >= 0.0)
        self.assertTrue(0.0 <= res["confidence_score"] <= 1.0)
        self.assertEqual(res["source_badge"], "AI PREDICTION")
        self.assertTrue(len(res["top_factors"]) > 0)

if __name__ == "__main__":
    unittest.main()
