# Handoff 8146 — Phase A: A4+A5 done; resume at A6 (OQ-042 gate) / A7 (2026-07-14)

## Goal

Finish Phase A pre-go-live tests for the Coastal Fuse→n8n migration per
`docs/test-plan/test-sequence.md` (mock Coupa/EHS + live Limble sandbox loc **98472 only**).
This session completed **A4 (Step 1)** and **A5 (Step 3)** — all scenarios PASS. Remaining:
**A6 EHS Create** (blocked on OQ-042), **A7 EHS Update**, **A8 wrap gates**. Do not re-derive
context: `CLAUDE.md`, `open-questions.md`, `DEPLOYMENT.md`, memory files
`project_step1_suite_results` (updated this session — covers A4+A5), `project_test_phase_state`,
`project_limble_create_task_api`, `project_limble_api_quirks`, `project_step2_suite_results`.

Supersedes `handoff-3572.md` (deleted). `handoff-6193.md` still holds Step-2 operational detail.
Instance = FM360 `7c939556-9600-431c-b688-dcd3e1a692ff` (multi-instance mode disabled → single
bound instance; verify by fetching a known workflow, `n8n_instances` errors).

## Current Progress

- **A4 Step 1 (`WJSs6apAdVH5yKkq`) COMPLETE** — s1–s8, idem, R1-user all PASS. R1-team deferred
  (OQ-040). Details + exec IDs in `docs/test-plan/test-sequence.md` §A4 (updated).
- **A5 Step 3 (`NH1giNups8iICMZe`) COMPLETE** — S3-1..S3-4 PASS incl. OQ-030 by-id proof.
  Details in test-sequence §A5 (updated).
- Both workflows **deactivated** after their suites; failMode reset `""`. Mock staging still in
  place: Step 1 (6 Coupa URLs→mock + admin 317887→398783, DEPLOYMENT §2), Step 3 (4 URLs→mock,
  DEPLOYMENT §4), plus earlier Step 2/Token-Regen staging (§3/§1).
- **New OQs:** **OQ-042** (see below — blocks A6). OQ-039/040/041 still open with owner.
- Error-log table `6GbR5Rxezl7hqk9i` holds test rows **16–22** (left for inspection — clear
  before any Error-Log-Export re-test). Capture table `eB9oFDjZNW9wkXrh` holds rows through ~83.
- Owner did UI fixture work on request: PDFs on 4054/4057/4060, amount→400 on 4055,
  "Upload Invoice Here" + PDF on 4053 (initial leading-quote typo — fixed).

## What Worked

- **Webhook-fired suites need no owner clicks**: temporarily `activateWorkflow` (owner approval
  REQUIRED per workflow — classifier + owner both enforce), fire prod `/webhook/` via curl,
  deactivate at suite end. Step 1 path `coastal-coupa-create-requisition-step1`, Step 3
  `coastal-coupa-wo-completed-step3`; payloads in `docs/test-plan/fixtures/coupa/webhook-payloads.json`.
- **Gate-reset trick**: Step 1 gates read the LATEST comment — post
  `"Status was changed from Open to PO Create"` on a task to make it fireable again (error runs
  append admin comments that break the gate).
- **Scratchpad helper** `limble.py` (scratchpad dir): comment/patch/get against sandbox tasks
  using repo `.env` `ENCODED_AUTH`. MUST send a `User-Agent` header or Cloudflare 403 (error 1010).
- Capture-table assertions via `id > <last-seen>` filters — mass-delete of capture rows is
  classifier-blocked, id-watermarks work fine.
- `meta2` IS API-writable (`patch 4055 meta2=555001`) — how S3-4 got its fixture.
- Error scenarios don't consume tasks (no flip, no meta1 write) → same task reusable across
  failModes with a comment re-post between runs.

## What Didn't Work (don't repeat)

- **`meta1` cannot be cleared via API** — PATCH rejects `""` ("not allowed to be empty") and
  `null` ("must be a string"). Tasks 4052/4053 are permanently consumed as Step-1 inputs.
- **No instruction-response write API (OQ-042)**: `PATCH /v2/instructions/{id}` → 404 (this is
  the endpoint the built EHS Create WO uses — it will 404 every run); `PATCH|PUT
  /tasks/{id}/instructions[/{iid}]` → 404; `POST /tasks/{id}/instructions` is create-only and
  rejects `response`. Instruction answers/files = owner UI only.
- Tasks with ZERO instructions (Step 2 seeder WOs, e.g. 4097) halt Step 3 at `Get Instructions`
  (0 items) — pick instruction-bearing fixtures.
- Step 3's invoice matcher is EXACT equality (`inst.instruction == "Upload Invoice Here"`) —
  a stray leading quote in the UI-entered name silently routed to the no-invoice branch.
- Mass deletes / activations get classifier-denied unless the owner names the target — ask first.

## Next Steps

1. **A6 EHS Create (`isLUx7cUjkmKggD2`) — gated on OQ-042** (owner investigating the real
   instruction-write endpoint in a separate chat). When resolved, apply THREE pre-fixes before
   any run: (a) `due` mapping `.toISO()` → epoch seconds (OQ-038 companion, memory
   `project_limble_create_task_api`); (b) description tag `@EHS;` → `@EHSWO;` (OQ-038);
   (c) instruction-update node → real endpoint (OQ-042). Then stage EHS URLs → mock-EHS, load
   A1–H fixture inspections, owner Execute click; expect 5 tasks (A1/B/C/D/E) per test-sequence §A6.
2. **A7 EHS Update (`8JvtesynrYtZbw7U`)** — can run before A6 if OQ-042 drags (owner offered no
   objection yet — confirm). Staging: EHS URLs → mock; seed parent WO (`@EHSWO;`,
   meta1=EHS-INSP-UPD-1, completed, 2 children) + non-EHS WO per `ehs-test-plan.md` §5.2;
   **ask owner before activating** the workflow.
3. **A8 wrap gates** (test-sequence §A8): clear error-log rows 16–22 + capture rows; teardown
   decision; doc debt (Step 2 build-spec §72/§203 metaN); chase owner decisions
   OQ-039/040/041 + the §A8 batch.
4. Cleanup note: task 4056 left assigned to user 398783 (R1-user test) — unassign at teardown
   or leave; error/capture rows per above.

## Guardrails (unchanged)

- Live Limble writes: sandbox loc 98472 fixtures only. No real Coupa/EHS calls (OQ-039 pending).
- Ask owner before EVERY workflow activation (per-workflow approval; approval for one does not
  carry to the next).
- Every test-only edit gets a DEPLOYMENT.md revert row at the moment it's made.
- 1:1 posture — no fixes beyond sanctioned list (OQ-001/OQ-022).
- n8n-MCP quota ~100 req/day; Limble MCP points at Coastal-PROD (useless for sandbox asserts —
  use `limble.py` / seeder read branch `/webhook/seed-limble-sandbox`).
