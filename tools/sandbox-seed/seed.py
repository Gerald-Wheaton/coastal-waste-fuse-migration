#!/usr/bin/env python3
"""Seed Gerald's Limble sandbox with the Step 1 test fixtures (OQ-028).

Reads ENCODED_AUTH (base64 client_id:secret) from the repo .env — never prints it.
Idempotent: every create is preceded by a lookup; existing fixtures are reused.
Endpoints that turn out not to exist (404/405) become UI-checklist lines instead
of failures.

Usage:
  python3 tools/sandbox-seed/seed.py                 # seed everything it can
  python3 tools/sandbox-seed/seed.py --template-id N # also create scenario tasks from template N
  python3 tools/sandbox-seed/seed.py --verify TASKID # dump task state (meta1, statusID, comments)
"""

import argparse
import base64
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

BASE = "https://api.limblecmms.com/v2"
LOCATION_ID = 98472
LOCATION_NAME = "Coastal 99 - Sandbox Test"
SM_FIRST = "Site Manager"
SM_LAST = "Sandbox NinetyNine"
SM_EMAIL = "gerald+sm99@fm360consulting.com"
STATUSES_NEEDED = ["PO Create", "PO Requested"]
TRIGGER_COMMENT = "Status was changed from Open to PO Create"

# Scenario tasks (plan: scenario matrix). Instruction responses are set per
# scenario where the API allows; otherwise they land on the UI checklist.
SCENARIOS = [
    {"key": "s1-happy-gt500-capex", "desc": "TEST scenario 1 happy path @CoupaWO;"},
    {"key": "s2-le500", "desc": "TEST scenario 2 amount<=500 @CoupaWO;"},
    {"key": "s3-capex-no", "desc": "TEST scenario 3 capex no @CoupaWO;"},
    {"key": "s4-ampersand-contractor", "desc": "TEST scenario 4 ampersand @CoupaWO;"},
    {"key": "s5-fail-supplier", "desc": "TEST scenario 5 FAIL-SUPPLIER @CoupaWO;"},
    {"key": "s6a-fail-user", "desc": "TEST scenario 6a FAIL-USER @CoupaWO;"},
    {"key": "s6b-fail-addr", "desc": "TEST scenario 6b FAIL-ADDR @CoupaWO;"},
    {"key": "s6c-fail-acct", "desc": "TEST scenario 6c FAIL-ACCT @CoupaWO;"},
    {"key": "s7-fail-createreq", "desc": "TEST scenario 7 FAIL-CREATEREQ @CoupaWO;"},
]

checklist = []


def load_auth():
    env = Path(__file__).resolve().parents[2] / ".env"
    for line in env.read_text().splitlines():
        if line.strip().startswith("ENCODED_AUTH"):
            val = line.split("=", 1)[1].strip().strip('"').strip("'")
            # sanity: must be decodable base64, never echoed
            base64.b64decode(val)
            return val
    sys.exit("ENCODED_AUTH not found in .env")


AUTH = None


def call(method, path, params=None, body=None):
    """Returns (status_code, parsed_json_or_None). Never raises on HTTP errors."""
    url = BASE + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", "Basic " + AUTH)
    req.add_header("Content-Type", "application/json")
    # Limble's WAF 403s the default Python-urllib user agent
    req.add_header("User-Agent", "coastal-oq028-seeder/1.0")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read()
            return resp.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            parsed = json.loads(raw) if raw else None
        except ValueError:
            parsed = raw.decode(errors="replace")[:300]
        return e.code, parsed
    except urllib.error.URLError as e:
        sys.exit(f"network error calling {method} {path}: {e.reason}")


def note(item):
    checklist.append(item)
    print(f"  [UI CHECKLIST] {item}")


