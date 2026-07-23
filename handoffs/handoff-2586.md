# Handoff — Pre-deployment status review

## Goal
User asked: "what is left to do here prior to DEPLOYMENT." This session was a
**status-review only** — no files edited, no builds, no live calls. Purpose was
to consolidate what's outstanding across `open-questions.md` and `DEPLOYMENT.md`
into one answer.

## Current Progress
Read `open-questions.md` (full, both pages) and `DEPLOYMENT.md` in full, and
produced a consolidated punch-list for the user (in-conversation, not saved as
a file). No repo files were changed this session.

## What Worked
Reading both source-of-truth docs end-to-end and cross-referencing was
sufficient — no need to re-derive from blueprint JSON or functions.js for this
question. Don't duplicate that list here; re-derive it fresh by re-reading
`open-questions.md` (esp. OQ-039 through OQ-042, the newest entries) and
`DEPLOYMENT.md` §0 and the per-workflow checklists (§1–§7), since both files
are the actual source of truth and may have moved since this session.

## What Didn't Work
N/A — nothing attempted beyond reading.

## Next Steps
1. Re-read `open-questions.md` and `DEPLOYMENT.md` fresh (don't trust a stale
   summary) — they are living documents and get updated frequently.
2. Highest-priority open item as of this session: **OQ-042** (BLOCKER) — no
   confirmed Limble API route to write an instruction's `response` field;
   EHS Create WO's `updateAnInstruction` node 404s. Owner was to open a Limble
   support ticket — check if that's landed.
3. Other still-open decisions worth checking on first: OQ-013, OQ-014, OQ-018,
   OQ-019, OQ-020, OQ-035, OQ-037, OQ-039, OQ-040, OQ-041 (all in
   `open-questions.md`, all unresolved as of 2026-07-15).
4. `DEPLOYMENT.md` — none of the per-workflow checklist items (§1–§7) are
   checked off yet; Data Table IDs in §0 are still blank placeholders. Confirm
   whether any of this has been actioned since.
5. Untested-before-go-live surface flagged in OQ-028 (R1–R4): real-Coupa
   acceptance never tested against anything but a mock; contractor-comment
   User/Team variants and the admin-comment node never exercised with real
   data; Error Log Export never fired end-to-end.
