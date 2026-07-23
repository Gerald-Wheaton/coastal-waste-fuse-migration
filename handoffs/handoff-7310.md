# Handoff — Pre-deployment status review (repeat pass)

## Goal
User asked again: "what is left to do here prior to DEPLOYMENT." Same question as
the session that produced `handoff-2586.md` (same day, 2026-07-15). This was again
a **status-review only** session — no files edited, no builds, no live calls.

## Current Progress
Read `DEPLOYMENT.md` (full) and `open-questions.md` (full, both pages) exactly as
the prior session did — conclusions match `handoff-2586.md` and nothing has moved
in the interim. Additionally this session read `docs/test-plan/README.md` and
`docs/test-plan/test-sequence.md` (untracked file, not covered by the 2586 pass),
which gave the Phase A/B/C execution breakdown that DEPLOYMENT.md/open-questions.md
don't spell out on their own:

- **Phase A** (pre-go-live, mock Coupa/EHS + live Limble sandbox 98472): Step1,
  Step3, Token Regen, Error Log Export suites all COMPLETE. Still open: A1 S2-2
  team-comment (blocked OQ-040), A6 EHS Create WO (not run, `due` epoch-seconds fix
  needed first), A7 EHS Update Inspection (not run, depends on A6), A8 wrap-up
  (failMode resets, sandbox teardown, doc debt).
- **Phase B** (cutover mechanics) = `DEPLOYMENT.md`'s revert checklist: mock URLs →
  real hosts, sandbox creds → prod creds, admin lookup 398783 → real 317887, mock
  token rows purged, real Coupa/EHS creds installed, webhooks repointed, email
  recipients restored, final cron timezones set.
- **Phase C** (go-live validation, real APIs, one workflow at a time): Token Regen →
  Step 2 → Error Log Export → Step 1 → Step 3 → EHS Create → EHS Update, each with
  specific things to watch (real API response shapes were never verified — biggest
  risk lands at Step 2/C2 and EHS/C6-C7 since those are all mock-only so far).

No repo files were changed this session either.

## What Worked
Reading `DEPLOYMENT.md` + `open-questions.md` + `docs/test-plan/README.md` +
`docs/test-plan/test-sequence.md` together gives the complete current picture —
the first two are the authoritative decision/checklist log, the latter two give
the execution sequencing that ties them together. Don't re-derive from blueprint
JSON or `functions.js` for this kind of question — the four docs above are
sufficient and are the actual source of truth.

## What Didn't Work
N/A — nothing attempted beyond reading. Note for whoever picks this up: this is
the second consecutive session asked this exact question with no work done
between them. If a third one comes in, worth asking the user directly whether
they want the punch-list restated or whether they actually want someone to start
executing items on it (OQ-042's Limble support ticket, EHS Create WO's `due` fix,
etc.) instead of just re-reading.

## Next Steps
1. Re-read `DEPLOYMENT.md`, `open-questions.md`, and `docs/test-plan/test-sequence.md`
   fresh before answering again — they're living docs, may have moved.
2. Highest-priority blocker: **OQ-042** — no confirmed Limble API route to write an
   instruction's `response` field; EHS Create WO's `updateAnInstruction` node 404s.
   Owner was to open a Limble support ticket — check if that's landed.
3. Second blocker: **OQ-040** — Step 2's S2-2 team-comment path unprovable in
   sandbox (team 107065 is a "View Only" role-team). Needs a real maintenance team
   at sandbox loc 98472, or owner accepts deferring to Phase C.
4. Before A6 (EHS Create WO) can even run: fix the `due: .toISO()` bug on
   `isLUx7cUjkmKggD2` (Limble `POST /v2/tasks` needs epoch seconds, not ISO —
   see project memory `project_limble_create_task_api.md`).
5. Still-open decisions worth chasing: OQ-011/OQ-014 (timezone — recon suggests
   America/New_York is correct, not the assumed America/Denver, needs Coastal
   confirmation), OQ-013, OQ-018, OQ-019, OQ-020, OQ-035, OQ-037, OQ-039
   (Coupa TEST instance — authorize live testing against it?), OQ-041 (Coupa
   token rotate-vs-concurrent semantics, affects Token Regen activation order
   at cutover).
6. `DEPLOYMENT.md` §0 Data Table IDs are still blank placeholders — confirm
   whether created yet.
