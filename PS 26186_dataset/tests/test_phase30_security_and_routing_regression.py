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
from db.models.recommendation import WelfareRecommendation


class TestPhase30SecurityAndRoutingRegression(unittest.TestCase):
    """
    Phase 30 Automated Security & Welfare-Routing Regression Test Suite.
    PostgreSQL-backed verification of:
      1. Strict Battalion + Location visibility (all 4 permutation combinations)
      2. Jawan ownership boundaries and peer data isolation
      3. Complete end-to-end welfare lifecycle (pending -> acknowledged -> in_progress -> resolved)
      4. Independent Cross-scope update rejections (Battalion mismatch, Location mismatch, Both mismatch)
      5. Strict test data isolation and automated cleanup
    """

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.db: Session = SessionLocal()
        cls.cleanup_user_ids = []
        cls.cleanup_personnel_ids = []
        cls.cleanup_request_ids = []

    @classmethod
    def tearDownClass(cls):
        # Comprehensive cleanup of all test entities
        if cls.cleanup_request_ids:
            cls.db.query(WelfareRequest).filter(WelfareRequest.id.in_(cls.cleanup_request_ids)).delete(synchronize_session=False)
        if cls.cleanup_personnel_ids:
            cls.db.query(WelfareRecommendation).filter(WelfareRecommendation.personnel_id.in_(cls.cleanup_personnel_ids)).delete(synchronize_session=False)
            cls.db.query(StressAssessment).filter(StressAssessment.personnel_id.in_(cls.cleanup_personnel_ids)).delete(synchronize_session=False)
            cls.db.query(User).filter(User.personnel_id.in_(cls.cleanup_personnel_ids)).delete(synchronize_session=False)
            cls.db.query(Personnel).filter(Personnel.id.in_(cls.cleanup_personnel_ids)).delete(synchronize_session=False)
        if cls.cleanup_user_ids:
            cls.db.query(User).filter(User.id.in_(cls.cleanup_user_ids)).delete(synchronize_session=False)
        cls.db.commit()
        cls.db.close()

    def _register_jawan(self, battalion: str, location: str, name_prefix: str = "P30_Jawan"):
        s = uuid.uuid4().hex[:8]
        code = f"P30-{s.upper()}"
        res = self.client.post("/api/auth/register-jawan", json={
            "username": f"jwn_{s}",
            "password": "Password123!",
            "name": f"{name_prefix} {s}",
            "personnel_code": code,
            "age": 27,
            "gender": "Male",
            "department": "Security",
            "battalion": battalion,
            "job_role": "Constable / GD",
            "location": location,
            "experience_years": 3.5,
            "duty_hours_per_week": 44.0
        })
        self.assertEqual(res.status_code, 201, f"Jawan registration failed: {res.text}")
        data = res.json()
        pid = data["personnel_id"]
        self.cleanup_personnel_ids.append(pid)
        # Record user id for cleanup
        user_row = self.db.query(User).filter(User.username == f"jwn_{s}").first()
        if user_row:
            self.cleanup_user_ids.append(user_row.id)
        return data["access_token"], pid, code

    def _register_commander(self, battalion: str, location: str, name_prefix: str = "P30_Cmdr"):
        s = uuid.uuid4().hex[:8]
        res = self.client.post("/api/auth/register-commander", json={
            "username": f"cmd_{s}",
            "password": "Password123!",
            "name": f"{name_prefix} {s}",
            "battalion": battalion,
            "location": location
        })
        self.assertEqual(res.status_code, 201, f"Commander registration failed: {res.text}")
        data = res.json()
        user_row = self.db.query(User).filter(User.username == f"cmd_{s}").first()
        if user_row:
            self.cleanup_user_ids.append(user_row.id)
        return data["access_token"], user_row.id if user_row else None

    # =========================================================================
    # A. STRICT BATTALION + LOCATION VISIBILITY (4 PERMUTATIONS)
    # =========================================================================

    def test_01_scope_visibility_matching_battalion_and_location_allowed(self):
        """A.1: Valid matching Battalion + Location allows viewing welfare request in list and detail."""
        token_jawan, pid, _ = self._register_jawan("7th Battalion", "Jamshedpur")
        token_cmdr, _ = self._register_commander("7th Battalion", "Jamshedpur")

        res_req = self.client.post("/api/welfare/requests", json={
            "category": "Operational Stress & Fatigue",
            "urgency": "High",
            "message": "Routine tactical fatigue assistance."
        }, headers={"Authorization": f"Bearer {token_jawan}"})
        self.assertEqual(res_req.status_code, 201)
        req_id = res_req.json()["id"]
        self.cleanup_request_ids.append(req_id)

        # 1. Commander queries list
        res_list = self.client.get("/api/welfare/requests", headers={"Authorization": f"Bearer {token_cmdr}"})
        self.assertEqual(res_list.status_code, 200)
        req_ids = [r["id"] for r in res_list.json()]
        self.assertIn(req_id, req_ids)

        # 2. Commander queries detail
        res_detail = self.client.get(f"/api/welfare/requests/{req_id}", headers={"Authorization": f"Bearer {token_cmdr}"})
        self.assertEqual(res_detail.status_code, 200)
        self.assertEqual(res_detail.json()["id"], req_id)
        self.assertEqual(res_detail.json()["battalion"], "7th Battalion")
        self.assertEqual(res_detail.json()["location"], "Jamshedpur")

    def test_02_scope_visibility_battalion_mismatch_hidden(self):
        """A.2: Same Location, different Battalion -> Record is not exposed in list or direct GET."""
        token_jawan, pid, _ = self._register_jawan("7th Battalion", "Jamshedpur")
        token_cmdr_diff_batt, _ = self._register_commander("8th Battalion", "Jamshedpur")

        res_req = self.client.post("/api/welfare/requests", json={
            "category": "Duty Schedule Overload",
            "urgency": "Medium"
        }, headers={"Authorization": f"Bearer {token_jawan}"})
        req_id = res_req.json()["id"]
        self.cleanup_request_ids.append(req_id)

        # List must NOT include request
        res_list = self.client.get("/api/welfare/requests", headers={"Authorization": f"Bearer {token_cmdr_diff_batt}"})
        self.assertEqual(res_list.status_code, 200)
        self.assertNotIn(req_id, [r["id"] for r in res_list.json()])

        # Direct GET must return 403 Forbidden
        res_get = self.client.get(f"/api/welfare/requests/{req_id}", headers={"Authorization": f"Bearer {token_cmdr_diff_batt}"})
        self.assertEqual(res_get.status_code, 403)
        self.assertIn("outside your assigned Battalion and Location scope", res_get.json()["detail"])

    def test_03_scope_visibility_location_mismatch_hidden(self):
        """A.3: Same Battalion, different Location -> Record is not exposed in list or direct GET."""
        token_jawan, pid, _ = self._register_jawan("7th Battalion", "Jamshedpur")
        token_cmdr_diff_loc, _ = self._register_commander("7th Battalion", "Ranchi")

        res_req = self.client.post("/api/welfare/requests", json={
            "category": "Rest & Restorative Recovery",
            "urgency": "Routine"
        }, headers={"Authorization": f"Bearer {token_jawan}"})
        req_id = res_req.json()["id"]
        self.cleanup_request_ids.append(req_id)

        # List must NOT include request
        res_list = self.client.get("/api/welfare/requests", headers={"Authorization": f"Bearer {token_cmdr_diff_loc}"})
        self.assertEqual(res_list.status_code, 200)
        self.assertNotIn(req_id, [r["id"] for r in res_list.json()])

        # Direct GET must return 403 Forbidden
        res_get = self.client.get(f"/api/welfare/requests/{req_id}", headers={"Authorization": f"Bearer {token_cmdr_diff_loc}"})
        self.assertEqual(res_get.status_code, 403)
        self.assertIn("outside your assigned Battalion and Location scope", res_get.json()["detail"])

    def test_04_scope_visibility_both_mismatch_hidden(self):
        """A.4: Both Battalion and Location different -> Record is not exposed in list or direct GET."""
        token_jawan, pid, _ = self._register_jawan("7th Battalion", "Jamshedpur")
        token_cmdr_both_diff, _ = self._register_commander("8th Battalion", "Srinagar")

        res_req = self.client.post("/api/welfare/requests", json={
            "category": "Emergency SOS Support",
            "urgency": "High"
        }, headers={"Authorization": f"Bearer {token_jawan}"})
        req_id = res_req.json()["id"]
        self.cleanup_request_ids.append(req_id)

        # List must NOT include request
        res_list = self.client.get("/api/welfare/requests", headers={"Authorization": f"Bearer {token_cmdr_both_diff}"})
        self.assertEqual(res_list.status_code, 200)
        self.assertNotIn(req_id, [r["id"] for r in res_list.json()])

        # Direct GET must return 403 Forbidden
        res_get = self.client.get(f"/api/welfare/requests/{req_id}", headers={"Authorization": f"Bearer {token_cmdr_both_diff}"})
        self.assertEqual(res_get.status_code, 403)
        self.assertIn("outside your assigned Battalion and Location scope", res_get.json()["detail"])

    # =========================================================================
    # B. JAWAN OWNERSHIP & PEER PRIVACY ISOLATION
    # =========================================================================

    def test_05_jawan_can_access_own_records(self):
        """B.1: Jawan can access own personnel profile, assessments, and welfare requests."""
        token_jawan, pid, code = self._register_jawan("7th Battalion", "Srinagar")
        headers = {"Authorization": f"Bearer {token_jawan}"}

        # 1. Own personnel profile
        p_res = self.client.get(f"/api/personnel/{pid}", headers=headers)
        self.assertEqual(p_res.status_code, 200)
        self.assertEqual(p_res.json()["personnel_code"], code)

        # 2. Own assessment execution
        ass_res = self.client.post(f"/api/personnel/{pid}/assess", json={
            "duty_hours_per_week": 48.0,
            "sleep_hours": 6.5,
            "mood_score": 4
        }, headers=headers)
        self.assertEqual(ass_res.status_code, 201)

        # 3. Own assessment history
        hist_res = self.client.get(f"/api/personnel/{pid}/assessments", headers=headers)
        self.assertEqual(hist_res.status_code, 200)
        self.assertGreaterEqual(len(hist_res.json()), 1)

        # 4. Own welfare requests
        w_res = self.client.post("/api/welfare/requests", json={
            "category": "Personal & Family Matters",
            "urgency": "Routine"
        }, headers=headers)
        self.assertEqual(w_res.status_code, 201)
        req_id = w_res.json()["id"]
        self.cleanup_request_ids.append(req_id)

        my_res = self.client.get("/api/welfare/requests/my", headers=headers)
        self.assertEqual(my_res.status_code, 200)
        self.assertIn(req_id, [r["id"] for r in my_res.json()])

    def test_06_jawan_cannot_access_peer_records(self):
        """B.2: Jawan A attempting to access Jawan B's data is rejected with 403 Forbidden."""
        token_a, pid_a, _ = self._register_jawan("7th Battalion", "Srinagar", "JawanAlpha")
        token_b, pid_b, _ = self._register_jawan("7th Battalion", "Srinagar", "JawanBravo")

        headers_a = {"Authorization": f"Bearer {token_a}"}
        headers_b = {"Authorization": f"Bearer {token_b}"}

        # Jawan B creates a welfare request
        res_req_b = self.client.post("/api/welfare/requests", json={
            "category": "Confidential Counseling",
            "urgency": "High"
        }, headers=headers_b)
        req_b_id = res_req_b.json()["id"]
        self.cleanup_request_ids.append(req_b_id)

        # 1. Jawan A attempts to view Jawan B's personnel profile -> 403
        res1 = self.client.get(f"/api/personnel/{pid_b}", headers=headers_a)
        self.assertEqual(res1.status_code, 403)
        self.assertIn("Access denied", res1.json()["detail"])

        # 2. Jawan A attempts to view Jawan B's assessment history -> 403
        res2 = self.client.get(f"/api/personnel/{pid_b}/assessments", headers=headers_a)
        self.assertEqual(res2.status_code, 403)
        self.assertIn("Access denied", res2.json()["detail"])

        # 3. Jawan A attempts to view Jawan B's specific welfare request -> 403
        res3 = self.client.get(f"/api/welfare/requests/{req_b_id}", headers=headers_a)
        self.assertEqual(res3.status_code, 403)
        self.assertIn("Access denied", res3.json()["detail"])

    def test_07_jawan_unauthorized_update_attempts_rejected(self):
        """B.3: Jawan attempting to assess another jawan or update welfare status is rejected."""
        token_a, pid_a, _ = self._register_jawan("7th Battalion", "Srinagar")
        token_b, pid_b, _ = self._register_jawan("7th Battalion", "Srinagar")
        headers_a = {"Authorization": f"Bearer {token_a}"}

        # 1. Jawan A attempts to trigger an assessment for Jawan B -> 403
        ass_res = self.client.post(f"/api/personnel/{pid_b}/assess", json={
            "duty_hours_per_week": 60.0
        }, headers=headers_a)
        self.assertEqual(ass_res.status_code, 403)

        # 2. Jawan A creates own welfare request then attempts to mark it resolved via PATCH -> 403
        req_res = self.client.post("/api/welfare/requests", json={
            "category": "Medical Welfare",
            "urgency": "Routine"
        }, headers=headers_a)
        req_id = req_res.json()["id"]
        self.cleanup_request_ids.append(req_id)

        patch_res = self.client.patch(f"/api/welfare/requests/{req_id}/status", json={
            "status": "resolved"
        }, headers=headers_a)
        self.assertEqual(patch_res.status_code, 403)
        self.assertIn("roles", patch_res.json()["detail"].lower())

    # =========================================================================
    # C. COMPLETE WELFARE CASE LIFECYCLE (pending -> acknowledged -> in_progress -> resolved)
    # =========================================================================

    def test_08_complete_welfare_lifecycle_and_db_state_synchronization(self):
        """C: Complete transition pending -> acknowledged -> in_progress -> resolved with DB verification."""
        token_jawan, pid, _ = self._register_jawan("7th Battalion", "Jamshedpur")
        token_cmdr, _ = self._register_commander("7th Battalion", "Jamshedpur")

        headers_jawan = {"Authorization": f"Bearer {token_jawan}"}
        headers_cmdr = {"Authorization": f"Bearer {token_cmdr}"}

        # 1. Creation -> starts in 'pending'
        create_res = self.client.post("/api/welfare/requests", json={
            "category": "Operational Stress & Morale",
            "urgency": "High",
            "message": "Full lifecycle verification"
        }, headers=headers_jawan)
        self.assertEqual(create_res.status_code, 201)
        req_id = create_res.json()["id"]
        self.cleanup_request_ids.append(req_id)

        # Verify DB state: pending
        db_req = self.db.query(WelfareRequest).filter(WelfareRequest.id == req_id).first()
        self.assertIsNotNone(db_req)
        self.assertEqual(db_req.status, "pending")
        self.assertIsNone(db_req.resolved_at)

        # 2. Transition -> 'acknowledged'
        ack_res = self.client.patch(f"/api/welfare/requests/{req_id}/status", json={
            "status": "acknowledged"
        }, headers=headers_cmdr)
        self.assertEqual(ack_res.status_code, 200)
        self.assertEqual(ack_res.json()["status"], "acknowledged")

        self.db.expire(db_req)
        self.assertEqual(db_req.status, "acknowledged")
        self.assertIsNone(db_req.resolved_at)

        # 3. Transition -> 'in_progress'
        prog_res = self.client.patch(f"/api/welfare/requests/{req_id}/status", json={
            "status": "in_progress"
        }, headers=headers_cmdr)
        self.assertEqual(prog_res.status_code, 200)
        self.assertEqual(prog_res.json()["status"], "in_progress")

        self.db.expire(db_req)
        self.assertEqual(db_req.status, "in_progress")
        self.assertIsNone(db_req.resolved_at)

        # 4. Transition -> 'resolved'
        res_res = self.client.patch(f"/api/welfare/requests/{req_id}/status", json={
            "status": "resolved"
        }, headers=headers_cmdr)
        self.assertEqual(res_res.status_code, 200)
        self.assertEqual(res_res.json()["status"], "resolved")

        self.db.expire(db_req)
        self.assertEqual(db_req.status, "resolved")
        self.assertIsNotNone(db_req.resolved_at)

        # 5. Jawan checks own requests -> reflects resolved
        jawan_view = self.client.get("/api/welfare/requests/my", headers=headers_jawan)
        self.assertEqual(jawan_view.status_code, 200)
        target = next(r for r in jawan_view.json() if r["id"] == req_id)
        self.assertEqual(target["status"], "resolved")
        self.assertIsNotNone(target["resolved_at"])

    # =========================================================================
    # D. INDEPENDENT CROSS-SCOPE UPDATE REJECTION
    # =========================================================================

    def test_09_cross_battalion_update_rejected(self):
        """D.1: Commander from different Battalion (same location) cannot update welfare status."""
        token_jawan, pid, _ = self._register_jawan("7th Battalion", "Jamshedpur")
        token_cmdr_diff_batt, _ = self._register_commander("8th Battalion", "Jamshedpur")

        res_req = self.client.post("/api/welfare/requests", json={
            "category": "Duty Schedule Overload",
            "urgency": "Medium"
        }, headers={"Authorization": f"Bearer {token_jawan}"})
        req_id = res_req.json()["id"]
        self.cleanup_request_ids.append(req_id)

        # Attempt PATCH status update
        res_patch = self.client.patch(f"/api/welfare/requests/{req_id}/status", json={
            "status": "in_progress"
        }, headers={"Authorization": f"Bearer {token_cmdr_diff_batt}"})
        self.assertEqual(res_patch.status_code, 403)
        self.assertIn("outside your assigned Battalion and Location scope", res_patch.json()["detail"])

        # Direct DB verify: status remains pending
        db_req = self.db.query(WelfareRequest).filter(WelfareRequest.id == req_id).first()
        self.assertEqual(db_req.status, "pending")

    def test_10_cross_location_update_rejected(self):
        """D.2: Commander from different Location (same battalion) cannot update welfare status."""
        token_jawan, pid, _ = self._register_jawan("7th Battalion", "Jamshedpur")
        token_cmdr_diff_loc, _ = self._register_commander("7th Battalion", "Ranchi")

        res_req = self.client.post("/api/welfare/requests", json={
            "category": "Duty Schedule Overload",
            "urgency": "Medium"
        }, headers={"Authorization": f"Bearer {token_jawan}"})
        req_id = res_req.json()["id"]
        self.cleanup_request_ids.append(req_id)

        # Attempt PATCH status update
        res_patch = self.client.patch(f"/api/welfare/requests/{req_id}/status", json={
            "status": "in_progress"
        }, headers={"Authorization": f"Bearer {token_cmdr_diff_loc}"})
        self.assertEqual(res_patch.status_code, 403)
        self.assertIn("outside your assigned Battalion and Location scope", res_patch.json()["detail"])

        # Direct DB verify: status remains pending
        db_req = self.db.query(WelfareRequest).filter(WelfareRequest.id == req_id).first()
        self.assertEqual(db_req.status, "pending")

    def test_11_cross_scope_both_mismatch_update_rejected(self):
        """D.3: Commander with both Battalion and Location mismatch cannot update welfare status."""
        token_jawan, pid, _ = self._register_jawan("7th Battalion", "Jamshedpur")
        token_cmdr_both_diff, _ = self._register_commander("8th Battalion", "Srinagar")

        res_req = self.client.post("/api/welfare/requests", json={
            "category": "Duty Schedule Overload",
            "urgency": "Medium"
        }, headers={"Authorization": f"Bearer {token_jawan}"})
        req_id = res_req.json()["id"]
        self.cleanup_request_ids.append(req_id)

        # Attempt PATCH status update
        res_patch = self.client.patch(f"/api/welfare/requests/{req_id}/status", json={
            "status": "in_progress"
        }, headers={"Authorization": f"Bearer {token_cmdr_both_diff}"})
        self.assertEqual(res_patch.status_code, 403)
        self.assertIn("outside your assigned Battalion and Location scope", res_patch.json()["detail"])

        # Direct DB verify: status remains pending
        db_req = self.db.query(WelfareRequest).filter(WelfareRequest.id == req_id).first()
        self.assertEqual(db_req.status, "pending")


if __name__ == "__main__":
    unittest.main()
