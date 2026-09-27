import unittest
import uuid
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from api.main import app
from db.session import SessionLocal
from db.models.user import User
from db.models.personnel import Personnel
from db.models.hrms import HrmsServiceRecord
from db.models.telemetry import WearableTelemetry
from db.models.assessment import StressAssessment
from db.models.recommendation import WelfareRecommendation
from db.models.welfare_request import WelfareRequest


class TestPhase31IngestionBridge(unittest.TestCase):
    """
    Phase 31 Automated Test Suite for Mock HRMS & Simulated Wearable Ingestion Bridge.
    Verifies:
      1. Mock HRMS synchronization & idempotency
      2. HRMS security boundaries (RBAC, Battalion scope, Location scope, Jawan rejection)
      3. Simulated Wearable telemetry ingestion & time-series storage
      4. Wearable security boundaries (Jawan self-ownership, Commander scope, peer rejection)
      5. Input validation bounds (heart rate, sleep, hrv)
      6. Explicit synthetic-data source labeling ('mock_hrms', 'simulated_wearable')
      7. Automated teardown & test isolation
    """

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.db: Session = SessionLocal()
        cls.cleanup_user_ids = []
        cls.cleanup_personnel_ids = []

    @classmethod
    def tearDownClass(cls):
        # Delete created telemetry, hrms, and personnel records
        if cls.cleanup_personnel_ids:
            cls.db.query(WearableTelemetry).filter(WearableTelemetry.personnel_id.in_(cls.cleanup_personnel_ids)).delete(synchronize_session=False)
            cls.db.query(HrmsServiceRecord).filter(HrmsServiceRecord.personnel_id.in_(cls.cleanup_personnel_ids)).delete(synchronize_session=False)
            cls.db.query(WelfareRecommendation).filter(WelfareRecommendation.personnel_id.in_(cls.cleanup_personnel_ids)).delete(synchronize_session=False)
            cls.db.query(WelfareRequest).filter(WelfareRequest.personnel_id.in_(cls.cleanup_personnel_ids)).delete(synchronize_session=False)
            cls.db.query(StressAssessment).filter(StressAssessment.personnel_id.in_(cls.cleanup_personnel_ids)).delete(synchronize_session=False)
            cls.db.query(User).filter(User.personnel_id.in_(cls.cleanup_personnel_ids)).delete(synchronize_session=False)
            cls.db.query(Personnel).filter(Personnel.id.in_(cls.cleanup_personnel_ids)).delete(synchronize_session=False)
        if cls.cleanup_user_ids:
            cls.db.query(User).filter(User.id.in_(cls.cleanup_user_ids)).delete(synchronize_session=False)
        cls.db.commit()
        cls.db.close()

    def _register_jawan(self, battalion: str, location: str, name_prefix: str = "P31_Jawan"):
        s = uuid.uuid4().hex[:8]
        code = f"P31-{s.upper()}"
        res = self.client.post("/api/auth/register-jawan", json={
            "username": f"jwn31_{s}",
            "password": "Password123!",
            "name": f"{name_prefix} {s}",
            "personnel_code": code,
            "age": 28,
            "gender": "Male",
            "department": "Operations",
            "battalion": battalion,
            "job_role": "Constable",
            "location": location,
            "experience_years": 4.0,
            "duty_hours_per_week": 44.0
        })
        self.assertEqual(res.status_code, 201)
        data = res.json()
        pid = data["personnel_id"]
        self.cleanup_personnel_ids.append(pid)
        user_row = self.db.query(User).filter(User.username == f"jwn31_{s}").first()
        if user_row:
            self.cleanup_user_ids.append(user_row.id)
        return data["access_token"], pid, code

    def _register_commander(self, battalion: str, location: str, name_prefix: str = "P31_Cmdr"):
        s = uuid.uuid4().hex[:8]
        res = self.client.post("/api/auth/register-commander", json={
            "username": f"cmd31_{s}",
            "password": "Password123!",
            "name": f"{name_prefix} {s}",
            "battalion": battalion,
            "location": location
        })
        self.assertEqual(res.status_code, 201)
        data = res.json()
        user_row = self.db.query(User).filter(User.username == f"cmd31_{s}").first()
        if user_row:
            self.cleanup_user_ids.append(user_row.id)
        return data["access_token"], user_row.id if user_row else None

    # =========================================================================
    # HRMS INGESTION TESTS (1 - 7, 15)
    # =========================================================================

    def test_01_authorized_hrms_sync_succeeds(self):
        """1. Authorized commander successfully syncs HRMS service record."""
        token_jawan, pid, code = self._register_jawan("7th Battalion", "Srinagar")
        token_cmdr, _ = self._register_commander("7th Battalion", "Srinagar")

        sync_payload = {
            "personnel_id": pid,
            "service_number": f"SRV-{pid}-MOCK",
            "department": "Tactical Operations",
            "battalion": "7th Battalion",
            "location": "Srinagar",
            "job_role": "Section Commander",
            "rank": "Head Constable",
            "deployment_days": 120,
            "duty_hours_per_week": 54.0,
            "night_shifts_per_month": 8,
            "consecutive_duty_days": 14,
            "leave_gap_days": 90,
            "annual_leaves_taken": 15,
            "transfer_frequency": 2,
            "training_load": 4,
            "experience_years": 7.5,
            "raw_metadata": '{"hrms_system": "Simulated AFMS Node", "sync_batch": 101}'
        }

        res = self.client.post("/api/hrms/sync", json=sync_payload, headers={"Authorization": f"Bearer {token_cmdr}"})
        self.assertEqual(res.status_code, 200, f"HRMS sync failed: {res.text}")
        data = res.json()

        self.assertEqual(data["status"], "success")
        self.assertEqual(data["personnel_id"], pid)
        self.assertEqual(data["personnel_code"], code)
        self.assertEqual(data["service_number"], f"SRV-{pid}-MOCK")
        self.assertEqual(data["source"], "mock_hrms")
        self.assertIn("Mock HRMS", data["disclaimer"])

    def test_02_existing_personnel_is_correctly_linked_in_db(self):
        """2. HRMS record is persisted in PostgreSQL and linked to Personnel entity."""
        token_jawan, pid, _ = self._register_jawan("7th Battalion", "Srinagar")
        token_cmdr, _ = self._register_commander("7th Battalion", "Srinagar")

        self.client.post("/api/hrms/sync", json={
            "personnel_id": pid,
            "service_number": "SN-LINK-TEST",
            "deployment_days": 85,
            "duty_hours_per_week": 52.0
        }, headers={"Authorization": f"Bearer {token_cmdr}"})

        # Query direct database session
        hrms_db = self.db.query(HrmsServiceRecord).filter(HrmsServiceRecord.personnel_id == pid).first()
        self.assertIsNotNone(hrms_db)
        self.assertEqual(hrms_db.service_number, "SN-LINK-TEST")
        self.assertEqual(hrms_db.deployment_days, 85)
        self.assertEqual(hrms_db.duty_hours_per_week, 52.0)
        self.assertEqual(hrms_db.source, "mock_hrms")

        # Verify linked personnel operational fields updated
        p_db = self.db.query(Personnel).filter(Personnel.id == pid).first()
        self.assertEqual(p_db.duty_hours_per_week, 52.0)
        self.assertEqual(p_db.deployment_days, 85)

    def test_03_repeated_sync_is_idempotent(self):
        """3. Repeated HRMS syncs update the existing record without duplicate creation."""
        token_jawan, pid, _ = self._register_jawan("7th Battalion", "Srinagar")
        token_cmdr, _ = self._register_commander("7th Battalion", "Srinagar")
        headers = {"Authorization": f"Bearer {token_cmdr}"}

        # First sync
        res1 = self.client.post("/api/hrms/sync", json={
            "personnel_id": pid,
            "service_number": "SN-IDEM-01",
            "duty_hours_per_week": 46.0
        }, headers=headers)
        rec_id_1 = res1.json()["record_id"]

        # Second sync with updated duty hours
        res2 = self.client.post("/api/hrms/sync", json={
            "personnel_id": pid,
            "service_number": "SN-IDEM-01",
            "duty_hours_per_week": 58.0
        }, headers=headers)
        rec_id_2 = res2.json()["record_id"]

        # Identical record ID must be updated
        self.assertEqual(rec_id_1, rec_id_2)

        # Count records in database for this personnel (must be exactly 1)
        count = self.db.query(HrmsServiceRecord).filter(HrmsServiceRecord.personnel_id == pid).count()
        self.assertEqual(count, 1)

        # Verify updated value in DB
        db_rec = self.db.query(HrmsServiceRecord).filter(HrmsServiceRecord.id == rec_id_1).first()
        self.assertEqual(db_rec.duty_hours_per_week, 58.0)

    def test_04_invalid_personnel_is_rejected(self):
        """4. Sync attempt for non-existent personnel ID returns 404 Not Found."""
        token_cmdr, _ = self._register_commander("7th Battalion", "Srinagar")
        res = self.client.post("/api/hrms/sync", json={
            "personnel_id": 9999999,
            "duty_hours_per_week": 50.0
        }, headers={"Authorization": f"Bearer {token_cmdr}"})
        self.assertEqual(res.status_code, 404)
        self.assertIn("not found", res.json()["detail"].lower())

    def test_05_cross_battalion_hrms_injection_rejected(self):
        """5. Commander from 8th Battalion attempting to sync 7th Battalion personnel returns 403."""
        token_jawan, pid, _ = self._register_jawan("7th Battalion", "Srinagar")
        token_cmdr_diff_batt, _ = self._register_commander("8th Battalion", "Srinagar")

        res = self.client.post("/api/hrms/sync", json={
            "personnel_id": pid,
            "duty_hours_per_week": 60.0
        }, headers={"Authorization": f"Bearer {token_cmdr_diff_batt}"})
        self.assertEqual(res.status_code, 403)
        self.assertIn("outside your assigned battalion and location scope", res.json()["detail"].lower())

    def test_06_cross_location_hrms_injection_rejected(self):
        """6. Commander from different Location attempting to sync personnel returns 403."""
        token_jawan, pid, _ = self._register_jawan("7th Battalion", "Srinagar")
        token_cmdr_diff_loc, _ = self._register_commander("7th Battalion", "Ranchi")

        res = self.client.post("/api/hrms/sync", json={
            "personnel_id": pid,
            "duty_hours_per_week": 60.0
        }, headers={"Authorization": f"Bearer {token_cmdr_diff_loc}"})
        self.assertEqual(res.status_code, 403)
        self.assertIn("outside your assigned battalion and location scope", res.json()["detail"].lower())

    def test_07_jawan_cannot_inject_hrms_data(self):
        """7. Personnel role user attempting to call HRMS sync is rejected with 403 Forbidden."""
        token_jawan, pid, _ = self._register_jawan("7th Battalion", "Srinagar")

        res = self.client.post("/api/hrms/sync", json={
            "personnel_id": pid,
            "duty_hours_per_week": 40.0
        }, headers={"Authorization": f"Bearer {token_jawan}"})
        self.assertEqual(res.status_code, 403)
        self.assertIn("forbidden", res.json()["detail"].lower())

    def test_15_hrms_source_is_stored_as_mock_hrms(self):
        """15. Stored HRMS record explicitly records source='mock_hrms'."""
        token_jawan, pid, _ = self._register_jawan("7th Battalion", "Srinagar")
        token_cmdr, _ = self._register_commander("7th Battalion", "Srinagar")

        res = self.client.post("/api/hrms/sync", json={
            "personnel_id": pid,
            "service_number": "SN-SOURCE-VERIFY"
        }, headers={"Authorization": f"Bearer {token_cmdr}"})
        self.assertEqual(res.status_code, 200)

        db_rec = self.db.query(HrmsServiceRecord).filter(HrmsServiceRecord.personnel_id == pid).first()
        self.assertEqual(db_rec.source, "mock_hrms")

    # =========================================================================
    # SIMULATED WEARABLE TELEMETRY TESTS (8 - 14)
    # =========================================================================

    def test_08_authorized_wearable_telemetry_ingestion_succeeds(self):
        """8. Authorized Jawan successfully ingests own wearable telemetry."""
        token_jawan, pid, _ = self._register_jawan("7th Battalion", "Jamshedpur")
        now_iso = datetime.now(timezone.utc).isoformat()

        payload = {
            "personnel_id": pid,
            "recorded_at": now_iso,
            "heart_rate": 74.5,
            "hrv_rmssd": 48.2,
            "sleep_duration_hours": 7.2,
            "sleep_quality_score": 82.0,
            "step_count": 8450,
            "active_minutes": 65,
            "device_model": "Simulated Tactical Band Alpha"
        }

        res = self.client.post("/api/telemetry/wearable", json=payload, headers={"Authorization": f"Bearer {token_jawan}"})
        self.assertEqual(res.status_code, 201, f"Telemetry ingestion failed: {res.text}")
        data = res.json()

        self.assertEqual(data["status"], "success")
        self.assertEqual(data["personnel_id"], pid)
        self.assertEqual(data["heart_rate"], 74.5)
        self.assertEqual(data["hrv_rmssd"], 48.2)
        self.assertEqual(data["sleep_duration_hours"], 7.2)
        self.assertEqual(data["source"], "simulated_wearable")
        self.assertIn("Simulated wearable telemetry", data["disclaimer"])

    def test_09_telemetry_is_stored_with_correct_personnel_and_timestamp(self):
        """9. Telemetry record is persisted in PostgreSQL with correct time-series timestamp."""
        token_jawan, pid, _ = self._register_jawan("7th Battalion", "Jamshedpur")
        target_time = datetime(2026, 9, 26, 8, 30, 0, tzinfo=timezone.utc)

        res = self.client.post("/api/telemetry/wearable", json={
            "personnel_id": pid,
            "recorded_at": target_time.isoformat(),
            "heart_rate": 81.0,
            "hrv_rmssd": 39.5,
            "sleep_duration_hours": 6.0,
            "step_count": 10200
        }, headers={"Authorization": f"Bearer {token_jawan}"})
        self.assertEqual(res.status_code, 201)
        t_id = res.json()["telemetry_id"]

        db_tele = self.db.query(WearableTelemetry).filter(WearableTelemetry.id == t_id).first()
        self.assertIsNotNone(db_tele)
        self.assertEqual(db_tele.personnel_id, pid)
        self.assertEqual(db_tele.heart_rate, 81.0)
        self.assertEqual(db_tele.hrv_rmssd, 39.5)
        self.assertEqual(db_tele.step_count, 10200)
        self.assertEqual(db_tele.source, "simulated_wearable")

    def test_10_invalid_telemetry_values_are_rejected(self):
        """10. Nonsensical physiological values fail Pydantic validation (422 Unprocessable Content)."""
        token_jawan, pid, _ = self._register_jawan("7th Battalion", "Jamshedpur")
        headers = {"Authorization": f"Bearer {token_jawan}"}
        now_iso = datetime.now(timezone.utc).isoformat()

        # 1. Negative heart rate
        res1 = self.client.post("/api/telemetry/wearable", json={
            "personnel_id": pid,
            "recorded_at": now_iso,
            "heart_rate": -15.0
        }, headers=headers)
        self.assertEqual(res1.status_code, 422)

        # 2. Impossible sleep hours (> 24)
        res2 = self.client.post("/api/telemetry/wearable", json={
            "personnel_id": pid,
            "recorded_at": now_iso,
            "sleep_duration_hours": 32.0
        }, headers=headers)
        self.assertEqual(res2.status_code, 422)

        # 3. Impossible HRV (> 350 ms)
        res3 = self.client.post("/api/telemetry/wearable", json={
            "personnel_id": pid,
            "recorded_at": now_iso,
            "hrv_rmssd": 500.0
        }, headers=headers)
        self.assertEqual(res3.status_code, 422)

    def test_11_cross_battalion_telemetry_injection_rejected(self):
        """11. Officer from 8th Battalion cannot inject telemetry for 7th Battalion personnel."""
        token_jawan, pid, _ = self._register_jawan("7th Battalion", "Jamshedpur")
        token_cmdr_diff_batt, _ = self._register_commander("8th Battalion", "Jamshedpur")

        res = self.client.post("/api/telemetry/wearable", json={
            "personnel_id": pid,
            "recorded_at": datetime.now(timezone.utc).isoformat(),
            "heart_rate": 72.0
        }, headers={"Authorization": f"Bearer {token_cmdr_diff_batt}"})
        self.assertEqual(res.status_code, 403)
        self.assertIn("outside your assigned battalion and location scope", res.json()["detail"].lower())

    def test_12_cross_location_telemetry_injection_rejected(self):
        """12. Officer from different Location cannot inject telemetry for personnel."""
        token_jawan, pid, _ = self._register_jawan("7th Battalion", "Jamshedpur")
        token_cmdr_diff_loc, _ = self._register_commander("7th Battalion", "Ranchi")

        res = self.client.post("/api/telemetry/wearable", json={
            "personnel_id": pid,
            "recorded_at": datetime.now(timezone.utc).isoformat(),
            "heart_rate": 72.0
        }, headers={"Authorization": f"Bearer {token_cmdr_diff_loc}"})
        self.assertEqual(res.status_code, 403)
        self.assertIn("outside your assigned battalion and location scope", res.json()["detail"].lower())

    def test_13_jawan_cannot_inject_telemetry_for_another_jawan(self):
        """13. Jawan A attempting to inject telemetry for Jawan B receives 403 Forbidden."""
        token_a, pid_a, _ = self._register_jawan("7th Battalion", "Jamshedpur", "JawanAlpha")
        token_b, pid_b, _ = self._register_jawan("7th Battalion", "Jamshedpur", "JawanBravo")

        res = self.client.post("/api/telemetry/wearable", json={
            "personnel_id": pid_b,
            "recorded_at": datetime.now(timezone.utc).isoformat(),
            "heart_rate": 70.0
        }, headers={"Authorization": f"Bearer {token_a}"})
        self.assertEqual(res.status_code, 403)
        self.assertIn("only submit telemetry for their own profile", res.json()["detail"].lower())

    def test_14_source_is_stored_as_simulated_wearable(self):
        """14. Stored telemetry explicitly records source='simulated_wearable'."""
        token_jawan, pid, _ = self._register_jawan("7th Battalion", "Jamshedpur")

        res = self.client.post("/api/telemetry/wearable", json={
            "personnel_id": pid,
            "recorded_at": datetime.now(timezone.utc).isoformat(),
            "heart_rate": 68.0
        }, headers={"Authorization": f"Bearer {token_jawan}"})
        self.assertEqual(res.status_code, 201)
        t_id = res.json()["telemetry_id"]

        db_rec = self.db.query(WearableTelemetry).filter(WearableTelemetry.id == t_id).first()
        self.assertEqual(db_rec.source, "simulated_wearable")


if __name__ == "__main__":
    unittest.main()
