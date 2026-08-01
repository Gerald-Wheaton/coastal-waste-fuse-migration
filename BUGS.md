# BUGS.md — what changed between Fuse and n8n

Summary of every behavior change made while porting Coastal's 7 Fuse (Make.com) scenarios to
n8n, plus the fixes that were proposed and deliberately **not** taken. Written at port
completion (2026-08-01, all 7 workflows live on `coastal.n8n.fm360consulting.com`, inactive).

**Authoritative detail lives in `open-questions.md`** (per-OQ resolutions, dates, evidence) and
in sections 8-13 of the affected build specs. This file is the digest.

## The posture that produced this list

The engagement is a **1:1 port plus a sanctioned fix list** (OQ-001). Default was always
"replicate what shipped, including its bugs." A fix had to be proposed individually and
approved before it was built. Nothing here was an unsolicited improvement.

The filter we applied, in practice:

**Fixed only when** the defect was provably dead code or a never-fired path (so "faithful"
would mean deliberately re-implementing something that has never worked), **or** the narrative
review docx documents an intent the code contradicts, **or** an n8n engine difference would
otherwise make the port behave *differently* from Make, **or** the fix was one node/one
expression and already covered by an existing test.

**Left 1:1 when** the change was future-proofing against headroom we measurably have, or would
require new test surface, or the "correct" behavior was genuinely ambiguous, or the client has
demonstrably accepted the current behavior in production. Several real, agreed-upon
imperfections are still in the port for exactly this reason — the schedule does not have room
to fix, re-spec, and re-test everything, and each extra fix widens the diff we have to defend
at cutover. Cutover risk is minimized by *resembling* the system Coastal already runs.

---

## A. Inherited Fuse defects that were fixed

| OQ | Where | Defect in Fuse | Fix in n8n |
| --- | --- | --- | --- |
| 006 | Error Log Export | `DeleteAllRecords` wiped the whole error datastore, not just the rows searched + emailed — anything written during the run was dropped, never reported | Delete only the row IDs actually exported that run |
| 017 | Step 1 "Add Quote" | Its `onerror` logged module 17's error (Create Requisition — already succeeded by then), so attachment failures logged an empty/wrong error | Error branch logs the Add Quote node's own error |
| 024 | Step 1/2/3 | Wrote `metadata.meta1` / `metadata.meta2`; Limble's API **rejects the `metadata` object outright** (400 on POST and PATCH) — metaN are top-level fields. The Coupa correlation key was never actually stored | Top-level `metaN`, stringified. Step 2's build was wrong and was fixed; Step 1's was already correct |
| 026 | Step 2 | Fetched the "PO Approved" statusID and never wrote it, so a processed WO stayed in "PO Requested", got re-selected by the next 5-min poll, and re-appended `\|\| Coupa PO# X` forever. Docx says the flip should happen | Flip the WO to "PO Approved". Doubles as the idempotency guard — flipped WOs leave the polled set |
| 030 | Step 3 | `GET /purchase_orders?po-number={{meta2}}` but `meta2` holds the PO **id** — always empty, every downstream `{{25.body[1].id}}` dereferenced nothing | Fetch the PO by id |
| 031 | Step 3 | Attachment POST sent `Authorization: <token>` with **no `Bearer ` prefix** (the other calls had it) | Fixed as a side effect of Bearer-for-all (section B) |
| 037 | EHS Create WO | `CoastalEHSFormFilter` compared `form.UpdatedDtm > filteredForms[j].UpdateDtm` — misspelled right side ⇒ `NaN` compare ⇒ replace branch **dead**, so dedupe kept the *first-seen* inspection per site, not the latest. And the docx-required draft exclusion (`RecurringTaskCompleteDtm`) existed **only inside that dead branch**, so drafts were never excluded either | Both restored: pre-dedupe draft guard + correct field name. Live EHS confirms `UpdatedDtm` (86/86 records; `UpdateDtm` does not exist). Not rare — 86 inspections across 31 sites in a 72h window, so same-site collisions are routine. `docs/functions.js` deliberately left un-edited: it is the record of what Make shipped |
| 038 | Both EHS workflows | Create stamped `@EHS;`, Update gated on `@EHSWO;` — disjoint strings, so the EHS write-back loop **has never fired**. Confirmed live: 10 prod WOs since 2025-10-30, all `@EHS;`, 5 completed, and all 5 EHS inspection records untouched since submission | Gate moved to `@EHS;` (direction reversed 2026-07-27 on Ethan's call — the client's live data is the standard, and this also adopts the 5 still-open prod WOs, which nobody would hand-edit). Closed loop Create→Update proven end-to-end |
| 042 | EHS Create WO | Ported instruction write hit `PATCH /v2/instructions/{id}` — 404. Fuse's private connector uses a route the public API does not expose | Correct route is `PATCH /v2/tasks/instructions/{id}` (Limble support confirmed); image is a **separate** `PUT .../image` call, now its own node. Also fixed here: `due` was `.toISO()`, but `POST /v2/tasks` requires **epoch seconds** |
| — | EHS Update | `Get Instructions` had no `limit`, and Limble's default page size is **2** — a parent with 3+ instructions silently dropped children 2 and beyond. Also: `.meta.associatedTask` threw on the meta-less text instruction (killing the run), and the value is a **relative path**, not a full URL | `?limit=100`, optional chaining, host prepended. Permanent port fixes, no cutover revert |

