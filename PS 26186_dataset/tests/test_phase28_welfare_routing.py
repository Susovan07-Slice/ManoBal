import unittest
import uuid
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from api.main import app
from db.session import SessionLocal
from db.models.user import User
from db.models.personnel import Personnel
from db.models.welfare_request import WelfareRequest
from db.models.assessment import StressAssessment
from core.security import create_access_token

class TestPhase28WelfareRouting(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.db: Session = SessionLocal()

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def setUp(self):
        self.suffix = uuid.uuid4().hex[:6]

    def _create_jawan(self, battalion: str, location: str, name_prefix: str = "Jawan"):
        s = uuid.uuid4().hex[:6]
        res = self.client.post("/api/auth/register-jawan", json={
            "username": f"jwn_{s}",
            "password": "Password123!",
            "name": f"{name_prefix} {s}",
            "personnel_code": f"P28-{s.upper()}",
            "age": 28,
            "gender": "Male",
            "department": "Operations",
            "battalion": battalion,
            "job_role": "Constable",
            "location": location,
            "experience_years": 4.5,
            "duty_hours_per_week": 48.0
        })
        self.assertEqual(res.status_code, 201, f"Jawan signup failed: {res.text}")
        data = res.json()
        return data["access_token"], data["personnel_id"], f"P28-{s.upper()}"

    def _create_commander(self, battalion: str, location: str, name_prefix: str = "Commander"):
        s = uuid.uuid4().hex[:6]
        res = self.client.post("/api/auth/register-commander", json={
            "username": f"cmd_{s}",
            "password": "Password123!",
            "name": f"{name_prefix} {s}",
            "battalion": battalion,
            "location": location
        })
        self.assertEqual(res.status_code, 201, f"Commander signup failed: {res.text}")
        data = res.json()
        return data["access_token"]

    def test_01_create_request_persists_in_postgres_with_scope(self):
        """Test 1: Jawan creates welfare request; verified persisted in DB with correct status & scope."""
        token_a, pid_a, pcode_a = self._create_jawan("7th Battalion", "Jamshedpur", "TestJawanA")
        headers = {"Authorization": f"Bearer {token_a}"}

        payload = {
            "category": "Emergency SOS Support",
            "urgency": "High",
            "message": "Urgent welfare assistance requested via mobile SOS button."
        }
        res = self.client.post("/api/welfare/requests", json=payload, headers=headers)
        self.assertEqual(res.status_code, 201)
        data = res.json()

        self.assertEqual(data["personnel_id"], pid_a)
        self.assertEqual(data["battalion"], "7th Battalion")
        self.assertEqual(data["location"], "Jamshedpur")
        self.assertEqual(data["status"], "pending")
        self.assertEqual(data["urgency"], "High")
        self.assertEqual(data["category"], "Emergency SOS Support")

        # Direct DB verification
        db_req = self.db.query(WelfareRequest).filter(WelfareRequest.id == data["id"]).first()
        self.assertIsNotNone(db_req)
        self.assertEqual(db_req.personnel_id, pid_a)
        self.assertEqual(db_req.battalion, "7th Battalion")
        self.assertEqual(db_req.location, "Jamshedpur")
        self.assertEqual(db_req.status, "pending")
        self.assertEqual(db_req.category, "Emergency SOS Support")

    def test_02_commander_a_receives_request_and_commander_b_isolated(self):
        """Tests 2 & 3: Commander A (7th Batt, Jamshedpur) sees request; Commander B (8th Batt, Ranchi) cannot."""
        token_jawan_a, pid_a, pcode_a = self._create_jawan("7th Battalion", "Jamshedpur")
        token_cmdr_a = self._create_commander("7th Battalion", "Jamshedpur")
        token_cmdr_b = self._create_commander("8th Battalion", "Ranchi")

        # Jawan A submits emergency request
        res = self.client.post("/api/welfare/requests", json={
            "category": "Emergency SOS Support",
            "urgency": "High",
            "message": "Scope isolation test request"
        }, headers={"Authorization": f"Bearer {token_jawan_a}"})
        req_id = res.json()["id"]

        # Commander A queries welfare requests -> MUST APPEAR
        res_a = self.client.get("/api/welfare/requests", headers={"Authorization": f"Bearer {token_cmdr_a}"})
        self.assertEqual(res_a.status_code, 200)
        items_a = res_a.json()
        ids_a = [r["id"] for r in items_a]
        self.assertIn(req_id, ids_a)

        # Commander B queries welfare requests -> MUST NOT APPEAR
        res_b = self.client.get("/api/welfare/requests", headers={"Authorization": f"Bearer {token_cmdr_b}"})
        self.assertEqual(res_b.status_code, 200)
        items_b = res_b.json()
        ids_b = [r["id"] for r in items_b]
        self.assertNotIn(req_id, ids_b)

    def test_03_cross_scope_api_security(self):
        """Test 4: Cross-scope commander attempting to GET or PATCH request gets 403 Forbidden."""
        token_jawan_a, pid_a, pcode_a = self._create_jawan("7th Battalion", "Jamshedpur")
        token_cmdr_b = self._create_commander("8th Battalion", "Ranchi")

        res = self.client.post("/api/welfare/requests", json={
            "category": "Duty Schedule & Workload",
            "urgency": "Medium"
        }, headers={"Authorization": f"Bearer {token_jawan_a}"})
        req_id = res.json()["id"]

        # Commander B attempts to view request A via GET
        get_res = self.client.get(
            f"/api/welfare/requests/{req_id}",
            headers={"Authorization": f"Bearer {token_cmdr_b}"}
        )
        self.assertEqual(get_res.status_code, 403)
        self.assertIn("outside your assigned Battalion and Location scope", get_res.json()["detail"])

        # Commander B attempts to modify request A via PATCH
        patch_res = self.client.patch(
            f"/api/welfare/requests/{req_id}/status",
            json={"status": "acknowledged"},
            headers={"Authorization": f"Bearer {token_cmdr_b}"}
        )
        self.assertEqual(patch_res.status_code, 403)
        self.assertIn("outside your assigned Battalion and Location scope", patch_res.json()["detail"])

    def test_04_status_update_lifecycle_and_jawan_visibility(self):
        """Test 5: Commander A updates status pending -> acknowledged; Jawan sees updated status."""
        token_jawan_a, pid_a, pcode_a = self._create_jawan("7th Battalion", "Jamshedpur")
        token_cmdr_a = self._create_commander("7th Battalion", "Jamshedpur")

        res = self.client.post("/api/welfare/requests", json={
            "category": "Personal & Family Matters",
            "urgency": "Routine"
        }, headers={"Authorization": f"Bearer {token_jawan_a}"})
        req_id = res.json()["id"]

        # Commander updates to acknowledged
        patch_res = self.client.patch(
            f"/api/welfare/requests/{req_id}/status",
            json={"status": "acknowledged"},
            headers={"Authorization": f"Bearer {token_cmdr_a}"}
        )
        self.assertEqual(patch_res.status_code, 200)
        self.assertEqual(patch_res.json()["status"], "acknowledged")

        # Jawan retrieves own requests -> shows acknowledged
        jawan_view = self.client.get("/api/welfare/requests/my", headers={"Authorization": f"Bearer {token_jawan_a}"})
        self.assertEqual(jawan_view.status_code, 200)
        my_reqs = jawan_view.json()
        target = next(r for r in my_reqs if r["id"] == req_id)
        self.assertEqual(target["status"], "acknowledged")

    def test_05_commander_dashboard_kpi_scoping(self):
        """Test 6: Commander A KPI counts only Request A; Commander B counts only Request B."""
        token_jawan_a, pid_a, _ = self._create_jawan("7th Battalion", "Jamshedpur")
        token_jawan_b, pid_b, _ = self._create_jawan("8th Battalion", "Ranchi")
        token_cmdr_a = self._create_commander("7th Battalion", "Jamshedpur")
        token_cmdr_b = self._create_commander("8th Battalion", "Ranchi")

        init_kpi_a = self.client.get("/api/dashboard/summary", headers={"Authorization": f"Bearer {token_cmdr_a}"}).json()["pending_recommendations"]
        init_kpi_b = self.client.get("/api/dashboard/summary", headers={"Authorization": f"Bearer {token_cmdr_b}"}).json()["pending_recommendations"]

        # Request A
        self.client.post("/api/welfare/requests", json={
            "category": "Duty Schedule & Workload",
            "urgency": "Medium"
        }, headers={"Authorization": f"Bearer {token_jawan_a}"})

        # Request B
        self.client.post("/api/welfare/requests", json={
            "category": "Rest & Sleep Fatigue",
            "urgency": "High"
        }, headers={"Authorization": f"Bearer {token_jawan_b}"})

        new_kpi_a = self.client.get("/api/dashboard/summary", headers={"Authorization": f"Bearer {token_cmdr_a}"}).json()["pending_recommendations"]
        new_kpi_b = self.client.get("/api/dashboard/summary", headers={"Authorization": f"Bearer {token_cmdr_b}"}).json()["pending_recommendations"]

        self.assertEqual(new_kpi_a, init_kpi_a + 1)
        self.assertEqual(new_kpi_b, init_kpi_b + 1)

    def test_06_strict_and_location_same_battalion_different(self):
        """Test 7: Location same (Jamshedpur), Battalion different (7th vs 8th) -> strict AND enforced."""
        token_jawan_a, _, _ = self._create_jawan("7th Battalion", "Jamshedpur")
        token_jawan_b, _, _ = self._create_jawan("8th Battalion", "Jamshedpur")
        token_cmdr = self._create_commander("7th Battalion", "Jamshedpur")

        res_a = self.client.post("/api/welfare/requests", json={
            "category": "Duty Schedule & Workload",
            "urgency": "Routine"
        }, headers={"Authorization": f"Bearer {token_jawan_a}"})
        req_a_id = res_a.json()["id"]

        res_b = self.client.post("/api/welfare/requests", json={
            "category": "Duty Schedule & Workload",
            "urgency": "Routine"
        }, headers={"Authorization": f"Bearer {token_jawan_b}"})
        req_b_id = res_b.json()["id"]

        cmdr_view = self.client.get("/api/welfare/requests", headers={"Authorization": f"Bearer {token_cmdr}"}).json()
        ids = [r["id"] for r in cmdr_view]
        self.assertIn(req_a_id, ids)
        self.assertNotIn(req_b_id, ids)

    def test_07_strict_and_battalion_same_location_different(self):
        """Test 8: Battalion same (7th), Location different (Jamshedpur vs Ranchi) -> strict AND enforced."""
        token_jawan_a, _, _ = self._create_jawan("7th Battalion", "Jamshedpur")
        token_jawan_b, _, _ = self._create_jawan("7th Battalion", "Ranchi")
        token_cmdr = self._create_commander("7th Battalion", "Jamshedpur")

        res_a = self.client.post("/api/welfare/requests", json={
            "category": "Operational Stress & Morale",
            "urgency": "High"
        }, headers={"Authorization": f"Bearer {token_jawan_a}"})
        req_a_id = res_a.json()["id"]

        res_b = self.client.post("/api/welfare/requests", json={
            "category": "Operational Stress & Morale",
            "urgency": "High"
        }, headers={"Authorization": f"Bearer {token_jawan_b}"})
        req_b_id = res_b.json()["id"]

        cmdr_view = self.client.get("/api/welfare/requests", headers={"Authorization": f"Bearer {token_cmdr}"}).json()
        ids = [r["id"] for r in cmdr_view]
        self.assertIn(req_a_id, ids)
        self.assertNotIn(req_b_id, ids)

    def test_08_duplicate_active_request_returns_409_conflict(self):
        """Test 9: Attempting to submit duplicate active request of same category returns 409 Conflict."""
        token_jawan, pid, _ = self._create_jawan("7th Battalion", "Jamshedpur")
        headers = {"Authorization": f"Bearer {token_jawan}"}

        # First request succeeds
        res1 = self.client.post("/api/welfare/requests", json={
            "category": "Emergency SOS Support",
            "urgency": "High"
        }, headers=headers)
        self.assertEqual(res1.status_code, 201)

        # Second identical category request returns 409 Conflict
        res2 = self.client.post("/api/welfare/requests", json={
            "category": "Emergency SOS Support",
            "urgency": "High"
        }, headers=headers)
        self.assertEqual(res2.status_code, 409)
        self.assertIn("already have an active pending welfare request", res2.json()["detail"])

    def test_09_continuous_float_risk_score_serialization(self):
        """Test 10: Ensures floating-point risk scores serialize properly without Pydantic ValidationError."""
        token_jawan, pid, _ = self._create_jawan("7th Battalion", "Jamshedpur")
        token_cmdr = self._create_commander("7th Battalion", "Jamshedpur")
        headers_jawan = {"Authorization": f"Bearer {token_jawan}"}
        headers_cmdr = {"Authorization": f"Bearer {token_cmdr}"}

        # Jawan completes assessment resulting in a float continuous risk score
        ass_res = self.client.post(f"/api/personnel/{pid}/assess", json={
            "duty_hours_per_week": 65.0,
            "consecutive_duty_days": 18,
            "night_shifts_per_month": 12,
            "sleep_hours_per_night": 4.0,
            "physical_activity_hours_per_week": 1.5,
            "operational_exposure": "High",
            "remote_isolated_posting": "Yes",
            "overall_mood": 1,
            "burnout_symptoms": "Often",
            "feeling_down_depressed": "Nearly every day",
            "trouble_concentrating": "More than half the days"
        }, headers=headers_cmdr)
        self.assertEqual(ass_res.status_code, 201)
        ass_data = ass_res.json()
        expected_score = ass_data["assessment"]["risk_score"] if "assessment" in ass_data else ass_data["risk_score"]
        self.assertIsInstance(expected_score, float)

        # Jawan submits welfare request
        req_res = self.client.post("/api/welfare/requests", json={
            "category": "Operational Stress & Morale",
            "urgency": "High"
        }, headers=headers_jawan)
        self.assertEqual(req_res.status_code, 201)
        req_data = req_res.json()
        self.assertEqual(req_data["current_risk_score"], expected_score)

        # Commander queries welfare requests -> float serialized without 500 error
        cmdr_res = self.client.get("/api/welfare/requests", headers=headers_cmdr)
        self.assertEqual(cmdr_res.status_code, 200)
        found = next(r for r in cmdr_res.json() if r["id"] == req_data["id"])
        self.assertEqual(found["current_risk_score"], expected_score)

if __name__ == "__main__":
    unittest.main()
