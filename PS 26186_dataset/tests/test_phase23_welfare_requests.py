import unittest
import uuid
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from api.main import app
from db.session import get_db
from db.models.user import User
from db.models.personnel import Personnel
from db.models.welfare_request import WelfareRequest
from core.security import create_access_token

class TestPhase23WelfareRequests(unittest.TestCase):
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

    def _create_jawan(self, suffix: str) -> tuple:
        signup_payload = {
            "name": f"Jawan Welfare {suffix}",
            "username": f"jawan_welfare_{suffix}",
            "password": "Password123!",
            "personnel_code": f"PW-{suffix.upper()}",
            "age": 27,
            "gender": "Male",
            "department": "Operations",
            "job_role": "Constable",
            "location": "Srinagar",
            "experience_years": 4.0,
            "duty_hours_per_week": 48.0
        }
        res = self.client.post("/api/auth/register-jawan", json=signup_payload)
        self.assertEqual(res.status_code, 201)
        data = res.json()
        return data["access_token"], data["personnel_id"]

    def test_01_jawan_creates_welfare_request_persisted_in_db(self):
        """Jawan creates a welfare request -> persisted in PostgreSQL with status 'pending'."""
        suffix = str(uuid.uuid4())[:8]
        token, personnel_id = self._create_jawan(suffix)
        headers = {"Authorization": f"Bearer {token}"}

        payload = {
            "category": "Duty Schedule & Workload",
            "urgency": "Medium",
            "message": "Requesting a review of consecutive night patrol assignments."
        }

        res = self.client.post("/api/welfare/requests", json=payload, headers=headers)
        self.assertEqual(res.status_code, 201)
        data = res.json()

        self.assertEqual(data["personnel_id"], personnel_id)
        self.assertEqual(data["category"], "Duty Schedule & Workload")
        self.assertEqual(data["urgency"], "Medium")
        self.assertEqual(data["message"], "Requesting a review of consecutive night patrol assignments.")
        self.assertEqual(data["status"], "pending")
        self.assertEqual(data["source"], "Jawan Request")
        self.assertIsNone(data["resolved_at"])

        # Check database directly
        db_req = self.db.query(WelfareRequest).filter(WelfareRequest.id == data["id"]).first()
        self.assertIsNotNone(db_req)
        self.assertEqual(db_req.personnel_id, personnel_id)
        self.assertEqual(db_req.status, "pending")

    def test_02_jawan_can_retrieve_own_requests_but_not_others(self):
        """Jawan can retrieve their own requests; cannot view another Jawan's requests."""
        suffix_a = str(uuid.uuid4())[:8]
        token_a, pid_a = self._create_jawan(suffix_a)
        headers_a = {"Authorization": f"Bearer {token_a}"}

        suffix_b = str(uuid.uuid4())[:8]
        token_b, pid_b = self._create_jawan(suffix_b)
        headers_b = {"Authorization": f"Bearer {token_b}"}

        # Jawan A creates a request
        self.client.post("/api/welfare/requests", json={
            "category": "Rest & Sleep Fatigue",
            "urgency": "High",
            "message": "Severe sleep debt after 14 continuous days on forward post."
        }, headers=headers_a)

        # Jawan A retrieves own requests
        res_a = self.client.get("/api/welfare/requests/my", headers=headers_a)
        self.assertEqual(res_a.status_code, 200)
        items_a = res_a.json()
        self.assertEqual(len(items_a), 1)
        self.assertEqual(items_a[0]["personnel_id"], pid_a)

        # Jawan B retrieves own requests -> receives empty list
        res_b = self.client.get("/api/welfare/requests/my", headers=headers_b)
        self.assertEqual(res_b.status_code, 200)
        items_b = res_b.json()
        self.assertEqual(len(items_b), 0)

        # Jawan A attempts to access commander-only endpoint -> 403 Forbidden
        forbidden = self.client.get("/api/welfare/requests", headers=headers_a)
        self.assertEqual(forbidden.status_code, 403)

    def test_03_officer_can_retrieve_all_and_transition_status(self):
        """Officer views requests and updates status: pending -> acknowledged -> in_progress -> resolved."""
        suffix = str(uuid.uuid4())[:8]
        token, pid = self._create_jawan(suffix)
        jawan_headers = {"Authorization": f"Bearer {token}"}
        officer_headers = self._create_officer_token()

        # Jawan submits
        create_res = self.client.post("/api/welfare/requests", json={
            "category": "Personal & Family Matters",
            "urgency": "Routine",
            "message": "Requesting compassionate leave schedule coordination."
        }, headers=jawan_headers)
        req_id = create_res.json()["id"]

        # 1. Officer retrieves all requests
        list_res = self.client.get("/api/welfare/requests", headers=officer_headers)
        self.assertEqual(list_res.status_code, 200)
        all_reqs = list_res.json()
        target = next((r for r in all_reqs if r["id"] == req_id), None)
        self.assertIsNotNone(target)
        self.assertEqual(target["status"], "pending")

        # 2. Officer acknowledges request
        ack_res = self.client.patch(
            f"/api/welfare/requests/{req_id}/status",
            json={"status": "acknowledged"},
            headers=officer_headers
        )
        self.assertEqual(ack_res.status_code, 200)
        self.assertEqual(ack_res.json()["status"], "acknowledged")

        # Jawan sees 'acknowledged'
        jawan_view1 = self.client.get("/api/welfare/requests/my", headers=jawan_headers).json()
        self.assertEqual(jawan_view1[0]["status"], "acknowledged")

        # 3. Officer moves to 'in_progress'
        prog_res = self.client.patch(
            f"/api/welfare/requests/{req_id}/status",
            json={"status": "in_progress"},
            headers=officer_headers
        )
        self.assertEqual(prog_res.status_code, 200)
        self.assertEqual(prog_res.json()["status"], "in_progress")

        # 4. Officer resolves request
        res_res = self.client.patch(
            f"/api/welfare/requests/{req_id}/status",
            json={"status": "resolved"},
            headers=officer_headers
        )
        self.assertEqual(res_res.status_code, 200)
        data_resolved = res_res.json()
        self.assertEqual(data_resolved["status"], "resolved")
        self.assertIsNotNone(data_resolved["resolved_at"])

        # Jawan sees 'resolved'
        jawan_view2 = self.client.get("/api/welfare/requests/my", headers=jawan_headers).json()
        self.assertEqual(jawan_view2[0]["status"], "resolved")

    def test_04_jawan_cannot_modify_status(self):
        """Jawan cannot modify status of their own or others' requests."""
        suffix = str(uuid.uuid4())[:8]
        token, pid = self._create_jawan(suffix)
        headers = {"Authorization": f"Bearer {token}"}

        create_res = self.client.post("/api/welfare/requests", json={
            "category": "Operational Stress & Morale",
            "urgency": "Routine"
        }, headers=headers)
        req_id = create_res.json()["id"]

        # Jawan tries to PATCH status -> 403 Forbidden
        patch_res = self.client.patch(
            f"/api/welfare/requests/{req_id}/status",
            json={"status": "resolved"},
            headers=headers
        )
        self.assertEqual(patch_res.status_code, 403)

    def test_05_pending_welfare_requests_update_dashboard_kpi(self):
        """Dashboard summary pending_recommendations count includes pending Jawan welfare requests."""
        officer_headers = self._create_officer_token()
        sum_before = self.client.get("/api/dashboard/summary", headers=officer_headers).json()
        pending_before = sum_before["pending_recommendations"]

        suffix = str(uuid.uuid4())[:8]
        token, pid = self._create_jawan(suffix)
        headers = {"Authorization": f"Bearer {token}"}

        # Jawan submits new pending welfare request
        self.client.post("/api/welfare/requests", json={
            "category": "General Welfare Consultation",
            "urgency": "Medium"
        }, headers=headers)

        sum_after = self.client.get("/api/dashboard/summary", headers=officer_headers).json()
        pending_after = sum_after["pending_recommendations"]

        self.assertEqual(pending_after, pending_before + 1)

if __name__ == "__main__":
    unittest.main()
