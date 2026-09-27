import urllib.request
import json
import uuid

BASE_URL = 'http://127.0.0.1:8000/api'

def post_json(endpoint, data, token=None):
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    req = urllib.request.Request(
        f'{BASE_URL}{endpoint}',
        data=json.dumps(data).encode('utf-8'),
        headers=headers
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode('utf-8'))

def patch_json(endpoint, data, token):
    headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {token}'}
    req = urllib.request.Request(
        f'{BASE_URL}{endpoint}',
        data=json.dumps(data).encode('utf-8'),
        headers=headers,
        method='PATCH'
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode('utf-8'))

def get_json(endpoint, token):
    headers = {'Authorization': f'Bearer {token}'}
    req = urllib.request.Request(
        f'{BASE_URL}{endpoint}',
        headers=headers
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode('utf-8'))

def run_tests():
    print('=== 1. COMMANDER LOGIN (officer_sharma) ===')
    cmd_token_data = post_json('/auth/login', {'username': 'officer_sharma', 'password': 'officer123'})
    cmd_token = cmd_token_data['access_token']
    print(f"Logged in as: {cmd_token_data['username']}, role: {cmd_token_data['role']}, battalion: {cmd_token_data['battalion']}")

    cmd_summary = get_json('/dashboard/summary', cmd_token)
    print(f"Commander Dashboard Summary: Total Personnel = {cmd_summary['total_personnel']}, Assessed = {cmd_summary['assessed_personnel']}")
    assert cmd_summary['total_personnel'] > 0, 'Total personnel should not be 0!'

    cmd_personnel = get_json('/personnel?page=1&size=5', cmd_token)
    print(f"Commander Personnel Roster items returned: {len(cmd_personnel['items'])} / Total: {cmd_personnel['total']}")
    assert cmd_personnel['total'] > 0, 'Commander should see personnel!'

    cmd_welfare = get_json('/welfare/requests', cmd_token)
    print(f"Commander Initial Welfare Requests count: {len(cmd_welfare)}")

    print('\n=== 2. JAWAN LOGIN (jawan_verma) ===')
    jwn_token_data = post_json('/auth/login', {'username': 'jawan_verma', 'password': 'jawan123'})
    jwn_token = jwn_token_data['access_token']
    jwn_id = jwn_token_data['personnel_id']
    print(f"Logged in as: {jwn_token_data['username']}, role: {jwn_token_data['role']}, linked personnel_id: {jwn_id}")

    # If jawan has an existing active request, resolve it as Commander first so a fresh SOS can be tested
    my_requests = get_json('/welfare/requests/my', jwn_token)
    for r in my_requests:
        if r['status'] in ['pending', 'acknowledged', 'in_progress']:
            print(f"Resolving previous active request #{r['id']} as commander...")
            patch_json(f"/welfare/requests/{r['id']}/status", {'status': 'resolved'}, cmd_token)

    print('\n=== 3. JAWAN SENDS WELFARE ALERT / SOS ===')
    sos_payload = {
        'category': 'Emergency SOS Support',
        'urgency': 'High',
        'message': 'Urgent welfare assistance requested via mobile SOS button from Leh outpost.'
    }
    sos_res = post_json('/welfare/requests', sos_payload, jwn_token)
    print(f"SOS Request created successfully! ID: {sos_res['id']}, Status: {sos_res['status']}, Urgency: {sos_res['urgency']}")

    print('\n=== 4. COMMANDER RECEIVES AND ACKNOWLEDGES WELFARE ALERT ===')
    cmd_welfare_after = get_json('/welfare/requests', cmd_token)
    matching_req = next((r for r in cmd_welfare_after if r['id'] == sos_res['id']), None)
    print(f"Matching SOS request found in Commander Dashboard: {matching_req is not None}")
    assert matching_req is not None, 'SOS alert must be visible to Commander!'
    print(f"Request Details: Personnel={matching_req['personnel_name']}, Code={matching_req['personnel_code']}, Category={matching_req['category']}, Status={matching_req['status']}")

    ack_res = patch_json(f"/welfare/requests/{sos_res['id']}/status", {'status': 'acknowledged'}, cmd_token)
    print(f"Commander successfully acknowledged SOS alert! New status: {ack_res['status']}")

    print('\n=== 5. JAWAN TAKES STRESS ASSESSMENT ===')
    assess_payload = {
        "duty_hours_per_week": 65.0,
        "night_shifts_per_month": 8,
        "consecutive_duty_days": 18,
        "leave_gap_days": 90,
        "operational_exposure": "High",
        "remote_posting": "Yes"
    }
    assess_res = post_json(f"/personnel/{jwn_id}/assess", assess_payload, jwn_token)
    assess_data = assess_res['assessment']
    print(f"Assessment recorded! Score: {assess_data['risk_score']}, Level: {assess_data['stress_level']}, Priority: {assess_data['risk_priority']}")

    print('\n=== 6. COMMANDER VIEWS UPDATED RECENT ASSESSMENTS ===')
    recent = get_json('/dashboard/recent-assessments?limit=5', cmd_token)
    print(f"Top Recent Assessment in Commander Dashboard: Personnel={recent[0]['personnel_name']}, Score={recent[0]['risk_score']}, Level={recent[0]['stress_level']}")
    assert recent[0]['personnel_id'] == jwn_id, 'Commander recent assessments should show latest Jawan assessment!'

    print('\n=== 7. JAWAN APP SELF-REGISTRATION TEST ===')
    uid = uuid.uuid4().hex[:6]
    new_jawan_data = {
        'username': f'cadet_{uid}',
        'password': 'CadetPassword123!',
        'personnel_code': f'CRPF-{uid.upper()}',
        'name': f'Cadet Vikram {uid.upper()}',
        'age': 24,
        'gender': 'Male',
        'department': 'Operations',
        'battalion': '7th Battalion',
        'location': 'Srinagar',
        'job_role': 'Rifleman',
        'experience_years': 2,
        'duty_hours_per_week': 48.0
    }
    reg_res = post_json('/auth/register-jawan', new_jawan_data)
    print(f"Self-registered new Jawan: {reg_res['username']}, Personnel ID: {reg_res['personnel_id']}")

    cmd_personnel_after = get_json(f'/personnel?battalion=7th+Battalion', cmd_token)
    registered_found = any(p['personnel_code'] == f'CRPF-{uid.upper()}' for p in cmd_personnel_after['items'])
    print(f"Newly registered Jawan appears in Commander Roster: {registered_found}")
    assert registered_found, 'Commander roster must display newly registered Jawan!'

    print('\n>>> ALL 7 INTEGRATION CHECKS PASSED PERFECTLY! <<<')

if __name__ == '__main__':
    run_tests()
