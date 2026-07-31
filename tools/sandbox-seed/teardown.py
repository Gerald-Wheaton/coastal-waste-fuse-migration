#!/usr/bin/env python3
"""Sandbox fixture teardown — ledger-driven, guarded deletes.

Staged 2026-07-27 during the [M] cutover-prep pass (run was blocked by the session's
permission classifier — script itself is ready). Ledger sources:
docs/test-plan/sandbox-seed-record-a6.md + DEPLOYMENT.md [M] teardown boxes +
test-sequence.md A7 block. Deletes ONLY explicitly ledgered IDs.

Guards:
  - Auth from repo .env ENCODED_AUTH (sandbox Basic cred) — never printed.
  - Every task is GET-verified to live at a fixture location before DELETE.
  - Already-gone objects are reported, not errors.
Order: tasks -> teams -> unassign location regions -> regions -> locations (probe).
Ends with a leftover sweep of loc 98472 + fixture locations.

Usage: python3 tools/sandbox-seed/teardown.py
"""
import base64
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

BASE = "https://api.limblecmms.com/v2"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
FIXTURE_LOCS = {98472, 98872, 98873, 98875, 98876, 98877, 98878}

TASKS = [4080, 4081, 4082, 4083, 4189, 4192, 4193, 4194, 4195, 4196,
         4198, 4199, 4200, 4201, 4202, 4213, 4218, 4220, 4222, 4223,
         4224, 4225, 4226, 4227, 4228, 4229, 4234, 4235, 4236, 4237, 4238]
TEAMS = [605957, 602734, 602735, 602736, 602737, 605550]
REGIONS = [7944, 7946, 7947, 7948, 7949, 7950]
LOCATIONS = [98872, 98873, 98875, 98876, 98877, 98878]  # owner-created; DELETE route unprobed


def load_auth():
    env = Path(__file__).resolve().parents[2] / ".env"
    for line in env.read_text().splitlines():
        if line.strip().startswith("ENCODED_AUTH"):
            val = line.split("=", 1)[1].strip().strip('"').strip("'")
            base64.b64decode(val)
            return val
    sys.exit("ENCODED_AUTH not found in .env")


AUTH = load_auth()


def call(method, path, body=None):
    req = urllib.request.Request(
        BASE + path,
        method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={
            "Authorization": "Basic " + AUTH,
            "User-Agent": UA,
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read().decode()
            try:
                return r.status, json.loads(raw) if raw else None
            except json.JSONDecodeError:
                return r.status, raw[:200]
    except urllib.error.HTTPError as e:
        raw = e.read().decode()[:200]
        return e.code, raw
    except Exception as e:  # noqa: BLE001
        return None, str(e)[:200]


results = []


def log(kind, oid, action, detail=""):
    line = f"{kind} {oid}: {action}" + (f" — {detail}" if detail else "")
    results.append(line)
    print(line, flush=True)


# ---- tasks ----
for tid in TASKS:
    st, body = call("GET", f"/tasks?tasks={tid}&limit=1")
    if st != 200:
        log("task", tid, "SKIP", f"lookup HTTP {st}")
        continue
    if not body:
        log("task", tid, "already gone")
        continue
    loc = body[0].get("locationID")
    if loc not in FIXTURE_LOCS:
        log("task", tid, "SKIP — GUARD", f"locationID {loc} not a fixture location")
        continue
    st, _ = call("DELETE", f"/tasks/{tid}")
    log("task", tid, "deleted" if st == 200 else f"DELETE HTTP {st}", f"loc {loc}")

# ---- teams ----
for tm in TEAMS:
    st, body = call("GET", f"/teams?teams={tm}&limit=1")
    if st == 200 and not body:
        log("team", tm, "already gone")
        continue
    if st == 200 and body and body[0].get("locationID") not in FIXTURE_LOCS:
        log("team", tm, "SKIP — GUARD", f"locationID {body[0].get('locationID')}")
        continue
    st, detail = call("DELETE", f"/teams/{tm}")
    log("team", tm, "deleted" if st == 200 else f"DELETE HTTP {st}", "" if st == 200 else str(detail))

# ---- unassign regions from locations, then delete regions ----
for lid in LOCATIONS:
    st, detail = call("PATCH", f"/locations/{lid}", {"regionID": 0})
    log("loc-region-unassign", lid, f"HTTP {st}", "" if st == 200 else str(detail))

for rid in REGIONS:
    st, detail = call("DELETE", f"/regions/{rid}")
    log("region", rid, "deleted" if st == 200 else f"DELETE HTTP {st}", "" if st == 200 else str(detail))

# ---- locations (route unprobed — expect possible 404/405) ----
for lid in LOCATIONS:
    st, detail = call("DELETE", f"/locations/{lid}")
    log("location", lid, "deleted" if st == 200 else f"DELETE HTTP {st}", "" if st == 200 else str(detail))

# ---- leftover sweep ----
print("\n=== leftover sweep ===", flush=True)
for lid in sorted(FIXTURE_LOCS):
    st, body = call("GET", f"/tasks?locations={lid}&limit=100")
    if st != 200:
        print(f"loc {lid}: sweep HTTP {st}", flush=True)
        continue
    if not body:
        print(f"loc {lid}: no tasks remain", flush=True)
        continue
    for t in body:
        print(f"loc {lid}: REMAINS task {t.get('taskID')} — {str(t.get('name'))[:60]!r}", flush=True)

print(f"\n{len(results)} operations logged.", flush=True)
