#!/usr/bin/env python3
"""Extended Limble sandbox seeder — DESIGN ARTIFACT (not run this session).

Extends the Step-1-only seeder at tools/sandbox-seed/seed.py to cover the fixtures
the OTHER six workflows need (Step 2, Step 3, EHS-Create, EHS-Update). See the plan
in docs/test-plan/limble-sandbox-fixtures.md.

DESIGN STATUS
  This is a well-commented skeleton mirroring the base seeder's style. It is NOT
  executed in the design phase and CANNOT run here: this clone has no .env
  (ENCODED_AUTH) and no Limble MCP (both git-ignored, absent). It is safe to run
  ONLY once the owner restores the sandbox credential and only against Gerald's
  Limble SANDBOX. It performs NO Coupa/EHS calls (those stay mocked).

REUSE (do not re-implement — imported from the base seeder):
  base.call            authenticated HTTP w/ WAF-safe User-Agent, never raises on 4xx/5xx
  base.note            append a UI-checklist line and print it
  base.load_auth       read ENCODED_AUTH from repo .env (never printed)
  base.find_task_by_name / base.verify_task / base.verify_template_task
  base.LOCATION_ID (98472), base.LOCATION_NAME, base.SM_* , base.EXPECTED_INSTRUCTIONS
  base.ensure_statuses/ensure_site_manager/verify_location  (baseline re-verify)

WHAT THIS ADDS (all idempotent: lookup-before-create, API-attempt then UI fallback):
  ensure_status(name)                    -> a single extra status ("PO Approved")
  stamp_meta(task_id, meta1, meta2)       -> PATCH metadata.meta1/meta2 (+ verify)
  set_status_by_name(task_id, name)       -> flip a task to a named status
  set_assignment(task_id, kind, ref_id)   -> assign task to a team or user
  complete_task(task_id, notes)           -> mark complete + completion notes
  ensure_ehs_team(location_id)            -> "EHS Approver Assignee" team @ location
  verify_region_allowlisted(loc, allow)   -> read location's region, checklist if not in allowlist
  seed_step2_fixtures()                   -> tasks in PO Requested (team & user assigned)
  seed_step3_fixtures()                   -> completed CoupaWO tasks w/ meta1+meta2 (+/- invoice)
  seed_ehs_update_parent()                -> completed @EHSWO; parent (+ child-WO UI checklist)
  reset_chain_task(task_id)               -> return a chained task to PO Create, clear meta

Usage (future, with .env restored):
  python3 docs/test-plan/seed/seed_ext.py --reverify           # re-verify OQ-028 baseline
  python3 docs/test-plan/seed/seed_ext.py --step2              # seed Step 2 inputs
  python3 docs/test-plan/seed/seed_ext.py --step3              # seed Step 3 inputs
  python3 docs/test-plan/seed/seed_ext.py --ehs                # EHS team/region/template checklist + EHS-Update parent
  python3 docs/test-plan/seed/seed_ext.py --all
  python3 docs/test-plan/seed/seed_ext.py --reset 4052         # reset a chained task
"""

import argparse
import sys
from pathlib import Path

# --- import & reuse the base Step-1 seeder ---------------------------------
BASE_DIR = Path(__file__).resolve().parents[2] / "tools" / "sandbox-seed"
sys.path.insert(0, str(BASE_DIR))
import seed as base  # noqa: E402  (tools/sandbox-seed/seed.py)

# --- config for the NEW fixtures -------------------------------------------
LOCATION_ID = base.LOCATION_ID                      # 98472 "Coastal 99 - Sandbox Test"
PO_APPROVED = "PO Approved"                          # Step 2 flip target (exact spelling, OQ-025)
EHS_TEAM_NAME = "EHS Approver Assignee"              # EHS-Create listTeams lookup
REGION_ALLOWLIST = [                                 # EHS-Create region guard (OQ-034)
    "Central Florida", "Southwest Florida",
    "Coastal Materials Management", "South Florida", "South Atlantic",
]
REGION_TARGET = "South Florida"                      # the one we want on the sandbox location

