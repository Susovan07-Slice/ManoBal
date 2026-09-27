import urllib.request
import json
import uuid

BASE = "http://127.0.0.1:8000/api"

def make_req(path, method="GET", data=None, token=None):
    url = f"{BASE}{path}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode('utf-8') if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        err_body = e.read().decode('utf-8')
        try:
            return e.code, json.loads(err_body)
        except:
            return e.code, err_body

print("--- 1. Login as Admin / Commander (admin / admin123) ---")
st, admin_login = make_req("/auth/login", "POST", {"username": "admin", "password": "admin123"})
print(f"Admin login status: {st}")
admin_token = admin_login.get("access_token")

rand_suffix = uuid.uuid4().hex[:6]
jawan_username = f"jawan_{rand_suffix}"
jawan_code = f"JWN-{rand_suffix.upper()}"

print(f"\n--- 2. Register New Jawan ({jawan_username} / {jawan_code}) in Jawan App ---")
jawan_payload = {
    "username": jawan_username,
    "password": "Password123!",
    "name": "Sepoy Vikram Singh",
    "personnel_code": jawan_code,
    "battalion": "7th Battalion",
    "location": "Srinagar",
    "age": 27,
    "gender": "Male",
    "department": "Operations",
    "job_role": "Rifleman",
    "experience_years": 4.5
}
st, jawan_reg = make_req("/auth/register-jawan", "POST", jawan_payload)
print(f"Jawan register status: {st}")
jawan_token = jawan_reg.get("access_token")

print("\n--- 3. Check Jawan Info (/auth/me) ---")
st, me = make_req("/auth/me", "GET", token=jawan_token)
print(f"Jawan /auth/me: {st} | Role: {me.get('role')} | Personnel ID: {me.get('personnel_id')} | Scope: {me.get('battalion')} • {me.get('location')}")
pid = me.get("personnel_id")

print("\n--- 4. Verify Jawan Appears in Commander Dashboard (/personnel) ---")
st, plist = make_req("/personnel", "GET", token=admin_token)
print(f"Commander /personnel status: {st}")
if isinstance(plist, dict):
    personnel_items = plist.get("items", [])
    found = any(p.get("id") == pid or p.get("personnel_code") == jawan_code for p in personnel_items)
    print(f"Total personnel in DB: {len(personnel_items)}. Newly created Jawan found in Commander's list: {found}")
else:
    print(f"plist is: {plist}")

print("\n--- 5. Submit Welfare Alert / SOS from Jawan App ---")
sos_payload = {
    "request_type": "stress_fatigue",
    "description": "EMERGENCY SOS: Experiencing severe exhaustion and sleep deficit after night patrols.",
    "urgency": "urgent",
    "contact_preference": "immediate_callback"
}
st, welfare_out = make_req("/welfare/requests", "POST", sos_payload, token=jawan_token)
print(f"Submit Welfare Request status: {st}")
print(f"Welfare Request ID: {welfare_out.get('id')}, Urgency: {welfare_out.get('urgency')}, Status: {welfare_out.get('status')}")

print("\n--- 6. Query Welfare Alerts from Commander Dashboard ---")
st, cmd_alerts = make_req("/welfare/requests", "GET", token=admin_token)
print(f"Commander /welfare/requests status: {st}")
if isinstance(cmd_alerts, list):
    print(f"Total welfare requests visible to Commander: {len(cmd_alerts)}")
    matching = [r for r in cmd_alerts if r.get("id") == welfare_out.get("id")]
    print(f"Alert successfully received in Commander Dashboard: {len(matching) > 0}")
    if matching:
        m = matching[0]
        print(f"  Alert details: ID {m.get('id')} | Personnel: #{m.get('personnel_id')} ({m.get('personnel_name')}) | Battalion: {m.get('battalion')} | Urgency: {m.get('urgency')}")
else:
    print(f"cmd_alerts response: {cmd_alerts}")

print("\n--- 7. Submit Stress Assessment from Jawan App ---")
assess_payload = {
    "duty_hours_per_week": 65.0,
    "consecutive_duty_days": 14,
    "night_shifts_per_month": 8,
    "sleep_hours": 4.5,
    "physical_fatigue": 4,
    "mood_score": 2,
    "burnout_symptoms": "Often"
}
st, assess_res = make_req(f"/personnel/{pid}/assess", "POST", assess_payload, token=jawan_token)
print(f"Jawan Assessment status: {st}")
if isinstance(assess_res, dict):
    print(f"  Assessment Risk Score: {assess_res.get('risk_score')}, Level: {assess_res.get('stress_level')}, Priority: {assess_res.get('risk_priority')}")

print("\n--- 8. Verify Assessment Appears in Commander Dashboard ---")
st, recent = make_req("/dashboard/recent-assessments", "GET", token=admin_token)
print(f"Commander /dashboard/recent-assessments status: {st}, Count: {len(recent) if isinstance(recent, list) else recent}")

st, high_risk = make_req("/dashboard/high-risk", "GET", token=admin_token)
print(f"Commander /dashboard/high-risk status: {st}, Count: {len(high_risk) if isinstance(high_risk, list) else high_risk}")
if isinstance(recent, list):
    found_recent = any(r.get("personnel_id") == pid for r in recent)
    print(f"Newly submitted assessment visible in Commander Recent Assessments: {found_recent}")