## B. Make → n8n engine differences (changes made to *preserve* behavior)

These are not source bugs. Make and n8n differ, and a literal node-for-node copy would have
behaved differently.

| OQ | Difference | What we did |
| --- | --- | --- |
| 005 | Make datastore 324 is a shared multi-tenant credential store; n8n has no equivalent | Isolated n8n credential per system. Token Regeneration **kept** as a workflow writing to a Data Table (see D — native OAuth2 was rejected as too large a change) |
| 012 | Datastore 326 wrote `timestamp` as inconsistently pre-formatted display strings (`MM/DD/YYYY hh:mm A`, `MM/DD/YY hh:mm A`, long-form EST) | n8n Data Table with a native **Date** column; formatting moved to the report email |
| 016/027/031 | Auth for several Coupa calls lived inside Make connection 1766, which is not in the export — 3 Step 1 lookups and both Step 2 calls send no header at all | **Bearer-for-all**: every Coupa call across Step 1/2/3 sends the daily token from the OAuth Token table. Decision, not verification — a 401/403 on the first live run reopens it (section E) |
| 022 #1 | Make serializes scenario runs; **n8n webhook executions run concurrently** — two rapid status flips or a redelivery could both pass the "PO Create" gate and create duplicate Coupa requisitions | IF guard after the task fetch: exit early if `meta1` is already populated |
| 043 / 045 / — | **Zero-input skip.** A Make aggregator emits an empty bundle on zero inputs and the flow continues; an n8n node with 0 input items is *skipped*, taking the rest of the chain with it — while the execution still reports "success" | Three fixes: EHS Update `Collect Child Links` rewire (a zero-child parent silently skipped the entire write-back tail — proven, exec 127258); EHS Create watchdog guards reconnecting to the loop (a location missing its team killed **the rest of the day's forms**, not just its own); `alwaysOutputData` on Step 1 + Step 3 `Get Instructions` |
| 011/014 | Make's schedule timezone is not in the export; `workflow-list.md` said MST | **America/New_York** everywhere (schedules, error-report rendering, completion-note timestamps). All 49 Coastal locations are Eastern — the blueprints' hardcoded EST was right, the doc was wrong |
| 010 | Email node swap | Ionos for all outbound; real recipients preserved in config, dev-routed to gerald@ until go-live |

## C. Sanctioned additions and consolidations

Behavior-neutral cleanups and a small number of agreed gap-fills.

- **OQ-008** — Step 2 had *zero* error handling (Step 1/3 log to the shared table). Added an
  error subgraph: error outputs on the 5 failure-capable calls → shared error-log table +
  admin @-mention. Step 2 is now the third writer to the same table, not a second log.
- **OQ-013** — Error Log Export had no self-error handling. Added retry + one alert email.
  Accepted blind spot: the alert uses the same SMTP as the report, so a hard SMTP outage is
  still silent. The second-channel variant was offered and declined.
- **OQ-018** — Step 1's `listUsers limit=500` had no pagination. Added cursor pagination as
  future-proofing (79 users today, so zero runtime change). **This fix caused the only
  regression of the migration:** the as-applied expression `{{ $response.body.last().userID }}`
  throws on the *first* request, and Step 1 died at that node on every run until corrected to
  `{{ $response?.body?.last()?.userID ?? 0 }}`. It had passed a config read-back and a REST
  contract probe — neither is execution proof.
- **OQ-019** — Limble admin `317887` was hardcoded 6x in the Fuse Step 1 error paths. Hoisted
  to an `Integration Config` Data Table row so the escalation contact is a one-row edit.
- **OQ-021 / 033 / 034 / 036** — consolidations, all verified behavior-neutral: dropped dead
  modules (Step 1 comment feeder/aggregator, Step 3 feeder/aggregator, EHS Update's unread
  comments fetch); merged Step 1's two identical dollar branches into one tail; converged its
  5 near-identical error paths into one subgraph; two sequential task PATCHes into one; EHS
  Create's 3 byte-identical region routes into 1 branch + allowlist (unmatched regions still
  drop, matching the source's missing `else`).
- **OQ-022 #2** — Retry (3x) on the 4 Coupa **GET** lookups only. Never on the create or
  attachment POSTs: a retry after a timeout can double-create.

## D. Proposed, and deliberately left 1:1

Each of these was on the table and was declined — in most cases because the fix costs more
test surface than the risk justifies at this point in the schedule.

| OQ | Proposal | Why we didn't |
| --- | --- | --- |
| 004 | Add error logging to the two EHS workflows (they have none, unlike the Coupa side) | Faithful port. Matches current prod behavior exactly; a new logging path is new untested surface |
| 032 | Give Step 3's error handling the admin @-mention Step 1/2 have | Faithful log-only. Step 3's comments go to Coupa, not Limble — an admin Limble comment is a call the source does not make |
| 022 #3 | Read the quote attachment by instruction **text** instead of position `[5]` | Declined. The quote instruction sits at position 5 on the live template today; pure future-proofing against a template reorder |
| 022 #4 | Replace the 500-user fetch + client-side scan with a location-filtered call | Dropped — infeasible. Limble's users endpoint has no location filter |
| 022 #5 | Hardcode status IDs instead of `%PO Create%` name lookups at runtime | Kept the name lookups. 2-3 extra calls per run buys resilience to statusID churn |
| 022 #6 | Use n8n's native OAuth2 credential auto-refresh | Rejected. It would delete the Token Regeneration workflow and its Data Table outright — a far bigger behavior change than the posture sanctions, on an already-built workflow |
| 035 | Iterate *all* unacceptable inspection questions instead of only the last | Not a bug — the docx specifies last-question-only; it is a roll-up summary question. The alternative would spawn WOs the inspector deliberately excluded. Positional-vs-named hardening also declined (form is stable) |
| 046 | Paginate EHS Create's `listTeams limit=500` for symmetry with OQ-018 | No change. 45 of 500 used, name-filtered server-side, and growth tracks location count not headcount. `/v2/teams` pagination is unprobed and patching the node reopens a passed test suite |
| 047 #3/#4 | Match the docx: priority 3 and same-day due date (code sends priority 2, due +7d) | Accepted as intended. All 10 WOs the Fuse scenario created over ~10 months are priority 2 / +7d, unedited, 5 completed — the docx lines describe the *template's* stored defaults, which the integration deliberately overrides |
| 041 | Resolve Coupa's `client_credentials` token semantics before cutover | Mooted by the hot-swap design — Fuse and n8n are never active simultaneously, so cross-invalidation cannot occur. Runbook conditions instead |
| — | Cross-run dedupe in EHS Create (nothing checks whether a WO already exists for an inspection) | Source has no guard either. Flagged, not changed |
| — | Token-refresh-vs-mid-execution race inside a single engine | Pre-existing in Fuse (datastore 324); carried over 1:1 |
| — | `alwaysOutputData` on EHS Update's `Get Instructions` (the one remaining zero-input skip, found 2026-07-27) | Not fixed unilaterally. Requires a parent with **zero** instructions; template 842 always creates 3. Same reachability profile as the accepted OQ-045 residual — documented, decision owed |

## E. Carried into cutover as watch items, not fixes

- **Coupa / EHS response shapes are still guesses** (OQ-028/039). All test-phase Coupa and EHS
  traffic hit mock rigs whose shapes were reverse-engineered from the blueprints. Owner ruled
  against a Coupa test-instance pass: real shapes get examined at go-live under the C4
  first-shepherd watch, with Fuse **disabled, not deleted**, as the rollback lever.
- **Bearer-for-all is unconfirmed** (OQ-016). A 401/403 on the previously header-less lookups
  means our decision was wrong; a 4xx on create-requisition is the inherited Fuse-era defect
  (the one real prod task, 1953, failed at that same POST, twice). *Where* it dies is the
  diagnosis.
- **`CreatedAfter` vs `DatePerformed`** (OQ-047 #2) — the only unfixed silent-data-loss path.
  An inspection drafted one day and submitted the next falls outside the window and never
  becomes a WO, with nothing logging the miss. Blocked on an EHS contract question (does the
  list endpoint even filter on `DatePerformed`? it is date-only, so a naive swap changes which
  day lands in the window). C6 watch item.
- **OQ-018's multi-page branch has never executed** — only the single-page path has run.
- **EHS API key** was hardcoded in plaintext in both EHS blueprints (9 occurrences) and is
  confirmed live against prod. Client ruled 2026-08-01 to deploy on the existing key and rotate
  post-deployment (C8 window).
- **No working prod baseline exists for the Coupa side** (OQ-024): `meta1` is null on every real
  task and the requisition path has essentially never succeeded in Fuse. There is nothing to
  regression-test against — cutover validates against synthetic tasks driven through every path.
