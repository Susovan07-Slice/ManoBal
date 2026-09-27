import os
import sys
import unittest
from fastapi.testclient import TestClient

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api.main import app
from db.seed import seed_database

class TestFastAPIBackend(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        seed_database()
        cls.client = TestClient(app)
        
        # Login to obtain auth headers for protected endpoints
        login_resp = cls.client.post("/api/auth/login", json={"username": "admin", "password": "AdminPassword123!"})
        cls.token = login_resp.json()["access_token"]
        cls.auth_headers = {"Authorization": f"Bearer {cls.token}"}
        
        # Standard valid request payload
        cls.valid_payload = {
            "age": 34,
            "gender": "Male",
            "marital_status": "Married",
            "department": "Operations",
            "job_role": "Section Commander",
            "experience_years": 10.5,
            "monthly_salary_inr": 85000,
            "working_hours_per_week": 54.0,
            "duty_hours_per_week": 58.0,
            "sleep_hours": 5.0,
            "physical_activity_hours_per_week": 2.5,
            "annual_leaves_taken": 6,
            "night_shifts_per_month": 7,
            "consecutive_duty_days": 8,
            "leave_gap_days": 110,
            "deployment_days": 60,
            "remote_posting": "Yes",
            "operational_exposure": "High",
            "health_issues": "Hypertension",
            "burnout_symptoms": "Often"
        }

    def test_health_check_endpoint(self):
        """Test /api/health returns 200 and model loaded status."""
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertTrue(data["model_loaded"])

    def test_valid_prediction_request(self):
        """Test POST /api/predict with valid payload and JWT returns complete response schema."""
        response = self.client.post("/api/predict", json=self.valid_payload, headers=self.auth_headers)
        self.assertEqual(response.status_code, 200, f"Failed with: {response.text}")
        data = response.json()
        
        # Verify required keys
        expected_keys = [
            "stress_level", "risk_score", "risk_priority",
            "probabilities", "key_factors", "recommendations", "disclaimer"
        ]
        for key in expected_keys:
            self.assertIn(key, data)
            
        # Verify schema validity
        self.assertIn(data["stress_level"], ["Low", "Medium", "High"])
        self.assertTrue(0 <= data["risk_score"] <= 100)
        self.assertIn(data["risk_priority"], ["Routine", "Preventive", "Priority"])
        self.assertIn(len(data["probabilities"]), [3, 5])
        self.assertGreater(len(data["key_factors"]), 0)
        self.assertGreater(len(data["recommendations"]), 0)

    def test_missing_required_field(self):
        """Test POST /api/predict rejects missing required field with HTTP 422."""
        incomplete_payload = self.valid_payload.copy()
        del incomplete_payload["duty_hours_per_week"]
        
        response = self.client.post("/api/predict", json=incomplete_payload, headers=self.auth_headers)
        self.assertEqual(response.status_code, 422)
        data = response.json()
        self.assertEqual(data["error"], "Validation Error")
        self.assertTrue(any("duty_hours_per_week" in d["field"] for d in data["details"]))

    def test_invalid_numerical_range(self):
        """Test POST /api/predict rejects out-of-range numerical values with HTTP 422."""
        invalid_payload = self.valid_payload.copy()
        invalid_payload["sleep_hours"] = 35.0  # Impossible daily sleep duration
        
        response = self.client.post("/api/predict", json=invalid_payload, headers=self.auth_headers)
        self.assertEqual(response.status_code, 422)
        data = response.json()
        self.assertTrue(any("sleep_hours" in d["field"] for d in data["details"]))

    def test_invalid_categorical_value(self):
        """Test POST /api/predict rejects invalid categorical enum with HTTP 422."""
        invalid_payload = self.valid_payload.copy()
        invalid_payload["department"] = "SpaceForce"  # Invalid department
        
        response = self.client.post("/api/predict", json=invalid_payload, headers=self.auth_headers)
        self.assertEqual(response.status_code, 422)
        data = response.json()
        self.assertTrue(any("department" in d["field"] for d in data["details"]))

    def test_unit_aggregates_endpoint(self):
        """Test GET /api/unit-aggregates returns valid aggregate telemetry."""
        response = self.client.get("/api/unit-aggregates")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("unit_id", data)
        self.assertIn("risk_distribution", data)
        self.assertIn("welfare_summary", data)

    def test_submit_checkin_endpoint(self):
        """Test POST /api/submit-checkin evaluates check-in and returns assessment."""
        response = self.client.post("/api/submit-checkin", json=self.valid_payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("assessment", data)
        self.assertIn("risk_score", data["assessment"])

if __name__ == '__main__':
    unittest.main()
