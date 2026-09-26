import os
import sys
import unittest
import uuid
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api.main import app
from db.seed import seed_database
from db.session import get_db
from db.models.user import User
from db.models.personnel import Personnel
from db.models.assessment import StressAssessment
from db.models.recommendation import WelfareRecommendation

class TestJawanSelfSignupAndCheckin(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        seed_database()
        cls.client = TestClient(app)

        # Login as Officer to test commander views
        login_resp = cls.client.post("/api/auth/login", json={"username": "officer_sharma", "password": "OfficerPassword123!"})
        cls.officer_token = login_resp.json()["access_token"]
        cls.officer_headers = {"Authorization": f"Bearer {cls.officer_token}"}

    def test_01_jawan_self_signup_success(self):
        """Verify Jawan self-registration atomically creates User + Personnel with role='personnel'."""
        unique_suffix = uuid.uuid4().hex[:6]
        signup_payload = {
            "name": f"Cadet Arjun {unique_suffix}",
            "username": f"arjun_{unique_suffix}",
            "password": "SecurePassword123!",
            "personnel_code": f"TEST-{unique_suffix.upper()}",
            "age": 26,
            "gender": "Male",
            "department": "Operations",
            "job_role": "Constable",
            "location": "Dantewada",
            "experience_years": 3.0,
            "duty_hours_per_week": 42.0
        }

        resp = self.client.post("/api/auth/register-jawan", json=signup_payload)
        self.assertEqual(resp.status_code, 201, f"Signup failed: {resp.text}")
        data = resp.json()

        # Token returned with role personnel
        self.assertIn("access_token", data)
        self.assertEqual(data["role"], "personnel")
        self.assertEqual(data["username"], f"arjun_{unique_suffix}")
        self.assertIsNotNone(data["personnel_id"])

        # Immediate login with credentials
        login_resp = self.client.post("/api/auth/login", json={
            "username": f"arjun_{unique_suffix}",
            "password": "SecurePassword123!"
        })
        self.assertEqual(login_resp.status_code, 200)
        login_data = login_resp.json()
        self.assertEqual(login_data["role"], "personnel")
        self.assertEqual(login_data["personnel_id"], data["personnel_id"])

    def test_02_jawan_duplicate_rejection(self):
        """Verify registration rejects duplicate username and duplicate personnel ID."""
        unique_suffix = uuid.uuid4().hex[:6]
        signup_payload = {
            "name": "Duplicate Test",
            "username": f"dup_{unique_suffix}",
            "password": "Password123!",
            "personnel_code": f"DUP-{unique_suffix.upper()}",
            "age": 25,
            "gender": "Male",
            "department": "Operations",
            "job_role": "Constable",
            "location": "Delhi",
            "experience_years": 2.0
        }

        # 1. First signup succeeds
        r1 = self.client.post("/api/auth/register-jawan", json=signup_payload)
        self.assertEqual(r1.status_code, 201)

        # 2. Duplicate username fails
        payload_dup_user = dict(signup_payload)
        payload_dup_user["personnel_code"] = f"OTHER-{unique_suffix.upper()}"
        r2 = self.client.post("/api/auth/register-jawan", json=payload_dup_user)
        self.assertEqual(r2.status_code, 400)
        self.assertIn("already registered", r2.json()["detail"].lower())

        # 3. Duplicate personnel_code fails
        payload_dup_code = dict(signup_payload)
        payload_dup_code["username"] = f"other_{unique_suffix}"
        r3 = self.client.post("/api/auth/register-jawan", json=payload_dup_code)
        self.assertEqual(r3.status_code, 400)
        self.assertIn("already registered", r3.json()["detail"].lower())

    def test_03_jawan_access_control(self):
        """Verify newly registered Jawan cannot access Commander endpoints or other personnel."""
        unique_suffix = uuid.uuid4().hex[:6]
        signup_payload = {
            "name": f"Security Jawan {unique_suffix}",
            "username": f"sec_{unique_suffix}",
            "password": "Password123!",
            "personnel_code": f"SEC-{unique_suffix.upper()}",
            "age": 27,
            "gender": "Male",
            "department": "Operations",
            "job_role": "Constable",
            "location": "Srinagar",
            "experience_years": 4.0
        }

        r = self.client.post("/api/auth/register-jawan", json=signup_payload)
        self.assertEqual(r.status_code, 201)
        jawan_token = r.json()["access_token"]
        jawan_headers = {"Authorization": f"Bearer {jawan_token}"}

        # Cannot access Commander dashboard summary (403)
        dash_resp = self.client.get("/api/dashboard/summary", headers=jawan_headers)
        self.assertEqual(dash_resp.status_code, 403)

        # Cannot access another personnel's dossier (e.g. ID 1)
        other_resp = self.client.get("/api/personnel/1", headers=jawan_headers)
        self.assertEqual(other_resp.status_code, 403)

    def test_04_initial_and_subsequent_checkin_persistence(self):
        """Verify check-in creates historical assessments and updates commander dashboard."""
        unique_suffix = uuid.uuid4().hex[:6]
        code = f"CHK-{unique_suffix.upper()}"
        signup_payload = {
            "name": f"Checkin Cadet {unique_suffix}",
            "username": f"chk_{unique_suffix}",
            "password": "Password123!",
            "personnel_code": code,
            "age": 30,
            "gender": "Male",
            "department": "Operations",
            "job_role": "Constable",
            "location": "Srinagar",
            "experience_years": 6.0
        }

        signup_resp = self.client.post("/api/auth/register-jawan", json=signup_payload)
        self.assertEqual(signup_resp.status_code, 201)
        jawan_token = signup_resp.json()["access_token"]
        jawan_pid = signup_resp.json()["personnel_id"]
        jawan_headers = {"Authorization": f"Bearer {jawan_token}"}

        # 1. Initial Check-in
        checkin_payload_1 = {
            "personnel_id": jawan_pid,
            "age": 30,
            "gender": "Male",
            "department": "Operations",
            "job_role": "Constable",
            "experience_years": 6.0,
            "working_hours_per_week": 60.0,
            "duty_hours_per_week": 60.0,
            "sleep_hours": 4.5,
            "physical_activity_hours_per_week": 2.0,
            "annual_leaves_taken": 4,
            "night_shifts_per_month": 10,
            "consecutive_duty_days": 12,
            "leave_gap_days": 120
        }

        resp1 = self.client.post("/api/submit-checkin", json=checkin_payload_1, headers=jawan_headers)
        self.assertEqual(resp1.status_code, 200)
        data1 = resp1.json()
        self.assertEqual(data1["status"], "success")
        self.assertIn("assessment", data1)
        self.assertIn("stress_level", data1["assessment"])
        self.assertIn("risk_score", data1["assessment"])

        # Check assessment history has 1 record
        hist_resp1 = self.client.get(f"/api/personnel/{jawan_pid}/assessments", headers=jawan_headers)
        self.assertEqual(hist_resp1.status_code, 200)
        history1 = hist_resp1.json()
        self.assertEqual(len(history1), 1)

        # 2. Subsequent Check-in later (duty hours reduced, rest improved)
        checkin_payload_2 = dict(checkin_payload_1)
        checkin_payload_2["duty_hours_per_week"] = 44.0
        checkin_payload_2["sleep_hours"] = 7.0
        checkin_payload_2["night_shifts_per_month"] = 2
        checkin_payload_2["consecutive_duty_days"] = 3

        resp2 = self.client.post("/api/submit-checkin", json=checkin_payload_2, headers=jawan_headers)
        self.assertEqual(resp2.status_code, 200)

        # Check assessment history now has 2 distinct historical records
        hist_resp2 = self.client.get(f"/api/personnel/{jawan_pid}/assessments", headers=jawan_headers)
        self.assertEqual(hist_resp2.status_code, 200)
        history2 = hist_resp2.json()
        self.assertEqual(len(history2), 2)
        # Most recent is first
        self.assertGreaterEqual(history2[0]["id"], history2[1]["id"])

        # 3. Verify newly registered Jawan appears in Commander Dashboard
        list_resp = self.client.get("/api/personnel?size=100", headers=self.officer_headers)
        self.assertEqual(list_resp.status_code, 200)
        items = list_resp.json()["items"]
        found = [p for p in items if p["personnel_code"] == code]
        self.assertEqual(len(found), 1, f"Personnel {code} not found in Commander list")
        new_jawan_entry = found[0]
        self.assertIsNotNone(new_jawan_entry["latest_risk_score"])
        self.assertIsNotNone(new_jawan_entry["latest_stress_level"])
        self.assertIsNotNone(new_jawan_entry["latest_priority"])

if __name__ == '__main__':
    unittest.main()
