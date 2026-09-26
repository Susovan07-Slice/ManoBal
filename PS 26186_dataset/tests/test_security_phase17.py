import os
import sys
import unittest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from jose import jwt

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api.main import app
from core.config import settings, Settings
from core.security import create_access_token
from db.seed import seed_database

class TestSecurityPhase17(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        seed_database()
        cls.client = TestClient(app)
        
        # Admin credentials
        resp_admin = cls.client.post("/api/auth/login", json={"username": "admin", "password": "AdminPassword123!"})
        cls.admin_token = resp_admin.json()["access_token"]
        cls.admin_headers = {"Authorization": f"Bearer {cls.admin_token}"}
        
        # Officer credentials
        resp_officer = cls.client.post("/api/auth/login", json={"username": "officer_sharma", "password": "OfficerPassword123!"})
        cls.officer_token = resp_officer.json()["access_token"]
        cls.officer_headers = {"Authorization": f"Bearer {cls.officer_token}"}
        
        # Personnel credentials (linked to id=1)
        resp_personnel = cls.client.post("/api/auth/login", json={"username": "jawan_verma", "password": "PersonnelPassword123!"})
        cls.personnel_token = resp_personnel.json()["access_token"]
        cls.personnel_headers = {"Authorization": f"Bearer {cls.personnel_token}"}

        # Valid payload for prediction
        cls.valid_payload = {
            "age": 30,
            "gender": "Male",
            "department": "Operations",
            "job_role": "Field Operative",
            "experience_years": 6.0,
            "duty_hours_per_week": 50.0,
            "night_shifts_per_month": 6,
            "consecutive_duty_days": 8,
            "leave_gap_days": 75,
            "sleep_hours": 6.0,
            "physical_activity_hours_per_week": 3.0,
            "annual_leaves_taken": 8,
            "working_hours_per_week": 48.0
        }

    # =========================================================================
    # 1. JWT SECRET SECURITY TESTS
    # =========================================================================
    def test_missing_jwt_secret_fails_safely(self):
        """Verify that Settings raises RuntimeError when no JWT secret is provided in env."""
        old_secret = os.environ.get("SECRET_KEY")
        old_jwt_secret = os.environ.get("JWT_SECRET")
        try:
            if "SECRET_KEY" in os.environ:
                del os.environ["SECRET_KEY"]
            if "JWT_SECRET" in os.environ:
                del os.environ["JWT_SECRET"]
                
            # Attempting to initialize Settings without any secret must fail safely
            with self.assertRaises(RuntimeError) as ctx:
                Settings()
            self.assertIn("JWT secret environment variable is required", str(ctx.exception))
        finally:
            if old_secret:
                os.environ["SECRET_KEY"] = old_secret
            if old_jwt_secret:
                os.environ["JWT_SECRET"] = old_jwt_secret

    def test_invalid_jwt_token_rejected(self):
        """Verify that an invalid or forged JWT token is rejected with HTTP 401."""
        invalid_headers = {"Authorization": "Bearer forged.invalid.token.signature"}
        response = self.client.get("/api/auth/me", headers=invalid_headers)
        self.assertEqual(response.status_code, 401)
        self.assertIn("Invalid or expired access token", response.json()["detail"])

    def test_expired_jwt_token_rejected(self):
        """Verify that an expired JWT token is rejected with HTTP 401."""
        # Generate token with expiration in the past
        past_expire = datetime.now(timezone.utc) - timedelta(minutes=10)
        claims = {
            "sub": "admin",
            "role": "admin",
            "exp": past_expire
        }
        expired_token = jwt.encode(claims, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        expired_headers = {"Authorization": f"Bearer {expired_token}"}
        
        response = self.client.get("/api/auth/me", headers=expired_headers)
        self.assertEqual(response.status_code, 401)
        self.assertIn("Invalid or expired access token", response.json()["detail"])

    # =========================================================================
    # 2. PREDICT ENDPOINT PROTECTION TESTS
    # =========================================================================
    def test_predict_unauthenticated_rejected(self):
        """Verify that POST /api/predict without credentials rejects with HTTP 401."""
        response = self.client.post("/api/predict", json=self.valid_payload)
        self.assertEqual(response.status_code, 401)
        self.assertIn("Authentication credentials were not provided", response.json()["detail"])

    def test_predict_authenticated_authorized(self):
        """Verify that POST /api/predict with valid credentials succeeds."""
        response = self.client.post("/api/predict", json=self.valid_payload, headers=self.officer_headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("stress_level", data)
        self.assertIn("risk_score", data)
        self.assertIn("recommendations", data)

    # =========================================================================
    # 3. CORS SECURITY TESTS
    # =========================================================================
    def test_cors_authorized_origin_accepted(self):
        """Verify that requests from authorized frontend origin (localhost:3000) receive CORS headers."""
        headers = {
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
        }
        response = self.client.options("/api/predict", headers=headers)
        # CORS preflight response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("access-control-allow-origin"), "http://localhost:3000")
        self.assertEqual(response.headers.get("access-control-allow-credentials"), "true")

    def test_cors_mobile_origin_accepted(self):
        """Verify that requests from mobile web origin (localhost:3001) receive CORS headers."""
        headers = {
            "Origin": "http://localhost:3001",
            "Access-Control-Request-Method": "POST",
        }
        response = self.client.options("/api/predict", headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("access-control-allow-origin"), "http://localhost:3001")

    def test_cors_arbitrary_unauthorized_origin_rejected(self):
        """Verify that arbitrary untrusted origin does NOT receive access-control-allow-origin header."""
        headers = {
            "Origin": "http://malicious-untrusted-site.com",
            "Access-Control-Request-Method": "POST",
        }
        response = self.client.options("/api/predict", headers=headers)
        # When origin is untrusted, CORS middleware does not reflect the origin
        allow_origin = response.headers.get("access-control-allow-origin")
        self.assertNotEqual(allow_origin, "http://malicious-untrusted-site.com")
        self.assertNotEqual(allow_origin, "*")

    # =========================================================================
    # 4. RBAC RE-VERIFICATION TESTS
    # =========================================================================
    def test_rbac_personnel_cannot_access_dashboard_summary(self):
        """Verify that Personnel role cannot access commander dashboard summary."""
        response = self.client.get("/api/dashboard/summary", headers=self.personnel_headers)
        self.assertEqual(response.status_code, 403)

    def test_rbac_personnel_cannot_access_other_personnel_record(self):
        """Verify that Personnel role cannot access another personnel record."""
        # jawan_verma is linked to ID 1, attempting to access ID 2
        response = self.client.get("/api/personnel/2", headers=self.personnel_headers)
        self.assertEqual(response.status_code, 403)

    def test_rbac_officer_can_access_dashboard_and_personnel(self):
        """Verify that Officer role can access dashboard summary and personnel records."""
        resp_dash = self.client.get("/api/dashboard/summary", headers=self.officer_headers)
        self.assertEqual(resp_dash.status_code, 200)
        resp_p = self.client.get("/api/personnel/2", headers=self.officer_headers)
        self.assertEqual(resp_p.status_code, 200)

if __name__ == '__main__':
    unittest.main()