# EHS-Update parent: description MUST contain @EHSWO; (NOT the @EHS; that EHS-Create writes;
# see the tag-divergence flag §2a in the plan). meta1 must equal the RowUID the EHS mock returns.
# COORDINATED with the concurrent EHS mock (docs/test-plan/fixtures/ehs/): the mock defines a
# dedicated update inspection keyed EHS-INSP-UPD-1 (in ehs-inspection-fetch.json), and its trigger
# payload update-inspection-webhook.json (scenario U1) expects a parent WO tagged @EHSWO; with
# meta1=EHS-INSP-UPD-1 and 2 completed child WOs. This parent task's Limble taskID must be written
# back into that webhook fixture (the worker used a placeholder), so fire.sh replays the right id.
EHS_UPDATE_PARENT_NAME = "TEST EHSUpdate parent"
EHS_UPDATE_PARENT_DESC = "TEST EHS-Update completed parent @EHSWO;"
EHS_MOCK_ROWUID = "EHS-INSP-UPD-1"                   # matches docs/test-plan/fixtures/ehs/ehs-inspection-fetch.json
EHS_UPDATE_COMPLETION_NOTES = "Deficiency remediated in sandbox test. Verified complete."

# Step 2 / Step 3 fixtures reuse the existing 405x scenario tasks where possible.
STEP2_TEAM_TASK = 4052    # happy-path task; team-assign for Step 2 team branch (also chains from Step 1)
STEP2_USER_TASK = 4053    # user-assign for Step 2 user branch
STEP3_INVOICE_TASK = 4052 # chain from Step 2; complete WITH an invoice file (UI)
STEP3_NOINVOICE_TASK = 4054  # complete WITHOUT an invoice file
DUMMY_REQ_ID = "424242"   # matches the OQ-028 mock's deterministic create-req id
DUMMY_PO_ID = "515151"    # any non-empty PO id; the Coupa GET is mocked


# ---------------------------------------------------------------------------
# Status (single) — generalises base.ensure_statuses for one extra name
# ---------------------------------------------------------------------------
def ensure_status(name):
    """Ensure one status exists (exact spelling). API attempt -> UI checklist fallback."""
    print(f"== Status {name!r}")
    code, body = base.call("GET", "/statuses/", {"limit": 100})
    existing = {s.get("name", "").strip(): s.get("statusID")
                for s in body} if isinstance(body, list) else {}
    if name in existing:
        print(f'  exists: "{name}" (statusID {existing[name]})')
        return existing[name]
    code, body = base.call("POST", "/statuses/", body={"name": name})
    if code in (200, 201) and isinstance(body, (dict, list)):
        row = body[0] if isinstance(body, list) else body
        sid = row.get("statusID")
        print(f'  created: "{name}" (statusID {sid})')
        return sid
    base.note(f'Create status "{name}" in Limble UI (API said HTTP {code}). '
              f"Exact spelling matters — the workflow looks it up by %name%.")
    return None


