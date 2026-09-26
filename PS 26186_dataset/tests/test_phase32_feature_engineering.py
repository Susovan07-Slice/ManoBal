import os
import sys
import unittest
import uuid
from datetime import datetime, timezone, timedelta
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

from src.prediction import get_welfare_service
from src.risk_scoring import calculate_risk_score
from src.explain import StressModelExplainer
from src.external_validation import load_and_inspect_d2

class TestPhase32FeatureEngineering(unittest.TestCase):
    """
    Phase 32 Regression and Validation Test Suite:
    HRMS + Wearable Feature Engineering and Risk-Pipeline Integration.
    """

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.db: Session = SessionLocal()
        cls.cleanup_user_ids = []
        cls.cleanup_personnel_ids = []

    @classmethod
    def tearDownClass(cls):
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

    def _register_jawan(self, battalion: str = "7th Battalion", location: str = "Leh", name_prefix: str = "P32_Jawan"):
        s = uuid.uuid4().hex[:8]
        code = f"P32-{s.upper()}"
        res = self.client.post("/api/auth/register-jawan", json={
            "username": f"jwn32_{s}",
            "password": "Password123!",
            "name": f"{name_prefix} {s}",
            "personnel_code": code,
            "age": 29,
            "gender": "Male",
            "department": "Operations",
            "battalion": battalion,
            "job_role": "Constable",
            "location": location,
            "experience_years": 5.0,
            "duty_hours_per_week": 48.0
        })
        self.assertEqual(res.status_code, 201)
        data = res.json()
        pid = data["personnel_id"]
        self.cleanup_personnel_ids.append(pid)
        user_row = self.db.query(User).filter(User.username == f"jwn32_{s}").first()
        if user_row:
            self.cleanup_user_ids.append(user_row.id)
        return data["access_token"], pid, code

    def _register_commander(self, battalion: str = "7th Battalion", location: str = "Leh", name_prefix: str = "P32_Cmdr"):
        s = uuid.uuid4().hex[:8]
        res = self.client.post("/api/auth/register-commander", json={
            "username": f"cmd32_{s}",
            "password": "Password123!",
            "name": f"{name_prefix} {s}",
            "battalion": battalion,
            "location": location
        })
        self.assertEqual(res.status_code, 201)
        data = res.json()
        user_row = self.db.query(User).filter(User.username == f"cmd32_{s}").first()
        if user_row:
            self.cleanup_user_ids.append(user_row.id)
        return data["access_token"], user_row.id if user_row else None

    # =========================================================================
    # 1. HRMS DERIVED FEATURES TESTS (1 - 5)
    # =========================================================================

    def test_01_hrms_feature_snapshot_generated_correctly(self):
        """1. HRMS feature snapshot generated correctly with proper source stamp."""
        token_jwn, pid, code = self._register_jawan("7th Battalion", "Leh")
        token_cmd, _ = self._register_commander("7th Battalion", "Leh")

        sync_res = self.client.post("/api/hrms/sync", json={
            "personnel_id": pid,
            "service_number": f"ARMY-HRMS-{pid}",
            "years_of_service": 6.0,
            "leave_balance_days": 20,
            "leaves_taken_past_year": 10,
            "duty_hours_per_week": 50.0,
            "consecutive_days_on_duty": 8
        }, headers={"Authorization": f"Bearer {token_cmd}"})
        self.assertEqual(sync_res.status_code, 200)

        snap_res = self.client.get(f"/api/analytics/personnel/{pid}/features", headers={"Authorization": f"Bearer {token_cmd}"})
        self.assertEqual(snap_res.status_code, 200)
        data = snap_res.json()

        self.assertEqual(data["personnel_id"], pid)
        self.assertTrue(data["hrms_features"]["has_hrms_record"])
        self.assertEqual(data["hrms_features"]["source"], "mock_hrms")
        self.assertTrue(data["hrms_features"]["is_simulated"])
        self.assertEqual(data["hrms_features"]["service_number"], f"ARMY-HRMS-{pid}")

    def test_02_years_of_service_preserved_correctly(self):
        """2. Years of service is accurately preserved in HRMS features."""
        token_jwn, pid, code = self._register_jawan("7th Battalion", "Leh")
        token_cmd, _ = self._register_commander("7th Battalion", "Leh")

        self.client.post("/api/hrms/sync", json={
            "personnel_id": pid,
            "service_number": f"SRV-{pid}-YOS",
            "years_of_service": 8.5
        }, headers={"Authorization": f"Bearer {token_cmd}"})

        res = self.client.get(f"/api/analytics/personnel/{pid}/features", headers={"Authorization": f"Bearer {token_cmd}"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["hrms_features"]["years_of_service"], 8.5)

    def test_03_leave_indicators_calculated_correctly(self):
        """3. Leave balance and leaves taken are correctly extracted."""
        token_jwn, pid, code = self._register_jawan("7th Battalion", "Leh")
        token_cmd, _ = self._register_commander("7th Battalion", "Leh")

        self.client.post("/api/hrms/sync", json={
            "personnel_id": pid,
            "leave_balance_days": 25,
            "leaves_taken_past_year": 14
        }, headers={"Authorization": f"Bearer {token_cmd}"})

        res = self.client.get(f"/api/analytics/personnel/{pid}/features", headers={"Authorization": f"Bearer {token_cmd}"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["hrms_features"]["leave_balance_days"], 25)
        self.assertEqual(data["hrms_features"]["leaves_taken_past_year"], 14)

    def test_04_duty_workload_indicators_calculated_correctly(self):
        """4. Duty workload indicators (hours/week, consecutive days) extracted correctly."""
        token_jwn, pid, code = self._register_jawan("7th Battalion", "Leh")
        token_cmd, _ = self._register_commander("7th Battalion", "Leh")

        self.client.post("/api/hrms/sync", json={
            "personnel_id": pid,
            "duty_hours_per_week": 58.5,
            "consecutive_days_on_duty": 16
        }, headers={"Authorization": f"Bearer {token_cmd}"})

        res = self.client.get(f"/api/analytics/personnel/{pid}/features", headers={"Authorization": f"Bearer {token_cmd}"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["hrms_features"]["duty_hours_per_week"], 58.5)
        self.assertEqual(data["hrms_features"]["consecutive_days_on_duty"], 16)

    def test_05_unsupported_unstructured_fields_not_fabricated_into_metrics(self):
        """5. Unstructured text is preserved without fabricating artificial NLP numbers."""
        token_jwn, pid, code = self._register_jawan("7th Battalion", "Leh")
        token_cmd, _ = self._register_commander("7th Battalion", "Leh")

        deploy_text = "Deployment: High Altitude Reconnaissance, Sector 4, 2024-2025."
        transfer_text = "Transferred from HQ Northern Command to Forward Base 3."
        self.client.post("/api/hrms/sync", json={
            "personnel_id": pid,
            "deployment_history": deploy_text,
            "transfer_history": transfer_text
        }, headers={"Authorization": f"Bearer {token_cmd}"})

        res = self.client.get(f"/api/analytics/personnel/{pid}/features", headers={"Authorization": f"Bearer {token_cmd}"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["hrms_features"]["deployment_history_raw"], deploy_text)
        self.assertEqual(data["hrms_features"]["transfer_history_raw"], transfer_text)
        self.assertNotIn("deployment_nlp_score", data["hrms_features"])

    # =========================================================================
    # 2. WEARABLE DERIVED FEATURES TESTS (6 - 14)
    # =========================================================================

    def test_06_seven_day_aggregation_is_correct(self):
        """6. 7-day rolling aggregation only aggregates records within 7 days of reference time."""
        token_jwn, pid, code = self._register_jawan("7th Battalion", "Leh")
        token_cmd, _ = self._register_commander("7th Battalion", "Leh")

        ref_time = datetime(2026, 9, 20, 12, 0, 0, tzinfo=timezone.utc)
        t1 = ref_time - timedelta(days=2)
        t2 = ref_time - timedelta(days=4)
        t3 = ref_time - timedelta(days=15)

        for t, hr, hrv, slp, stp in [(t1, 70.0, 40.0, 7.0, 8000), (t2, 80.0, 30.0, 6.0, 6000), (t3, 90.0, 25.0, 5.0, 4000)]:
            self.client.post("/api/telemetry/wearable", json={
                "personnel_id": pid,
                "recorded_at": t.isoformat(),
                "heart_rate": hr,
                "hrv_rmssd": hrv,
                "sleep_duration_hours": slp,
                "step_count": stp
            }, headers={"Authorization": f"Bearer {token_cmd}"})

        ref_str = ref_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        res = self.client.get(f"/api/analytics/personnel/{pid}/features", params={"reference_time": ref_str}, headers={"Authorization": f"Bearer {token_cmd}"})
        self.assertEqual(res.status_code, 200)
        data = res.json()

        w7 = data["wearable_7d"]
        self.assertEqual(w7["window_days"], 7)
        self.assertEqual(w7["observation_count"], 2)
        self.assertTrue(w7["data_available"])

    def test_07_thirty_day_aggregation_is_correct(self):
        """7. 30-day rolling aggregation includes records spanning 30 days."""
        token_jwn, pid, code = self._register_jawan("7th Battalion", "Leh")
        token_cmd, _ = self._register_commander("7th Battalion", "Leh")

        ref_time = datetime(2026, 9, 20, 12, 0, 0, tzinfo=timezone.utc)
        t1 = ref_time - timedelta(days=2)
        t2 = ref_time - timedelta(days=10)
        t3 = ref_time - timedelta(days=25)

        for t in [t1, t2, t3]:
            self.client.post("/api/telemetry/wearable", json={
                "personnel_id": pid,
                "recorded_at": t.isoformat(),
                "heart_rate": 72.0,
                "hrv_rmssd": 45.0,
                "sleep_duration_hours": 7.0
            }, headers={"Authorization": f"Bearer {token_cmd}"})

        ref_str = ref_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        res = self.client.get(f"/api/analytics/personnel/{pid}/features", params={"reference_time": ref_str}, headers={"Authorization": f"Bearer {token_cmd}"})
        self.assertEqual(res.status_code, 200)
        data = res.json()

        w30 = data["wearable_30d"]
        self.assertEqual(w30["window_days"], 30)
        self.assertEqual(w30["observation_count"], 3)
        self.assertTrue(w30["data_available"])

    def test_08_mean_heart_rate_is_correct(self):
        """8. Heart rate mathematical aggregates (mean, min, max, std) are exact."""
        token_jwn, pid, code = self._register_jawan("7th Battalion", "Leh")
        token_cmd, _ = self._register_commander("7th Battalion", "Leh")

        ref_time = datetime(2026, 9, 20, 12, 0, 0, tzinfo=timezone.utc)
        self.client.post("/api/telemetry/wearable", json={
            "personnel_id": pid,
            "recorded_at": (ref_time - timedelta(days=1)).isoformat(),
            "heart_rate": 70.0,
            "hrv_rmssd": 40.0,
            "sleep_duration_hours": 7.0
        }, headers={"Authorization": f"Bearer {token_cmd}"})

        self.client.post("/api/telemetry/wearable", json={
            "personnel_id": pid,
            "recorded_at": (ref_time - timedelta(days=2)).isoformat(),
            "heart_rate": 80.0,
            "hrv_rmssd": 30.0,
            "sleep_duration_hours": 6.0
        }, headers={"Authorization": f"Bearer {token_cmd}"})

        ref_str = ref_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        res = self.client.get(f"/api/analytics/personnel/{pid}/features", params={"reference_time": ref_str}, headers={"Authorization": f"Bearer {token_cmd}"})
        self.assertEqual(res.status_code, 200)
        w7 = res.json()["wearable_7d"]

        self.assertEqual(w7["mean_heart_rate"], 75.0)
        self.assertEqual(w7["min_heart_rate"], 70.0)
        self.assertEqual(w7["max_heart_rate"], 80.0)
        self.assertAlmostEqual(w7["heart_rate_std"], 7.071, places=2)

    def test_09_hrv_aggregation_is_correct(self):
        """9. HRV RMSSD mathematical aggregates are exact."""
        token_jwn, pid, code = self._register_jawan("7th Battalion", "Leh")
        token_cmd, _ = self._register_commander("7th Battalion", "Leh")

        ref_time = datetime(2026, 9, 20, 12, 0, 0, tzinfo=timezone.utc)
        self.client.post("/api/telemetry/wearable", json={
            "personnel_id": pid,
            "recorded_at": (ref_time - timedelta(days=1)).isoformat(),
            "heart_rate": 72.0,
            "hrv_rmssd": 40.0,
            "sleep_duration_hours": 7.0
        }, headers={"Authorization": f"Bearer {token_cmd}"})

        self.client.post("/api/telemetry/wearable", json={
            "personnel_id": pid,
            "recorded_at": (ref_time - timedelta(days=2)).isoformat(),
            "heart_rate": 76.0,
            "hrv_rmssd": 30.0,
            "sleep_duration_hours": 6.0
        }, headers={"Authorization": f"Bearer {token_cmd}"})

        ref_str = ref_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        res = self.client.get(f"/api/analytics/personnel/{pid}/features", params={"reference_time": ref_str}, headers={"Authorization": f"Bearer {token_cmd}"})
        w7 = res.json()["wearable_7d"]

        self.assertEqual(w7["mean_hrv_rmssd"], 35.0)
        self.assertEqual(w7["min_hrv_rmssd"], 30.0)
        self.assertAlmostEqual(w7["hrv_rmssd_std"], 7.071, places=2)

    def test_10_sleep_aggregation_is_correct(self):
        """10. Sleep duration and quality aggregates are exact."""
        token_jwn, pid, code = self._register_jawan("7th Battalion", "Leh")
        token_cmd, _ = self._register_commander("7th Battalion", "Leh")

        ref_time = datetime(2026, 9, 20, 12, 0, 0, tzinfo=timezone.utc)
        self.client.post("/api/telemetry/wearable", json={
            "personnel_id": pid,
            "recorded_at": (ref_time - timedelta(days=1)).isoformat(),
            "heart_rate": 72.0,
            "hrv_rmssd": 40.0,
            "sleep_duration_hours": 7.0,
            "sleep_quality_score": 80.0
        }, headers={"Authorization": f"Bearer {token_cmd}"})

        self.client.post("/api/telemetry/wearable", json={
            "personnel_id": pid,
            "recorded_at": (ref_time - timedelta(days=2)).isoformat(),
            "heart_rate": 76.0,
            "hrv_rmssd": 30.0,
            "sleep_duration_hours": 6.0,
            "sleep_quality_score": 70.0
        }, headers={"Authorization": f"Bearer {token_cmd}"})

        ref_str = ref_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        res = self.client.get(f"/api/analytics/personnel/{pid}/features", params={"reference_time": ref_str}, headers={"Authorization": f"Bearer {token_cmd}"})
        w7 = res.json()["wearable_7d"]

        self.assertEqual(w7["mean_sleep_duration"], 6.5)
        self.assertEqual(w7["min_sleep_duration"], 6.0)
        self.assertAlmostEqual(w7["sleep_duration_std"], 0.707, places=2)
        self.assertEqual(w7["mean_sleep_quality"], 75.0)

    def test_11_activity_aggregation_is_correct(self):
        """11. Physical activity aggregates (steps and active minutes) are exact."""
        token_jwn, pid, code = self._register_jawan("7th Battalion", "Leh")
        token_cmd, _ = self._register_commander("7th Battalion", "Leh")

        ref_time = datetime(2026, 9, 20, 12, 0, 0, tzinfo=timezone.utc)
        self.client.post("/api/telemetry/wearable", json={
            "personnel_id": pid,
            "recorded_at": (ref_time - timedelta(days=1)).isoformat(),
            "heart_rate": 72.0,
            "hrv_rmssd": 40.0,
            "sleep_duration_hours": 7.0,
            "step_count": 8000,
            "active_minutes": 60
        }, headers={"Authorization": f"Bearer {token_cmd}"})

        self.client.post("/api/telemetry/wearable", json={
            "personnel_id": pid,
            "recorded_at": (ref_time - timedelta(days=2)).isoformat(),
            "heart_rate": 76.0,
            "hrv_rmssd": 30.0,
            "sleep_duration_hours": 6.0,
            "step_count": 6000,
            "active_minutes": 40
        }, headers={"Authorization": f"Bearer {token_cmd}"})

        ref_str = ref_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        res = self.client.get(f"/api/analytics/personnel/{pid}/features", params={"reference_time": ref_str}, headers={"Authorization": f"Bearer {token_cmd}"})
        w7 = res.json()["wearable_7d"]

        self.assertEqual(w7["mean_step_count"], 7000.0)
        self.assertEqual(w7["mean_active_minutes"], 50.0)

    def test_12_observation_count_is_correct(self):
        """12. Observation count matches the exact number of telemetry records in window."""
        token_jwn, pid, code = self._register_jawan("7th Battalion", "Leh")
        token_cmd, _ = self._register_commander("7th Battalion", "Leh")

        ref_time = datetime(2026, 9, 20, 12, 0, 0, tzinfo=timezone.utc)
        for i in range(1, 5):
            self.client.post("/api/telemetry/wearable", json={
                "personnel_id": pid,
                "recorded_at": (ref_time - timedelta(days=i)).isoformat(),
                "heart_rate": 70.0 + i,
                "hrv_rmssd": 35.0,
                "sleep_duration_hours": 6.5
            }, headers={"Authorization": f"Bearer {token_cmd}"})

        ref_str = ref_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        res = self.client.get(f"/api/analytics/personnel/{pid}/features", params={"reference_time": ref_str}, headers={"Authorization": f"Bearer {token_cmd}"})
        w7 = res.json()["wearable_7d"]
        self.assertEqual(w7["observation_count"], 4)

    def test_13_insufficient_data_handled_without_converting_to_false_zero_values(self):
        """13. Zero observations produce None / null metrics, NEVER fabricated 0.0 values."""
        token_jwn, pid, code = self._register_jawan("7th Battalion", "Leh")
        token_cmd, _ = self._register_commander("7th Battalion", "Leh")

        ref_time = datetime(2026, 9, 20, 12, 0, 0, tzinfo=timezone.utc)
        ref_str = ref_time.strftime("%Y-%m-%dT%H:%M:%SZ")

        res = self.client.get(f"/api/analytics/personnel/{pid}/features", params={"reference_time": ref_str}, headers={"Authorization": f"Bearer {token_cmd}"})
        self.assertEqual(res.status_code, 200)
        data = res.json()

        w7 = data["wearable_7d"]
        self.assertEqual(w7["observation_count"], 0)
        self.assertFalse(w7["data_available"])
        self.assertEqual(w7["data_sufficiency"], "no_data")
        self.assertIsNone(w7["mean_heart_rate"])
        self.assertIsNone(w7["min_heart_rate"])
        self.assertIsNone(w7["max_heart_rate"])
        self.assertIsNone(w7["heart_rate_std"])
        self.assertIsNone(w7["mean_hrv_rmssd"])
        self.assertIsNone(w7["mean_sleep_duration"])
        self.assertIsNone(w7["mean_step_count"])

    def test_14_explicit_reference_time_produces_deterministic_results(self):
        """14. Explicit reference_time yields reproducible results and excludes future records."""
        token_jwn, pid, code = self._register_jawan("7th Battalion", "Leh")
        token_cmd, _ = self._register_commander("7th Battalion", "Leh")

        ref_time = datetime(2026, 9, 20, 12, 0, 0, tzinfo=timezone.utc)

        # Past record (included)
        self.client.post("/api/telemetry/wearable", json={
            "personnel_id": pid,
            "recorded_at": (ref_time - timedelta(days=2)).isoformat(),
            "heart_rate": 72.0,
            "hrv_rmssd": 38.0,
            "sleep_duration_hours": 7.0
        }, headers={"Authorization": f"Bearer {token_cmd}"})

        # Future record relative to ref_time (must be excluded)
        self.client.post("/api/telemetry/wearable", json={
            "personnel_id": pid,
            "recorded_at": (ref_time + timedelta(days=2)).isoformat(),
            "heart_rate": 110.0,
            "hrv_rmssd": 15.0,
            "sleep_duration_hours": 3.0
        }, headers={"Authorization": f"Bearer {token_cmd}"})

        ref_str = ref_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        res1 = self.client.get(f"/api/analytics/personnel/{pid}/features", params={"reference_time": ref_str}, headers={"Authorization": f"Bearer {token_cmd}"})
        res2 = self.client.get(f"/api/analytics/personnel/{pid}/features", params={"reference_time": ref_str}, headers={"Authorization": f"Bearer {token_cmd}"})

        self.assertEqual(res1.status_code, 200)
        self.assertEqual(res2.status_code, 200)
        d1 = res1.json()
        d2 = res2.json()

        self.assertEqual(d1, d2)
        self.assertEqual(d1["wearable_7d"]["observation_count"], 1)
        self.assertEqual(d1["wearable_7d"]["mean_heart_rate"], 72.0)

    # =========================================================================
    # 3. SECURITY & ACCESS CONTROL TESTS (15 - 20)
    # =========================================================================

    def test_15_authorized_commander_can_retrieve_in_scope_feature_snapshot(self):
        """15. Commander can access feature snapshot for personnel in same Battalion and Location."""
        token_jwn, pid, code = self._register_jawan("7th Battalion", "Delhi")
        token_cmd, _ = self._register_commander("7th Battalion", "Delhi")

        res = self.client.get(f"/api/analytics/personnel/{pid}/features", headers={"Authorization": f"Bearer {token_cmd}"})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["personnel_id"], pid)

    def test_16_cross_battalion_access_is_rejected(self):
        """16. Cross-Battalion feature snapshot query is rejected with HTTP 403."""
        token_jwn, pid, code = self._register_jawan("7th Battalion", "Delhi")
        token_cmd_b2, _ = self._register_commander("8th Battalion", "Delhi")

        res = self.client.get(f"/api/analytics/personnel/{pid}/features", headers={"Authorization": f"Bearer {token_cmd_b2}"})
        self.assertEqual(res.status_code, 403)
        detail_msg = res.json()["detail"].lower()
        self.assertTrue("denied" in detail_msg or "forbidden" in detail_msg or "scope" in detail_msg)

    def test_17_cross_location_access_is_rejected(self):
        """17. Cross-Location feature snapshot query is rejected with HTTP 403."""
        token_jwn, pid, code = self._register_jawan("7th Battalion", "Delhi")
        token_cmd_loc2, _ = self._register_commander("7th Battalion", "Jammu")

        res = self.client.get(f"/api/analytics/personnel/{pid}/features", headers={"Authorization": f"Bearer {token_cmd_loc2}"})
        self.assertEqual(res.status_code, 403)
        detail_msg = res.json()["detail"].lower()
        self.assertTrue("denied" in detail_msg or "forbidden" in detail_msg or "scope" in detail_msg)

    def test_18_jawan_can_retrieve_own_feature_snapshot(self):
        """18. Jawan can access their own analytical feature snapshot."""
        token_jwn, pid, code = self._register_jawan("12th Battalion", "Ranchi")

        res = self.client.get(f"/api/analytics/personnel/{pid}/features", headers={"Authorization": f"Bearer {token_jwn}"})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["personnel_id"], pid)

    def test_19_jawan_cannot_retrieve_another_jawans_feature_snapshot(self):
        """19. Jawan cannot access another Jawan's analytical feature snapshot."""
        token_jwn_a, pid_a, _ = self._register_jawan("12th Battalion", "Ranchi", name_prefix="JawanA")
        token_jwn_b, pid_b, _ = self._register_jawan("12th Battalion", "Ranchi", name_prefix="JawanB")

        res = self.client.get(f"/api/analytics/personnel/{pid_b}/features", headers={"Authorization": f"Bearer {token_jwn_a}"})
        self.assertEqual(res.status_code, 403)
        detail_msg = res.json()["detail"].lower()
        self.assertTrue("denied" in detail_msg or "forbidden" in detail_msg or "authorized" in detail_msg)

    def test_20_unauthenticated_request_is_rejected(self):
        """20. Unauthenticated feature query returns HTTP 401 Unauthorized."""
        token_jwn, pid, _ = self._register_jawan("12th Battalion", "Ranchi")

        res = self.client.get(f"/api/analytics/personnel/{pid}/features")
        self.assertEqual(res.status_code, 401)

    # =========================================================================
    # 4. REGRESSION TESTS (21 - 25)
    # =========================================================================

    def test_21_phase30_security_regression_still_intact(self):
        """21. Phase 30 cross-scope update and routing boundaries remain intact."""
        token_jwn, pid, _ = self._register_jawan("7th Battalion", "Delhi")
        token_cmd_other, _ = self._register_commander("8th Battalion", "Delhi")

        res = self.client.get(f"/api/personnel/{pid}", headers={"Authorization": f"Bearer {token_cmd_other}"})
        self.assertEqual(res.status_code, 403)

    def test_22_phase31_ingestion_endpoints_still_intact(self):
        """22. Phase 31 HRMS sync and wearable telemetry ingestion remain fully functional."""
        token_jwn, pid, _ = self._register_jawan("7th Battalion", "Delhi")
        token_cmd, _ = self._register_commander("7th Battalion", "Delhi")

        # HRMS sync
        hrms_res = self.client.post("/api/hrms/sync", json={
            "personnel_id": pid,
            "service_number": f"REG31-{pid}",
            "duty_hours_per_week": 44.0
        }, headers={"Authorization": f"Bearer {token_cmd}"})
        self.assertEqual(hrms_res.status_code, 200)
        self.assertEqual(hrms_res.json()["source"], "mock_hrms")

        # Wearable ingestion
        wearable_res = self.client.post("/api/telemetry/wearable", json={
            "personnel_id": pid,
            "recorded_at": datetime.now(timezone.utc).isoformat(),
            "heart_rate": 74.0,
            "hrv_rmssd": 44.0,
            "sleep_duration_hours": 7.2
        }, headers={"Authorization": f"Bearer {token_cmd}"})
        self.assertEqual(wearable_res.status_code, 201)
        self.assertEqual(wearable_res.json()["source"], "simulated_wearable")

    def test_23_existing_ml_prediction_endpoint_still_works(self):
        """23. Existing production ML prediction endpoint (/api/predict) operates unchanged."""
        token_cmd, _ = self._register_commander("7th Battalion", "Delhi")

        pred_res = self.client.post("/api/predict", json={
            "Age": 30,
            "Gender": "Male",
            "Department": "Operations",
            "Job_Role": "Field Officer",
            "Working_Hours_per_Week": 45.0,
            "Duty_Hours_Per_Week": 45.0,
            "Sleep_Hours": 7.0,
            "Physical_Activity_Hours_per_Week": 4.0,
            "Experience_Years": 6.0,
            "Annual_Leaves_Taken": 12,
            "Consecutive_Duty_Days": 4,
            "Night_Shifts_Per_Month": 2,
            "Leave_Gap_Days": 30
        }, headers={"Authorization": f"Bearer {token_cmd}"})

        self.assertEqual(pred_res.status_code, 200)
        data = pred_res.json()
        self.assertIn(data["stress_level"], ["Low", "Medium", "High"])
        self.assertTrue(0.0 <= data["risk_score"] <= 100.0)
        self.assertTrue(len(data["key_factors"]) > 0)
        self.assertTrue(len(data["recommendations"]) > 0)

    def test_24_existing_shap_and_risk_functionality_still_works(self):
        """24. TreeSHAP explainer and calibrated risk scoring logic operate without degradation."""
        service = get_welfare_service()
        self.assertIsNotNone(service.explainer)
        self.assertTrue(len(service.explainer.feature_names) > 0)

        # Direct test on calibrated risk calculation with proper signature
        score, level, priority = calculate_risk_score(
            probabilities={'Low': 0.85, 'Medium': 0.12, 'High': 0.03},
            predicted_class='Low',
            record={'Duty_Hours_Per_Week': 40.0, 'Consecutive_Duty_Days': 3}
        )
        self.assertEqual(level, 'Low')
        self.assertEqual(priority, 'Routine')
        self.assertLess(score, 40.0)

    def test_25_d2_external_validation_isolation_verified(self):
        """25. D2 external validation dataset remains isolated from synthetic ingestion data."""
        possible_paths = [
            os.path.join(os.path.dirname(__file__), '..', 'data', 'D2_cleaned.csv'),
            os.path.join(os.path.dirname(__file__), '..', 'D2_cleaned.csv'),
            '/app/data/D2_cleaned.csv'
        ]
        d2_path = next((p for p in possible_paths if os.path.exists(p)), None)
        self.assertIsNotNone(d2_path, "D2_cleaned.csv file must exist for external validation.")

        df_d2, d2_info = load_and_inspect_d2(d2_path)
        self.assertEqual(d2_info["shape"][0], 2000)
        self.assertEqual(d2_info["shape"][1], 14)

        # Confirm zero contamination: no HRMS or wearable synthetic column names in D2
        d2_cols = set(df_d2.columns)
        self.assertNotIn("source", d2_cols)
        self.assertNotIn("mock_hrms", d2_cols)
        self.assertNotIn("simulated_wearable", d2_cols)
        self.assertNotIn("service_number", d2_cols)
        self.assertNotIn("hrv_rmssd", d2_cols)
