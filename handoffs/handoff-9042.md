# Handoff 9042 — A6 PASSED, A7 staged + blocked on owner UI checklist (2026-07-21)

Continues handoff-8146 lineage. Read first: `docs/test-plan/test-sequence.md` (live scoreboard),
`docs/test-plan/sandbox-seed-record-a6.md` (teardown ledger + A7 owner checklist),
`open-questions.md`. Memory files `project_test_phase_state` and `project_limble_create_task_api`
carry the same state in compressed form.

## Goal

Finish Phase A of the pre-go-live test sequence for the Coastal Fuse→n8n migration:
A6 (EHS Create WO) ✅ done, **A7 (EHS Update Inspection, `8JvtesynrYtZbw7U`) is next**, then A8
wrap-up gates, then Phase B revert checklist and Phase C go-live validation per
`test-sequence.md` and `DEPLOYMENT.md`.

## Current Progress

- **A6 PASSED 2026-07-21, execution 126934** on `isLUx7cUjkmKggD2`. Exactly 5 tasks (4192–4196 =
  A1/B/C/D/E) at correct locations/teams, meta1=RowUID, epoch due, `@EHSWO;`, instruction
  verbiage patched on all 5, scenario B got the image via the `Attach Instruction Image` PUT
  node. Negative scenarios all held (G acceptable-answer gate, F region allowlist, H + A2 never
  reached the split). Full assertion detail ticked in `test-sequence.md` A6 block.
- **A7 staged**: `8JvtesynrYtZbw7U` EHS nodes n11/n13 → mock host (host-only swap, validates
  clean, creds already attached); mock routes curl-verified; Limble fixture skeletons seeded at
  sandbox loc 98472 — 4198 (U1 parent, `@EHSWO;` + meta1=EHS-INSP-UPD-1), 4199/4200 (children),
  4201 (U3 non-EHS control), 4202 (U4 zero-children parent, optional).
- **A7 blocked on owner UI checklist** (in `sandbox-seed-record-a6.md`): link 2 children to 4198,
  complete children/parent with exact note strings, optionally complete 4202. Blocked because
  Limble's public API rejects `completionNotes`, `dateCompleted`, and instruction
  `meta.associatedTask` (all 400 "not allowed"); `POST /v2/tasks/{id}/complete` → 404.
  Completion state + child links are UI-only.
- All docs/ledger/memory updates for the above are already written; repo has uncommitted changes
  (this session's + prior) — nothing committed, owner hasn't asked.

## What Worked

- A6 first attempt (exec 126921) crashed on n28 `Update Instruction (No Image)`: body used
  `$json.questionList.Verification` but `$json` there is the Limble instruction object →
  expression → `undefined` → "not valid JSON". Fix: reference the source node explicitly,
  `$('Extract Last Question').item.json.questionList.Verification` (mirrors n27). **Pattern
  lesson: on branch pairs, keep body expressions node-referenced, not `$json`-relative.**
- Orphan task 4191 from the partial run was deleted before re-run to keep the "exactly 5 tasks"
  assertion clean — check for partial-run orphans after any failed execution that passed the
  create node.
- Execution assertion flow that worked: `n8n_executions` mode=preview for per-node item counts →
  mode=filtered on key nodes → direct Limble GETs (tasks at fixture locations, then
  `/v2/tasks/{id}/instructions`) to verify writes landed. Note: filtered mode on loop-embedded
  nodes returns only the last iteration's items — verify full sets via the target API instead.
- `POST /v2/tasks/{taskID}/instructions` works (201) — discovered during A7 seeding, in the
  OQ-009 contract list in `sandbox-seed-record-a6.md`.

## What Didn't Work

- Writing task completion fields or child-WO links via API — every route/field probed returns
  400 "not allowed" or 404 (list in `sandbox-seed-record-a6.md`). Don't re-probe; use the UI.
- API-created instructions return **no `meta` key at all**. A7 run risk: `Has Child WO?` in
  `8JvtesynrYtZbw7U` reads `$json.meta.associatedTask` — may throw (not filter) on meta-less
  instructions. Whether UI child-linking adds `meta.associatedTask` is unverified; owner
  checklist step 1 settles it. If it throws, likely fix is optional chaining in that node's
  condition — propose, don't silently apply.

## Next Steps

1. **Wait for owner** to finish the A7 UI checklist (5 items, `sandbox-seed-record-a6.md`). If
   the UI spawned new child tasks instead of linking 4199/4200, delete 4199/4200 and record new
   IDs in the ledger.
2. After checklist: verify `GET /v2/tasks/4198/instructions` now carries `meta.associatedTask`.
3. Activate `8JvtesynrYtZbw7U` if needed, fire A7 via curl (webhook-triggered, no Execute
   clicks): U1 `{"status":"COMPLETE","taskID":4198}`, U2 non-completion payload, U3 taskID 4201,
   U4 (optional) 4202. Assert per `test-sequence.md` A7 block: mock capture row
   `inspectionID=EHS-INSP-UPD-1`, `udfCompletionNotes` exact concat (ehs-test-plan section 4.3,
   Denver tz), U2/U3 drop at gates, OQ-036 negative. Deactivate after.
4. Record results in `test-sequence.md` + ledger + memory; append any new tasks to the ledger.
5. A8 wrap-up gates, then Phase B/C per `test-sequence.md`.
6. Outstanding elsewhere: S2-2 team-assigned still blocked (OQ-040); OQ decision-batch emails
   drafted in `oq-resolution-plan.md`, unsent.

## Credentials / security notes (redacted)

- Limble sandbox Basic credential: provided by owner in-chat this session; NOT in any repo file.
  A copy sits in the session scratchpad at `<scratchpad>/.limble_auth` (session-isolated; a fresh
  session must ask the owner for it again). Owner already advised to rotate after test window.
- EHS credential `ZEf4C1rpYSbBgLbX` (n8n store) is the rotated real key; Limble sandbox n8n cred
  `MX0lwgfyFiGUBh5W`. Old exposed EHS key tracked in DEPLOYMENT.md section 0.
- Live-write scope: Limble sandbox fixtures only (owner-authorized); Coupa + EHS fully mocked;
  prod Limble off-limits.
