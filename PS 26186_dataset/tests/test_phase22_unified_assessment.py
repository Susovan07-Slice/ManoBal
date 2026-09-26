import unittest
import uuid
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from api.main import app
from db.session import get_db
from db.models.user import User
from db.models.personnel import Personnel
from db.models.assessment import StressAssessment
from db.models.recommendation import WelfareRecommendation
from core.security import create_access_token

class TestPhase22UnifiedAssessment(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def setUp(self):
        self.db = next(get_db())

    def tearDown(self):
        self.db.close()

    def _create_officer_token(self) -> dict:
        officer = self.db.query(User).filter(User.username == "officer_sharma").first()
        if not officer:
            officer = User(
                username="officer_sharma",
                email="officer.sharma@crpf.gov.in",
                hashed_password="hashed_dummy_pw",
                role="officer",
                is_active=True
            )
            self.db.add(officer)
            self.db.commit()
            self.db.refresh(officer)
        token = create_access_token({"sub": officer.username, "role": officer.role, "personnel_id": None})
        return {"Authorization": f"Bearer {token}"}

    def test_01_new_jawan_initial_assessment_due(self):
        """Scenario A: New jawan signup creates personnel with NO assessments -> assessment_due is True."""
        unique_suffix = str(uuid.uuid4())[:8]
        signup_payload = {
            "name": f"Cadet New {unique_suffix}",
            "username": f"cadet_{unique_suffix}",
            "password": "Password123!",
            "personnel_code": f"P22-{unique_suffix.upper()}",
            "age": 24,
            "gender": "Male",
            "department": "Operations",
            "job_role": "Constable",
            "location": "Srinagar",
            "experience_years": 2.0,
            "duty_hours_per_week": 44.0
        }
        res_signup = self.client.post("/api/auth/register-jawan", json=signup_payload)
        self.assertEqual(res_signup.status_code, 201)
        data = res_signup.json()
        token = data["access_token"]
        personnel_id = data["personnel_id"]
        self.assertIsNotNone(personnel_id)

        headers = {"Authorization": f"Bearer {token}"}

        # Query 24-hour schedule status via both endpoints
        status_res = self.client.get(f"/api/personnel/{personnel_id}/assessment-status", headers=headers)
        self.assertEqual(status_res.status_code, 200)
        status_data = status_res.json()

        self.assertEqual(status_data["personnel_id"], personnel_id)
        self.assertFalse(status_data["has_assessment"])
        self.assertIsNone(status_data["last_assessment_at"])
        self.assertTrue(status_data["assessment_due"])
        self.assertIsNone(status_data["hours_since_last_assessment"])
        self.assertIn("immediately due", status_data["message"].lower())

        # Also test /api/assessment/status convenience route
        me_status = self.client.get("/api/assessment/status", headers=headers)
        self.assertEqual(me_status.status_code, 200)
        self.assertTrue(me_status.json()["assessment_due"])

    def test_02_single_unified_assessment_submission(self):
        """Scenario B: Submitting unified assessment creates ONE record, ONE risk score, ONE recommendation set."""
        unique_suffix = str(uuid.uuid4())[:8]
        signup_payload = {
            "name": f"Cadet Assess {unique_suffix}",
            "username": f"cadet_ass_{unique_suffix}",
            "password": "Password123!",
            "personnel_code": f"P22-A{unique_suffix.upper()}",
            "age": 28,
            "gender": "Female",
            "department": "Operations",
            "job_role": "Head Constable",
            "location": "Jammu",
            "experience_years": 4.5,
            "duty_hours_per_week": 46.0
        }
        res_signup = self.client.post("/api/auth/register-jawan", json=signup_payload)
        token = res_signup.json()["access_token"]
        personnel_id = res_signup.json()["personnel_id"]
        headers = {"Authorization": f"Bearer {token}"}

        # Submit unified assessment with combined inputs (Section A, B, C)
        assessment_payload = {
            "duty_hours_per_week": 54.0,
            "night_shifts_per_month": 4,
            "consecutive_duty_days": 8,
            "leave_gap_days": 45,
            "sleep_hours": 6.0,
            "physical_activity_hours_per_week": 4.0,
            "operational_exposure": "Medium",
            "remote_posting": "No",
            "mood_score": 3,
            "burnout_symptoms": "Sometimes"
        }

        assess_res = self.client.post(
            f"/api/personnel/{personnel_id}/assess",
            json=assessment_payload,
            headers=headers
        )
        self.assertEqual(assess_res.status_code, 201)
        res_data = assess_res.json()
        assessment = res_data["assessment"]

        # Verify ONE combined assessment result
        self.assertIn(assessment["stress_level"], ["Low", "Medium", "High"])
        self.assertGreaterEqual(assessment["risk_score"], 0)
        self.assertLessEqual(assessment["risk_score"], 100)
        self.assertIn(assessment["risk_priority"], ["Routine", "Preventive", "Priority"])
        self.assertGreater(len(assessment["recommendations"]), 0)

        # Verify exactly ONE assessment record exists in DB
        records = self.db.query(StressAssessment).filter(StressAssessment.personnel_id == personnel_id).all()
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].risk_score, assessment["risk_score"])
        self.assertEqual(records[0].stress_level, assessment["stress_level"])

        # Immediately check schedule status: should now be NOT due (< 24h)
        status_res = self.client.get(f"/api/personnel/{personnel_id}/assessment-status", headers=headers)
        self.assertEqual(status_res.status_code, 200)
        status_data = status_res.json()
        self.assertTrue(status_data["has_assessment"])
        self.assertFalse(status_data["assessment_due"])
        self.assertLess(status_data["hours_since_last_assessment"], 1.0)
        self.assertEqual(status_data["latest_risk_score"], assessment["risk_score"])
        self.assertEqual(status_data["latest_stress_level"], assessment["stress_level"])

    def test_03_server_backed_24_hour_schedule_rule(self):
        """Scenario C & D: Timestamp < 24h -> not due; Artificial timestamp >= 24h -> due."""
        unique_suffix = str(uuid.uuid4())[:8]
        signup_payload = {
            "name": f"Cadet Timer {unique_suffix}",
            "username": f"cadet_tim_{unique_suffix}",
            "password": "Password123!",
            "personnel_code": f"P22-T{unique_suffix.upper()}",
            "age": 30,
            "gender": "Male",
            "department": "Operations",
            "job_role": "Sub-Inspector",
            "location": "Dantewada",
            "experience_years": 6.0,
            "duty_hours_per_week": 48.0
        }
        res_signup = self.client.post("/api/auth/register-jawan", json=signup_payload)
        token = res_signup.json()["access_token"]
        personnel_id = res_signup.json()["personnel_id"]
        headers = {"Authorization": f"Bearer {token}"}

        # Perform initial assessment
        self.client.post(
            f"/api/personnel/{personnel_id}/assess",
            json={"duty_hours_per_week": 42.0, "sleep_hours": 7.5, "mood_score": 4},
            headers=headers
        )

        record = self.db.query(StressAssessment).filter(StressAssessment.personnel_id == personnel_id).first()
        self.assertIsNotNone(record)

        # 1. Artificially set timestamp to 8 hours ago (< 24h)
        record.assessment_timestamp = datetime.now(timezone.utc) - timedelta(hours=8)
        self.db.commit()

        status_8h = self.client.get(f"/api/personnel/{personnel_id}/assessment-status", headers=headers).json()
        self.assertTrue(status_8h["has_assessment"])
        self.assertFalse(status_8h["assessment_due"], "Assessment should NOT be due at 8 hours")
        self.assertAlmostEqual(status_8h["hours_since_last_assessment"], 8.0, delta=0.5)

        # 2. Artificially set timestamp to 23 hours ago (< 24h)
        record.assessment_timestamp = datetime.now(timezone.utc) - timedelta(hours=23)
        self.db.commit()

        status_23h = self.client.get(f"/api/personnel/{personnel_id}/assessment-status", headers=headers).json()
        self.assertFalse(status_23h["assessment_due"], "Assessment should NOT be due at 23 hours")

        # 3. Artificially set timestamp to 25 hours ago (>= 24h)
        record.assessment_timestamp = datetime.now(timezone.utc) - timedelta(hours=25)
        self.db.commit()

        status_25h = self.client.get(f"/api/personnel/{personnel_id}/assessment-status", headers=headers).json()
        self.assertTrue(status_25h["assessment_due"], "Assessment MUST be due after 24 hours")
        self.assertAlmostEqual(status_25h["hours_since_last_assessment"], 25.0, delta=0.5)

    def test_04_subsequent_assessment_updates_current_risk_and_preserves_history(self):
        """Scenario E: Second assessment creates new record, updates current risk, keeps history."""
        unique_suffix = str(uuid.uuid4())[:8]
        signup_payload = {
            "name": f"Cadet History {unique_suffix}",
            "username": f"cadet_his_{unique_suffix}",
            "password": "Password123!",
            "personnel_code": f"P22-H{unique_suffix.upper()}",
            "age": 26,
            "gender": "Male",
            "department": "Engineering",
            "job_role": "Constable",
            "location": "Leh",
            "experience_years": 3.0,
            "duty_hours_per_week": 44.0
        }
        res_signup = self.client.post("/api/auth/register-jawan", json=signup_payload)
        token = res_signup.json()["access_token"]
        personnel_id = res_signup.json()["personnel_id"]
        headers = {"Authorization": f"Bearer {token}"}

        # Assessment 1: Low stress profile
        resp1 = self.client.post(
            f"/api/personnel/{personnel_id}/assess",
            json={"duty_hours_per_week": 36.0, "sleep_hours": 8.0, "consecutive_duty_days": 2, "mood_score": 5},
            headers=headers
        )
        self.assertEqual(resp1.status_code, 201)
        score1 = resp1.json()["assessment"]["risk_score"]

        # Assessment 2: High stress profile
        resp2 = self.client.post(
            f"/api/personnel/{personnel_id}/assess",
            json={"duty_hours_per_week": 72.0, "sleep_hours": 4.0, "consecutive_duty_days": 18, "mood_score": 1, "burnout_symptoms": "Often"},
            headers=headers
        )
        self.assertEqual(resp2.status_code, 201)
        score2 = resp2.json()["assessment"]["risk_score"]

        # Verify history has 2 records
        history_res = self.client.get(f"/api/personnel/{personnel_id}/assessments", headers=headers)
        self.assertEqual(history_res.status_code, 200)
        history = history_res.json()
        self.assertEqual(len(history), 2)
        # Most recent is first (ordered by timestamp desc)
        self.assertEqual(history[0]["risk_score"], score2)
        self.assertEqual(history[1]["risk_score"], score1)

        # Status reflects latest assessment (score2)
        status_res = self.client.get(f"/api/personnel/{personnel_id}/assessment-status", headers=headers).json()
        self.assertEqual(status_res["latest_risk_score"], score2)

    def test_05_commander_sees_exact_same_unified_risk_score(self):
        """Scenario F: Commander views personnel assessment and sees identical unified risk score."""
        unique_suffix = str(uuid.uuid4())[:8]
        signup_payload = {
            "name": f"Cadet CmdrCheck {unique_suffix}",
            "username": f"cadet_cmd_{unique_suffix}",
            "password": "Password123!",
            "personnel_code": f"P22-C{unique_suffix.upper()}",
            "age": 29,
            "gender": "Male",
            "department": "Operations",
            "job_role": "Havildar",
            "location": "Srinagar",
            "experience_years": 5.0,
            "duty_hours_per_week": 48.0
        }
        res_signup = self.client.post("/api/auth/register-jawan", json=signup_payload)
        token = res_signup.json()["access_token"]
        personnel_id = res_signup.json()["personnel_id"]
        jawan_headers = {"Authorization": f"Bearer {token}"}

        # Jawan completes unified assessment
        assess_resp = self.client.post(
            f"/api/personnel/{personnel_id}/assess",
            json={"duty_hours_per_week": 50.0, "sleep_hours": 6.5, "mood_score": 3},
            headers=jawan_headers
        )
        jawan_risk = assess_resp.json()["assessment"]["risk_score"]
        jawan_stress = assess_resp.json()["assessment"]["stress_level"]
        jawan_priority = assess_resp.json()["assessment"]["risk_priority"]

        # Officer views same personnel's assessments
        officer_headers = self._create_officer_token()
        officer_history = self.client.get(f"/api/personnel/{personnel_id}/assessments", headers=officer_headers)
        self.assertEqual(officer_history.status_code, 200)
        history_data = officer_history.json()
        self.assertGreater(len(history_data), 0)

        # Identical authoritative risk score and stress level
        cmdr_latest = history_data[0]
        self.assertEqual(cmdr_latest["risk_score"], jawan_risk)
        self.assertEqual(cmdr_latest["stress_level"], jawan_stress)
        self.assertEqual(cmdr_latest["risk_priority"], jawan_priority)

    def test_06_rbac_access_restrictions(self):
        """Scenario G: Jawan A cannot view Jawan B's assessment status or history."""
        # Create Jawan A
        suffix_a = str(uuid.uuid4())[:8]
        res_a = self.client.post("/api/auth/register-jawan", json={
            "name": f"Jawan A {suffix_a}", "username": f"jawana_{suffix_a}", "password": "Password123!",
            "personnel_code": f"PA-{suffix_a.upper()}", "age": 25, "gender": "Male",
            "department": "Operations", "job_role": "Constable", "location": "Delhi",
            "experience_years": 2.0, "duty_hours_per_week": 40.0
        })
        token_a = res_a.json()["access_token"]
        headers_a = {"Authorization": f"Bearer {token_a}"}

        # Create Jawan B
        suffix_b = str(uuid.uuid4())[:8]
        res_b = self.client.post("/api/auth/register-jawan", json={
            "name": f"Jawan B {suffix_b}", "username": f"jawanb_{suffix_b}", "password": "Password123!",
            "personnel_code": f"PB-{suffix_b.upper()}", "age": 27, "gender": "Male",
            "department": "Operations", "job_role": "Constable", "location": "Delhi",
            "experience_years": 3.0, "duty_hours_per_week": 40.0
        })
        pid_b = res_b.json()["personnel_id"]

        # Jawan A tries to view Jawan B's assessment status -> 403 Forbidden
        forbidden_status = self.client.get(f"/api/personnel/{pid_b}/assessment-status", headers=headers_a)
        self.assertEqual(forbidden_status.status_code, 403)

        # Jawan A tries to view Jawan B's assessments -> 403 Forbidden
        forbidden_history = self.client.get(f"/api/personnel/{pid_b}/assessments", headers=headers_a)
        self.assertEqual(forbidden_history.status_code, 403)

if __name__ == "__main__":
    unittest.main()
