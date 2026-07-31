# Handoff 3157 — cutover-readiness verdict + OQ-048 ruling (new target instance); port NOT started

Written 2026-07-30. Prior context: `handoffs/handoff-6482.md` (the partial [M] pass and its
blocked op list — still the authoritative record of what mechanical work remains).

## Goal

Answer "are we ready to execute the cutover?" — and record the owner ruling that answer
surfaced. Next session's job: execute the **OQ-048 port** (see Next Steps).

## Current Progress

- **Readiness verdict delivered: NOT ready.** Phase A testing complete (all 7 suites green,
  scoreboard `docs/test-plan/test-sequence.md`), but DEPLOYMENT.md holds 42 unchecked boxes:
  the [M] mechanical pass from handoff-6482 is still pending, plus the [EXT] set (OQ-020
  webhook admin — NO owner, gates 3 of 7 workflows; EHS key rotation unverified; OQ-019
  confirmation; Coupa PROD scope capture) and the owner-click items (section 7 Eastern
  re-run, ethan@ recipient restore).
- **NEW OWNER RULING captured as OQ-048** (`open-questions.md`, full entry with all
  sub-decisions — read it before doing anything): cutover target moved to the new dedicated
  instance **`https://coastal.n8n.fm360consulting.com`** (MCP display name `Coastal-Waste`).
  FM360 (`fm360.n8n.fm360consulting.com`) becomes the build/test sandbox + mock rigs. Split
  of labor: we port all 7 workflows + create **placeholder credentials/data tables**; owner
  manually populates credential values. Owner sizing: "shouldn't be a huge job."
- **Docs synced to the ruling**: project `CLAUDE.md` tooling section now lists both hosts
  with roles; OQ-048 added to index + body; memory file
  `project_coastal_instance_port.md` written.
- **No n8n writes or reads beyond one `n8n_instances mode=list`** — user said a parallel
  session was mid-use (binding sat on `City-of-Sparks`), so all switches were held.
- **Live verification NOT done**: workflow state on FM360 (mock URLs, creds, active flags)
  was not re-read this session. handoff-6482's blocked-op list is the latest record but is
  2 days old — re-verify by filtered fetch before editing anything.

## What Worked

- Answering readiness from the triangulated docs (test-sequence.md + DEPLOYMENT.md triage +
  handoff-6482) without burning MCP quota — the [EXT] blockers alone settle the verdict.
- Asking before switching the shared MCP binding — parallel session WAS active; a blind
  switch could have hijacked its writes.
- Flagging the unexplained `Coastal-Waste` instance in the MCP list instead of assuming it
  irrelevant — it turned out to be the new go-live target, a scope change no doc knew about.

## What Didn't Work

(nothing failed this session — assessment + recording only)

## Next Steps

1. **Execute the OQ-048 port** when the MCP binding is free. Confirm with the user first
   that no parallel session is using n8n-MCP, then `n8n_instances mode=switch` →
   `Coastal-Waste`, and **verify by URL + a known-answer read** (instance list has lied
   before — see global lessons). Serialize ALL writes in one session; re-list workflows
   immediately before each create; ~100 MCP calls/day quota.
2. Port shape (recommended in OQ-048, not yet owner-ratified): create the 7 coastal copies
   **already in cutover config** — real Coupa/EHS hosts, prod-type placeholder credentials
   (`httpHeaderAuth` Limble/EHS, `httpCustomAuth` Coupa, SMTP Ionos), repointed data-table
   IDs — folding handoff-6482's blocked [M] ops (URL reverts, cred swaps, recipient
   restores) into the port so nothing is edited twice. FM360 copies stay in test config as
   the regression rig. Verification = `n8n_validate_workflow` + node inspection; first
   execution is Phase C by design (OQ-039). Confirm this sequencing with the owner before
   building.
3. Create the 3 data tables on coastal (token, error-log, Integration Config w/
   `escalation_admin_user_id` row) — decide with owner whether the test-only `failMode`
   table ports at all. Record ALL new IDs (workflows, creds, tables) in OQ-048 + DEPLOYMENT.md.
4. Watch the permission classifier: last workflow-write pass (handoff-6482) was blocked in
   auto mode. Get accept-edits mode or per-call approvals BEFORE starting, don't burn
   retries.
5. Independent of the port: sandbox teardown (`python3 tools/sandbox-seed/teardown.py`,
   guarded/ledger-driven), section 7 Eastern re-run Execute click (error-log rows 23/24 are
   the staged fixture — do NOT clean them), then ethan@ recipient restore.
6. [EXT] chase unchanged (owner/Ethan): OQ-020 — now must target **coastal** webhook URLs;
   EHS key rotation + old-key revocation; OQ-019 confirmation → config row
   `398783`→`317887`; Coupa scope + fresh client_id/secret capture.
7. Uncommitted repo changes from prior sessions plus today's (CLAUDE.md, open-questions.md,
   DEPLOYMENT.md, test-plan docs, handoffs) — commit when convenient.

## Standing constraints (unchanged)

- Never activate a workflow without asking the owner. Verify n8n instance by URL before any
  MCP call (shared binding). Mock rigs only for Coupa/EHS; Limble writes sandbox-only
  (loc 98472). No real credential values in repo files, ever.
