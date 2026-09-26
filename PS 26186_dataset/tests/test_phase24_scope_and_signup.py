import unittest
import uuid
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from api.main import app
from db.session import SessionLocal
from db.models.user import User
from db.models.personnel import Personnel
from db.models.welfare_request import WelfareRequest
from core.security import create_access_token

class TestPhase24ScopeAndSignup(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.db: Session = SessionLocal()

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def setUp(self):
        self.suffix = uuid.uuid4().hex[:8]

    # 1. Organization canonical endpoints
    def test_01_organizations_api(self):
        """GET /api/organizations/battalions and /locations return canonical lists."""
        res_b = self.client.get("/api/organizations/battalions")
        self.assertEqual(res_b.status_code, 200)
        battalions = res_b.json()
        self.assertIn("7th Battalion", battalions)
        self.assertIn("8th Battalion", battalions)

        res_l = self.client.get("/api/organizations/locations")
        self.assertEqual(res_l.status_code, 200)
        locations = res_l.json()
        self.assertIn("Jamshedpur", locations)
        self.assertIn("Ranchi", locations)

    # 2. Commander signup assigns officer role and scope
    def test_02_commander_signup(self):
        """Commander signup binds user strictly to officer role and assigned scope."""
        payload = {
            "username": f"cmd_{self.suffix}",
            "password": "Password123!",
            "name": "Major A. Sharma",
            "battalion": "7th Battalion",
            "location": "Jamshedpur"
        }
        res = self.client.post("/api/auth/register-commander", json=payload)
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertEqual(data["role"], "officer")
        self.assertEqual(data["battalion"], "7th Battalion")
        self.assertEqual(data["location"], "Jamshedpur")
        self.assertIn("access_token", data)

        # Database verification
        user = self.db.query(User).filter(User.username == f"cmd_{self.suffix}").first()
        self.assertIsNotNone(user)
        self.assertEqual(user.role, "officer")
        self.assertEqual(user.battalion, "7th Battalion")
        self.assertEqual(user.location, "Jamshedpur")

        # Invalid scope rejection
        bad_payload = dict(payload, username=f"cmd_bad_{self.suffix}", battalion="NonExistent 99th")
        res_bad = self.client.post("/api/auth/register-commander", json=bad_payload)
        self.assertEqual(res_bad.status_code, 400)

    # 3. Jawan signup requires and validates battalion and location
    def test_03_jawan_signup_with_scope(self):
        """Jawan signup enforces canonical battalion and location on user and personnel records."""
        payload = {
            "username": f"jwn_{self.suffix}",
            "password": "Password123!",
            "name": "Constable R. Kumar",
            "personnel_code": f"JWN-{self.suffix.upper()}",
            "age": 27,
            "gender": "Male",
            "department": "Operations",
            "battalion": "7th Battalion",
            "job_role": "Patrol Scout",
            "location": "Jamshedpur",
            "experience_years": 4.0,
            "duty_hours_per_week": 45.0
        }
        res = self.client.post("/api/auth/register-jawan", json=payload)
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertEqual(data["role"], "personnel")
        self.assertEqual(data["battalion"], "7th Battalion")
        self.assertEqual(data["location"], "Jamshedpur")

        # Database verification
        personnel = self.db.query(Personnel).filter(Personnel.personnel_code == payload["personnel_code"]).first()
        self.assertIsNotNone(personnel)
        self.assertEqual(personnel.battalion, "7th Battalion")
        self.assertEqual(personnel.location, "Jamshedpur")

    # 4. Multi-scope isolation test
    def test_04_multi_scope_isolation_and_cross_access(self):
        """
        Verify complete scope isolation:
        Commander A (7th Battalion, Jamshedpur) sees ONLY Scope A Jawans.
        Commander B (8th Battalion, Ranchi) sees ONLY Scope B Jawans.
        Cross-scope access returns 403 Forbidden.
        """
        # Create Scope A: Commander A + Jawan A1, Jawan A2
        scope_a_suffix = uuid.uuid4().hex[:6]
        c_a_res = self.client.post("/api/auth/register-commander", json={
            "username": f"cmda_{scope_a_suffix}",
            "password": "Password123!",
            "name": "Commander Alpha",
            "battalion": "7th Battalion",
            "location": "Bhubaneswar"
        }).json()
        headers_a = {"Authorization": f"Bearer {c_a_res['access_token']}"}
        init_a = self.client.get("/api/dashboard/summary", headers=headers_a).json()["total_personnel"]

        # Create Scope B: Commander B
        scope_b_suffix = uuid.uuid4().hex[:6]
        c_b_res = self.client.post("/api/auth/register-commander", json={
            "username": f"cmdb_{scope_b_suffix}",
            "password": "Password123!",
            "name": "Commander Bravo",
            "battalion": "8th Battalion",
            "location": "Ranchi"
        }).json()
        headers_b = {"Authorization": f"Bearer {c_b_res['access_token']}"}
        init_b = self.client.get("/api/dashboard/summary", headers=headers_b).json()["total_personnel"]

        # Create Jawans for Scope A
        j_a1_res = self.client.post("/api/auth/register-jawan", json={
            "username": f"jwa1_{scope_a_suffix}",
            "password": "Password123!",
            "name": "Jawan Alpha One",
            "personnel_code": f"JA1-{scope_a_suffix.upper()}",
            "age": 25,
            "gender": "Male",
            "department": "Operations",
            "battalion": "7th Battalion",
            "job_role": "Patrol",
            "location": "Bhubaneswar",
            "experience_years": 3.0
        }).json()
        p_a1_id = j_a1_res["personnel_id"]

        j_a2_res = self.client.post("/api/auth/register-jawan", json={
            "username": f"jwa2_{scope_a_suffix}",
            "password": "Password123!",
            "name": "Jawan Alpha Two",
            "personnel_code": f"JA2-{scope_a_suffix.upper()}",
            "age": 29,
            "gender": "Male",
            "department": "Communications",
            "battalion": "7th Battalion",
            "job_role": "Specialist",
            "location": "Bhubaneswar",
            "experience_years": 5.0
        }).json()
        p_a2_id = j_a2_res["personnel_id"]

        # Create Jawans for Scope B
        j_b1_res = self.client.post("/api/auth/register-jawan", json={
            "username": f"jwb1_{scope_b_suffix}",
            "password": "Password123!",
            "name": "Jawan Bravo One",
            "personnel_code": f"JB1-{scope_b_suffix.upper()}",
            "age": 31,
            "gender": "Male",
            "department": "Operations",
            "battalion": "8th Battalion",
            "job_role": "Team Lead",
            "location": "Ranchi",
            "experience_years": 8.0
        }).json()
        p_b1_id = j_b1_res["personnel_id"]

        # --- A. List Personnel Scoping ---
        list_a = self.client.get("/api/personnel", headers=headers_a).json()
        a_codes = [item["personnel_code"] for item in list_a["items"]]
        self.assertIn(f"JA1-{scope_a_suffix.upper()}", a_codes)
        self.assertIn(f"JA2-{scope_a_suffix.upper()}", a_codes)
        self.assertNotIn(f"JB1-{scope_b_suffix.upper()}", a_codes)

        list_b = self.client.get("/api/personnel", headers=headers_b).json()
        b_codes = [item["personnel_code"] for item in list_b["items"]]
        self.assertIn(f"JB1-{scope_b_suffix.upper()}", b_codes)
        self.assertNotIn(f"JA1-{scope_a_suffix.upper()}", b_codes)
        self.assertNotIn(f"JA2-{scope_a_suffix.upper()}", b_codes)

        # --- B. Cross-Scope Direct Detail Request Rejected with 403 ---
        # Commander A tries to access Jawan B1
        res_cross_a = self.client.get(f"/api/personnel/{p_b1_id}", headers=headers_a)
        self.assertEqual(res_cross_a.status_code, 403)
        self.assertIn("outside your assigned Battalion and Location scope", res_cross_a.json()["detail"])

        # Commander B tries to access Jawan A1
        res_cross_b = self.client.get(f"/api/personnel/{p_a1_id}", headers=headers_b)
        self.assertEqual(res_cross_b.status_code, 403)

        # --- C. Query Parameter Tampering Cannot Expand Scope ---
        tamper_res = self.client.get(
            "/api/personnel?battalion=8th%20Battalion&location=Ranchi",
            headers=headers_a
        )
        tamper_codes = [item["personnel_code"] for item in tamper_res.json()["items"]]
        self.assertNotIn(f"JB1-{scope_b_suffix.upper()}", tamper_codes)

        # --- D. Cross-Scope Telemetry Assessment / Simulation Rejected with 403 ---
        sim_res = self.client.post(
            f"/api/personnel/{p_b1_id}/assess",
            json={"duty_hours_per_week": 65.0},
            headers=headers_a
        )
        self.assertEqual(sim_res.status_code, 403)

        # --- E. Cross-Scope Welfare Requests & Updates ---
        headers_j_a1 = {"Authorization": f"Bearer {j_a1_res['access_token']}"}
        headers_j_b1 = {"Authorization": f"Bearer {j_b1_res['access_token']}"}

        # A1 creates welfare request
        req_a_res = self.client.post(
            "/api/welfare/requests",
            json={"category": "Duty Schedule & Workload", "urgency": "Medium", "message": "Scope A request"},
            headers=headers_j_a1
        ).json()
        req_a_id = req_a_res["id"]

        # B1 creates welfare request
        req_b_res = self.client.post(
            "/api/welfare/requests",
            json={"category": "Rest & Sleep Fatigue", "urgency": "High", "message": "Scope B request"},
            headers=headers_j_b1
        ).json()
        req_b_id = req_b_res["id"]

        # Commander A lists requests: sees A1, not B1
        w_list_a = self.client.get("/api/welfare/requests", headers=headers_a).json()
        w_ids_a = [r["id"] for r in w_list_a]
        self.assertIn(req_a_id, w_ids_a)
        self.assertNotIn(req_b_id, w_ids_a)

        # Commander B lists requests: sees B1, not A1
        w_list_b = self.client.get("/api/welfare/requests", headers=headers_b).json()
        w_ids_b = [r["id"] for r in w_list_b]
        self.assertIn(req_b_id, w_ids_b)
        self.assertNotIn(req_a_id, w_ids_b)

        # Commander A attempts to update Commander B's welfare request
        cross_patch = self.client.patch(
            f"/api/welfare/requests/{req_b_id}/status",
            json={"status": "acknowledged"},
            headers=headers_a
        )
        self.assertEqual(cross_patch.status_code, 403)

        # --- F. Dashboard Summary Scoping ---
        sum_a = self.client.get("/api/dashboard/summary", headers=headers_a).json()
        self.assertEqual(sum_a["total_personnel"] - init_a, 2)

        sum_b = self.client.get("/api/dashboard/summary", headers=headers_b).json()
        self.assertEqual(sum_b["total_personnel"] - init_b, 1)

    # 5. Admin role retains system-wide access
    def test_05_admin_retains_system_wide_access(self):
        """Admin has system-wide access without organizational scope limitations."""
        admin_token = create_access_token({"sub": "admin", "role": "admin", "personnel_id": None})
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        # Admin summary counts all personnel across all scopes
        sum_admin = self.client.get("/api/dashboard/summary", headers=admin_headers).json()
        self.assertGreaterEqual(sum_admin["total_personnel"], 3)

        # Admin lists all welfare requests
        w_admin = self.client.get("/api/welfare/requests", headers=admin_headers).json()
        self.assertGreaterEqual(len(w_admin), 1)

if __name__ == "__main__":
    unittest.main()
