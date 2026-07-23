# Handoff 4827 — Coastal Waste test-execution phase (2026-07-09)

## Goal

Two owner-authorized workstreams, in order:
1. **#2 (DONE)** Build the OQ-008/OQ-029 error-log subgraph into Step 2 (`WYJyHdQGcdeD8wEr`).
2. **#1 (IN PROGRESS, blocked)** Execute the mock-based test suites against the built n8n workflows, starting with **Step 2**. Mocks stand in for Coupa + EHS; the real **Limble sandbox (location 98472 only)** is exercised live.

Broader context, module-translation rules, persistence model, and constraints: see `CLAUDE.md` and `open-questions.md`. Do not re-derive.

## ⚠️ Verify first (instance identity)

The n8n-MCP was disconnected and reconnected onto a "fresh credits" plan mid-session. On reconnect, `n8n_health_check` returned a **different `instanceId`** (`7c939556-9600-431c-b688-dcd3e1a692ff`) than earlier in the session (`5ed5bdb1-5d20-44fa-8f26-05dd5b900562`), both named "FM360". **Before any write, confirm you're on the instance that actually holds the Coastal workflows** (`n8n_list_workflows`, look for `WYJyHdQGcdeD8wEr` etc. and the mocks). If it's a different instance, STOP and ask the owner — do not recreate anything. (Lesson already in CLAUDE.md: verify live instance, don't trust labels.)

## Current progress

### #2 — Step 2 error subgraph: COMPLETE
- Built into `WYJyHdQGcdeD8wEr` ("Update Limble WO on New PRs (Step 2)"), 16→26 nodes, mirrors Step 1 (`WJSs6apAdVH5yKkq`) §4.9 exactly.
- Full node list + rationale recorded in `open-questions.md` OQ-029 (now `[resolved]`) and `docs/build-specs/coupa-check-prs-step2-build-spec.md` §4.2 header.
- **Validation caveat (important):** `n8n_validate_workflow` reports 4 "Incorrect error output configuration" errors on the `Err:` Set nodes. These are a **known heuristic false-positive** on the converged-error fan-out (Err Set → Insert + Merge on `main[0]`). Step 1, the tested-passing reference, throws the identical 5 of the same type. **Do NOT apply the validator's suggested fix** (moving targets to the Set node's `main[1]` error output) — a Set node never fires its error output, so it would break the subgraph. Everything else validates clean (35 valid connections, 0 invalid, 49 expressions OK).