# ---------------------------------------------------------------------------
# Task mutators (used to build Step 2 / Step 3 / EHS-Update states)
# ---------------------------------------------------------------------------
def stamp_meta(task_id, meta1=None, meta2=None):
    """PATCH metadata.meta1/meta2, then GET to verify it surfaces.

    updateATask (what Step 1/2 use) writes metadata.meta*; the same PATCH shape is
    assumed here. meta1=424242 was confirmed surfacing via GET in the OQ-028 run, so
    verify-after-write is meaningful. If the tasks API rejects a direct metadata PATCH,
    fall back to producing meta by RUNNING Step 1/Step 2 (chain approach A) — flagged, not
    silently ignored.
    """
    meta = {}
    if meta1 is not None:
        meta["meta1"] = meta1
    if meta2 is not None:
        meta["meta2"] = meta2
    print(f"== Stamp meta on task {task_id}: {meta}")
    code, _ = base.call("PATCH", f"/tasks/{task_id}", body={"metadata": meta})
    if code not in (200, 201):
        base.note(f"Set {meta} on task {task_id} via UI or by running the upstream workflow "
                  f"(PATCH metadata said HTTP {code} — direct metadata write may be unsupported).")
        return
    # verify it actually surfaces on GET (the OQ-024 concern)
    code, body = base.call("GET", "/tasks/", {"tasks": task_id, "limit": 1})
    row = (body[0] if isinstance(body, list) and body else {}) or {}
    got1, got2 = row.get("meta1"), row.get("meta2")
    ok = (meta1 is None or str(got1) == str(meta1)) and (meta2 is None or str(got2) == str(meta2))
    print(f"  {'ok' if ok else 'MISMATCH'}: GET returns meta1={got1!r} meta2={got2!r}")
    if not ok:
        base.note(f"meta on task {task_id} did not surface as written (got meta1={got1}, "
                  f"meta2={got2}) — verify the tasks-API metadata contract (OQ-024).")


def set_status_by_name(task_id, status_name, status_id=None):
    """Flip a task to a named status (PATCH statusID). Looks up the id if not given."""
    if status_id is None:
        code, body = base.call("GET", "/statuses/", {"name": f"%{status_name}%", "limit": 1})
        rows = body if isinstance(body, list) else []
        status_id = rows[0].get("statusID") if rows else None
    if not status_id:
        base.note(f'Set task {task_id} status to "{status_name}" in UI '
                  f"(status id not resolvable via API).")
        return
    code, _ = base.call("PATCH", f"/tasks/{task_id}", body={"statusID": status_id})
    if code not in (200, 201):
        base.note(f'Set task {task_id} status to "{status_name}" in UI (PATCH said HTTP {code}).')
    else:
        print(f'  task {task_id} -> "{status_name}" (statusID {status_id})')


def set_assignment(task_id, kind, ref_id):
    """Assign a task to a team or user so Step 2 exercises both comment branches.

    Mirrors EHS-Create's createATask assignment shape: assignmentType + assignment.
    """
    assert kind in ("team", "user")
    print(f"== Assign task {task_id} -> {kind} {ref_id}")
    code, _ = base.call("PATCH", f"/tasks/{task_id}",
                        body={"assignmentType": kind, "assignment": ref_id})
    if code not in (200, 201):
        base.note(f"Assign task {task_id} to {kind} {ref_id} in UI (PATCH said HTTP {code}).")
    else:
        print(f"  ok")


def complete_task(task_id, notes):
    """Mark a task complete with completion notes (Step 3 / EHS-Update need dateCompleted +
    completionNotes on the task). API attempt -> UI fallback."""
    print(f"== Complete task {task_id}")
    # Exact completion field names are unverified (OQ-009); try the common shape, else UI.
    code, _ = base.call("PATCH", f"/tasks/{task_id}",
                        body={"statusID": 2, "completionNotes": notes})  # 2 = "Complete" (prod)
    if code not in (200, 201):
        base.note(f'Complete task {task_id} in the UI and type completion notes: "{notes}" '
                  f"(PATCH said HTTP {code}; the completion field names are unverified — OQ-009).")
    else:
        print("  ok (verify dateCompleted + completionNotes surface via GET before firing)")


# ---------------------------------------------------------------------------
# EHS-Create fixtures: team + region on the shared sandbox location
# ---------------------------------------------------------------------------
def ensure_ehs_team(location_id=LOCATION_ID):
    """Ensure team "EHS Approver Assignee" exists at the location (EHS-Create listTeams
    filter is team.locationID == locationID). Teams are often admin-UI-only -> checklist."""
    print(f"== Team {EHS_TEAM_NAME!r} @ location {location_id}")
    code, body = base.call("GET", "/teams/", {"name": f"{EHS_TEAM_NAME}", "limit": 500})
    teams = body if isinstance(body, list) else []
    match = [t for t in teams if t.get("locationID") == location_id]
    if match:
        print(f"  exists: teamID {match[0].get('teamID')}")
        return match[0].get("teamID")
    code, body = base.call("POST", "/teams/",
                          body={"name": EHS_TEAM_NAME, "locationID": location_id})
    if code in (200, 201):
        row = body[0] if isinstance(body, list) else body
        print(f"  created: teamID {(row or {}).get('teamID')}")
        return (row or {}).get("teamID")
    base.note(f'Create team "{EHS_TEAM_NAME}" at location {location_id} ("{base.LOCATION_NAME}") '
              f"in the Limble UI (API said HTTP {code}; teams are typically admin-UI only).")
    return None


