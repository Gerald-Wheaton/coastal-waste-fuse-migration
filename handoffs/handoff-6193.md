# Handoff 6193 — Coastal Step 2 test execution, mid-suite (2026-07-09)

## Goal

Run the mock-based Step 2 test suite against n8n workflow **`WYJyHdQGcdeD8wEr`** ("Update Limble
WO on New PRs (Step 2)"). Mocks stand in for Coupa; live Limble **sandbox loc 98472 only**.
Supersedes `handoff-4827.md` (its #1 seeder task is now DONE). Broader context: `CLAUDE.md`,
`open-questions.md`, and memory files `project_limble_create_task_api`,
`project_limble_api_quirks`, `project_test_phase_state` — **do not re-derive**.

## Instance (verified this session)

Correct n8n instance = `instanceId 7c939556-9600-431c-b688-dcd3e1a692ff` ("FM360"). All Coastal
workflows + mocks present. Confirm before any write.

## Current progress

### Seeder — DONE
`qyMChP0DKfI04r4a` write branch (path `/webhook/coastal-seed-step2`) finished: create (top-level
`meta1`) → PATCH (statusID). Read branch (path `/webhook/seed-limble-sandbox`) reports statuses +
tasks incl. meta1/meta2 — **use it to assert Limble DB state after each run.**

### Step 2 staging — DONE (all test-only edits + 2 sanctioned fixes)
See `DEPLOYMENT.md` §3 for the full revert-on-deploy list. Summary: 2 Coupa URLs → mock host,
10 Limble nodes → sandbox cred `MX0lwgfyFiGUBh5W`, mock token row seeded in `QAj62weJaWmRBJ76`
(`client=coastal_waste`/`MOCK-TOKEN-COUPA`), `Get Admin User` retargeted 317887 → sandbox **398783**.

### Bugs found + fixed in Step 2 write node (both sanctioned under OQ-024)
1. `metadata: { meta2 }` → **top-level `meta2`** (Limble rejects the `metadata` object).
2. `meta2: <number>` → **`String(...)`** (400 `` `meta2` must be a string ``).
Full API contract + why in memory `project_limble_create_task_api`. Step 1 (`WJSs6apAdVH5yKkq`
n32) was already correct; Step 3 (`NH1giNups8iICMZe`) has no metaN write. OQ-024 now `[resolved]`.

### S2-4 happy path — PASS (exec 126546, 2026-07-09)
WOs **4083** (our fixture) + **4053** (Step 1 leftover, both were PO-Requested + meta1) flipped to
status **8074 PO Approved**, `meta2="555001"`, desc appended `|| Coupa PO# PO-555001`, no comment
(neither-assigned), no error. Mock base URL `https://fm360.n8n.fm360consulting.com/webhook/mock-coupa`
CONFIRMED working.

## Key facts (don't rediscover)
- Sandbox task statuses (loc 98472, owner instance — NOT Coastal-prod IDs): Open 0, PO Create
  **8054**, PO Requested **8055**, PO Approved **8074**. Step 2 looks statuses up by name
  (`%PO Requested%`/`%PO Approved%`), so IDs self-resolve.
- Fixture task **4083** = the clean Step 2 input (now consumed/flipped to 8074).
- Dud seeder tasks **4080/4081/4082** (meta1 null → Step 2 gate skips them) — leave for teardown.
- failMode config table = `YkCIlyx7lUUNs7vG` (key=`default`); currently `""`. Mock endpoint failModes:
  `reqpending`, `getreq`, `getpo` (see Mock Coupa `F05TiUurpc2kqxe0` Build node).
- Step 2 error-log table = `6GbR5Rxezl7hqk9i`.
- Step 2 is **schedule-triggered** → owner clicks Execute; agent stages + asserts (can't fire
  headless via MCP).

## Next steps (in order)
1. **Idempotency** (owner re-runs now, failMode `""`): assert poll returns **0** WOs (4083/4053
   now at 8074, no longer 8055). Read exec + confirm no writes.
2. **Re-seed** a fresh PO-Requested fixture before the remaining scenarios (all current
   PO-Requested @CoupaWO WOs are consumed): fire seeder `/webhook/coastal-seed-step2` → new 8055 +
   meta1=424242 WO.
3. **S2-1** `failMode=reqpending` → Execute → WO untouched (requisition not ordered).
4. **Error paths** `failMode=getreq`, then `getpo` → Execute each → assert a row in
   `6GbR5Rxezl7hqk9i`; admin comment now safely posts to sandbox **398783** (not Brandon 317887).
5. Reset `failMode=""` when done.
6. **Deferred sub-decision:** S2-2/S2-3 (team/user assignment variants) need a team + user
   provisioned at 98472 — defer or provision. Neither-path already covered by S2-4.

## Watch out for
- n8n-MCP quota = 100 req/day (fresh-credits plan this session). If exhausted: app.n8n-mcp.com
  chat assistant (separate quota).
- `validate_workflow` reports 4 false-positive "Incorrect error output" errors on the `Err:` Set
  nodes — known, do NOT apply its fix (see `handoff-4827.md` / OQ-029).
- `patchNodeField` does NOT support array-index paths (`parameters.x[0].value`) — use `updateNode`
  with `updates: {"parameters.x": {...}}` to replace the whole object.

## Doc debt
- Step 2 build-spec (`docs/build-specs/coupa-check-prs-step2-build-spec.md` §72/§203) still says
  `metadata.metaN` — correct to top-level + `String()` to match the fixed workflow.