### #1 — Test execution: staging started, then blocked
State discovered (docs were stale — verify, don't trust names):
- Mocks + seeder are **active** (`F05TiUurpc2kqxe0` Coupa mock, `EBIzCJ0XJaJ5jUpp` EHS mock, `qyMChP0DKfI04r4a` "Seed Limble Sandbox").
- BUT: target workflow Coupa/EHS URLs were **never swapped** to the mocks; the mock token row was **never seeded**; **no suite had ever executed**; the "Seed Limble Sandbox" workflow is **read-only** (an inspector, not a writer); sandbox loc **98472 was completely bare** (0 tasks/teams/users).
- Started building a write seeder as a **second webhook branch** inside `qyMChP0DKfI04r4a` (path `/webhook/coastal-seed-step2`): nodes `Seed Step2 Webhook` → `Create Step2 WO (neither)` → `Respond Step2`, using sandbox cred `MX0lwgfyFiGUBh5W`. Fired it twice; each failure taught an API-shape fact (below). The `statusID` removal fix did **not** apply — that call hit the quota wall, so the create node still contains `statusID: 5782` and does not yet succeed. Branch is inert until fired; nothing broken.

### Scope decisions logged (owner, 2026-07-09) — see `open-questions.md` OQ-003 addendum (2026-07-09)
- n8n-MCP **write** access granted across all Coastal workflows/tables/mocks for the test phase.
- **Live Limble calls authorized, sandbox location 98472 ONLY** (reads + workflows' own writes). Coupa/EHS stay mocked; prod Limble off-limits; reverts at teardown.
- Schedule-triggered workflows can't be fired headless via MCP → **owner clicks "Execute Workflow" in the editor**; agent stages + asserts. Webhook-triggered (Step 1, Step 3, EHS Update, the seeder) can be driven via `n8n_test_workflow`.
- Sequencing: **Step 2 first**.

## What worked
- `n8n_update_partial_workflow` for surgical multi-op builds (Step 2 subgraph, seeder branch). Reliable. Include all nodes **and** their connections in one atomic call (it validates final state — disconnected nodes get rejected and rolled back).
- Error-output wiring via `addConnection` with `sourceOutput: "main", sourceIndex: 1`.
- Firing the webhook seeder via `n8n_test_workflow` (triggerType webhook, path `coastal-seed-step2`) to get live Limble responses fast.

## What didn't work / dead ends
- `n8n_create_workflow` repeatedly failed with `InputValidationError: could not be parsed as JSON` on the large nested node payload (harness wrapped it into a `{"raw","len"}` blob). Workaround used: add nodes to an existing workflow via `n8n_update_partial_workflow` instead. If you must create fresh, try a minimal payload or the partial-update-into-existing approach.
- Direct `mcp__limble-mcp__get_tasks` was initially **denied by the auto-mode classifier** (OQ-003 "no live calls") until OQ-003 was amended for the sandbox; after the amendment the read succeeded. If denied again, the classifier reads project config — ensure OQ-003's 2026-07-09 addendum is intact, or have the owner approve interactively.
- `mcp__limble-mcp__get_users` returns ~13k lines (too big) — dumped to a tool-results file; grep it, don't inline it.

## Live Limble API findings (durable — also in memory `project_limble_create_task_api.md`)
Against `POST https://api.limblecmms.com/v2/tasks`:
1. **`due` must be a NUMBER (unix epoch seconds)**, not ISO. Use `Math.round($now.plus({days:7}).toSeconds())`.
2. **`statusID` is NOT allowed at create.** Create first, then PATCH `/v2/tasks/{id}` `{statusID}` (PATCH statusID is accepted — Step 2's own updatetask does this).
3. **Latent bug:** EHS Create WO (`isLUx7cUjkmKggD2`) node `Create Deficiency Task` sends `due: ...toISO()` → will 400 live. Fix to epoch seconds before the EHS suite / go-live (propose as sanctioned fix). Check for other `.toISO()` create nodes.

Sandbox statuses (customer-wide): `PO Requested`=5782, `PO Approved`=5783, `PO Create`=5784.

## Blocker
n8n-MCP free tier = 100 requests/day; exhausted mid-seeding. Owner moved to a new plan with fresh credits (hence the instance-id caveat above). Alt if quota recurs: app.n8n-mcp.com chat assistant (separate quota).

## Next steps (Step 2 test, in order)
1. **Verify instance** (see warning above).
2. **Finish the seeder** (`qyMChP0DKfI04r4a`, node `Create Step2 WO (neither)`): remove `statusID: 5782, ` from the `jsonBody`; add an HTTP PATCH `/v2/tasks/{createdId}` `{statusID:5782}` after create, wire `create → patch → respond`; you'll need to capture the create-response taskID field shape (fire once, inspect) since it wasn't captured before the cutoff.
3. **Fire seeder**, verify one WO at loc 98472: statusID 5782, `meta1=424242`, description contains `@CoupaWO;`.
4. **Stage Step 2** (`WYJyHdQGcdeD8wEr`): swap the 2 Coupa URLs (`Get Associated Requisition`, `Get PO Created From Req.`) host → `https://fm360.n8n.fm360consulting.com/webhook/mock-coupa` (confirm exact mock host from a mock webhook node); swap **all 10** Limble nodes' cred PROD `qn6u8jEK085DoHT8` → sandbox `MX0lwgfyFiGUBh5W` (the 8 originals + the 2 new error-subgraph nodes `Get Admin User`, `Post Admin Comment`).
5. **Seed token row** in `QAj62weJaWmRBJ76`: `client=coastal_waste`, `oauth_token=MOCK-TOKEN-COUPA`, a `scope` value. (Only the real `Coastal_Waste (TEST)` row exists now.)
6. **Owner clicks Execute** on Step 2 per scenario; agent reads executions + asserts. Scenarios (Coupa test plan §3.3): S2-1 (failMode `reqpending`, WO untouched), S2-4 neither-assigned happy (flip to 5783 + meta2=555001 + desc append, no comment), idempotency (flipped WO drops from next poll), and **error paths** via failMode `getreq`/`getpo` to exercise the NEW subgraph → assert a row in error-log table `6GbR5Rxezl7hqk9i`. Toggle `failMode` in config table `YkCIlyx7lUUNs7vG` between runs; reset to `''` after.
7. **Teardown when done:** Coupa test plan §6 (revert URLs, revert Step 2 Limble cred to PROD, purge dummy token row + test error rows). Remove the seeder branch if not reused.

## Open sub-decisions (get owner input before these)
- **Assignment-variant fixtures (S2-2 team / S2-3 user):** sandbox 98472 has no team or user. Either provision a team + user there (user creation is a heavy Limble account action) or defer these two scenarios. Neither-variant covers the core path already.
- **Admin-comment target:** the error subgraph @-mentions hardcoded Limble user 317887 (Brandon Ray Freckleton, a real prod user). Running error-path scenarios will post a real notification to him on the test WO. Decide whether to point `Get Admin User` at a sandbox stand-in first (none exists yet) or accept the test notification.

## Key artifacts (don't duplicate — read these)
- `open-questions.md` — OQ-003 (2026-07-09 addendum: scope relaxation), OQ-008/OQ-029 (Step 2 error subgraph, resolved), OQ-005/006/012/016/024/025/027 (Coupa decisions).
- `DEPLOYMENT.md` — pre-cutover gates per workflow; §0 credentials/tables/IDs.
- `docs/build-specs/coupa-check-prs-step2-build-spec.md` — Step 2 spec (§4.2 error handling).
- `docs/test-plan/coupa-test-plan.md` (§3.3 Step 2 scenarios, failModes, cred-swap caveat) and `docs/test-plan/ehs-test-plan.md`.
- Memory: `project_test_phase_state.md`, `project_limble_create_task_api.md`, `project_limble_api_quirks.md`, `project_email_delivery.md`.