def verify_region_allowlisted(location_id=LOCATION_ID, allow=REGION_ALLOWLIST):
    """Read the location's region and confirm its name is in the EHS-Create allowlist.

    Region create/assignment is an admin-UI operation — this only VERIFIES and emits a
    checklist line if the location's region isn't allowlisted.
    """
    print(f"== Region check for location {location_id}")
    code, body = base.call("GET", "/locations/", {"locations": location_id, "limit": 1})
    loc = (body[0] if isinstance(body, list) and body else {}) or {}
    region_id = loc.get("regionID")
    if not region_id:
        base.note(f'Assign location {location_id} to a Region named "{REGION_TARGET}" in the '
                  f"Limble UI (location currently has no regionID; EHS-Create needs an "
                  f"allowlisted region).")
        return
    code, body = base.call("GET", "/regions/", {"regions": region_id, "limit": 1})
    reg = (body[0] if isinstance(body, list) and body else {}) or {}
    name = reg.get("regionName") or reg.get("name")
    if name in allow:
        print(f'  ok: region "{name}" (regionID {region_id}) is allowlisted')
    else:
        base.note(f'Location {location_id} region is "{name}" (not in EHS-Create allowlist). '
                  f'Set it to "{REGION_TARGET}" in the Limble UI, or the region guard drops it.')


# ---------------------------------------------------------------------------
# Per-workflow fixture builders
# ---------------------------------------------------------------------------
def seed_step2_fixtures():
    """Step 2 reads all tasks in "PO Requested" that carry meta1 + @CoupaWO;.
    Cover both router branches: one team-assigned, one user-assigned. (An unassigned
    PO-Requested task covers the 'neither' no-comment branch — reuse any other 405x.)"""
    print("\n### Step 2 fixtures")
    # Team branch: reuse the happy-path chain task (4052). If Step 1 already ran, meta1 is
    # stamped and it's already PO Requested; stamp_meta/set_status are idempotent.
    team_id = ensure_ehs_team()  # reuse the sandbox team as an assignable team (any team works)
    stamp_meta(STEP2_TEAM_TASK, meta1=DUMMY_REQ_ID)
    if team_id:
        set_assignment(STEP2_TEAM_TASK, "team", team_id)
    set_status_by_name(STEP2_TEAM_TASK, "PO Requested")

    # User branch: reuse 4053, assign to the sandbox Site Manager user.
    sm_uid = base.ensure_site_manager()
    stamp_meta(STEP2_USER_TASK, meta1=DUMMY_REQ_ID)
    if sm_uid:
        set_assignment(STEP2_USER_TASK, "user", sm_uid)
    set_status_by_name(STEP2_USER_TASK, "PO Requested")

    base.note("Step 2 calls Coupa (GET requisition / GET purchase_orders) — the Coupa MOCK must "
              "be redeployed (torn down 2026-07-06) or Step 2 will fail at the Coupa calls.")
    base.note('Step 2 flips to "PO Approved" — ensure that status exists (run --step2 which calls '
              "ensure_status, or the UI).")


