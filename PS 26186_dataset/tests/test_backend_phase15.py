import os
import sys
import unittest
from fastapi.testclient import TestClient

# Ensure root directory is on PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api.main import app
from db.base import Base
from db.session import engine, SessionLocal
from db.models.user import User
from db.models.personnel import Personnel
from db.models.assessment import StressAssessment
from db.models.recommendation import WelfareRecommendation
from db.seed import seed_database

import uuid

class TestBackendPhase15(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Ensure tables exist and seed demo data
        seed_database()
        cls.client = TestClient(app)
        cls.run_id = uuid.uuid4().hex[:6]

        # Obtain tokens for each role
        # 1. Admin
        resp_admin = cls.client.post("/api/auth/login", json={"username": "admin", "password": "AdminPassword123!"})
        cls.admin_token = resp_admin.json()["access_token"]
        cls.admin_headers = {"Authorization": f"Bearer {cls.admin_token}"}

        # 2. Officer
        resp_officer = cls.client.post("/api/auth/login", json={"username": "officer_sharma", "password": "OfficerPassword123!"})
        cls.officer_token = resp_officer.json()["access_token"]
        cls.officer_headers = {"Authorization": f"Bearer {cls.officer_token}"}

        # 3. Welfare
        resp_welfare = cls.client.post("/api/auth/login", json={"username": "counselor_priya", "password": "WelfarePassword123!"})
        cls.welfare_token = resp_welfare.json()["access_token"]
        cls.welfare_headers = {"Authorization": f"Bearer {cls.welfare_token}"}

        # 4. Personnel (linked to PF-0001, id=1)
        resp_personnel = cls.client.post("/api/auth/login", json={"username": "jawan_verma", "password": "PersonnelPassword123!"})
        cls.personnel_token = resp_personnel.json()["access_token"]
        cls.personnel_headers = {"Authorization": f"Bearer {cls.personnel_token}"}

    # =========================================================================
    # 1. AUTHENTICATION TESTS
    # =========================================================================
    def test_01_user_registration_success(self):
        """Test registering a new user account hashes password and returns 201."""
        test_user = f"new_cadet_{self.run_id}"
        payload = {
            "username": test_user,
            "password": "SecurePassword999!",
            "role": "personnel"
        }
        res = self.client.post("/api/auth/register", json=payload, headers=self.admin_headers)
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertEqual(data["username"], test_user)
        self.assertEqual(data["role"], "personnel")
        self.assertNotIn("password", data)
        self.assertNotIn("hashed_password", data)

    def test_02_duplicate_registration_rejected(self):
        """Test registering an existing username returns 400."""
        payload = {
            "username": "admin",
            "password": "AnotherPassword123!",
            "role": "admin"
        }
        res = self.client.post("/api/auth/register", json=payload, headers=self.admin_headers)
        self.assertEqual(res.status_code, 400)
        self.assertIn("already registered", res.json()["detail"])

    def test_03_login_successful(self):
        """Test login returns JWT access token and user metadata."""
        res = self.client.post("/api/auth/login", json={"username": "admin", "password": "AdminPassword123!"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("access_token", data)
        self.assertEqual(data["token_type"], "bearer")
        self.assertEqual(data["role"], "admin")

    def test_04_login_invalid_password_rejected(self):
        """Test login with incorrect password returns 401."""
        res = self.client.post("/api/auth/login", json={"username": "admin", "password": "WrongPassword"})
        self.assertEqual(res.status_code, 401)

    def test_05_protected_endpoint_without_token_rejected(self):
        """Test accessing /api/auth/me without token returns 401."""
        res = self.client.get("/api/auth/me")
        self.assertEqual(res.status_code, 401)

    def test_06_protected_endpoint_with_valid_token(self):
        """Test accessing /api/auth/me with valid Bearer token returns current profile."""
        res = self.client.get("/api/auth/me", headers=self.admin_headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["username"], "admin")
        self.assertEqual(data["role"], "admin")

    # =========================================================================
    # 2. RBAC & AUTHORIZATION TESTS
    # =========================================================================
    def test_07_personnel_cannot_create_personnel_record(self):
        """Test personnel role cannot create a personnel record (403 Forbidden)."""
        payload = {
            "personnel_code": "PF-9999",
            "name": "Unauthorized Cadet",
            "age": 28,
            "gender": "Male",
            "department": "Operations",
            "job_role": "Scout",
            "location": "Delhi",
            "experience_years": 3.0,
            "duty_hours_per_week": 45.0
        }
        res = self.client.post("/api/personnel", json=payload, headers=self.personnel_headers)
        self.assertEqual(res.status_code, 403)

    def test_08_personnel_can_access_own_record(self):
        """Test personnel user can access their own personnel record (id=1)."""
        res = self.client.get("/api/personnel/1", headers=self.personnel_headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["personnel_code"], "PF-0001")

    def test_09_personnel_forbidden_from_other_records(self):
        """Test personnel user attempting to access another person's record (id=2) receives 403."""
        res = self.client.get("/api/personnel/2", headers=self.personnel_headers)
        self.assertEqual(res.status_code, 403)
        self.assertIn("Access denied", res.json()["detail"])

    def test_10_personnel_forbidden_from_dashboard_summary(self):
        """Test personnel user attempting to access dashboard summary receives 403."""
        res = self.client.get("/api/dashboard/summary", headers=self.personnel_headers)
        self.assertEqual(res.status_code, 403)

    # =========================================================================
    # 3. PERSONNEL CRUD TESTS
    # =========================================================================
    def test_11_officer_can_create_personnel(self):
        """Test Officer role can create a new personnel record."""
        code = f"PF-T{self.run_id.upper()}"
        payload = {
            "personnel_code": code,
            "name": "Constable Test Singh",
            "age": 26,
            "gender": "Male",
            "department": "Operations",
            "job_role": "Rifleman",
            "location": "Srinagar",
            "experience_years": 3.5,
            "duty_hours_per_week": 50.0,
            "night_shifts_per_month": 6,
            "consecutive_duty_days": 8,
            "transfer_frequency": 1,
            "training_load": 2,
            "leave_gap_days": 60,
            "deployment_days": 100,
            "remote_posting": "Yes",
            "operational_exposure": "Medium"
        }
        res = self.client.post("/api/personnel", json=payload, headers=self.officer_headers)
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertEqual(data["personnel_code"], code)
        self.__class__.created_personnel_id = data["id"]

    def test_12_update_personnel(self):
        """Test updating a personnel record's duty hours and location."""
        p_id = getattr(self.__class__, "created_personnel_id", 1)
        update_payload = {
            "duty_hours_per_week": 58.0,
            "location": "Srinagar"
        }
        res = self.client.put(f"/api/personnel/{p_id}", json=update_payload, headers=self.admin_headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["duty_hours_per_week"], 58.0)
        self.assertEqual(data["location"], "Srinagar")

    def test_13_list_personnel_pagination_and_filtering(self):
        """Test paginated personnel list with department filtering."""
        res = self.client.get("/api/personnel?page=1&size=5&department=Operations", headers=self.admin_headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("items", data)
        self.assertLessEqual(len(data["items"]), 5)
        self.assertGreaterEqual(data["total"], 1)
        for item in data["items"]:
            self.assertEqual(item["department"], "Operations")

    # =========================================================================
    # 4. ASSESSMENT & WELFARE RECOMMENDATION TESTS
    # =========================================================================
    def test_14_run_assessment_persists_to_database(self):
        """Test running assessment triggers ML pipeline and persists assessment & recommendations."""
        p_id = getattr(self.__class__, "created_personnel_id", 1)
        override = {
            "duty_hours_per_week": 62.0,
            "night_shifts_per_month": 11,
            "consecutive_duty_days": 16,
            "leave_gap_days": 150
        }
        res = self.client.post(f"/api/personnel/{p_id}/assess", json=override, headers=self.officer_headers)
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertEqual(data["status"], "success")
        ass = data["assessment"]
        self.assertIn(ass["stress_level"], ["Low", "Medium", "High"])
        self.assertTrue(0 <= ass["risk_score"] <= 100)
        self.assertIn(ass["risk_priority"], ["Routine", "Preventive", "Priority"])
        self.assertGreater(len(ass["recommendations"]), 0)

        # Store recommendation ID for testing status update
        self.__class__.sample_rec_id = ass["recommendations"][0]["id"]
        self.__class__.sample_ass_id = ass["id"]

    def test_15_get_personnel_assessment_history(self):
        """Test fetching chronological assessment history for personnel."""
        p_id = getattr(self.__class__, "created_personnel_id", 1)
        res = self.client.get(f"/api/personnel/{p_id}/assessments", headers=self.welfare_headers)
        self.assertEqual(res.status_code, 200)
        history = res.json()
        self.assertIsInstance(history, list)
        self.assertGreaterEqual(len(history), 1)

    def test_16_get_individual_assessment_by_id(self):
        """Test fetching a single assessment by ID."""
        ass_id = getattr(self.__class__, "sample_ass_id", 1)
        res = self.client.get(f"/api/assessments/{ass_id}", headers=self.admin_headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["id"], ass_id)
        self.assertIn("key_factors", data)
        self.assertIn("recommendations", data)

    def test_17_welfare_can_update_recommendation_status(self):
        """Test Welfare role can update status of a recommendation."""
        rec_id = getattr(self.__class__, "sample_rec_id", 1)
        status_payload = {"status": "acknowledged"}
        res = self.client.patch(f"/api/recommendations/{rec_id}/status", json=status_payload, headers=self.welfare_headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["id"], rec_id)
        self.assertEqual(data["status"], "acknowledged")

    # =========================================================================
    # 5. DASHBOARD DATA API TESTS
    # =========================================================================
    def test_18_dashboard_summary(self):
        """Test GET /api/dashboard/summary returns database-derived aggregates."""
        res = self.client.get("/api/dashboard/summary", headers=self.admin_headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertGreater(data["total_personnel"], 0)
        self.assertGreater(data["assessed_personnel"], 0)
        self.assertEqual(
            data["assessed_personnel"],
            data["low_risk"] + data["medium_risk"] + data["high_risk"]
        )
        self.assertGreaterEqual(data["pending_recommendations"], 0)
        self.assertGreaterEqual(data["acknowledged_recommendations"], 0)

    def test_19_dashboard_stress_distribution(self):
        """Test GET /api/dashboard/stress-distribution returns valid class percentages."""
        res = self.client.get("/api/dashboard/stress-distribution", headers=self.officer_headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("distribution", data)
        self.assertGreater(data["total_assessed"], 0)
        labels = [item["label"] for item in data["distribution"]]
        self.assertIn("Low", labels)
        self.assertIn("Medium", labels)
        self.assertIn("High", labels)

    def test_20_dashboard_risk_distribution(self):
        """Test GET /api/dashboard/risk-distribution returns Routine, Preventive, Priority breakdown."""
        res = self.client.get("/api/dashboard/risk-distribution", headers=self.welfare_headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        labels = [item["label"] for item in data["distribution"]]
        self.assertIn("Routine", labels)
        self.assertIn("Preventive", labels)
        self.assertIn("Priority", labels)

    def test_21_dashboard_recent_assessments(self):
        """Test GET /api/dashboard/recent-assessments returns chronological items."""
        res = self.client.get("/api/dashboard/recent-assessments?limit=5", headers=self.admin_headers)
        self.assertEqual(res.status_code, 200)
        items = res.json()
        self.assertIsInstance(items, list)
        self.assertLessEqual(len(items), 5)
        if len(items) > 0:
            self.assertIn("personnel_code", items[0])
            self.assertIn("risk_score", items[0])

    def test_22_dashboard_high_risk_list(self):
        """Test GET /api/dashboard/high-risk returns flagged personnel."""
        res = self.client.get("/api/dashboard/high-risk", headers=self.officer_headers)
        self.assertEqual(res.status_code, 200)
        items = res.json()
        self.assertIsInstance(items, list)
        for item in items:
            self.assertTrue(item["risk_priority"] == "Priority" or item["risk_score"] >= 60)
            self.assertIn("key_factors", item)
            self.assertIn("pending_recommendations_count", item)

    # =========================================================================
    # 6. BACKWARD COMPATIBILITY
    # =========================================================================
    def test_23_backward_compatibility_predict(self):
        """Verify original POST /api/predict continues working unchanged."""
        valid_payload = {
            "age": 32,
            "gender": "Male",
            "department": "Operations",
            "job_role": "Field Operative",
            "experience_years": 8.0,
            "duty_hours_per_week": 55.0,
            "night_shifts_per_month": 7,
            "consecutive_duty_days": 10,
            "leave_gap_days": 90,
            "sleep_hours": 5.5,
            "physical_activity_hours_per_week": 4.0,
            "annual_leaves_taken": 10,
            "working_hours_per_week": 55.0
        }
        res = self.client.post("/api/predict", json=valid_payload, headers=self.officer_headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("stress_level", data)
        self.assertIn("risk_score", data)
        self.assertIn("recommendations", data)

if __name__ == '__main__':
    unittest.main()