def verify_location():
    print(f"== Location {LOCATION_ID}")
    code, body = call("GET", "/locations/", {"locations": LOCATION_ID, "limit": 10})
    rows = body if isinstance(body, list) else []
    match = [r for r in rows if r.get("locationID") == LOCATION_ID]
    if not match:
        sys.exit(f"location {LOCATION_ID} not found (HTTP {code}) — was it created?")
    name = match[0].get("name", "")
    if name != LOCATION_NAME:
        sys.exit(f'location {LOCATION_ID} is named "{name}", expected "{LOCATION_NAME}" — rename it')
    print(f'  ok: "{name}"')


def ensure_statuses():
    print("== Statuses")
    # recon: GET /statuses is unreliable (returns only "In Progress"), so a miss
    # here does not prove absence — attempt create, fall back to checklist.
    code, body = call("GET", "/statuses/", {"limit": 100})
    existing = {s.get("name", "").strip(): s.get("statusID") for s in body} if isinstance(body, list) else {}
    ids = {}
    for name in STATUSES_NEEDED:
        if name in existing:
            ids[name] = existing[name]
            print(f'  exists: "{name}" (statusID {existing[name]})')
            continue
        code, body = call("POST", "/statuses/", body={"name": name})
        if code in (200, 201) and isinstance(body, (dict, list)):
            row = body[0] if isinstance(body, list) else body
            ids[name] = row.get("statusID")
            print(f'  created: "{name}" (statusID {ids[name]})')
        else:
            note(f'Create status "{name}" in Limble UI (API said HTTP {code}). '
                 f"Exact spelling matters — Step 1 looks it up by name.")
    return ids


def ensure_site_manager():
    print("== Site Manager user")
    code, body = call("GET", "/users/", {"limit": 500})
    users = body if isinstance(body, list) else []
    for u in users:
        if u.get("firstName") == SM_FIRST and u.get("email") == SM_EMAIL:
            print(f"  exists: userID {u.get('userID')}")
            return u.get("userID")
    payload = {
        "firstName": SM_FIRST,
        "lastName": SM_LAST,
        "email": SM_EMAIL,
        "locationID": LOCATION_ID,
        "roleID": 37676,  # "View Only" (GET /roles, this sandbox)
    }
    code, body = call("POST", "/users/", body=payload)
    if code in (200, 201):
        row = body[0] if isinstance(body, list) else body
        uid = (row or {}).get("userID")
        print(f"  created: userID {uid}")
        return uid
    note(f"Create user in UI: firstName '{SM_FIRST}', lastName '{SM_LAST}', email {SM_EMAIL}, "
         f'role "View Only" at "{LOCATION_NAME}", active (API said HTTP {code}).')
    return None


EXPECTED_INSTRUCTIONS = [
    "Describe the Work that Needs to be Done",
    "Is this a Capex Work Order?",
    "Select the Contractor who will Complete the Work",
    ("Insert Estimated Dollar Amount for Work (Amount from Quote, if Applicable). "
     "NOTE: Set to $500 if Estimate is Less than $500"),
    "Upload the Contractor's Quote Here for Coupa",  # must be 5th (1-indexed)
    "Select Which Type of Capex Work This Is",
]


def verify_template_task(task_id):
    """Verify a task spawned from the template carries the load-bearing instructions."""
    code, body = call("GET", f"/tasks/{task_id}/instructions", {"limit": 100})
    if code != 200 or not isinstance(body, list):
        note(f"Could not list instructions for task {task_id} (HTTP {code}) — verify template in UI.")
        return
    texts = [str(i.get("instruction", "")).strip() for i in body]
    import re
    plain = [re.sub(r"<[^>]+>", "", t) for t in texts]
    problems = []
    for want in EXPECTED_INSTRUCTIONS:
        if want not in plain:
            problems.append(f'missing instruction: "{want[:60]}..."' if len(want) > 60 else f'missing instruction: "{want}"')
    if len(plain) < 5 or plain[4] != "Upload the Contractor's Quote Here for Coupa":
        got = plain[4] if len(plain) >= 5 else "(fewer than 5 instructions)"
        problems.append(f'position 5 must be the quote-upload instruction, got: "{got}"')
    if problems:
        for p in problems:
            note(f"Template problem (task {task_id}): {p}")
    else:
        print(f"  template instructions verified on task {task_id} ({len(plain)} instructions, quote at position 5)")