def seed_step3_fixtures():
    """Step 3 reads a COMPLETED @CoupaWO; task with meta1 AND meta2, and its instructions
    (Upload Invoice Here -> response link). Two tasks: invoice present / absent."""
    print("\n### Step 3 fixtures")
    # Invoice-present: chain from Step 2 (4052 already has meta1); add meta2, upload invoice, complete.
    stamp_meta(STEP3_INVOICE_TASK, meta1=DUMMY_REQ_ID, meta2=DUMMY_PO_ID)
    base.note(f'Upload any PDF to the "Upload Invoice Here" instruction on task '
              f"{STEP3_INVOICE_TASK} in the UI (invoice-present route).")
    complete_task(STEP3_INVOICE_TASK, "Sandbox invoice uploaded; work complete.")

    # No-invoice: 4054, meta1+meta2, complete, NO invoice file (else route).
    stamp_meta(STEP3_NOINVOICE_TASK, meta1=DUMMY_REQ_ID, meta2=DUMMY_PO_ID)
    complete_task(STEP3_NOINVOICE_TASK, "Sandbox no-invoice route; work complete.")

    base.note("Step 3 calls Coupa (GET PO by id, attach, comment) — Coupa MOCK must be redeployed.")


def seed_ehs_create_fixtures():
    """EHS-Create WRITES tasks into Limble; per site that reaches createATask it needs a matching
    Limble location + an allowlisted region on it + an "EHS Approver Assignee" team + the EHS
    template. No input task to seed; verify the created WO(s) after a run.

    CROSS-WORKER MISMATCH (see plan §EHS-Create coordination): the concurrent EHS mock under
    docs/test-plan/fixtures/ehs/ drives 6 sites to createATask (Coastal 10 / 12 / 23-Miami Hauling
    East / 24-Lake Worth Hauling / 30 / and "Corporate Office" from the no-digit passthrough) —
    NONE of which is the sandbox's only location "Coastal 99" (98472). As-is, every listLocations
    lookup misses and (EHS-Create has no error handling) the run likely halts. Resolve one of two
    ways with the EHS-mock worker + owner BEFORE testing EHS-Create:
      (A) MINIMAL (recommended): retarget exactly ONE mock inspection's hierarchy Title so it maps
          to the existing "Coastal 99" location (e.g. Title "99 Sandbox" -> EHSLimbleLocationMapping
          -> "Coastal 99"), and make the other inspections drop BEFORE listLocations (acceptable
          last answer, or wrong QuestionsSelector — the mock already does this for BE-40/BE-50).
          Then only location 98472 is needed on the Limble side.
      (B) FULL COVERAGE: seed all 6 mapped locations in the sandbox, each with an allowlisted region
          and an "EHS Approver Assignee" team, to exercise the special-case mappings + image path.
          Heavier; only if branch coverage of EHSLimbleLocationMapping is wanted in-sandbox.
    """
    print("\n### EHS-Create fixtures (workflow CREATES the task; seed its inputs)")
    verify_region_allowlisted()          # for the location(s) that will reach createATask
    ensure_ehs_team()                    # "EHS Approver Assignee" at each such location
    base.note("Create the EHS deficiency TEMPLATE (prod-842 analog) in the Limble UI with these "
              "instructions VERBATIM: (1) \"Work that Needs to be Done (from the EHS Inspection)\" "
              "and (2) a \"generate child WO\" button instruction (for EHS-Update's child structure). "
              "Record its templateID.")
    base.note("Point the built EHS-Create workflow's createATask templateID (\"842\") at the sandbox "
              "template ID for the test run (config swap, like the Coupa base-URL swap).")
    base.note("COORDINATE with the EHS mock (docs/test-plan/fixtures/ehs/): its AuditInspection/list "
              "+ hierarchy-fetch drive sites Coastal 10/12/23/24/30/'Corporate Office' — none is the "
              "sandbox 'Coastal 99' (98472). Either retarget one mock inspection to map to Coastal 99 "
              "(minimal, recommended) or seed the 6 mapped locations. See plan §EHS-Create.")


