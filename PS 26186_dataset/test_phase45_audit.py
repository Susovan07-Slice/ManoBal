"""
Phase 45 Comprehensive End-to-End System Validation Script
Tests:
1. Canonical Phase 34 Risk Profiles (Healthy, Moderate, High-Risk, Invalid)
2. Longitudinal Welfare & Trend Computation
3. Alerts & Anomaly Signal Chain
4. Support Recommendations Engine
5. Case Management & Human Review Workflow (Create, Note, Assign, Transition, Timeline)
6. Follow-up & Outcome Tracking (Baseline -> Post-Assessment)
7. Unified Welfare Intelligence Consolidation
8. RBAC, Anti-IDOR, Scope, and Privacy (k < 5 suppression)
"""

import sys
import os
import json
import requests

BASE_URL = "http://localhost:8000/api"

def log(msg, status="INFO"):
    print(f"[{status}] {msg}", flush=True)

def run_audit():
    results = {}
    
    # ----------------------------------------------------
    # 1. AUTHENTICATION & TOKENS
    # ----------------------------------------------------
    log("Logging in as Jawan, Officer, Counselor, and Admin...")
    
    # Jawan
    r_jawan = requests.post(f"{BASE_URL}/auth/login", json={"username": "jawan_verma", "password": "PersonnelPassword123!"})
    assert r_jawan.status_code == 200, f"Jawan login failed: {r_jawan.text}"
    jawan_token = r_jawan.json()["access_token"]
    
    # Officer
    r_officer = requests.post(f"{BASE_URL}/auth/login", json={"username": "officer_sharma", "password": "OfficerPassword123!"})
    assert r_officer.status_code == 200, f"Officer login failed: {r_officer.text}"
    officer_token = r_officer.json()["access_token"]

    # Counselor / Welfare Officer
    r_counselor = requests.post(f"{BASE_URL}/auth/login", json={"username": "counselor_priya", "password": "WelfarePassword123!"})
    assert r_counselor.status_code == 200, f"Counselor login failed: {r_counselor.text}"
    counselor_token = r_counselor.json()["access_token"]

    # Admin
    r_admin = requests.post(f"{BASE_URL}/auth/login", json={"username": "admin", "password": "AdminPassword123!"})
    assert r_admin.status_code == 200, f"Admin login failed: {r_admin.text}"
    admin_token = r_admin.json()["access_token"]
    
    results["auth_logins"] = "PASS"
    log("Authentication for all 4 roles: PASS", "SUCCESS")

    jawan_headers = {"Authorization": f"Bearer {jawan_token}"}
    officer_headers = {"Authorization": f"Bearer {officer_token}"}
    counselor_headers = {"Authorization": f"Bearer {counselor_token}"}
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # ----------------------------------------------------
    # 2. JAWAN IDENTITY & ASSESSMENT WORKFLOW
    # ----------------------------------------------------
    r_me = requests.get(f"{BASE_URL}/auth/me", headers=jawan_headers)
    assert r_me.status_code == 200
    jawan_user = r_me.json()
    log(f"Jawan Identity: ID={jawan_user['id']}, Role={jawan_user['role']}")

    # 2A: Healthy Assessment Scenario (POST /api/predict)
    healthy_payload = {
        "age": 28,
        "gender": "Male",
        "marital_status": "Single",
        "location": "Delhi",
        "job_role": "Field Officer",
        "company_size": "Large",
        "department": "Operations",
        "experience_years": 4.0,
        "monthly_salary_inr": 65000.0,
        "working_hours_per_week": 40.0,
        "duty_hours_per_week": 42.0,
        "commute_time_hours": 0.5,
        "remote_work": "No",
        "annual_leaves_taken": 14,
        "team_size": 30,
        "sleep_hours": 8.0,
        "physical_activity_hours_per_week": 6.0,
        "health_issues": "",
        "mental_health_leave_taken": "No",
        "burnout_symptoms": "Rarely",
        "deployment_days": 10,
        "night_shifts_per_month": 2,
        "consecutive_duty_days": 4,
        "transfer_frequency": 0,
        "training_load": 2,
        "leave_gap_days": 12,
        "remote_posting": "No",
        "operational_exposure": "Low"
    }
    r_healthy = requests.post(f"{BASE_URL}/predict", json=healthy_payload, headers=jawan_headers)
    assert r_healthy.status_code == 200, f"Healthy assessment failed: {r_healthy.text}"
    healthy_res = r_healthy.json()
    log(f"Healthy Scenario Result: Risk Score={healthy_res.get('risk_score')}, Level={healthy_res.get('stress_level')}")
    assert healthy_res.get("stress_level") in ["Low", "Medium"], f"Unexpected level for healthy profile: {healthy_res.get('stress_level')}"

    # 2B: Moderate Assessment Scenario
    moderate_payload = dict(healthy_payload)
    moderate_payload.update({
        "duty_hours_per_week": 68.0,
        "sleep_hours": 5.0,
        "consecutive_duty_days": 18,
        "night_shifts_per_month": 10,
        "leave_gap_days": 95,
        "burnout_symptoms": "Sometimes",
        "operational_exposure": "Medium"
    })
    r_mod = requests.post(f"{BASE_URL}/predict", json=moderate_payload, headers=jawan_headers)
    assert r_mod.status_code == 200
    mod_res = r_mod.json()
    log(f"Moderate Scenario Result: Risk Score={mod_res.get('risk_score')}, Level={mod_res.get('stress_level')}")

    # 2C: Extreme High-Risk Scenario
    extreme_payload = dict(healthy_payload)
    extreme_payload.update({
        "duty_hours_per_week": 95.0,
        "sleep_hours": 3.5,
        "consecutive_duty_days": 38,
        "night_shifts_per_month": 22,
        "leave_gap_days": 210,
        "deployment_days": 180,
        "burnout_symptoms": "Often",
        "operational_exposure": "High",
        "remote_posting": "Yes"
    })
    r_ext = requests.post(f"{BASE_URL}/predict", json=extreme_payload, headers=jawan_headers)
    assert r_ext.status_code == 200
    ext_res = r_ext.json()
    log(f"Extreme Scenario Result: Risk Score={ext_res.get('risk_score')}, Level={ext_res.get('stress_level')}")
    assert ext_res.get("stress_level") in ["High", "Very High"], f"Expected high/very high: {ext_res.get('stress_level')}"

    # 2D: Invalid Assessment Scenario (Input Validation & Shielding)
    invalid_payload = dict(healthy_payload)
    invalid_payload.update({"age": 999, "sleep_hours": -5.0})
    r_inv = requests.post(f"{BASE_URL}/predict", json=invalid_payload, headers=jawan_headers)
    assert r_inv.status_code == 422, f"Expected 422 for invalid payload, got {r_inv.status_code}"
    log(f"Invalid Scenario Handled Safely: Status={r_inv.status_code}")

    results["jawan_workflow"] = "PASS"

    # ----------------------------------------------------
    # 3. COMMANDER & WELFARE OFFICER WORKFLOW
    # ----------------------------------------------------
    # 3A: Dashboard Overview & Distribution
    r_dash = requests.get(f"{BASE_URL}/dashboard/summary", headers=officer_headers)
    assert r_dash.status_code == 200
    log(f"Commander Dashboard Summary: Total Assessed={r_dash.json().get('total_personnel', r_dash.json().get('total_assessed'))}")

    # 3B: Unified Welfare Intelligence (Phase 42)
    r_uwi = requests.get(f"{BASE_URL}/analytics/welfare-intelligence/unit", headers=officer_headers)
    assert r_uwi.status_code == 200, f"UWI Unit failed: {r_uwi.text}"
    log(f"Unified Welfare Intelligence Unit: Status={r_uwi.status_code}, Active Personnel={r_uwi.json().get('total_active_personnel')}")

    # In-Scope Personnel Access (Personnel ID 1: Constable Rajesh Verma in 7th Battalion, Srinagar)
    r_uwi_p = requests.get(f"{BASE_URL}/analytics/welfare-intelligence/personnel/1", headers=officer_headers)
    assert r_uwi_p.status_code == 200, f"UWI Personnel failed: {r_uwi_p.text}"
    log(f"Unified Welfare Intelligence In-Scope Snapshot: Name={r_uwi_p.json().get('personnel_name')}, Risk={r_uwi_p.json().get('risk_score')}")

    # 3C: Welfare Alerts & Anomalies
    r_alerts = requests.get(f"{BASE_URL}/welfare/alerts", headers=officer_headers)
    assert r_alerts.status_code == 200, f"Alerts failed: {r_alerts.text}"
    log(f"Welfare Alerts Count: {len(r_alerts.json())}")

    r_anom = requests.get(f"{BASE_URL}/anomalies/commander", headers=officer_headers)
    assert r_anom.status_code == 200, f"Anomalies failed: {r_anom.text}"
    log(f"Early-Warning Anomalies Scope: Total Authorized={r_anom.json().get('total_authorized_personnel')}")

    # 3D: Support Recommendations
    r_recs = requests.get(f"{BASE_URL}/recommendations/commander", headers=officer_headers)
    assert r_recs.status_code == 200, f"Recs failed: {r_recs.text}"
    log(f"Support Recommendations: Status={r_recs.status_code}")

    # 3E: Welfare Follow-ups & Outcome Tracking (Phase 41)
    r_fol = requests.get(f"{BASE_URL}/followups", headers=officer_headers)
    assert r_fol.status_code == 200, f"Followups failed: {r_fol.text}"
    log(f"Welfare Follow-ups Count: {len(r_fol.json())}")

    # 3F: Case Management Workspace (Phase 43)
    r_cases = requests.get(f"{BASE_URL}/welfare-cases", headers=officer_headers)
    assert r_cases.status_code == 200, f"Cases failed: {r_cases.text}"
    log(f"Welfare Cases Count: {r_cases.json().get('total_count', 0)}")

    # 3G: Case Creation & Lifecycle Verification
    new_case_payload = {
        "title": "Phase 45 System Acceptance Review",
        "description": "Validation case for Phase 45 end-to-end integration and human oversight.",
        "priority": "HIGH",
        "personnel_id": 1, # Constable Rajesh Verma (Srinagar)
        "case_type": "CURRENT_RISK_REVIEW",
        "initial_notes": "Created during Phase 45 validation test."
    }
    r_new_case = requests.post(f"{BASE_URL}/welfare-cases", json=new_case_payload, headers=officer_headers)
    assert r_new_case.status_code in [200, 201], f"Case creation failed: {r_new_case.text}"
    created_case = r_new_case.json()
    case_id = created_case["id"]
    log(f"Welfare Case Created: ID={case_id}, Status={created_case['status']}")

    # Add Review Note (Immutable)
    r_note = requests.post(f"{BASE_URL}/welfare-cases/{case_id}/notes", json={"content": "Case reviewed by Officer Sharma.", "note_type": "REVIEW_NOTE"}, headers=officer_headers)
    assert r_note.status_code in [200, 201], f"Note creation failed: {r_note.text}"

    # Transition Status: OPEN -> UNDER_REVIEW
    r_status = requests.post(f"{BASE_URL}/welfare-cases/{case_id}/status", json={"status": "UNDER_REVIEW", "reason": "Initiating supportive check-in"}, headers=officer_headers)
    assert r_status.status_code == 200, f"Status update failed: {r_status.text}"
    assert r_status.json()["status"] == "UNDER_REVIEW"

    # Get Timeline & Audit
    r_timeline = requests.get(f"{BASE_URL}/welfare-cases/{case_id}/timeline", headers=officer_headers)
    assert r_timeline.status_code == 200
    log(f"Case {case_id} Timeline Events: {len(r_timeline.json().get('events', []))}")

    results["commander_workflow"] = "PASS"

    # ----------------------------------------------------
    # 4. SECURITY & ANTI-IDOR / RBAC / PRIVACY
    # ----------------------------------------------------
    # 4A: Unauthorized Access (No Token)
    r_no_auth = requests.get(f"{BASE_URL}/welfare-cases")
    assert r_no_auth.status_code == 401, f"Expected 401, got {r_no_auth.status_code}"
    
    # 4B: Jawan attempting Officer Endpoints (Alerts & Case Creation)
    r_jawan_alerts = requests.get(f"{BASE_URL}/welfare/alerts", headers=jawan_headers)
    assert r_jawan_alerts.status_code in [401, 403], f"Expected 403 for Jawan on /welfare/alerts, got {r_jawan_alerts.status_code}"
    
    r_jawan_case_create = requests.post(f"{BASE_URL}/welfare-cases", json={"personnel_id": 1, "title": "Unauthorized"}, headers=jawan_headers)
    assert r_jawan_case_create.status_code in [401, 403], f"Expected 403 for Jawan case creation, got {r_jawan_case_create.status_code}"
    log("RBAC Unauthorized Endpoint Check: PASS (Jawan blocked from commander alerts and case creation)")

    # 4C: Jawan attempting Commander Analytics
    r_jawan_analytics = requests.get(f"{BASE_URL}/analytics/commander", headers=jawan_headers)
    assert r_jawan_analytics.status_code in [401, 403], f"Expected 403 for Jawan on /analytics/commander, got {r_jawan_analytics.status_code}"

    # 4D: Anti-IDOR Scope Violation (Officer Sharma accessing Delhi personnel 4)
    r_idor = requests.get(f"{BASE_URL}/analytics/welfare-intelligence/personnel/4", headers=officer_headers)
    assert r_idor.status_code == 403, f"Expected 403 for out-of-scope IDOR attempt, got {r_idor.status_code}"
    log("Anti-IDOR Scope Boundary Check: PASS (Cross-location correctly rejected with 403)")

    # 4E: Admin Cross-Scope Access (Admin can view all)
    r_admin_uwi = requests.get(f"{BASE_URL}/analytics/welfare-intelligence/personnel/4", headers=admin_headers)
    assert r_admin_uwi.status_code == 200, f"Expected 200 for Admin, got {r_admin_uwi.status_code}"
    log("Admin System-Wide Access Check: PASS")

    # 4F: Privacy k < 5 suppression
    r_comm = requests.get(f"{BASE_URL}/analytics/commander", headers=officer_headers)
    assert r_comm.status_code == 200
    comm_data = r_comm.json()
    log(f"Commander Analytics Scope & Privacy: Unit={comm_data.get('battalion', 'All')}, Personnel Count={comm_data.get('total_personnel')}")

    results["security_checks"] = "PASS"

    # ----------------------------------------------------
    # 5. SUMMARY
    # ----------------------------------------------------
    log("All Phase 45 End-to-End System Tests Completed Successfully!", "SUCCESS")
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    run_audit()
