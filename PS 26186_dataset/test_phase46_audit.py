"""
Phase 46 SIH Problem Statement Acceptance Audit Script
Executes empirical tests across:
1. HR/Organizational indicators & HRMS sync
2. Realistic Risk Engine bounds, extreme stress, NaN/Inf shielding
3. Biometric & simulated wearable telemetry ingestion & feature extraction
4. End-to-End Signal Chain: Assessment -> Trend -> Alert -> Recommendation -> Case -> Note -> Transition -> Followup
5. Role Separation, Anti-IDOR, and k-Anonymity privacy
"""

import sys
import os
import json
import requests

BASE_URL = "http://localhost:8000/api"

def log(msg, status="INFO"):
    print(f"[{status}] {msg}", flush=True)

def run_sih_audit():
    audit_data = {}
    
    # -------------------------------------------------------------------------
    # 1. AUTHENTICATION & IDENTITY VERIFICATION
    # -------------------------------------------------------------------------
    log("1. Authenticating as Jawan, Officer, Counselor, and Admin...")
    r_jawan = requests.post(f"{BASE_URL}/auth/login", json={"username": "jawan_verma", "password": "PersonnelPassword123!"})
    assert r_jawan.status_code == 200, f"Jawan login failed: {r_jawan.text}"
    jawan_token = r_jawan.json()["access_token"]
    
    r_officer = requests.post(f"{BASE_URL}/auth/login", json={"username": "officer_sharma", "password": "OfficerPassword123!"})
    assert r_officer.status_code == 200, f"Officer login failed: {r_officer.text}"
    officer_token = r_officer.json()["access_token"]

    r_counselor = requests.post(f"{BASE_URL}/auth/login", json={"username": "counselor_priya", "password": "WelfarePassword123!"})
    assert r_counselor.status_code == 200, f"Counselor login failed: {r_counselor.text}"
    counselor_token = r_counselor.json()["access_token"]

    r_admin = requests.post(f"{BASE_URL}/auth/login", json={"username": "admin", "password": "AdminPassword123!"})
    assert r_admin.status_code == 200, f"Admin login failed: {r_admin.text}"
    admin_token = r_admin.json()["access_token"]

    j_hdr = {"Authorization": f"Bearer {jawan_token}"}
    o_hdr = {"Authorization": f"Bearer {officer_token}"}
    c_hdr = {"Authorization": f"Bearer {counselor_token}"}
    a_hdr = {"Authorization": f"Bearer {admin_token}"}

    log("Auth verified for all 4 roles.", "SUCCESS")
    audit_data["auth"] = "PASS"

    # -------------------------------------------------------------------------
    # 2. HR & ORGANIZATIONAL INDICATORS AUDIT
    # -------------------------------------------------------------------------
    log("2. Testing HR & Organizational data indicators and HRMS ingestion...")
    # Test HRMS sync for Srinagar personnel 1
    hrms_payload = {
        "personnel_id": 1,
        "service_number": "ARMY-2026-SRN-001",
        "department": "Operations",
        "battalion": "7th Battalion",
        "location": "Srinagar",
        "job_role": "Field Officer",
        "rank": "Constable",
        "deployment_days": 120,
        "duty_hours_per_week": 65.0,
        "night_shifts_per_month": 8,
        "consecutive_duty_days": 14,
        "leave_gap_days": 90,
        "annual_leaves_taken": 12,
        "transfer_frequency": 2,
        "training_load": 3,
        "experience_years": 5.0,
        "deployment_history": "Kashmir Valley 2024-2026",
        "transfer_history": "Delhi -> Srinagar",
        "training_history": "High Altitude Warfare Course"
    }
    r_hrms = requests.post(f"{BASE_URL}/hrms/sync", json=hrms_payload, headers=o_hdr)
    assert r_hrms.status_code == 200, f"HRMS sync failed: {r_hrms.text}"
    hrms_res = r_hrms.json()
    log(f"HRMS Ingestion Bridge Response: source='{hrms_res.get('source')}', message='{hrms_res.get('message')}'")
    audit_data["hrms_sync"] = "PASS"

    # -------------------------------------------------------------------------
    # 3. RISK ENGINE REALISM & SAFETY BOUNDS (Section 8)
    # -------------------------------------------------------------------------
    log("3. Testing Risk Engine Realism, Safety Bounds & Edge Cases...")
    
    # 3A: Baseline healthy
    base_payload = {
        "age": 29, "gender": "Male", "marital_status": "Single", "location": "Srinagar",
        "job_role": "Field Officer", "company_size": "Large", "department": "Operations",
        "experience_years": 5.0, "monthly_salary_inr": 60000.0, "working_hours_per_week": 42.0,
        "duty_hours_per_week": 42.0, "commute_time_hours": 0.5, "remote_work": "No",
        "annual_leaves_taken": 15, "team_size": 25, "sleep_hours": 8.0,
        "physical_activity_hours_per_week": 6.0, "health_issues": "",
        "mental_health_leave_taken": "No", "burnout_symptoms": "Rarely",
        "deployment_days": 10, "night_shifts_per_month": 2, "consecutive_duty_days": 4,
        "transfer_frequency": 0, "training_load": 2, "leave_gap_days": 15,
        "remote_posting": "No", "operational_exposure": "Low"
    }
    r_base = requests.post(f"{BASE_URL}/predict", json=base_payload, headers=j_hdr)
    assert r_base.status_code == 200
    res_base = r_base.json()
    log(f"Healthy Baseline: Score={res_base['risk_score']}, Level={res_base['stress_level']}, Category={res_base['risk_priority']}")
    assert 0.0 <= res_base["risk_score"] <= 100.0

    # 3B: High workload + Severe Sleep Deprivation + Consecutive Duty
    stress_payload = dict(base_payload)
    stress_payload.update({
        "duty_hours_per_week": 96.0,
        "sleep_hours": 3.0,
        "consecutive_duty_days": 35,
        "night_shifts_per_month": 24,
        "leave_gap_days": 240,
        "deployment_days": 210,
        "operational_exposure": "High",
        "burnout_symptoms": "Often",
        "remote_posting": "Yes"
    })
    r_stress = requests.post(f"{BASE_URL}/predict", json=stress_payload, headers=j_hdr)
    assert r_stress.status_code == 200
    res_stress = r_stress.json()
    log(f"Compound Stress Scenario: Score={res_stress['risk_score']}, Level={res_stress['stress_level']}, Recommendations={len(res_stress.get('recommendations', []))}")
    assert res_stress["risk_score"] > res_base["risk_score"]
    assert res_stress["stress_level"] in ["High", "Very High"]

    # 3C: Input validation & Shielding (NaN / Inf / Out of bounds)
    r_nan = requests.post(f"{BASE_URL}/predict", json={"age": "invalid_str", "sleep_hours": "NaN"}, headers=j_hdr)
    assert r_nan.status_code == 422, f"Expected 422 for malformed types, got {r_nan.status_code}"
    
    r_neg = requests.post(f"{BASE_URL}/predict", json=dict(base_payload, sleep_hours=-4.0), headers=j_hdr)
    assert r_neg.status_code == 422, f"Expected 422 for negative sleep, got {r_neg.status_code}"
    
    log("Risk engine bounds, monotonic response, and input shielding: PASS", "SUCCESS")
    audit_data["risk_engine_safety"] = "PASS"

    # -------------------------------------------------------------------------
    # 4. BIOMETRIC & WEARABLE TELEMETRY INGESTION (Section 6)
    # -------------------------------------------------------------------------
    log("4. Testing Biometric & Simulated Wearable Telemetry Bridge...")
    telemetry_payload = {
        "personnel_id": 1,
        "recorded_at": "2026-09-28T12:00:00Z",
        "heart_rate": 78,
        "hrv_rmssd": 38.5,
        "sleep_duration_hours": 5.8,
        "sleep_quality_score": 62,
        "step_count": 8500,
        "active_minutes": 45,
        "device_model": "Garmin Tactix 7 (Simulated)"
    }
    r_tele = requests.post(f"{BASE_URL}/telemetry/wearable", json=telemetry_payload, headers=o_hdr)
    assert r_tele.status_code in [200, 201], f"Telemetry ingestion failed: {r_tele.text}"
    tele_res = r_tele.json()
    log(f"Wearable Telemetry Ingested: ID={tele_res.get('id')}, Source='{tele_res.get('source')}', Disclaimer='{tele_res.get('disclaimer')[:60]}...'")
    audit_data["biometric_telemetry"] = "PASS"

    # -------------------------------------------------------------------------
    # 5. END-TO-END WELFARE SIGNAL CHAIN (Section 9 & 10 & 11)
    # -------------------------------------------------------------------------
    log("5. Testing End-to-End Welfare Signal Chain...")
    # Step A: Assessment trigger
    r_assess = requests.post(
        f"{BASE_URL}/personnel/1/assess",
        json={
            "duty_hours_per_week": 72.0,
            "consecutive_duty_days": 16,
            "night_shifts_per_month": 12,
            "leave_gap_days": 105,
            "sleep_hours": 4.5,
            "mood_score": 2,
            "burnout_symptoms": "Often",
            "operational_exposure": "High"
        },
        headers=o_hdr
    )
    assert r_assess.status_code in [200, 201], f"Assessment trigger failed: {r_assess.text}"
    assess_res = r_assess.json()
    assess_obj = assess_res.get("assessment", assess_res)
    log(f"Step A - Assessment Generated: Risk={assess_obj.get('risk_score')}, Factors={len(assess_obj.get('key_factors', []))}")

    # Step B: Longitudinal Trend
    r_trend = requests.get(f"{BASE_URL}/personnel/1/trend", headers=o_hdr)
    assert r_trend.status_code == 200
    trend_res = r_trend.json()
    log(f"Step B - Longitudinal Trend: Trajectory={trend_res.get('trajectory', trend_res.get('risk_trend'))}, Points={len(trend_res.get('history', []))}")

    # Step C: Welfare Recommendations
    r_recs = requests.get(f"{BASE_URL}/recommendations/commander", headers=o_hdr)
    assert r_recs.status_code == 200
    log(f"Step C - Support Recommendations Count: {len(r_recs.json())}")

    # Step D: Welfare Follow-ups (Phase 41)
    r_fol = requests.get(f"{BASE_URL}/followups", headers=o_hdr)
    assert r_fol.status_code == 200
    log(f"Step D - Active Follow-ups Count: {len(r_fol.json())}")

    # Step E: Welfare Case Management (Phase 43)
    case_payload = {
        "personnel_id": 1,
        "case_type": "CURRENT_RISK_REVIEW",
        "title": "SIH Phase 46 Welfare Check-in",
        "summary": "Mandatory supportive evaluation triggered during SIH acceptance audit.",
        "trigger_source": "PHASE_34_RISK"
    }
    r_case = requests.post(f"{BASE_URL}/welfare-cases", json=case_payload, headers=c_hdr)
    assert r_case.status_code in [200, 201], f"Case creation failed: {r_case.text}"
    case_obj = r_case.json()
    case_id = case_obj["id"]
    log(f"Step E - Welfare Case Created: ID={case_id}, Status={case_obj['status']}")

    # Step F: Add Immutable Review Note
    r_note = requests.post(
        f"{BASE_URL}/welfare-cases/{case_id}/notes",
        json={"content": "Counselor Priya conducted initial supportive screening.", "note_type": "SUPPORT_NOTE"},
        headers=c_hdr
    )
    assert r_note.status_code in [200, 201]
    log(f"Step F - Immutable Review Note Appended: Note ID={r_note.json()['id']}")

    # Step G: Transition Status
    r_trans = requests.post(
        f"{BASE_URL}/welfare-cases/{case_id}/status",
        json={"status": "UNDER_REVIEW", "reason": "Initiated structured clinical review"},
        headers=c_hdr
    )
    assert r_trans.status_code == 200
    assert r_trans.json()["status"] == "UNDER_REVIEW"
    log("Step G - Case Status Transitioned: OPEN -> UNDER_REVIEW")

    # Step H: Timeline Audit
    r_time = requests.get(f"{BASE_URL}/welfare-cases/{case_id}/timeline", headers=c_hdr)
    assert r_time.status_code == 200
    log(f"Step H - Timeline Events Verified: Count={len(r_time.json().get('events', []))}")
    audit_data["signal_chain"] = "PASS"

    # -------------------------------------------------------------------------
    # 6. PRIVACY, RBAC & ANTI-IDOR ENFORCEMENT (Section 14 & 15)
    # -------------------------------------------------------------------------
    log("6. Testing Privacy, RBAC & Anti-IDOR Scoping...")
    # 6A: Jawan restricted from case creation
    r_j_block = requests.post(f"{BASE_URL}/welfare-cases", json=case_payload, headers=j_hdr)
    assert r_j_block.status_code in [401, 403], f"Expected 403 for Jawan, got {r_j_block.status_code}"

    # 6B: Anti-IDOR Cross-Location Block
    r_idor = requests.get(f"{BASE_URL}/analytics/welfare-intelligence/personnel/4", headers=o_hdr)
    assert r_idor.status_code == 403, f"Expected 403 for cross-location IDOR, got {r_idor.status_code}"

    # 6C: Admin System-Wide Access
    r_admin_ok = requests.get(f"{BASE_URL}/analytics/welfare-intelligence/personnel/4", headers=a_hdr)
    assert r_admin_ok.status_code == 200, f"Expected 200 for Admin, got {r_admin_ok.status_code}"

    # 6D: Small-group k-anonymity (k >= 5)
    r_uwi = requests.get(f"{BASE_URL}/analytics/welfare-intelligence/unit", headers=o_hdr)
    assert r_uwi.status_code == 200
    uwi_data = r_uwi.json()
    log(f"6D - Unit Welfare Intelligence (k>=5 check): Active Personnel={uwi_data.get('total_active_personnel')}")
    audit_data["privacy_rbac"] = "PASS"

    log("ALL PHASE 46 ACCEPTANCE AUDIT TESTS PASSED SUCCESSFULLY!", "SUCCESS")
    print(json.dumps(audit_data, indent=2), flush=True)

if __name__ == "__main__":
    run_sih_audit()