def seed_ehs_update_parent():
    """EHS-Update reads a COMPLETED @EHSWO; parent task with meta1 = EHS inspection RowUID and
    completionNotes. Description MUST contain @EHSWO; (NOT @EHS; — tag-divergence flag §2a)."""
    print("\n### EHS-Update fixture (completed @EHSWO; parent)")
    existing = base.find_task_by_name(EHS_UPDATE_PARENT_NAME)
    if existing:
        task_id = existing.get("taskID")
        print(f"  exists: {EHS_UPDATE_PARENT_NAME} (taskID {task_id})")
    else:
        payload = {
            "name": EHS_UPDATE_PARENT_NAME,
            "type": 2,
            "locationID": LOCATION_ID,
            "description": EHS_UPDATE_PARENT_DESC,   # contains @EHSWO;
            "priority": 2,
        }
        code, body = base.call("POST", "/tasks/", body=payload)
        if code not in (200, 201):
            base.note(f"Create task '{EHS_UPDATE_PARENT_NAME}' in the UI with description "
                      f"containing '@EHSWO;' (API said HTTP {code}).")
            return
        row = body[0] if isinstance(body, list) else body
        task_id = (row or {}).get("taskID")
        print(f"  created: taskID {task_id}")

    # meta1 = the EHS inspection RowUID the mock recognises on AuditInspection/fetch|update.
    stamp_meta(task_id, meta1=EHS_MOCK_ROWUID)
    complete_task(task_id, EHS_UPDATE_COMPLETION_NOTES)
    base.note("Write this parent's taskID into docs/test-plan/fixtures/ehs/update-inspection-webhook.json "
              "(scenario U1's taskID) so fire.sh replays the right id to /webhook/coastal-ehs-update-inspection.")
    base.note("Mock scenario U1 expects 2 COMPLETED child WOs: on this parent, use the template's "
              "\"generate child WO\" button in the UI twice (each creates an instruction with "
              "meta.associatedTask), then complete each child with its own completion notes — "
              "exercises CoastalGetChildWONotes. If skipped, EHS-Update still runs with an empty "
              "child list (returns \"\") — a valid lighter fixture, but not the U1 scenario.")
    base.note(f"meta1={EHS_MOCK_ROWUID!r} matches docs/test-plan/fixtures/ehs/ehs-inspection-fetch.json.")


def reset_chain_task(task_id):
    """Return a chained task to "PO Create" with meta cleared, for a clean re-run of the
    Step 1->2->3 chain (mirrors the OQ-028 idempotency re-fire hygiene)."""
    print(f"== Reset chain task {task_id} -> PO Create, clear meta")
    stamp_meta(task_id, meta1="", meta2="")
    set_status_by_name(task_id, "PO Create")


# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--reverify", action="store_true", help="re-verify the OQ-028 baseline")
    ap.add_argument("--step2", action="store_true", help="seed Step 2 inputs (+ PO Approved status)")
    ap.add_argument("--step3", action="store_true", help="seed Step 3 inputs")
    ap.add_argument("--ehs", action="store_true", help="EHS-Create inputs checklist + EHS-Update parent")
    ap.add_argument("--all", action="store_true", help="everything")
    ap.add_argument("--reset", type=int, metavar="TASKID", help="reset a chained task to PO Create")
    args = ap.parse_args()

    base.AUTH = base.load_auth()  # sets the base module's global; base.call uses it

    if args.reset:
        reset_chain_task(args.reset)
    if args.reverify or args.all:
        base.verify_location()
        base.ensure_statuses()          # PO Create + PO Requested
        base.ensure_site_manager()
    if args.step2 or args.all:
        ensure_status(PO_APPROVED)
        seed_step2_fixtures()
    if args.step3 or args.all:
        seed_step3_fixtures()
    if args.ehs or args.all:
        seed_ehs_create_fixtures()
        seed_ehs_update_parent()

    if base.checklist:
        print("\n== REMAINING UI CHECKLIST")
        for i, item in enumerate(base.checklist, 1):
            print(f"  {i}. {item}")
    else:
        print("\nAll requested fixtures handled via API — no UI steps remaining.")


if __name__ == "__main__":
    main()