def find_task_by_name(name):
    code, body = call("GET", "/tasks/", {"locations": LOCATION_ID, "limit": 200, "status": 0})
    for t in (body if isinstance(body, list) else []):
        if t.get("name") == name:
            return t
    return None


def create_scenario_tasks(template_id, status_ids):
    print("== Scenario tasks")
    po_create_id = status_ids.get("PO Create")
    created = {}
    for sc in SCENARIOS:
        name = f"TEST Step1 {sc['key']}"
        existing = find_task_by_name(name)
        if existing:
            created[sc["key"]] = existing.get("taskID")
            print(f"  exists: {name} (taskID {existing.get('taskID')})")
            continue
        payload = {
            "name": name,
            "type": 2,
            "locationID": LOCATION_ID,
            "templateID": str(template_id),
            "description": sc["desc"],
            "due": int(time.time()) + 7 * 86400,
            "priority": 2,
        }
        code, body = call("POST", "/tasks/", body=payload)
        if code not in (200, 201):
            note(f"Create task '{name}' from template {template_id} in UI (API said HTTP {code}).")
            continue
        row = body[0] if isinstance(body, list) else body
        task_id = (row or {}).get("taskID")
        created[sc["key"]] = task_id
        print(f"  created: {name} (taskID {task_id})")
        if po_create_id:
            code, _ = call("PATCH", f"/tasks/{task_id}", body={"statusID": po_create_id})
            if code not in (200, 201):
                note(f'Set task {task_id} status to "PO Create" in UI (PATCH said HTTP {code}).')
        else:
            note(f'Set task {task_id} status to "PO Create" in UI (status not created via API).')
        code, _ = call("POST", f"/tasks/{task_id}/comments",
                       body={"comment": TRIGGER_COMMENT, "showExternalUsers": False})
        if code not in (200, 201):
            note(f"Post trigger comment on task {task_id} in UI (or flip status away and back to "
                 f'"PO Create" to auto-generate it) — API said HTTP {code}.')
    if created:
        verify_template_task(next(iter(created.values())))
        note("Fill instruction responses per scenario in UI (capex option, contractor, dollar "
             "amount, description) and upload a quote file at instruction 5 for scenario s1 — "
             "see README.md scenario table.")
    return created


def verify_task(task_id):
    code, body = call("GET", "/tasks/", {"tasks": task_id, "limit": 1})
    print(json.dumps(body, indent=2)[:2000])
    code, body = call("GET", f"/tasks/{task_id}/comments", {"limit": 50})
    print(json.dumps(body, indent=2)[:3000])


def main():
    global AUTH
    ap = argparse.ArgumentParser()
    ap.add_argument("--template-id", type=int, help="sandbox template ID to spawn scenario tasks from")
    ap.add_argument("--verify", type=int, metavar="TASKID", help="dump task state and exit")
    args = ap.parse_args()
    AUTH = load_auth()

    if args.verify:
        verify_task(args.verify)
        return

    verify_location()
    status_ids = ensure_statuses()
    ensure_site_manager()
    if args.template_id:
        created = create_scenario_tasks(args.template_id, status_ids)
        print("\n== Created task IDs")
        for k, v in created.items():
            print(f"  {k}: {v}")
    else:
        note("Create the 17-instruction template in the UI (see README.md), then re-run with "
             "--template-id <ID> to spawn the scenario tasks.")

    if checklist:
        print("\n== REMAINING UI CHECKLIST")
        for i, item in enumerate(checklist, 1):
            print(f"  {i}. {item}")
    else:
        print("\nAll fixtures seeded via API — no UI steps remaining.")


if __name__ == "__main__":
    main()
