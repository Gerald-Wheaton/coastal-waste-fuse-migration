# Open Questions

Items pending resolution, awaiting input, or explicitly blocked.

- Add manually: /oq-add (or /scrum-question inside a scrum project)
- Scan repo for new items: /oq-scan (or /scrum-scan)
- Resolve items: /scrum-resolve

Items marked [resolved] are kept for history and ignored on future scans.

---

## Index

| ID                | Title                                                          | Type          | Status   | Added      |
| ----------------- | --------------------------------------------------------------- | ------------- | -------- | ---------- |
| [OQ-001](#oq-001) | Migration posture: 1:1 + sanctioned fixes                       | PENDING DECISION | Resolved | 2026-07-01 |
| [OQ-002](#oq-002) | Decomposition: mirror 1:1, 7 scenarios to 7 n8n workflows        | PENDING DECISION | Resolved | 2026-07-01 |
| [OQ-003](#oq-003) | Environment/MCP access scope for this phase                     | PENDING DECISION | Resolved | 2026-07-01 |
| [OQ-004](#oq-004) | EHS-side workflows have no error logging — port as-is        | PENDING DECISION | Resolved | 2026-07-01 |
| [OQ-005](#oq-005) | Coupa credential store: isolated n8n credential, not shared store | PENDING DECISION | Resolved | 2026-07-01 |
| [OQ-006](#oq-006) | Error Log Export drain race: fix to delete only exported records | PENDING DECISION | Resolved | 2026-07-01 |
| [OQ-007](#oq-007) | Target n8n workflow IDs needed per workflow                     | BLOCKER       | Resolved | 2026-07-01 |
| [OQ-008](#oq-008) | "Check For New PRs Ordered" (Step 2) has no error handling       | OPEN QUESTION | Resolved | 2026-07-01 |
| [OQ-009](#oq-009) | No authoritative Coupa/Limble/EHS API reference material found  | OPEN QUESTION | Open     | 2026-07-01 |
| [OQ-010](#oq-010) | Email delivery: Ionos integration, dev-mode recipient override    | PENDING DECISION | Resolved | 2026-07-01 |
| [OQ-011](#oq-011) | Schedule trigger timezone: fixed MST offset vs. DST-aware Mountain Time | OPEN QUESTION | Resolved | 2026-07-01 |
| [OQ-012](#oq-012) | Error log `timestamp`: native Date column + Mountain-time display | PENDING DECISION | Resolved | 2026-07-01 |
| [OQ-013](#oq-013) | "Coupa Integration Error Log Export" has no self-error-handling  | OPEN QUESTION | Open     | 2026-07-01 |
| [OQ-014](#oq-014) | Confirm timezone(s) w/ Coastal — MST vs EST vs mixed             | OPEN QUESTION | Open     | 2026-07-01 |
| [OQ-015](#oq-015) | API credentials needed: Limble (received), Coupa, EHS Insight, Ionos SMTP | BLOCKER | Resolved | 2026-07-02 |
| [OQ-016](#oq-016) | Step 1: auth inside Make connection 1766 (3 unauthenticated Coupa lookups) | OPEN QUESTION | Resolved | 2026-07-02 |
| [OQ-017](#oq-017) | Step 1: "Add Quote" onerror logs wrong module's error — fix?              | PENDING DECISION | Resolved | 2026-07-02 |
| [OQ-018](#oq-018) | Step 1: listUsers limit=500, no pagination — silent miss past 500 users    | OPEN QUESTION | Open | 2026-07-02 |
| [OQ-019](#oq-019) | Hardcoded Limble admin user 317887 in all Step 1 error paths — who is it?  | OPEN QUESTION | Open | 2026-07-02 |
| [OQ-020](#oq-020) | Limble webhook re-registration at cutover (hooks 775/776/777 → n8n URLs)   | OPEN QUESTION | Open | 2026-07-02 |
| [OQ-021](#oq-021) | Step 1 spec: sign-off on proposed consolidations (§4)                      | PENDING DECISION | Resolved | 2026-07-02 |
| [OQ-022](#oq-022) | Step 1 improvement candidates awaiting sanction (idempotency, retries, etc.) | PENDING DECISION | Resolved | 2026-07-02 |
| [OQ-023](#oq-023) | Sanction read-only Limble MCP recon before Step 1 build (OQ-003 amendment)   | PENDING DECISION | Resolved | 2026-07-03 |
| [OQ-024](#oq-024) | meta1 empty on every real CoupaWO task — top-level metaN, `metadata` obj rejected | OPEN QUESTION | Resolved | 2026-07-03 |
| [OQ-025](#oq-025) | "PO Requested"/"PO Approved"/"PO Create" status names — confirmed via direct API | OPEN QUESTION | Resolved | 2026-07-03 |
| [OQ-026](#oq-026) | Step 2: blueprint never flips WO to "PO Approved" (docx says it should) — fix | PENDING DECISION | Resolved | 2026-07-03 |
| [OQ-027](#oq-027) | Step 2: Coupa auth on 2 calls — resolved Bearer-for-all (matches OQ-016) | OPEN QUESTION | Resolved | 2026-07-03 |
| [OQ-028](#oq-028) | Mock-Coupa test rig: guessed response shapes; cutover teardown checklist | OPEN QUESTION | Open | 2026-07-05 |
| [OQ-029](#oq-029) | Step 2 built (`WYJyHdQGcdeD8wEr`) missing OQ-008 error-log subgraph | OPEN QUESTION | Resolved | 2026-07-09 |
| [OQ-030](#oq-030) | Step 3: PO lookup by po-number but meta2 holds PO id — fix to query by id | PENDING DECISION | Resolved | 2026-07-07 |
| [OQ-031](#oq-031) | Step 3: Coupa auth on 3 calls — Bearer-for-all (matches OQ-016/027) | OPEN QUESTION | Resolved | 2026-07-07 |
| [OQ-032](#oq-032) | Step 3: error handling — faithful log-only, no admin comment | PENDING DECISION | Resolved | 2026-07-07 |
| [OQ-033](#oq-033) | Step 3: drop dead comment Feeder/Aggregator (8/9) — consolidation | PENDING DECISION | Resolved | 2026-07-07 |
| [OQ-034](#oq-034) | EHS Create WO: consolidate 3 identical region routes → 1 + allowlist guard | PENDING DECISION | Resolved | 2026-07-08 |
| [OQ-035](#oq-035) | EHS Create WO: `last(Questions)` only inspects last question — flag | OPEN QUESTION | Open | 2026-07-08 |
| [OQ-036](#oq-036) | EHS Update Inspection: drop dead comments-fetch (63) / lastComment (64) | PENDING DECISION | Resolved | 2026-07-08 |
| [OQ-037](#oq-037) | `CoastalEHSFormFilter` dedupe never replaces (UpdateDtm/UpdatedDtm typo) — flag | OPEN QUESTION | Open | 2026-07-08 |
| [OQ-038](#oq-038) | EHS tag mismatch: Create stamps `@EHS;`, Update filters `@EHSWO;` — sanctioned fix to `@EHSWO;` | PENDING DECISION | Resolved | 2026-07-08 |
| [OQ-039](#oq-039) | Coupa TEST instance (`coastalwasteinc-test.coupahost.com`) exists w/ standing creds — authorize Phase-A live testing against it? | PENDING DECISION | Open | 2026-07-13 |
| [OQ-040](#oq-040) | Step 2 team-comment path unprovable in sandbox — team 107065 is "View Only" role-team, not returned by `/v2/teams` | OPEN QUESTION | Open | 2026-07-13 |
| [OQ-041](#oq-041) | Token Regen ↔ Fuse collision at cutover — same Coupa client creds; concurrent tokens or rotate-and-invalidate? | OPEN QUESTION | Open | 2026-07-13 |
| [OQ-042](#oq-042) | Limble instruction-answer write API — support confirmed NO public route to write a `response`/answer; EHS Create WO writes verbiage (`instruction`), not answer, so NOT blocked | BLOCKER | Resolved | 2026-07-13 |

---

## OQ-001 — [resolved] Migration posture: 1:1 + sanctioned fixes

**Type:** PENDING DECISION
**Added:** 2026-07-01

**Question / Description:**
Should this migration be a faithful 1:1 port of the 7 Make.com scenarios, or 1:1 plus
a sanctioned list of approved fixes?

**Resolution criteria:**
Owner picks a posture for the engagement.

**Resolved:** 2026-07-01
**Resolution:** 1:1 + sanctioned fixes. Fixes are allowed but must be individually
proposed and approved — no unilateral improvements. Each sanctioned fix should be
logged here (or in a constraints doc) by number, with approval date. See OQ-005 and
OQ-006 for the first two sanctioned fixes agreed under this posture.

**Sanctioned-fix register:** OQ-005 (isolated Coupa credential), OQ-006 (error-log drain
race), OQ-016/027/031 (Bearer-for-all Coupa auth), OQ-026 (Step 2 flip to "PO Approved"),
OQ-030 (Step 3 PO lookup by id), OQ-034 (EHS region-route consolidation), and
**OQ-024 (2026-07-09): write top-level `metaN`, not `metadata.metaN` — the raw Limble API
rejects the `metadata` object; applies to Step 1/2/3 workflows + build specs.**

---

## OQ-002 — [resolved] Decomposition: mirror 1:1, 7 scenarios to 7 n8n workflows

**Type:** PENDING DECISION
**Added:** 2026-07-01

**Question / Description:**
Should the 7 Make.com scenarios map to 7 separate n8n workflows (same trigger
boundaries), or should some be consolidated (e.g. merging the 3 Coupa steps)?

**Resolution criteria:**
Owner picks a decomposition strategy.

**Resolved:** 2026-07-01
**Resolution:** Mirror 1:1 — all 7 scenarios become 7 separate n8n workflows, with
the same webhook/schedule trigger boundaries preserved exactly as in the Make exports.

---

## OQ-003 — [resolved] Environment/MCP access scope for this phase

**Type:** PENDING DECISION
**Added:** 2026-07-01

**Question / Description:**
What's actually authorized in this environment right now — live API calls against
Limble/Coupa/EHS Insight, and/or use of the connected n8n MCP server for lookups or
actual workflow creation?

**Resolution criteria:**
Owner states the boundary explicitly.

**Resolved:** 2026-07-01
**Resolution:** This phase is design/spec only — no live API calls against Limble,
Coupa, or EHS Insight. The n8n MCP server is connected and may be used for read-only
lookups (node schemas, validation) but must NOT be used to create or deploy workflows
yet — the target workspace is still being built out. Do not proactively look into the
n8n instance until asked. See OQ-007 for the blocker on getting target workflow IDs.

**Addendum (2026-07-01):** owner issued a workflow ID for "Coupa Token Regeneration"
(`oCAl4h0SZenEtbNs`, see OQ-007) and explicitly authorized building it now. Write access to
n8n MCP is authorized **for this workflow only**, scoped to that ID — the other 6 scenarios
remain read-only/design-only until they each get their own ID + explicit go-ahead, per
OQ-007's one-at-a-time pattern.

**Addendum (2026-07-03, via OQ-023):** owner clarified the "no live API calls" boundary was
intended to cover **writes** only. Read-only Limble API calls via the connected Limble MCP
server are sanctioned for pre-build verification. Writes to Limble/Coupa/EHS remain
forbidden; Coupa and EHS Insight have no MCP connected, so they stay blueprint-only either way.

**Addendum (2026-07-03, later same day):** owner lifted the morning's Hold on Step 1 and
explicitly authorized building into `WJSs6apAdVH5yKkq` ("lift Hold, deploy now"). Deployed
2026-07-03, 49 nodes, left inactive. Write authorization consumed for this workflow; the
remaining 5 scenarios stay design-only until each gets its own go-ahead.

**Addendum (2026-07-09) — TEST-PHASE SCOPE RELAXATION:** owner authorized (a) n8n MCP
**write** access across the Coastal workflows/data-tables/mocks for the test-execution phase
(no longer one-workflow-at-a-time), and (b) **live Limble API calls scoped to the sandbox
location `98472` ("Coastal 99 - Sandbox Test") only** — both reads and the workflows' own
writes (task create, comment post, status flip, instruction patch). Coupa and EHS Insight
remain fully mocked (no live calls); **prod Limble locations remain off-limits** — sandbox
`98472` only. Rationale: the mock-based test plans intercept Coupa/EHS but by design exercise
the real Limble sandbox, so execution cannot proceed without this. Rollback: on test teardown
the boundary reverts to read-only Limble + no writes, per the pre-go-live posture. Owner will
click "Execute Workflow" in the n8n editor for schedule-triggered workflows (Token Regen,
Step 2, Error Log Export, EHS Create) since those cannot be fired headless via MCP.

---

## OQ-004 — [resolved] EHS-side workflows have no error logging — port as-is

**Type:** PENDING DECISION
**Added:** 2026-07-01

**Question / Description:**
"Create WO From EHS Inspection" and "Update EHS Inspection From Limble WO" have zero
`onerror` chains, unlike the Coupa-side workflows which log to a shared datastore and
email a report every 15 minutes. Should this asymmetry be ported as-is or fixed?

**Resolution criteria:**
Owner decides whether to add error logging to the EHS side under the sanctioned-fixes
posture (OQ-001), or leave the gap intact.

**Resolved:** 2026-07-01
**Resolution:** Faithful port — no error logging added to the EHS-side workflows.
Matches current production behavior exactly. (Note: this decision did not cover Step 2,
which has the same gap on the Coupa side — tracked separately as OQ-008.)

---

## OQ-005 — [resolved] Coupa credential store: isolated n8n credential, not shared store

**Type:** PENDING DECISION
**Added:** 2026-07-01

**Question / Description:**
Make datastore `324` ("CLIENTS - API Acct Information and Key") holds the Coupa OAuth
client_id/secret and is filtered by a `client` field = `"coastal_waste (PROD)"`, implying
it's a shared, multi-tenant datastore across FM360's other clients, not Coastal-exclusive.
n8n has no equivalent multi-tenant credential store. Should the n8n port isolate Coastal's
credential into its own n8n credential entry, or should this be verified with FM360 first?

**Resolution criteria:**
Owner picks the credential model for the n8n port.

**Resolved:** 2026-07-01
**Resolution:** Use an isolated n8n credential scoped to this instance only, populated
with Coastal's Coupa client_id/secret. Do not attempt to replicate the shared/multi-tenant
datastore pattern in n8n. Per CLAUDE.md's Secrets constraint, do not propagate the real
plaintext secret values found in the blueprint exports into any new docs — track
credential rotation/migration into n8n's credential store separately.

**Addendum (2026-07-01, during Coupa Token Regeneration build-spec):** this decision only
covered *where client_id/secret live*, not how the derived `oauth_token` flows to the
three downstream Coupa workflows (#2/#3/#4), since n8n credentials can't be written back
to from inside a workflow the way Make's `AddRecord` could. Resolved as part of scaffolding
"Coastal - Coupa Token Regeneration": faithful port — the workflow still calls Coupa's
`/oauth2/token` endpoint itself and writes the refreshed token to a dedicated n8n Data
Table (trimmed schema, not the full 7-field datastore record), rather than switching to
n8n's native OAuth2-credential auto-refresh (that would make this scheduled workflow
functionally vestigial, a bigger behavior change than OQ-005 sanctioned — flagged, not
taken). Consequences locked in for the build spec:
- The original `datastore:SearchRecord` lookup module is dropped entirely — client_id/secret
  come from an n8n **Custom Auth** generic credential (`httpCustomAuth`, a JSON blob merged
  into the outgoing request at send time) rather than a datastore read.
- `scope` (not itself secret) is hardcoded as a literal in the HTTP node, same treatment as
  `grant_type` already gets in the source blueprint. Verify the literal value against a live
  token call before go-live — blocked by OQ-003 (no live API calls this phase).
- Downstream workflows #2/#3/#4 (not yet built) will need to read the token from this new
  Data Table instead of datastore 324 — carry this forward when their build specs are written.
- Full node-level detail in `docs/build-specs/coupa-token-regeneration-build-spec.md`.

---

## OQ-006 — [resolved] Error Log Export drain race: fix to delete only exported records

**Type:** PENDING DECISION
**Added:** 2026-07-01

**Question / Description:**
"Coastal - Coupa Integration Error Log Export" does: Search (filtered on `timestamp exists`)
→ email the matched records to ethan@fm360consulting.com → `DeleteAllRecords`, which
wipes the entire datastore (326), not just the rows that were searched and emailed. A
record written between the Search and the Delete would be silently dropped, never
reported. Port this race condition as-is, or fix it?

**Resolution criteria:**
Owner decides whether to change the delete step to target only the exported record IDs.

**Resolved:** 2026-07-01
**Resolution:** Sanctioned fix — the n8n port should delete only the records that were
actually searched/exported in that run, not the entire table. Closes the race window
between Search and Delete.

---

## OQ-007 — [resolved] Target n8n workflow IDs needed per workflow

**Type:** BLOCKER
**Added:** 2026-07-01

**Question / Description:**
No n8n workflow IDs have been assigned yet for any of the 7 scenarios. Per CLAUDE.md's
constraints section, each target workflow must be created against a named ID from the
project owner — write only to the named ID, and track superseded/old IDs so they
aren't reused by accident. Per this session's decision (see OQ-003), n8n MCP is
authorized for read-only lookups/validation now, but not for creating/deploying
workflows until IDs are assigned.

**Resolution criteria:**
Owner provides one n8n workflow ID per scenario (or confirms IDs will be issued
one at a time, right before each workflow is built). Record the scenario-name →
workflow-ID mapping here or in a dedicated constraints doc once received.

**Progress (2026-07-01):** owner had already provisioned empty workflow shells for all 7
scenarios in the n8n instance before this was asked — found via `n8n_list_workflows` while
building the Token Regeneration spec (not something the owner listed out manually). All 7
IDs recorded below.

| Scenario | Workflow ID | n8n workflow name | Status |
| --- | --- | --- | --- |
| Coupa Token Regeneration | `oCAl4h0SZenEtbNs` | Coupa - Token Refresh | **Built** 2026-07-01 |
| Create Requisition in Coupa (Step 1) | `WJSs6apAdVH5yKkq` | Coupa - Create Requisition (Step 1) | **Built** 2026-07-03 (inactive; Limble cred = "Gerald Limble Sandbox" for test, swap to prod at cutover) |
| Check For New PRs Ordered (Step 2) | `WYJyHdQGcdeD8wEr` | Update Limble WO on New PRs (Step 2) | **Built** (confirmed 2026-07-07 via direct n8n read); inactive; OQ-008 error-log subgraph added 2026-07-09 (now 26 nodes) — OQ-029 resolved |
| WO Completed; Update Coupa PO (Step 3) | `NH1giNups8iICMZe` | Coupa - Update PO on WO Created (Step 3) | **Built** 2026-07-07 (13 nodes, inactive, validate clean); Limble cred = "Gerald Limble Sandbox" for test, swap to prod at cutover |
| Create WO From EHS Inspection | `isLUx7cUjkmKggD2` | Create WO from EHS Inspection | **Built** 2026-07-08 (29 nodes, inactive, validated clean); Limble cred = "Gerald Limble Sandbox" for test; EHS credential not yet created on instance, placeholder id in the node config |
| Update EHS Inspection From Limble WO | `8JvtesynrYtZbw7U` | Update EHS Inspection From Limble WO | **Built** 2026-07-08 (13 nodes, confirmed live 2026-07-09; inactive) — see `docs/build-specs/ehs-update-inspection-build-spec.md`; internals not re-audited this pass |
| Coupa Integration Error Log Export | `hR5YnDixecDz9HzJ` | Coupa - Integration Error Log Export | **Built** 2026-07-01 (confirmed 2026-07-07 via direct n8n read: 7 nodes, OQ-006 partial-delete fix present); inactive |

**Resolved:** 2026-07-01 — all 7 IDs are known. Write authorization (per OQ-003's addendum)
still applies one scenario at a time as each is explicitly greenlit for building, not all 6
remaining just because the IDs are now known.

---

## OQ-008 — [resolved] "Check For New PRs Ordered & Update Limble WO" (Step 2) has no error handling

**Type:** OPEN QUESTION
**Added:** 2026-07-01

**Question / Description:**
Blueprint walk of `Coastal - Check For New PRs Ordered & Update Limble WO (Step 2) (PROD).json`
found zero `onerror` chains (confirmed via raw `"onerror"` string count = 0). This is a
Coupa-side workflow — it polls every 5 minutes for PR/PO approval status — yet unlike
"Create Requisition" (Step 1) and "WO Completed" (Step 3), it never writes to the shared
error-log datastore (326) or otherwise surfaces failures. This wasn't covered by the
EHS-error-logging decision in OQ-004, which was scoped to the EHS-side workflows only.

**Resolution criteria:**
Owner decides: faithful port (Step 2 stays silent on error, consistent with current
production behavior), or sanctioned fix (add it to the same error-log-datastore +
15-min email-export pattern used by Step 1/Step 3). Record the decision and date here.

**Resolved:** 2026-07-03
**Resolution:** Sanctioned fix — add error logging. Step 2 becomes a third writer to the
shared **"Coastal - Coupa Integration Error Log"** Data Table (`6GbR5Rxezl7hqk9i`, alongside
Step 1/Step 3), with an admin @-mention comment on the WO, mirroring Step 1's converged error
subgraph (§4.9). Since the source has no `onerror` branches to port literally, the n8n design
adds "Continue (using error output)" on the failure-prone calls (Coupa GET requisition / GET
purchase_orders, updateATask, the two comment POSTs) feeding one shared subgraph that writes
`{limbleWONum, errorCode, errorMsg, timestamp=now ISO}` → GET admin 317887 → @admin comment,
then continues the loop (per-task isolation). Exact error-message wording proposed generic,
owner sign-off at build. Joins the sanctioned-fixes list. Detail: Step 2 build spec §4.2.

---

## OQ-009 — No authoritative Coupa/Limble/EHS API reference material found in repo

**Type:** OPEN QUESTION
**Added:** 2026-07-01

**Question / Description:**
CLAUDE.md's "Reference material" section is still an unfilled template placeholder.
The only materials found in `docs/` are two narrative .docx review documents (Coupa and
EHS integration reviews) and `functions.js` (custom IML/JS function bodies). Neither is
an API reference (e.g. a Swagger/OpenAPI spec or Postman collection) for Limble, Coupa,
or EHS Insight. Detailed field-level specs (e.g. Coupa Account segment structure,
Limble instruction/task schema) will be needed to write build-ready specs, especially
for the account-code mapping logic described in the Coupa review doc (entity, location,
GLAccount, department, commodity segments).

**Resolution criteria:**
Owner confirms whether such reference material exists elsewhere (even if mis-named,
per CLAUDE.md's guidance on mis-labeled Swagger/Postman files) and provides a pointer,
or confirms none exists and field-level facts must be reverse-engineered from the
blueprint mappers and docx review docs alone.

---

## OQ-010 — [resolved] Email delivery: Ionos integration, dev-mode recipient override

**Type:** PENDING DECISION
**Added:** 2026-07-01

**Question / Description:**
All 7 n8n workflows that send email — error notifications and reports (e.g. "Coupa
Integration Error Log Export", which currently emails ethan@fm360consulting.com) —
need a delivery mechanism and a recipient policy for the build/pre-launch period.

**Resolution criteria:**
Owner decision on integration choice and dev-phase recipient handling.

**Resolved:** 2026-07-01
**Resolution:** Use the **Ionos** email integration/node for all email-sending in the
n8n builds (replaces whatever Make used for `email:ActionSendEmail` / similar).
Preserve the real production receiver addresses in each workflow's config (e.g.
ethan@fm360consulting.com for the error log export) — do not delete or hardcode over
them. Until go-live, override the actual send-to address so all emails route only to
gerald@fm360consulting.com. Applies to every email-sending node across all 7
workflows. Re-enable real recipients when owner confirms go-live.

---

## OQ-011 — [resolved] Schedule trigger timezone: fixed MST offset vs. DST-aware Mountain Time

**Type:** OPEN QUESTION
**Added:** 2026-07-01

**Question / Description:**
`docs/workflow-list.md` records this workflow's trigger as "Daily @ 12:00AM (MST)" (and
"Create WO From EHS Inspection" as "Daily @ 4:00PM (MST)"). Make.com scenario schedules
aren't part of the blueprint JSON export, so the literal timezone configured on Make's side
isn't independently verifiable from these files alone. "MST" could mean a fixed UTC-7 offset
year-round, or it could be shorthand for "Mountain Time" (America/Denver), which shifts to
MDT (UTC-6) during daylight saving. This matters for exact trigger-boundary fidelity
(OQ-002) — an n8n Cron/Schedule Trigger node needs one or the other set explicitly.

**Resolution criteria:**
Owner confirms which was actually configured in Make (or confirms it doesn't matter enough
to verify and a DST-aware `America/Denver` assumption is fine). Applies to both daily
schedule triggers (Token Regeneration, Create WO From EHS Inspection).

**Resolved:** 2026-07-01
**Resolution:** DST-aware Mountain Time — set n8n Schedule Trigger nodes to `America/Denver`.
Applies to both daily-schedule workflows (Token Regeneration, Create WO From EHS Inspection).

---

## OQ-012 — [resolved] Error log `timestamp`: native Date column + Mountain-time display

**Type:** PENDING DECISION
**Added:** 2026-07-01

**Question / Description:**
Datastore 326's `timestamp` field is written by Step 1/Step 3's `onerror` handlers (neither
built yet) as a pre-formatted display string, inconsistently: `"MM/DD/YYYY hh:mm A"` in some
handlers, `"MM/DD/YY hh:mm A"` in others, one long-form `"Eastern Standard Time"` — all
hardcoded EST, not DST-aware. Since "Coupa Integration Error Log Export" is the first
workflow built against this shared table, it effectively defines the schema Step 1/3 must
later match. Keep the format-string-as-is (faithful, kicks cleanup downstream), or fix now?

**Resolution criteria:**
Owner decides column type (string vs. native Date) and, if native, what timezone the report
email should display timestamps in.

**Resolved:** 2026-07-01
**Resolution:** Sanctioned fix, decided while scoping "Coupa Integration Error Log Export"
build spec — two parts:
1. `timestamp` column on the new "Coastal - Coupa Integration Error Log" Data Table is a
   native **Date** type, not a formatted string. Step 1/3's future `onerror`-equivalent write
   steps must write a real ISO/date value — carried forward as a dependency for their specs.
2. The report email displays `timestamp` formatted in **America/Denver (Mountain)**, not EST
   — the source's hardcoded EST looks like a dev mistake given Coastal's own schedules use
   Mountain Time elsewhere (OQ-011).

Full detail: `docs/build-specs/coupa-error-log-export-build-spec.md` §4.

---

## OQ-013 — "Coupa Integration Error Log Export" has no self-error-handling

**Type:** OPEN QUESTION
**Added:** 2026-07-01

**Question / Description:**
Blueprint walk of `Coastal - Coupa Integration Error Log Export.json` found zero `onerror`
chains — a failure in this workflow itself (e.g. the SMTP send failing) is silent in
production. This is a third instance of the asymmetric-error-handling pattern already
tracked for the EHS side (OQ-004, resolved as faithful-port) and Step 2 (OQ-008, still open)
— but this one wasn't individually decided when OQ-004 was resolved, since OQ-004 was scoped
to the EHS workflows only. Surfaced while writing this workflow's build spec.

**Resolution criteria:**
Owner decides: faithful port (this workflow stays silent on its own failures, consistent with
current production behavior), or sanctioned fix (e.g. a direct failure-alert email, similar to
what Token Regeneration got under its own sanctioned fix). Record the decision and date here.

---

## OQ-014 — Confirm timezone(s) w/ Coastal — MST vs EST vs mixed

**Type:** OPEN QUESTION
**Added:** 2026-07-01

**Question / Description:**
OQ-011 assumed America/Denver (Mountain, DST-aware) for the two daily schedule triggers, and
OQ-012 assumed the source's hardcoded EST error-timestamp strings were a dev mistake and
switched display to Mountain — neither was confirmed directly with Coastal. Source blueprints
literally hardcode "EST"/"Eastern Standard Time" in multiple `formatDate` calls (Step 1/3
`onerror` handlers), which could mean FM360's dev environment runs Eastern while Coastal's
actual business/schedule intent is Mountain — i.e. a real split, not just a typo. Need the
client to confirm: (1) Coastal's actual business timezone, (2) whether the EST strings in the
blueprint were intentional or an artifact of the original developer's own clock, (3) whether
any schedule/report genuinely needs to run on Eastern rather than Mountain.

**Progress (2026-07-03, Limble MCP recon):** every one of Coastal's ~49 Limble locations has
`timezone: America/New_York` — the company is entirely Eastern (FL/GA/SC sites). This cuts
against OQ-011/OQ-012's America/Denver assumption: the blueprints' hardcoded "EST" now looks
intentional, and the "MST" in `docs/workflow-list.md` looks like the actual error.
Recommendation pending owner confirmation: flip OQ-011/OQ-012 to America/New_York (schedule
triggers and error-report display). Token Regen is already built with America/Denver — would
need a one-line schedule change if confirmed.

**Resolution criteria:**
Coastal (or FM360's point of contact) states explicitly which timezone(s) apply to which
workflows — confirming or overriding OQ-011/OQ-012's assumptions. Update those two entries
with the confirmed answer once received.

---

## OQ-015 — [resolved] API credentials needed per external system

**Type:** BLOCKER
**Added:** 2026-07-02

**Question / Description:**
Each of the 7 workflows needs live credentials for the external systems they call. None of
these are inlined in the blueprint exports (except the exposed EHS key). Real values must be
supplied and stored in the n8n credential store only (per OQ-005) — never written to any repo
file. Required:

| System | Purpose | Auth type | Status |
| --- | --- | --- | --- |
| **Limble** (CMMS) | all Limble reads/writes (was `fuse-limble-app:*`) | API client_id/secret (key) | **Received** 2026-07-02 (in `.env`) |
| **Coupa** (procurement) | Token Regen + Step 1/2/3, host `coastalwasteinc.coupahost.com` | OAuth2 client_id/secret | **Needed** — not in repo; pullable from Make datastore `324` (see below) |
| **EHS Insight** (safety) | Create WO From EHS, Update EHS From Limble | `X-ApiKey` header | **Value known — rotation only.** Not awaiting a value |
| **Ionos** (email) | all outbound email (dev-routed to gerald@fm360consulting.com, OQ-010) | SMTP user/pass | Needed |

**Progress (2026-07-02):**
- **Limble** — received; owner added them to the project `.env`.
- **EHS Insight** — the API key value is *already known*: it sits as a literal in both EHS
  blueprint exports (`apikey-160448cf-4e25-4a16-a7b3-170a56743a37`, 9 occurrences — CLAUDE.md/
  DEPLOYMENT.md say 8, actual count is 9). So we are **not** awaiting a value — we can test with
  it today. What is owed is a **rotation**: it's exposed in plaintext, so Coastal must issue a
  fresh key and only the new one goes into the n8n credential. Testing can proceed on the current
  key in the meantime.
- **Coupa** — **not** in the repo. Every Coupa cred reference in the blueprints is a datastore
  lookup, never a literal: `{{2.data.client_id}}` / `{{2.data.client_secret}}` (from Make
  datastore `324`, client `coastal_waste (PROD)`) and `{{N.data.oauth_token}}` / `access_token`
  (the daily token). Datastore `324` is not exported to JSON (Make cloud only), so we don't know
  the values from this repo. **Source:** whoever has access to Make datastore `324` can read the
  client_id + client_secret directly there. Do **not** bother grabbing the `oauth_token`/
  `access_token` — it's ephemeral, regenerated daily by the Token Regeneration workflow; once
  client_id/secret are in the n8n credential, our Token Regen workflow mints its own.

**Note:** per OQ-005 / CLAUDE.md, credentials belong in the n8n credential store only, not repo
files. The `.env` should be treated as a temporary hand-off drop, not the store of record —
move the Limble creds into an n8n credential and remove them from `.env` before/at build time.
Repo is not a git repo currently, so no commit-leak risk today, but that could change.

**Resolution criteria:**
Coupa client_id/secret (from datastore `324`) and Ionos SMTP credentials supplied and loaded into
n8n credentials; EHS key rotated and the new value loaded into n8n. Mark each row done as it
lands; close when all are in n8n. (EHS value is already usable for testing before rotation.)

**Resolved:** 2026-07-03
**Resolution:** All four systems loaded into the n8n credential store: Limble (moved from
`.env`, `.env` scrubbed), Coupa client_id/secret, rotated EHS Insight key, Ionos SMTP.

---

## OQ-016 — [resolved] Step 1: auth inside Make connection 1766 (3 unauthenticated Coupa lookups)

**Type:** OPEN QUESTION
**Added:** 2026-07-02

**Question / Description:**
In the Step 1 blueprint, 4 of the 7 `coupa:makeApiCall` modules send an explicit
`Authorization: Bearer {{13.data.oauth_token}}` header (supplier lookup, create requisition
x2, add attachment) — but the other 3 (users?login=, addresses?name=, accounts?segment-...)
send **no auth header at all**. They work in prod, so authentication must live inside Make
connection `1766` (the custom Coupa app's connection), which isn't part of the blueprint
export. The n8n port (spec §4.2) assumes **Bearer-token-for-all** — uniform use of the daily
token from the "Coastal - Coupa OAuth Token" Data Table.

**Progress (2026-07-03, from OQ-024 comment sweep):** the only real task that ever reached the
Coupa create-requisition POST (task 1953) **failed there twice** with the generic create-req
`onerror` comment — after all Limble lookups passed. That makes a Coupa-side auth/payload
problem the prime suspect for the integration's real-world non-function, and raises the stakes
on this question: the failing POST (module 17/15) is one of the 4 calls that *does* send the
explicit Bearer header, so if even the Bearer-authenticated calls were failing, either the
token was bad/expired at that time or the payload was rejected (400). Pulling the Make log for
1953's runs (see OQ-024) would distinguish auth (401/403) from payload (400) and directly
inform whether the Bearer-for-all assumption is safe.

**Resolution criteria:**
Either (a) someone with Make access opens connection 1766 and reports what credential it
carries, or (b) first live test run confirms the 3 lookups accept the Bearer token (no 401/
403). If the connection holds a different credential with different permissions, the spec's
auth section needs revisiting. **Note (2026-07-03):** path (b) is now the only pre-go-live
diagnostic — the historical Fuse logs that could have shown the 1953 Coupa error are erased
(see OQ-024), so connection 1766's live behavior can only be learned by opening it in Make
(a) or by the first live test (b).

**Resolved:** 2026-07-03
**Resolution:** Owner's call — proceed on the **Bearer-for-all** assumption: all 7 Coupa calls
(the 4 that already send `Authorization: Bearer <token>` plus the 3 lookups that sent no header
in the export) use the daily OAuth token from the "Coastal - Coupa OAuth Token" Data Table, as
spec §4.2 already assumed. This is a decision to build on, not an independent verification —
connection 1766 was not opened and the historical logs are gone (OQ-024), so the one remaining
confirmation is the first live test: if any of the 3 lookups return 401/403, revisit auth then.
No spec change needed; §4.2 stands.

---

## OQ-017 — [resolved] Step 1: "Add Quote" onerror logs wrong module's error — fix?

**Type:** PENDING DECISION
**Added:** 2026-07-02

**Question / Description:**
Module 24 ("Add Quote to Requisition") has an `onerror` chain whose error-log write (module
26) records `{{17.error.message}}` / `{{17.error.type}}` — module **17** is Create
Requisition, which by that point has already *succeeded*. Copy-paste bug in the source: an
attachment failure logs an empty/wrong error instead of its own. (`24.error` is referenced
nowhere in the file — confirmed.) Proposed sanctioned fix (spec §4.6): the n8n Add Quote
error branch logs the Add Quote node's actual error. Note the spec's branch-merge (§4.5)
makes literal replication of the bug awkward anyway — the faithful option would be
deliberately re-implementing a wrong reference.

**Resolution criteria:**
Owner approves (recommended) or rejects the fix. Log the decision + date here; if approved,
it joins OQ-005/OQ-006/OQ-012 on the sanctioned-fixes list.

**Resolved:** 2026-07-03
**Resolution:** Approved — sanctioned fix. The n8n Add Quote error branch logs the Add Quote
node's own `error.message`/`error.name`, not module 17's (Create Requisition's) error. Joins
OQ-005/OQ-006/OQ-012/OQ-021 on the sanctioned-fixes list. Spec §4.6 stands as written.

---

## OQ-018 — Step 1: listUsers limit=500, no pagination — silent miss past 500 users

**Type:** OPEN QUESTION
**Added:** 2026-07-02

**Question / Description:**
Step 1 fetches all Limble users in a single `listUsers limit=500` call and scans the result
for the location's "Site Manager" account (`CoastalSiteManagerExtract`). If Coastal ever
exceeds 500 Limble users, the site manager can silently drop out of the fetched page and
every requisition for that location fails with "Site Manager not found in Coupa" (misleading
message — the miss would actually be on the Limble side). Faithful port keeps the single
call; a paginate-all fix would be a sanctioned-fix candidate.

**Progress (2026-07-03, Limble MCP recon):** Coastal has **79 Limble users total** — 16% of
the 500 cap. The single-page fetch is safe for the foreseeable future; faithful port carries
no near-term risk. Also observed: 38 "Site Manager" accounts (firstName convention confirmed,
View Only role per location), but **16 of the 38 are inactive** — locations whose only site
manager is inactive fail the lookup today in prod (error path A) exactly as they would in the
port; as-is behavior, not a migration regression.

**Resolution criteria:**
Owner decides faithful (single page, current spec default, §4.10) vs. sanctioned paginate
fix. Knowing Coastal's current Limble user count would inform this.

---

## OQ-019 — Hardcoded Limble admin user 317887 in all Step 1 error paths — who is it?

**Type:** OPEN QUESTION
**Added:** 2026-07-02

**Question / Description:**
Every Step 1 error path (site-manager/location/account miss, create-req/add-quote onerror)
fetches Limble user ID `317887` and @mentions them in the task comment. The ID is hardcoded
6 times. Spec ports it as the same literal (faithful). Worth confirming: who is user 317887,
are they still active/correct as the escalation contact, and should the n8n port keep the ID
inline or hoist it somewhere more visible?

**Progress (2026-07-03, Limble MCP recon):** user `317887` = **Brandon Ray Freckleton**
(bfreckleton@coastalwasteinc.com, 954-574-7017), **active**, Super User (org-wide) + Manager
role at every location. Identity confirmed; remaining question is only whether he stays the
escalation contact for go-live.

**Resolution criteria:**
Owner confirms the identity and that the ID stays valid for go-live (or supplies a
replacement). Note: Step 3 likely has the same pattern — check when its spec is written.

---

## OQ-020 — Limble webhook re-registration at cutover (hooks 775/776/777 → n8n URLs)

**Type:** OPEN QUESTION
**Added:** 2026-07-02

**Question / Description:**
Three scenarios are Limble-webhook-triggered, each with its own Make hook: Step 1 (hook 776,
new task comment), Step 3 (hook 777, task completed), Update EHS From Limble WO (hook 775,
task completed). The hook definitions live in Limble/Make config, not the blueprint exports —
at cutover, each must be re-pointed (or re-created in Limble) at the corresponding n8n
production webhook URL, and the Make scenarios deactivated so both engines don't process the
same events. Who has access to Limble's webhook admin, and is a side-by-side window (both
firing) acceptable or must the swap be atomic per workflow?

**Progress (2026-07-03, Limble MCP recon):** `get_webhooks` shows exactly **3 webhooks on
Limble's side, all type "task", all enabled**: webhookIDs `1742`, `1743`, `1744`, pointing at
`https://hook.fuse.limblecmms.com/<mailbox>` URLs. These are the Limble-side registrations of
Make hooks 775/776/777 (Limble webhookID ≠ Make hook ID; which maps to which scenario isn't
determinable read-only — the mailbox strings are opaque). Cutover = re-point/replace these 3
registrations with the n8n production webhook URLs.

**Resolution criteria:**
Owner states the cutover mechanics (who, when, atomic vs. overlap) — likely belongs in
DEPLOYMENT.md once decided. Non-blocking for specs/builds; blocking for go-live.

---

## OQ-021 — [resolved] Step 1 spec: sign-off on proposed consolidations (§4)

**Type:** PENDING DECISION
**Added:** 2026-07-02

**Question / Description:**
`docs/build-specs/coupa-create-requisition-step1-build-spec.md` §4 proposes several
behavior-neutral consolidations that go beyond mechanical translation and were not
individually pre-approved (owner was away when asked, 2026-07-02): drop dead modules
(comments Feeder/Aggregator 79/80/81, unused due-date var), merge the two identical dollar
branches into one tail (single Create Requisition node + IF >$500 for the attachment;
normalizes the success-comment `!` inconsistency; drops 2 of 3 sleeps as branch-duplication
artifacts, keeps the 2s pre-attachment wait), converge the 5 near-identical error paths into
one shared subgraph, and combine the two sequential `updateATask` PATCHes into one. All
load-bearing filters/gates preserved exactly. Precedent: error-log-export spec's 5-module →
1-Code-node collapse.

**Resolution criteria:**
Owner reviews spec §4 and approves as-is or names items to revert to literal 1:1. Also the
per-question record of the 2026-07-02 ask: scope (spec-only assumed — build still needs its
own go-ahead), Coupa auth (OQ-016), onerror bug (OQ-017).

**Resolved:** 2026-07-03
**Resolution:** Approved as-is. All §4 consolidations sanctioned: dropped dead modules
(comments Feeder/Aggregator 79/80/81, unused due-date var), merged dollar branches into
one tail (single Create Requisition node + IF >$500 for attachment, normalized
success-comment `!` inconsistency, dropped 2 of 3 sleeps keeping the 2s pre-attachment
wait), converged 5 error paths into one shared subgraph, combined the two sequential
`updateATask` PATCHes into one.

---

## OQ-022 — [resolved] Step 1 improvement candidates awaiting sanction

**Type:** PENDING DECISION
**Added:** 2026-07-02

**Question / Description:**
Surfaced during owner-requested improvement/excess review of the Step 1 spec (2026-07-02,
owner away when asked — none of these are in the spec's default build path yet). Each is a
behavior change requiring individual sanction per OQ-001; unselected items stay faithful.

1. **Idempotency guard** (recommended): exit early if `task.meta1` is already populated.
   Migration-specific risk: Make serializes scenario runs, but n8n webhook executions run
   **concurrently** — two rapid status flips or a webhook redelivery could both pass the
   "status == PO Create" gate before either flips the status, creating **duplicate Coupa
   requisitions**. One IF node after the task fetch closes it.
2. **Retry on GET lookups only** (recommended): Retry On Fail (3x) on the 4 Coupa GET
   lookups (users/addresses/accounts/suppliers). Never on the Create Requisition or Add
   Attachment POSTs — a retry after a timeout can double-create. Source has no retries;
   today a transient 5xx ends the run and a human must toggle the status to re-fire.
3. **Attachment matched by instruction text, not position**: quote link currently read from
   the 5th instruction positionally (`6.array[5].response`); every other field matches by
   instruction text. Template reordering silently breaks or mis-attaches.
4. **Server-side user filter**: replace the 500-user fetch + client-side scan
   (`CoastalSiteManagerExtract`) with a location-filtered Limble users call, if the API
   supports it (unverifiable until build — OQ-003). Would also moot OQ-018's pagination
   ceiling.
5. **Status-ID handling**: recommendation is keep the runtime name lookups (`%PO Create%` /
   `%PO Requested%`) — 2-3 extra calls per run buys resilience to Limble statusID churn.
   Decide only if owner prefers hardcoded IDs.
6. **Native OAuth2 credential** (flagged, NOT recommended now): n8n OAuth2 credential
   auto-refresh would delete the Token Regen workflow + token Data Table entirely. Rejected
   during Token Regen build; that workflow is already built and validated — raising it again
   means rework. Recorded for completeness.

Also verify at test (not sanction items): `need-by-date` receives raw Limble `due` (epoch);
Coupa either coerces it or the field's been riding empty — check what prod PRs actually show.

**Progress (2026-07-03, Limble MCP recon):**
- Item 3 (attachment by position): the quote-upload instruction ("Upload the Contractor's
  Quote Here for Coupa", type 9) **is currently at position 5** on the live template
  (task 965, 17 instructions) — the positional read works today; the fix remains
  future-proofing, not a live bug.
- Item 4 (server-side user filter): the Limble users endpoint exposes filters for
  users/name/roles/teams only — **no location filter**. Roles repeat per location (role
  "View Only" = roleID `79212`-ish per location pairing), so a role filter still needs the
  client-side location match. Item 4 is likely **infeasible as imagined** — recommend
  dropping it and keeping the faithful fetch-and-scan (which OQ-018's 79-user count makes
  harmless anyway).
- `due` is a unix epoch, consistently 11:59:59 PM local (e.g. `1783655999`) — confirms the
  verify-at-test note's premise.

**Resolution criteria:**
Owner marks each numbered item sanctioned or faithful-port. Sanctioned items get folded into
the Step 1 build spec (§4) with this OQ referenced; then this closes.

**Resolved:** 2026-07-03
**Resolution:** Owner ruled on each item:
1. **Idempotency guard — SANCTIONED.** IF node after the task fetch: exit early if `task.meta1`
   is already populated. Closes the n8n-concurrent-execution duplicate-requisition risk (Make
   serialized runs; n8n does not). Joins the sanctioned-fixes list
   (OQ-005/006/012/017/021). Folded into spec §4.
2. **Retry on GET lookups only — SANCTIONED.** Retry On Fail (3x) on the 4 Coupa GET lookups
   (users/addresses/accounts/suppliers). **Never** on the Create Requisition or Add Attachment
   POSTs (retry-after-timeout can double-create). Folded into spec §4.
3. **Attachment matched by instruction text — FAITHFUL (not sanctioned).** Keep the positional
   `[5]` read. Recon confirmed the quote instruction sits at position 5 on the live template, so
   it works today; owner declined the future-proofing change. Stays 1:1 with source.
4. **Server-side user filter — DROPPED (infeasible).** Recon: Limble users endpoint exposes no
   location filter, so a server-side swap can't replace the client-side location match. Not
   pursued. Faithful fetch-and-scan stays (harmless at 79 users, OQ-018).
5. **Status-ID handling — FAITHFUL default.** Keep runtime `%PO Create%` / `%PO Requested%`
   name lookups (resilient to statusID churn); owner did not opt for hardcoded IDs.
6. **Native OAuth2 credential — REJECTED** (as at Token Regen build; would delete Token Regen
   + token Data Table, rework already-built workflow).

---

## OQ-023 — [resolved] Sanction read-only Limble MCP recon before Step 1 build (OQ-003 amendment)

**Type:** PENDING DECISION
**Added:** 2026-07-03

**Question / Description:**
A read-only Limble MCP server is now connected (`.mcp.json`). Using it means live Limble API
calls, which OQ-003's resolution forbids this phase ("no live API calls against Limble, Coupa,
or EHS Insight") — so it needs an explicit OQ-003 addendum, same as the n8n MCP read-only
carve-out got. If sanctioned, pre-build recon could close or inform several open items without
waiting for test phase:

- OQ-019: `get_users` lookup of hardcoded admin ID `317887` — identity + active status.
- OQ-018: paginated user count vs. the 500 cap; whether `get_users` supports a location filter
  (also informs OQ-022 item 4).
- OQ-020: `get_webhooks` — confirm hooks 775/776/777, event types, current Make URLs.
- Spec assumption checks: `get_statuses` ("PO Create" / "PO Requested" exact names + IDs),
  instruction texts + positional 5th quote slot on a real @CoupaWO task (OQ-022 item 3),
  real task `due` format (need-by-date question), `get_locations` name formats feeding
  `NumberToSpelledNumberConverter`, site-manager account convention
  (`firstName == "Site Manager"`, role "View Only").

Does not touch OQ-016 (Coupa-side) or the build go-ahead. First call on sanction:
`get_current_customer_info` to confirm the MCP points at Coastal's instance.

**Resolution criteria:**
Owner amends OQ-003 to allow read-only Limble MCP use (and says whether to run the recon
immediately), or declines and all verification waits for build/test phase. Record decision
+ date here and as an OQ-003 addendum if approved.

**Resolved:** 2026-07-03
**Resolution:** Approved — read-only Limble API calls via the MCP are permitted. Owner
clarified OQ-003's "no live API calls" was intended to cover writes only. Recon run
immediately on approval; findings recorded in OQ-018/019/020 and the Step 1 build spec.
OQ-003 addendum added same day.

---

## OQ-024 — [resolved] meta1 empty on every real CoupaWO task — Step 1 write / Step 2 read at risk?

**Type:** OPEN QUESTION
**Added:** 2026-07-03
**Resolved:** 2026-07-09

**Question / Description:**
Limble MCP recon (2026-07-03) swept all 504 incomplete + 1,335 recently-completed tasks
(completed since 2025-07-01) and found 54 tasks tagged `@CoupaWO;`: 46 are templates ("Main
WO Template (Limble-to-Coupa)", one per location) and only **8 are real tasks** (7 completed,
1 in-flight). **All 8 have `meta1` = null** — yet Step 1's whole correlation design stamps
`meta1` = Coupa requisition ID, and Step 2 reads `meta1` to poll PR→PO conversion (then
writes `meta2` = PO id; also null everywhere). Contrast: the EHS integration's `meta1` GUID
write shows up fine on its tasks (e.g. task 2405), so the API does surface meta fields.

Possible explanations, none confirmable read-only:
1. None of the 8 tasks ever completed the requisition path (e.g. all hit supplier-miss or
   other error routes, or statuses were never flipped to "PO Create") — i.e. the Coupa
   integration has ~zero successful prod volume in the past year.
2. Make's `updateATask` `metadata.meta1` write lands somewhere the v2 tasks API doesn't
   return as `meta1`.
3. Something downstream clears the fields.

Whichever is true matters: if (1), there is almost no real prod behavior to regression-test
against and cutover risk concentrates on the untested paths; if (2), the n8n port's PATCH
shape and Step 2's poll key both need re-verification against the real API.

Related recon facts: only statusIDs 0/1/2 ever observed (1 = "In Progress" per the statuses
endpoint; custom statuses "PO Create"/"PO Approved" are named verbatim in template
instruction 7 but never observed live on a task, and "PO Requested" appears nowhere except
the blueprints); the sole in-flight CoupaWO task (3199) sits at statusID 1 with no
instructions returned.

**Progress (2026-07-03, comment sweep of all 8 real tasks) — root cause is (1), not (2):**
Pulled every comment on the 8 tasks. Findings:
- **7 of 8 never entered the Coupa flow at all** — no status change to "PO Create", no
  integration comment. They carry the `@CoupaWO;` tag (created from the per-location template)
  but were used as plain work orders. So the tag count overstates real Coupa usage massively.
- **Only task 1953 ever ran Step 1** — status was set to "PO Create" on 2025-09-12, and again
  after a Pending→PO Create toggle on 2025-09-15. **Both runs failed**, each posting:
  "@Brandon Ray Freckleton, Task# 1953: An unexpected error occurred when creating the Coupa
  requisition. Please reach out to FM360 to resolve." (posted by integration user 308496).
- That exact string is the **`onerror` comment on the Coupa create-requisition module**
  (blueprint modules 17/15, `coupa:makeApiCall`) — confirmed by grep. It fires only *after*
  all four Limble→Coupa lookups (site manager, address, account, supplier) succeeded; a
  lookup miss would have posted a specific "…not found/does not exist in Coupa" comment
  instead. So the failure was the **actual Coupa PR POST**, not a Limble-side gap.

**Conclusion:** `meta1` is null because the requisition path has essentially never succeeded
in this instance — the one task that reached the Coupa POST failed there, twice. This is a
data/volume fact, not an API field-mapping trap. Hypothesis (2) (updateATask meta1 doesn't
surface) is downgraded to low probability — EHS's createATask meta1 surfaces fine (task 2405)
— but stays formally unverified until a successful Step 1 run exists to check. Two consequences
carried forward:
1. **No working prod baseline** — the Coupa integration cannot be regression-tested against
   real history. Cutover must validate against synthetic tasks driven through every path.
2. **The real-world failure was Coupa-side at create-requisition** — strong signal to
   prioritize OQ-016 (Coupa auth / connection 1766) and the PR payload shape. See OQ-016.

**Remaining to fully close:** ~~pull the Make execution log for task 1953's two runs~~
**Unrecoverable (confirmed 2026-07-03):** owner reports Make/Fuse execution logs from last
year are erased, so the actual Coupa HTTP error for 1953's runs (401 vs 400 vs missing field)
is gone and datastore 326 is not in the repo. We therefore **cannot** distinguish auth vs
payload as the historical failure cause. Consequence: the create-requisition call's
correctness rests entirely on (a) a faithful payload port from the blueprint mapper and (b) a
first live test at build. This pushes the OQ-016 (auth) question fully onto its verify-at-test
fallback — there is no history left to consult.

**Addendum (2026-07-03, owner reviewed Fuse Step-1 run history):** owner observed that runs
appear to die at module 136 ("Grab Task Comment") with "The bundle did not pass through the
filter", the failing condition being `{{2.description}} contains "@CoupaWO;"`. **This is the
designed gate, not a bug.** The link into 136 carries the filter "Is WO Coupa-Related AND PO
Create Status?" (`description contains @CoupaWO;` AND `task.statusID == PO Create ID`). The
webhook fires on *every* task comment in Coastal (the only pre-gate is
`status == "ADDED COMMENT TO TASK"`), so modules 19 + 2 run for every comment and 136 correctly
drops everything that isn't a @CoupaWO task currently in PO Create — i.e. ~all traffic. The
"never past 136" reading is contradicted by task 1953's downstream create-req error comments
(only postable from modules 17/15, far past 136), so the flow *did* clear 136 for 1953's two
genuine PO-Create events; those Sept-2025 runs have almost certainly aged out of Make's log
retention, leaving only recent firehose rejections visible. Verified live: 1953's description
is literally `"  @CoupaWO;"` and it was incomplete (status 0) at PO Create, satisfying module
2's `status=0` fetch and both 136 conditions. **Conclusion unchanged and reinforced:** the gate
is sound (port preserves it as-is), the real failure is Coupa-side at create-requisition, and
there is no observed successful Step 1 run to validate against — test with synthetic @CoupaWO
tasks driven to PO Create.

**Resolution criteria (revised 2026-07-03 — historical logs erased):** the 1953-log path is
dead. This now closes when a **synthetic Step 1 run succeeds post-build** and `meta1` is
observed populated on the task via the API — which simultaneously (a) proves the
create-requisition call works with the ported payload/auth, (b) formally clears hypothesis (2)
(updateATask meta1 surfaces), and (c) establishes the first working baseline the integration
has ever had. No pre-build diagnostic is available; correctness is a build-time test, not a
history lookup.

**Addendum (2026-07-06):** owner re-searched Fuse logs directly — no log for 1953, and the
neighboring runs (1955-1959) are also unreadable. Erasure re-confirmed; the log path stays
dead. Separately, the OQ-028 mock-rig run **partially satisfies the criteria**: (b) is now
PROVEN (`meta1=424242` observed via the API on task 4052 after a synthetic run) and (c) exists
against the mock. (a) remains open — the create-req call succeeded only against the mock's
guessed response shapes, so payload/auth acceptance by real Coupa is still unverified.
Interpretation note (owner asked 2026-07-06): a future live create-req rejection with a Coupa
validation error = inherited Fuse-era defect (1953 failed at the same POST); a 401/403 on the
three lookups = introduced by the OQ-016 Bearer-for-all decision, not inherited (1953's
lookups passed in Fuse). Where it dies is the diagnosis.

**RESOLVED (2026-07-09) — root cause is BOTH (1) and (2); (2) is the actionable one.** Live
Limble sandbox (loc 98472) create/PATCH calls proved the `/v2/tasks` API **rejects the
`metadata` object outright** — `` `metadata` is not allowed `` (HTTP 400) on BOTH POST and
PATCH. `meta1`/`meta2` are **top-level task fields**, not nested under `metadata`. So the Make
blueprint's `metadata.metaN` mapping never surfaced as API `meta1` (explanation 2), on top of
the near-zero real prod volume already established (explanation 1). Proof top-level works:
seeded task 4083 carries top-level `meta1=424242` + status 8055 after a create(top-level
meta1)+PATCH(statusID) sequence; existing fixtures 4052/4053 likewise.

**Sanctioned fix (owner-approved 2026-07-09, added to OQ-001 list): write top-level `metaN`,
not `metadata.metaN`, in every ported workflow.** Audit done 2026-07-09 across all three
Coupa workflows:
- **Step 2** (`WYJyHdQGcdeD8wEr`) node "Set 'PO Approved' Status and Save PO ID" WAS buggy
  (`metadata: { meta2: ... }` → would 400 live). **FIXED** → top-level `meta2`.
- **Step 1** (`WJSs6apAdVH5yKkq`) node "Update Task (meta1 + status)" was ALREADY correct —
  `JSON.stringify({ statusID, meta1: String(...) })`, top-level. No change needed. (This is
  why the earlier synthetic run stamped meta1=424242 on task 4052 — Step 1's write shape was
  always right; only Step 2's build diverged.)
- **Step 3** (`NH1giNups8iICMZe`) has no Limble task-write; reads `meta2` top-level. N/A.

Root cause was a build inconsistency between the two builders, not a systemic spec error.
**Still to do:** the Step 2 **build-spec doc** (`coupa-check-prs-step2-build-spec.md`, §72/§203)
still describes `metadata.metaN` — correct it to match the fixed workflow. See memory
`project_limble_create_task_api` for the full API contract (also: `statusID` not allowed at
create, `due`=epoch seconds, create-response = `{taskID}`).

**Also settled here (feeds OQ-025/OQ-026):** the sandbox (owner instance) task-status set has
NO "PO Approved" — only PO Create=8054, PO Requested=8055. A **budget** with a PO-Approved
state does NOT add a *task* status, so Step 2's runtime `%PO Approved%` lookup on `/v2/statuses`
returns nothing there. "PO Approved" must exist as a **task status** in the sandbox before S2-4
(the flip) can run/assert. (Coastal-prod task statuses were 5782/5783/5784; never reuse those
IDs against the sandbox — Step 2 looks statuses up by name, so no hardcoded-ID swap is needed.)

---

## OQ-025 — [resolved] "PO Requested"/"PO Approved"/"PO Create" status names confirmed via direct API

**Type:** OPEN QUESTION
**Added:** 2026-07-03

**Question / Description:**
Step 1's finalize path looks up the target status by name (`GET /v2/statuses?name=%PO
Requested%&limit=1`) and flips the task to it; Step 2 reads that same status. But **"PO
Requested" has never been observed live** — no task has ever reached it (consistent with Step 1
never succeeding in prod, OQ-024). The `get_statuses` MCP endpoint is unreliable (returns only
"In Progress"/statusID 1), so the exact spelling can't be confirmed read-only. If the real
Limble status name differs at all (spacing, casing, wording — cf. "Pending " with a trailing
space, which recon *did* observe), the `%PO Requested%` wildcard lookup returns 0 rows and the
**entire finalize path silently gates off**: the requisition gets created in Coupa but the task
is never flipped and `meta1` is never stamped, so Step 2 never picks it up. Confirmed real
statuses from recon: "PO Create", "Pending " (trailing space), "PO Approved" (template
instruction 7 only). "PO Requested" and "PO Create" are the two Step 1 depends on.

**Addendum (2026-07-03, Step 2 spec):** extend this to **"PO Approved"** as well. Step 2 both
reads "PO Requested" (to find WOs to poll) and writes/flips to "PO Approved" (module 20 lookup +
the §4.1 sanctioned flip, OQ-026). "PO Approved" has also never been observed live (named only
in template instruction 7 and the docx) — the docx is even internally inconsistent, calling the
first status both "PO Requested" and "PO Request Submitted". A mismatch on either makes the
`%...%` lookup return 0 rows and silently breaks Step 2's poll ("PO Requested") or its status
flip ("PO Approved"). Confirm exact strings for all three ("PO Create", "PO Requested", "PO
Approved") in the Limble UI.

**Progress (2026-07-03, Step 1 build):** owner opted to build Step 1 without confirmation
("not confirmed, keep as built"). Deployed with the runtime `%PO Requested%` lookup; on a
0-row result the n8n run halts at "Get PO Requested Status" (safer than source, which would
have PATCHed an empty statusID). Consequence of a mismatch unchanged: requisition created in
Coupa but task never flipped, `meta1` never stamped, Step 2 never picks it up.

**Addendum (2026-07-05, recon provenance + blueprint second-witness check):**
(a) Blueprint offers no independent confirmation of the strings: a full graph walk of Step 1/2
(filters, mappers, onerror) found no literal equality operator on any status name. Module 136
compares `{{2.statusID}}` to `{{19.body[1].statusID}}` — both sides fed by the same `%PO
Create%` wildcard lookup, circular. Module 3's `text:contain "to PO Create"` and the error
comments only witness "PO Create". "PO Requested"/"PO Approved" appear *only* inside the
`%...%` lookup URLs. The source scenario has the same blind spot as the port; a mismatch would
gate off silently there too (consistent with OQ-024).
(b) Owner raised that the Limble MCP is *currently* connected to their sandbox and was unsure
which instance the 2026-07-03 recon hit. Cross-evidence says recon was Coastal prod: task 1953
carried integration comments matching the blueprint onerror string verbatim (Sept 2025, user
308496), corroborated by owner's Fuse run-history review of the same task. Sandbox test data
would not contain that. Treat recon findings as Coastal-sourced but re-verify `get_statuses`
and the observed status set when the MCP is repointed at Coastal (owner will switch back after
finishing sandbox POST verification).

**Addendum (2026-07-06, MCP reconnected to Coastal — live re-verification):**
Confirmed instance: "Coastal Waste & Recycling" (enterprise). Findings:
1. **Recon provenance settled:** task 1953's comments match the blueprint onerror string
   verbatim (Sept 2025, integration user 308496) — the 2026-07-03 recon was Coastal prod.
2. **`get_statuses` quirk is real on Coastal, and worse than recorded.** Unfiltered
   `limit=100` returns exactly one row: "In Progress" (statusID 1). Wildcard mechanics work
   (`%In Progress%` matches), but `%PO%`, `%PO Requested%`, and `%Pending%` all return [].
   Even "Open" (witnessed in 1953's status-change comments) is absent. Decisive detail: task
   1953 carries `statusID: 2` and its own API `meta.status` link is `/v2/statuses?statuses=2`
   — which returns **[]**. The endpoint cannot resolve a statusID the API itself references.
   So an empty result does NOT prove a status doesn't exist; the endpoint returns a subset
   (or the custom statuses were deleted from config after Sept 2025 — indistinguishable
   read-only).
3. **Exact historical spellings, witnessed verbatim in 1953's status-change comments (Sept
   2025):** "Open", "In Progress", "PO Create", "Pending " (trailing space — "from Pending
   to PO Create" renders with a double space). **"PO Requested" and "PO Approved" have still
   never been witnessed anywhere live** — 1953 died at the Coupa POST, before Step 1's
   finalize lookup ever ran, so `%PO Requested%` returning a row has never been observed in
   the system's entire history. It is possible those statuses never existed in Coastal's
   Limble at all.
4. **Operational consequence:** if the deployed n8n workflow's Limble credential sees what
   the MCP key sees, Step 1 today halts at its status lookups on every run (0 rows from both
   `%PO Create%` and `%PO Requested%`). In Sept 2025 the `%PO Create%` lookup demonstrably
   returned a row (1953 passed module 136's statusID equality gate), so either the API's
   behavior, the key's visibility, or the status config changed since.

Two disambiguation paths: (a) Limble UI status list — settles existence AND spelling in one
screenshot; (b) manually execute the deployed Step 1 "Get PO Requested Status" node (read-only
GET with the workflow's own credential) — settles whether the MCP's empty result is key-scoped
visibility or API truth.

**Resolution criteria (revised 2026-07-06):**
Someone with Limble UI access confirms the custom statuses **exist** and their **exact**
name strings ("PO Requested", "PO Approved", "PO Create") — screenshot or verbatim copy. If
missing, they must be (re)created in Limble before cutover. Optionally corroborate via a
manual run of the deployed Step 1 lookup node. Update the Step 1 spec §3/§8 and Step 2 spec
§7 with the confirmed strings.

**Resolved:** 2026-07-06
**Resolution:** Owner pulled the full status list from Coastal Limble via a **direct API
call** (own credential, outside the MCP). All statuses exist, spellings match the blueprints
exactly:

| statusID | name | note |
|---|---|---|
| 0 | `Open` | default |
| 1 | `In Progress` | default — the only row the MCP tool returns |
| 2 | `Complete` | default — resolves the 1953 puzzle: its statusID 2 is plain "Complete" |
| 4764 | `Denied` | custom |
| 4765 | `On Hold` | custom |
| 4766 | `Pending ` | custom — **trailing space is real, in the official config** |
| 5782 | `PO Requested` | custom — Step 1 finalize / Step 2 poll |
| 5783 | `PO Approved` | custom — Step 2 flip (OQ-026 fix) |
| 5784 | `PO Create` | custom — Step 1 gate |

Consequences: (a) the deployed Step 1/2 `%...%` runtime lookups will match — no spec or
build change needed; (b) the 2026-07-06 "statuses may be absent" escalation is withdrawn —
the empty results were an **MCP-tool visibility artifact**, the real `/v2/statuses` endpoint
returns all 9 rows (quirk note updated: never use the MCP `get_statuses` tool for status
verification); (c) OQ-026's dependency on the exact "PO Approved" string is cleared;
(d) go-live checklist item "OQ-025 status-name check" is done. The historical Sept-2025
`%PO Create%` lookup success is now fully consistent: the API always had the statuses; only
the MCP tool couldn't see them.

---

## OQ-026 — [resolved] Step 2: blueprint never flips WO to "PO Approved" (docx says it should)

**Type:** PENDING DECISION
**Added:** 2026-07-03

**Question / Description:**
Step 2's blueprint fetches the "PO Approved" statusID (module 20) but the `updateATask` (module
15) never writes it — it sets `meta2` + description + `work_request` only, no `statusID`. So
module 20's lookup is dead and the WO is **not** flipped to "PO Approved". The Coupa Integration
Review docx (v1.2.0, final pre-go-live), §"Step 3: Checking for PR Ordering", explicitly states
the integration should "set the status of the Limble WO to the 'PO Approved' sub-status" (and
notes the status change drives progression to Step 4 while the separate comment drives the
assignee notification). Faithful literal port = no flip → the processed WO stays in "PO
Requested", gets re-selected by the next 5-min poll, and re-appends `|| Coupa PO# X` +
re-comments indefinitely. Never caught in prod because Step 1 has ~never succeeded (OQ-024), so
no WO ever reached this path. Fix to match docs, or port the bug literally?

**Resolution criteria:**
Owner decides faithful-vs-fix; docx treated as source of truth where it and the blueprint
disagree.

**Resolved:** 2026-07-03
**Resolution:** Sanctioned fix — wire module 20's "PO Approved" statusID into the n8n task
update so the WO is flipped, matching the docx (owner directive: docx is source of truth on
disagreements; the docx gives a clear, final answer here). The flip also serves as the natural
idempotency guard (flipped WOs drop out of the polled set, stopping the re-fire loop). Joins the
sanctioned-fixes list (OQ-005/006/008/012/017/021/022). Detail: Step 2 build spec §4.1.
Dependency: exact "PO Approved" status name must be confirmed (OQ-025, extended) — **cleared
2026-07-06**: confirmed `PO Approved`, statusID 5783 (OQ-025 resolution).

---

## OQ-027 — [resolved] Step 2: Coupa auth on the 2 Coupa calls — Bearer-for-all (matches OQ-016)

**Type:** OPEN QUESTION
**Added:** 2026-07-03

**Question / Description:**
Step 2's two `coupa:makeApiCall` modules (14 `GET api/requisitions/{meta1}`, 21 `GET
api/purchase_orders?...`) both use Make connection `1766` and send **no `Authorization` header**
in the export — the same shape as Step 1's 3 unauthenticated lookups. OQ-016 resolved *Step 1's*
Coupa calls to "Bearer-for-all" (daily token from the "Coastal - Coupa OAuth Token" Data Table).
Owner declined (2026-07-03) to auto-extend that decision to Step 2 — it needs its own call.

**Resolution criteria:**
Owner decides Step 2's Coupa auth: same Bearer-from-Data-Table pattern as Step 1 (spec's current
working assumption, unconfirmed), or something else. Same underlying uncertainty as OQ-016 —
connection 1766's real credential isn't in the export and the historical logs are erased
(OQ-024) — so the confirmation point is the first live test (401/403 on the 2 calls = revisit).
Only the two Coupa HTTP nodes' auth config depends on the outcome; nothing else in the Step 2
spec does. Detail: Step 2 build spec §4.3.

**Resolved:** 2026-07-06
**Resolution:** Owner decision — **Bearer-for-all**, same pattern as Step 1 (OQ-016): both
Step 2 Coupa calls send the Bearer token read from the "Coastal - Coupa OAuth Token" Data
Table (`QAj62weJaWmRBJ76`). Confirmation point unchanged: first live test; a 401/403 on
either call reopens this. Step 2 spec §4.3/§7 updated. Build itself remains on Hold pending
owner go-ahead (declined for now, 2026-07-06).

---

## OQ-028 — Mock-Coupa test rig: response shapes are guessed; cutover teardown checklist

**Type:** OPEN QUESTION
**Added:** 2026-07-05

**Question / Description:**
Owner sanctioned (2026-07-05) a pre-cutover test rig for Step 1:
- Limble sandbox seeded via local script + sandbox API key (owner-provided). Owner deletes
  location 98471 and recreates it as **"Coastal 99 - Sandbox Test"** (name verified against the
  §4 location transform: → "Coastal Ninety Nine"). Script creates the Site Manager user
  (firstName "Site Manager", View Only at that location), the 17-instruction template-shaped
  task (quote instruction at position 5), statuses "PO Create"/"PO Requested" (API if exposed,
  UI fallback), and the trigger comment.
- **Mock Coupa API**: new n8n workflow "Coastal - Mock Coupa API (TEST)" + data table
  "Coastal - Coupa Mock Capture (TEST)" — sanctioned under OQ-007. Returns canned responses,
  captures every inbound payload for diffing against spec §5. Error routes exercised via a
  `failMode` row in a small config table (payload markers can't reach the users/addresses
  lookups — their inputs are fixed); supplier failure via a `FAIL-SUPPLIER` contractor option.
- Real Step 1 workflow is the test target: Coupa base URL pointed at the mock; dummy token row
  inserted into "Coastal - Coupa OAuth Token" (`QAj62weJaWmRBJ76`); no real Coupa calls in test
  phase. Trigger = manual curl replay of the Limble webhook payload (shape from the blueprint
  gateway module) — no sandbox webhook registered, so webhook delivery itself stays untested
  until cutover (OQ-020 unchanged).

Two things keep this OQ open:
1. **Mock response shapes are reverse-engineered** from the blueprint mappers (OQ-009: no API
   spec). The rig proves Step 1 handles *expected* Coupa responses, not that expectations match
   Coupa reality. Real Coupa create-req acceptance (auth, payload, account segments) remains
   untested until first live call — OQ-016/OQ-024 confirmation points unchanged.
2. **Cutover teardown checklist — n8n side EXECUTED 2026-07-06** (owner: "reset n8n for
   deployment"): Step 1 deactivated; all 6 Coupa base URLs restored to
   `coastalwasteinc.coupahost.com` (verified by node read); dummy token row deleted (only the
   `Coastal_Waste (TEST)` row remains); 7 test rows purged from the error-log table (now
   empty); mock workflow `mSiLCsvOVdiSWOZP` + capture table `u7iAudMydWyhl7BJ` + config table
   `bZ78rLHH8sJfDbtN` deleted. Validation clean (only the 5 known false-positive
   error-subgraph warnings).
   **Deferred to go-ahead by owner decision (2026-07-06):** Limble credential swap sandbox →
   "Coastal Waste Limble" (`qn6u8jEK085DoHT8`) on all 16 Limble nodes. Full go-ahead sequence:
   (1) credential swap, (2) activate Token Refresh `oCAl4h0SZenEtbNs` + run once (dummy token
   gone — Step 1 halts without a real token), (3) activate Step 1, (4) register Limble webhook
   at `https://fm360.n8n.fm360consulting.com/webhook/coastal-coupa-create-requisition-step1` +
   disable Fuse scenario (OQ-020), (5) verify "PO Requested" in prod Limble UI (OQ-025).
   Limble sandbox fixtures (location 98472, template 4041, tasks 4052-4060) left in place —
   owner may clean up or reuse.

**Rig deployed (2026-07-05):**
- Mock workflow `mSiLCsvOVdiSWOZP` "Coastal - Mock Coupa API (TEST)", ACTIVE, base URL
  `https://fm360.n8n.fm360consulting.com/webhook/mock-coupa/api/...`. Smoke-tested (users
  route: 200, correct array shape, query echo, capture row written).
- Capture table `u7iAudMydWyhl7BJ`, config table `bZ78rLHH8sJfDbtN` (failMode row).
- Dummy token row id 2 in `QAj62weJaWmRBJ76` (`client=coastal_waste`, token
  `MOCK-TOKEN-OQ028-DELETE-AT-CUTOVER`).
- Step 1's 6 Coupa nodes' URLs swapped to the mock base (host substring only; paths, query,
  auth headers untouched).
- Local tooling: `tools/sandbox-seed/` (seed.py, fire.sh, README with UI checklist).

**Side discovery (2026-07-05):** the token table already held a row `client="Coastal_Waste
(TEST)"` with a JWT issued by `coastalwasteinc-test.coupahost.com` — a **Coupa TEST instance
exists** and Token Refresh appears to have run against it 2026-07-01. That instance may allow
closing item 1 (real Coupa acceptance) without touching prod — worth an owner decision; feeds
OQ-016/OQ-024.

**Test results (2026-07-06, all 8 scenarios fired against the rig):**
| Scenario | Result |
|---|---|
| s1 happy >500 capex (4052) | PASS end to end: create-req, quote attach, status flip to PO Requested (8055), **meta1=424242 stamped** (OQ-024 synthetic proof), success comment |
| s2 <=500 (4053) | PASS: route 2, no attach call, flip + meta1 + comment |
| s3 capex No (4054) | Core assertion PASS via capture: `segment-4=612200`. Finalize skipped: no quote file on a >$500 task throws in the attach node (faithful: source would 4xx at Coupa; lands in same error branch) |
| s4 ampersand (4055) | PASS via capture: `display-name=A & B Services` single-encoded, no double-escape — n8n-native encoding replaces the manual %26 correctly (spec §4.7) |
| s5 supplier missing (4056) | PASS: contractor-missing comment posted, NO error-log row (asymmetry preserved), no flip |
| s6a/b/c lookup misses (4057/8/9) | PASS: error paths A/B/C each wrote the correct error-log row; B's message proves the "Coastal Ninety Nine" transform; C exercised the capex-blank fallback (`Other Operating` in seg6) |
| s7 create-req 500 (4060) | PASS: onerror row logged with mock's 500 body |
| Idempotency re-fire (4052, meta1 set, back in PO Create) | PASS: early stop, zero Coupa traffic |

Fixes made to the RIG during testing (not to Step 1 — Step 1 needed zero changes):
- Mock accounts response must include `account-type.name` (Step 1's payload builder reads it) —
  documented response-shape expectation for OQ-009/OQ-016.
- n8n instance doesn't match mid-path webhook route params (`:reqId`); attachments route
  registered as literal `/requisitions/424242/attachments` (works because mock's create-req id
  is deterministic).
- Limble WAF 403s the default `Python-urllib` user agent — seeder sends a custom UA.
- Limble user-create API requires `locationID` + `roleID` ("View Only" = 37676 in sandbox).

Known sandbox-only gaps (fine for prod, no action):
- Admin user 317887 (Brandon) doesn't exist in sandbox → "Get Admin User" returns 0 items and
  admin error comments no-op in test. Prod has the user (OQ-019 recon).
- Comment-timestamp ties (3 seed comments in same second) can make the latest-comment tiebreak
  pick a non-trigger comment and gate the run — faithful port of the Make function's `>`
  comparison; prod comments never tie like seeded ones.

**Residual untested surface (inventoried 2026-07-06, owner-directed documentation; test
before go-ahead if access allows, else watch at hotswap):**
| # | Item | Why untested | Pre-launch mitigation | If deferred to hotswap, watch for |
|---|---|---|---|---|
| R1 | Contractor-comment **User/Team variants** ("Post Contractor Comment (User)"/"(Team)" + their mention expressions) | All rig tasks were unassigned — only the "Plain" variant ran | Assign a sandbox task to a user, re-fire supplier-fail; repeat with a team assignment | First real supplier-miss on an assigned task: comment posts, mention renders |
| R2 | **"Post Admin Comment" node** — never executed with data | Admin 317887 absent from sandbox, "Get Admin User" always returned 0 items | Temporarily point the Get Admin User lookup at a sandbox userID, fire one error scenario, revert | First real error-path hit: admin comment posts and @-mention renders (prod has 317887 = Brandon, active) |
| R3 | **Error Log Export end-to-end** (drain + Ionos email + OQ-006 partial delete) | Never fired; test rows were purged at teardown | Insert 1 synthetic row into `6GbR5Rxezl7hqk9i`, run the workflow, verify email at gerald@ and that only exported rows were deleted | First real error row: 15-min export emails it and the table drains correctly |
| R4 | **Real-Coupa acceptance** (OQ-016 auth + payload) — item 1 above | Rig mocked Coupa by design; Fuse history erased (OQ-024) | ONLY option: sanctioned run against `coastalwasteinc-test.coupahost.com` | First live fire: lookup 401/403 = our Bearer decision wrong; create-req 4xx/422 = inherited defect, error log now captures the full Coupa body |

Caveat on R1/R2 timing: the mock is torn down, so running them now sends live GETs to prod
Coupa with the unverified Bearer token (no writes — supplier-fail stops before create-req).
That's also exactly the OQ-016 lookup-auth probe, so R1 doubles as a partial R4.

**Resolution criteria:**
Closes when the test phase ends and every teardown item is verified done at cutover. Item 1
folds into the first-live-call confirmation (OQ-016) — or into a Coupa-TEST-instance run if
the owner sanctions that.

---

## OQ-029 — [resolved] Step 2 built (`WYJyHdQGcdeD8wEr`) missing OQ-008 error-log subgraph

**Type:** OPEN QUESTION
**Added:** 2026-07-07

**Question / Description:**
Status check (2026-07-07) found the build-spec doc and open-questions.md tracker both stale —
both said Step 2 was "design only, not built" / "empty shell". Direct read of the live n8n
workflow `WYJyHdQGcdeD8wEr` ("Update Limble WO on New PRs (Step 2)") shows it is fully built:
17 nodes, real logic (poll → Coupa requisition/PO check → "PO Approved" status flip →
team/user comment), `updatedAt` 2026-07-06 — after the spec's 2026-07-03 "design only" note.
Tracker table and build-spec header corrected in this pass to reflect Built.

However, comparing the built graph against the spec surfaced a gap: **the OQ-008 sanctioned
fix (spec §4.2 — error-log Data Table write + admin @-mention on failure) is not present**.
No node has an error-output branch wired, and there is no write to the shared
"Coastal - Coupa Integration Error Log" Data Table (`6GbR5Rxezl7hqk9i`) anywhere in the
workflow. Per spec §4.2 this should cover: Coupa `GET requisition`, Coupa `GET purchase_orders`,
`updateATask`, and the two comment POSTs, converging on one shared error subgraph (same shape
as Step 1 §4.9) — plus a workflow-level log-once path for the two status-lookup nodes.

Workflow is currently inactive, so this is not yet a live gap, but it must close before
activation — Step 2 would otherwise run without the error visibility Step 1/Step 3 have,
undermining the whole point of OQ-008's sanctioned fix.

**Resolution criteria:**
Closes when the OQ-008 error subgraph (error-output wiring on the 5 covered calls + shared
Data Table write + admin comment, per spec §4.2) is added to `WYJyHdQGcdeD8wEr` and verified,
or the owner explicitly defers/waives it with a reason recorded here.

**Resolved:** 2026-07-09
**Resolution:** Error subgraph built into `WYJyHdQGcdeD8wEr` (now 26 nodes, was 16), mirroring
Step 1 §4.9 exactly. Added: `onError: continueErrorOutput` on the 5 covered calls (Get
Associated Requisition, Get PO Created From Req., Set 'PO Approved' Status and Save PO ID, Post
Team Comment, Post User Comment) → 4 `Err:` Set nodes (per-call middle clause, signed-off
wording §4.2) → shared `Insert Error Log Row` (Data Table `6GbR5Rxezl7hqk9i`, `timestamp=$now`)
→ `Get Admin User` (317887) → `Merge Error Context` (combineByPosition) → `Post Admin Comment`
(@-mention on the WO). Plus a log-once setup path: the 3 pre-loop status/WO-list lookups (Get
'PO Requested' Status ID, Get 'PO Requested' WOs, Get 'PO Approved' Status ID) → `Err: Setup
Lookup Failed` → `Insert Setup Error Row` (log-only, no comment, `woNum=N/A`). Error-subgraph
Limble nodes use the same credential as Step 2's sibling Limble nodes (`qn6u8jEK085DoHT8`
"Coastal Waste Limble") so the test-phase sandbox cred swap (test plan §3.3) covers them
uniformly. `n8n_validate_workflow`: 35 valid connections, 0 invalid, 49 expressions OK, 0
warnings; the 4 "Incorrect error output configuration" errors are a known heuristic
false-positive on the converged-error fan-out (Err Set → Insert+Merge on main[0]) — Step 1
(`WJSs6apAdVH5yKkq`), the tested-passing reference, throws the identical 5 errors of the same
type. Unblocks the Step 2 error-path testing that test plan A3 said was blocked.

---

## OQ-030 — [resolved] Step 3: PO lookup by po-number but meta2 holds PO id — fix to query by id

**Type:** PENDING DECISION
**Added:** 2026-07-07

**Question / Description:**
Step 3 blueprint module 25 does `GET /api/purchase_orders?po-number={{2.meta2}}`, but `meta2`
holds the Coupa PO **id**, not its po-number — both Step 2's write (build spec §4.7:
`meta2 = purchase_orders[0].id`) and the docx (§"Soft Closing the Coupa PO": *"using the saved
PO ID in the meta2 field…"*) agree. Querying the po-number endpoint with an id value returns no
PO, and every downstream `{{25.body[1].id}}` dereferences an empty result. Never surfaced in
prod because `meta2` is null on every real task (OQ-024). Faithful port vs. sanctioned fix?

**Resolution criteria:**
Owner picks faithful (replicate the wrong key, flag as latent bug) or sanctioned fix (query by
id). If fixed, joins the sanctioned-fixes list.

**Resolved:** 2026-07-07
**Resolution:** Sanctioned fix — the n8n port fetches the PO by id (`GET /api/purchase_orders/
{{meta2}}`; fall back to `?id={{meta2}}` if the direct path isn't exposed — verify endpoint
shape at build). Matches Step 2's `meta2` = id contract and the docx. Joins the sanctioned-fixes
list (OQ-005/006/012/017/021/022/026/OQ-008). Detail: Step 3 build spec §4.1.

---

## OQ-031 — [resolved] Step 3: Coupa auth on 3 calls — Bearer-for-all

**Type:** OPEN QUESTION
**Added:** 2026-07-07

**Question / Description:**
Step 3's 3 Coupa calls are inconsistent: GET purchase_orders (25) sends no auth header; the
attachment POST (15) sends `Authorization: {{18.data.oauth_token}}` (**no `Bearer ` prefix** — a
likely bug); the comment POSTs (28/29) send `Authorization: Bearer {{18.data.oauth_token}}`. All
read the token from the datastore-324 record. Extend the Step 1 (OQ-016) / Step 2 (OQ-027)
Bearer-for-all resolution to Step 3?

**Resolution criteria:**
Owner confirms Bearer-for-all from the "Coastal - Coupa OAuth Token" Data Table (dropping the
datastore-324 read), or keeps the source's mixed-header/324-read shape.

**Resolved:** 2026-07-07
**Resolution:** Bearer-for-all — drop the datastore-324 read; all 3 Coupa calls send
`Authorization: Bearer <token>` from the "Coastal - Coupa OAuth Token" Data Table
(`QAj62weJaWmRBJ76`). Fixes the attachment POST's missing prefix as a side effect. Matches
OQ-016/OQ-027. Confirmation point is the first live test (401/403 = revisit). Detail: Step 3
build spec §4.2.

---

## OQ-032 — [resolved] Step 3: error handling — faithful log-only, no admin comment

**Type:** PENDING DECISION
**Added:** 2026-07-07

**Question / Description:**
Step 3's source logs its 3 Coupa POST failures (attachment 15, comments 28/29) to error
datastore 326 but posts **no** admin comment — unlike Step 1/2's converged subgraph, which also
@-mentions admin 317887 on the Limble WO. Step 3's comments go to Coupa, not Limble, so an admin
Limble comment would be a call the source lacks. GET po (25) and the reads have no `onerror`.
Port faithfully or align to the Step 1/2 subgraph?

**Resolution criteria:**
Owner picks faithful log-only vs. align-to-subgraph, and the error-coverage boundary.

**Resolved:** 2026-07-07
**Resolution:** Faithful log-only. Port the 3 POST `onerror` writes to the shared "Coastal -
Coupa Integration Error Log" Data Table (`6GbR5Rxezl7hqk9i`) with a **native Date/ISO**
`timestamp` (forced by OQ-012's schema, the one non-faithful detail). **No** admin @-mention
comment; admin user 317887 is not used by Step 3. Coverage = the 3 POSTs only (GET po / token
read / Limble reads stay uncovered, as in source). Detail: Step 3 build spec §4.3.

---

## OQ-033 — [resolved] Step 3: drop dead comment Feeder/Aggregator (8/9) — consolidation

**Type:** PENDING DECISION
**Added:** 2026-07-07

**Question / Description:**
Step 3 has a `BasicFeeder` (8) over the task comments → `BasicAggregator` (9) producing a
comment list that no downstream mapper references. Drop it as dead code (Step 1 OQ-021
precedent), or keep faithful?

**Resolution criteria:**
Confirm the docx doesn't expect a compiled comment/note list on the PO, then owner approves the
drop or keeps it literal.

**Resolved:** 2026-07-07
**Resolution:** Drop — consolidation, behavior-neutral. Verified against the docx §"Soft Closing
the Coupa PO": it specifies only invoice-attach + one PO notification comment; no compilation of
WO comments/notes (section keyword scan: note/completion/compile/list/summary = 0). The related
`CoastalGetChildWONotes` function exists in `functions.js` but is wired to nothing in Step 3 — an
abandoned scaffold, not a forgotten requirement. The comments GET (module 6) is retained only as
the "WO is Coupa related" gate, which reads task fields and moves onto the task fetch — so 6/8/9
all drop. Detail: Step 3 build spec §4.4/§5.

---

## OQ-034 — [resolved] EHS Create WO: consolidate 3 identical region routes → 1 + allowlist guard

**Type:** PENDING DECISION
**Added:** 2026-07-08

**Question / Description:**
"Create WO From EHS Inspection" router (module 70) has 3 routes gated by region name. The three
route bodies are byte-identical (same `listTeams` / `createATask` / instruction-update logic);
they differ only in the region-name filter and a `util:SetVariable2` `var` set to 1/2/3 that is
written and never read (dead). Consolidate to one create-task branch gated by a region
allowlist, or replicate 3 routes faithfully?

**Resolution criteria:**
Confirm behavior is identical after consolidation (same task created regardless of which of the
5 region names matched; unmatched regions still drop since the source router has no `else`).

**Resolved:** 2026-07-08
**Resolution:** Consolidate (sanctioned fix under OQ-001). One create-task branch gated by an IF
allowlisting the 5 region names (Central Florida, Southwest Florida, Coastal Materials
Management, South Florida, South Atlantic); regions outside drop, preserving the no-`else`
behavior. Dead `var` dropped. Behavior-neutral; ~2/3 fewer nodes. Detail: EHS Create WO build
spec §4.2/§6.

---

## OQ-035 — [open] EHS Create WO: `last(Questions)` only inspects last question — flag

**Type:** OPEN QUESTION
**Added:** 2026-07-08

**Question / Description:**
In "Create WO From EHS Inspection", `util:SetVariable2` (50) sets `questionList =
last(28.Questions)` — only the **last** question of the inspection is examined for an
unacceptable answer (`Answer == "0"`) and for a file attachment. An inspection with multiple
deficient questions captures only the last one into the Limble WO instruction. This is what
shipped in Make.

**Resolution criteria:**
Owner decides whether iterating all unacceptable questions (and attaching all their images) is a
wanted fix, or whether "last question only" is intended behavior. Ported faithfully (last-only)
for now under the 1:1 posture.

**Status:** Open — faithful port ships last-only; flagged for owner decision. Detail: EHS Create
WO build spec §4.4.

---

## OQ-036 — [resolved] EHS Update Inspection: drop dead comments-fetch (63) / lastComment (64)

**Type:** PENDING DECISION
**Added:** 2026-07-08

**Question / Description:**
In "Update EHS Inspection From Limble WO," module 63 (`universalModule` GET
`/v2/tasks/{taskID}/comments`) and module 64 (`SetVariable2 lastComment = last(63.body)`) run
on every trigger, but a grep of the full blueprint export for `{{63.` / `{{64.` returns zero
hits — nothing downstream ever reads either value. Drop them from the n8n port (consolidation,
same shape as OQ-033) or keep them as faithful dead weight?

**Resolution criteria:**
Owner decides whether to drop, after confirming the nodes aren't an under-configured version
of a documented requirement (i.e. check the EHS narrative review doc before assuming they're
safe to cut).

**Resolved:** 2026-07-08
**Resolution:** Drop. Cross-checked `Coastal - Limble Integration Review - EHS Integration
(v1.3.2).docx` — the completion-notes payload is documented as "the completion notes typed in
the EHS WO as well as the completion notes of all of its child WOs" (line 88), with no mention
anywhere of pulling a Limble task *comment* into that payload. Confirmed as pure dead
scaffolding, not a documented-but-misconfigured feature. The n8n port omits both nodes; the
"WO Completed?" gate moves onto the task-fetch step directly. Detail: EHS Update Inspection
build spec §4.1/§8.

---

## OQ-037 — `CoastalEHSFormFilter` dedupe never replaces (UpdateDtm/UpdatedDtm typo) — flag

**Type:** OPEN QUESTION
**Added:** 2026-07-08 (found while building `docs/build-specs/ehs-create-wo.n8n.json`)

**Question / Description:**
`CoastalEHSFormFilter` (`docs/functions.js`) dedupes fetched EHS inspections to one per site,
intending to keep the most recently completed. The replace-check reads:

```js
if (form.UpdatedDtm > filteredForms[j].UpdateDtm && form.RecurringTaskCompleteDtm && form.RecurringTaskCompleteDtm != "") {
  filteredForms[j] = form;
}
```

`filteredForms[j].UpdateDtm` is a typo — the field on these objects is `UpdatedDtm`. So
`filteredForms[j].UpdateDtm` is always `undefined`, and `anything > undefined` is always
`false` in JS. The replace branch can never fire. Net effect: for any site with more than one
matching inspection in the 24h window, the function keeps whichever inspection it happened to
see **first**, not the latest-completed one the comment/design intends. This has shipped in
production Make since before this migration — not something introduced by the port.

**Resolution criteria:**
Owner decides: (a) port bit-for-bit including the bug (current default under the 1:1 posture,
OQ-001) — same site could get judged on a stale inspection if it has multiple runs in the
window; or (b) sanction a fix (correct field name) as a new addition to the sanctioned-fix
list, changing behavior from what's shipped today.

**Status:** Open. `docs/build-specs/ehs-create-wo.n8n.json` ports the function bit-for-bit
including the typo (per OQ-001's default), with the bug called out in the node's notes/comment.
Not fixed pending owner decision.

---

## OQ-038 — [resolved] EHS tag mismatch: Create stamps `@EHS;`, Update filters `@EHSWO;`

**Type:** PENDING DECISION
**Added:** 2026-07-08

**Question / Description:**
"Create WO From EHS Inspection" stamps the Limble WO `description` with the tag **`@EHS;`**
(3 occurrences in `Coastal - Create WO From EHS Inspection (PROD).json`, one per region route),
but "Update EHS Inspection From Limble WO" gates on **`description contains "@EHSWO;"`**
(1 occurrence in `Coastal - Update EHS Inspection From Limble WO (PROD).json`). `"@EHS;"` is not a
substring of `"@EHSWO;"` (after `@EHS` the second string continues `WO;`, not `;`), so the two
literals are disjoint: a WO created by EHS-Create can **never** satisfy EHS-Update's trigger gate.
This is a **pre-existing defect in the shipped Make blueprints**, faithfully ported into the n8n
build (`isLUx7cUjkmKggD2` stamps `@EHS;`; `8JvtesynrYtZbw7U` reads `@EHSWO;`) — i.e. the EHS closed
loop has never worked in production (parallels OQ-024's "meta1 null on every task" finding on the
Coupa side: a designed correlation that essentially never fired). Surfaced 2026-07-08 while
building the test plan (grep across both EHS exports + read of the built workflows).

**Resolution criteria:**
Owner decides which side is authoritative and whether to fix. The EHS review docx (v1.3.2) is the
project's source of truth on disagreements.

**Resolved:** 2026-07-08
**Resolution:** Sanctioned fix. The EHS review docx settles the direction — it states both that the
created WO "will be populated with the site where the inspection took place (along with the
'@EHSWO;' tag)" **and** that Update "looks to see if the WO contains the '@EHSWO;' tag." So the
intended tag is `@EHSWO;` on both sides, and EHS-Create's `@EHS;` is the drifted/errant side. Fix:
**correct EHS-Create to stamp `@EHSWO;`** (leave EHS-Update's gate unchanged). Joins the
sanctioned-fix list (OQ-005/006/008/012/017/021/022/026/030/034/036).

Applied at the **design** level now, per the owner's concurrent "design-only, hold n8n writes"
directive: `docs/build-specs/ehs-create-wo-build-spec.md` (§3 create-task description template +
§8 summary table) and the EHS/Limble test-plan docs. The one-line edit to the **live** workflow
`isLUx7cUjkmKggD2` (description literal `@EHS;` → `@EHSWO;` on the create-task node) is **queued** —
apply it when the write/test phase is greenlit, then verify a real Create→Update closed-loop run.
The EHS-Update test fixture stamps `@EHSWO;` as the *correct* Create output (previously framed as a
workaround).

---

## OQ-039 — Coupa TEST instance exists with standing creds — authorize Phase-A live testing?

**Type:** PENDING DECISION
**Status:** Open
**Added:** 2026-07-13

**Question / Description:**
A standing row in the n8n Coupa OAuth Token table (`QAj62weJaWmRBJ76`, `client="Coastal_Waste (TEST)"`)
holds a real Coupa JWT whose `iss` claim is **`https://coastalwasteinc-test.coupahost.com`** — a
Coupa **test instance** — and whose `client_id` (embedded in the JWT) proves we hold working
client-credentials auth against it (token dated 2026-07-01; the token itself is now expired). The
fixture file `docs/test-plan/fixtures/coupa/datatable-seed-rows.json` already documents this row.
Pre-go-live testing is currently mock-only (OQ-003/OQ-028): the mock response shapes are guesses,
so the largest cutover risk (OQ-028) is that real Coupa GET/POST shapes differ from the mocks —
that risk only lands live in Phase C. **If we are authorized to point Token Regen and Step 2's
read-only Coupa GETs (`Get Associated Requisition`, `Get PO Created From Req.`) at
`coastalwasteinc-test.coupahost.com`, most of Phase C's guessed-shape risk converts to Phase-A
testing.** Surfaced 2026-07-13 during the Token Regen (A2) test when the token table was read.

**Resolution criteria:**
Owner confirms (a) the test instance is safe to call (non-prod data, won't disturb Coastal ops),
(b) which workflows/calls are cleared to use it (read-only GETs first; writes — createReq,
attachments, PO comments — are higher-touch), and (c) current valid client_id/secret for the test
instance are installed in the isolated n8n credential (OQ-005). Then re-run A2/A-Step-2 read paths
against the real test endpoint before cutover.

## OQ-040 — Step 2 team-comment path unprovable in sandbox (View Only role-team)

**Type:** OPEN QUESTION
**Status:** Open
**Added:** 2026-07-13

**Question / Description:**
In the Step 2 suite (2026-07-13), the user-assigned comment variant (S2-3) passed end-to-end, but
the team-assigned variant (S2-2) could not be proven. `Has Team?` routes correctly (it isolates the
team-assigned WO), but `Get Team` (`GET /v2/teams?teams=<id>&limit=1`) returns an empty array for
the sandbox's only team, **107065**. Direct probes confirmed: `teams=107065` → `200 []`
(`x-has-more:false`); `locations=98472` → `400 "locations is not allowed"`. Team 107065 is the
auto-created **"View Only" role-team** — it appears inside a user's `teams[]` array but is **not
returned by the teams-list endpoint**. A normal maintenance team should resolve fine, so Step 2's
team-comment path is *likely* correct in prod but **cannot be validated in the sandbox without a
real (non-View-Only) team at loc 98472**. Limble MCP is read-only (and points at Coastal-PROD, so
it returns nothing for sandbox tasks); no create-team API path was found.

**Resolution criteria:**
Owner either (a) provisions a real maintenance team at sandbox loc 98472 so S2-2 can be run to
completion, or (b) accepts deferring the team-comment assertion to Phase C go-live validation
(user-assigned variant already proves the assignment-comment machinery; team differs only in the
`/v2/teams` lookup + mention name).

## OQ-041 — Token Regen ↔ Fuse collision at cutover (shared Coupa client)

**Type:** OPEN QUESTION
**Status:** Open
**Added:** 2026-07-13

**Question / Description:**
The n8n "Coupa - Token Refresh" workflow uses `grant_type=client_credentials` against Coupa's
`/oauth2/token`, injecting client_id/secret from the isolated n8n credential (OQ-005). At go-live,
n8n and the still-running Fuse scenario would use the **same** Coastal Coupa OAuth client. Whether
n8n refreshing the token invalidates Fuse's live token (and vice-versa) depends on Coupa's server
behavior: if `client_credentials` issues **independent concurrent access tokens** per request
(typical), no impact and both systems run in parallel safely; if Coupa **rotates a single token per
client** (invalidating the prior on each issue), n8n's daily refresh breaks Fuse's next Coupa call
and Fuse's refresh breaks n8n's — during the parallel-run / rollback window (adjacent to OQ-020's
double-fire concern). Pre-go-live A2 testing is unaffected (it hits the mock + isolated n8n table,
never real Coupa or Fuse's datastore 324). Surfaced 2026-07-13 (A2), in response to the owner's
direct question "won't the token refresh mess up the Fuse workflow?".

**Resolution criteria:**
Confirm Coupa's `client_credentials` token semantics (concurrent vs. rotate-and-invalidate) —
ideally against the OQ-039 test instance. If rotate-and-invalidate: do NOT activate n8n Token Regen
until Fuse's Coupa scenarios are disabled at cutover (sequence it with the OQ-020 webhook cutover);
if concurrent: safe to run in parallel through the rollback window.

## OQ-042 — [resolved] Limble instruction-answer write API not found (does NOT block EHS Create WO)

**Type:** BLOCKER (EHS Create WO A6 pre-fix) / FINDING
**Status:** Resolved
**Added:** 2026-07-13
**Resolved:** 2026-07-20

**Question / Description:**
During A4 fixture prep (2026-07-13, sandbox 98472), attempts to write an instruction *response*
via the Limble v2 API all failed:
- `PATCH /v2/instructions/{id}` → **404 route not found** — this is exactly the endpoint+method
  the built EHS Create WO workflow (`isLUx7cUjkmKggD2`) uses for its `updateAnInstruction` port
  (build-spec flagged it as a guess under OQ-009). **The guess is now disproven.**
- `PATCH|PUT /v2/tasks/{id}/instructions/{iid}` → 404; `PATCH|PUT /v2/tasks/{id}/instructions`
  → 404.
- `POST /v2/tasks/{id}/instructions` EXISTS but is create-only: requires `instruction` (text),
  rejects `response` ("`response` is not allowed") — same create-then-PATCH split as tasks,
  except no instruction-PATCH route could be found at all.

**GET-shape proof (2026-07-14, conclusive).** A thorough deep dive (API docs + NotebookLM +
direct probes) confirms: the *only* instruction endpoint exposed by the public v2 API for the
answer data is a **read**, `GET /v2/tasks/{taskID}/instructions`. There is **no** PATCH/PUT route
to mutate an instruction's `response` field anywhere in the public v2 API. Sample response for
task `4053` (7 instructions from template 4041) shows the answer always lives in the per-item
`response` field, typed by instruction `type`:

| instructionID | type | meaning | `response` shape (example) |
|---|---|---|---|
| 13200 | 3 | text | string (`"Lorem ipsum…"`) |
| 13201 | 4 | dropdown (Capex? Yes/No) | `itemOptionID` int (`3800`) |
| 13202 | 4 | dropdown (contractor) | `itemOptionID` int (`3802`) |
| 13203 | 13 | amount ($) | number (`400`) |
| 13204 | 9 | file upload (quote) | array of file objects (empty `[]` here) |
| 13205 | 4 | dropdown (capex type) | `itemOptionID` int (`3807`) |
| 13992 | 9 | file upload (invoice) | array `[{fileName, link}]` (populated) |

Writing an answer = mutating that one `response` value; the public API offers no verb to do it.

**Exists-vs-impossible fork (the thing left to settle).** "No public-API route" ≠ "impossible."
Make's `fuse-limble-app:updateAnInstruction` clearly hits *some* route. Two outcomes:
1. If EHS Create WO's instruction-write step **runs clean in the live PROD Make scenario today**,
   the endpoint *exists* but is private/undocumented (an internal route the white-labeled Fuse
   connector calls, or a v1 path). → resolvable: capture the real request URL from fuse-limble-app
   source via FM360's Make access, or from a PROD execution log.
2. If it **never worked in PROD either** (cf. OQ-024's dead Coupa requisition loop), the write-back
   was always a no-op and a faithful 1:1 port = replicate a no-op (port nothing / drop the node).
Which one holds is not yet confirmed and gates the fix.

Consequence 1 (test rig): instruction responses (dropdowns, amounts, quote-file uploads) are
UI-only — sandbox fixtures needing responses/files require owner UI action.
Consequence 2 (build): EHS Create WO's "update instruction" node will 404 in every run until the
real write path is found (candidates: `PATCH /v2/tasks/instructions/{id}`, an undocumented v1
path, or a batch endpoint).

**Pending action (2026-07-14):** owner to open a **Limble support** ticket to obtain the real
instruction-response write endpoint. Uncovering the undisclosed route used by Make/Fuse's
`updateAnInstruction` is deferred behind that support interaction.

**Update (2026-07-17) — support ticket drafted.** Limble support ticket written and staged as a
Gmail draft (to `support@limblecmms.com`, from `gerald@fm360consulting.com`; subject: "API v2: how
to update an existing task instruction (text/response/image)? No PATCH route found"). Refers to the
integration as **Fuse** (Limble-familiar lingo), not Make.com. Asks three things: (1) is there a
supported public endpoint to update an existing instruction's text / response / image, with exact
method+path+payload; (2) if not public, what route does the Fuse connector's "Update An
Instruction" module call, and can we be authorized to use it; (3) if neither, is
instruction-response data UI-only by design. Includes the verified 404/probe evidence from this OQ.
Awaiting owner review + send, then Limble's reply.

**Update (2026-07-17) — live sandbox probe (loc 98472, task 4053, instr 13200) refines the
finding: the earlier paths were WRONG, a real update route exists, but `response` is forbidden
on it.** Probed with the sandbox Basic key against `https://api.limblecmms.com`:
- `PATCH /v2/tasks/instructions/{instructionID}` (no `{taskID}` segment) **EXISTS** — returns
  **200** on `{}` and on `{"instruction":"<text>"}`. This is the instruction-update route that
  OQ-042's prior probing missed: earlier tries were `/v2/instructions/{id}` (404) and
  `/v2/tasks/{taskID}/instructions/{iid}` (404) — both wrong shapes. Correct path drops the
  `{taskID}` and pluralizes: `/v2/tasks/instructions/{id}`.
- **But it will not write `response`.** `{"response":"..."}` → **400 `` `response` is not
  allowed ``** — same rejection as the create POST. Alt field names `answer`, `value` also
  400 "not allowed". So the route mutates the instruction **definition** (`instruction` text,
  presumably `type`/`options`), NOT the **answer**.
- Confirmed non-destructive: instruction 13200's text unchanged after the pass (sent its own
  current value back).

**Conclusion (public API): writing an instruction's `response` is impossible by any route/field
found.** Both the create POST and the (now-located) update PATCH explicitly reject `response`.
This *strengthens*, not overturns, the GET-shape proof: the answer data is public-API read-only.
Two consequences:
- **EHS Create WO (`isLUx7cUjkmKggD2`) cannot write instruction responses via the public API,
  full stop** — not just because its node uses the wrong path (`/v2/instructions/{id}`, 404),
  but because even the correct path 400s on `response`. Whichever way, the ported
  `updateAnInstruction` write fails live.
- **The support ticket sharpens:** we are no longer asking "is there an update route" (there is:
  `PATCH /v2/tasks/instructions/{id}`) — ask specifically "how does the Fuse connector's Update
  An Instruction module write the `response`/answer field, given the public PATCH route rejects
  it?" Update the drafted Gmail ticket to cite this exact 400 before sending.

The exists-vs-no-op fork (does PROD Make actually write responses?) is unchanged and still gates
the fix — Fuse must hit a private/internal route the public API doesn't expose.

**Resolution criteria:**
Confirm the exists-vs-impossible fork (does the PROD Make step write responses successfully?), then
either (a) obtain the real instruction-write endpoint (Limble support / inspect fuse-limble-app
source via FM360's Make access / probe remaining path shapes), fix the EHS Create WO node, and
re-validate; or (b) confirm it was always a no-op and drop the node. Blocks A6 per-task
instruction-update assertions.

**RESOLVED (2026-07-20) — Limble support answered + the premise was wrong.**

1. **Support's definitive answer** (Gmail thread `19f70f91c51a37ea`, sent + two replies): there is
   **no public v2 API route to write an instruction's fillable answer/`response`**. Rep escalated
   internally, came back negative — *"the Update Task Instruction PATCH call will update the verbiage
   on the instruction… but the portion that the user would be filling out cannot be updated from the
   API."* Rep offered to hear a use-case for a possible private/roadmap route (door left ajar, not
   pursued now). Confirmed working routes: verbiage `PATCH /v2/tasks/instructions/{id}`, image
   `PUT /v2/tasks/instructions/{id}/image`.

2. **The blocker premise was wrong.** This OQ assumed EHS Create WO writes an instruction
   **`response`**. It does not. Both update nodes on `isLUx7cUjkmKggD2` — `Update Instruction
   (No Image)` (n28) and `Update Instruction With Image` (n27) — write the **`instruction` field
   (verbiage)**: `{ instruction: "Deficiencies from Inspection:  " + Verification }`. Owner confirmed
   2026-07-20 that verbiage is the intended target. Support says verbiage **is** writable → **OQ-042
   does NOT block EHS Create WO.** The historical `PATCH /v2/instructions/{id}` 404 was a **path
   typo** (missing `/tasks/` segment), not the answer-write ban.

**Downgraded from BLOCKER to two ordinary build fixes on `isLUx7cUjkmKggD2`** (queued; both are
`n8n_update_partial_workflow` writes, so gated on n8n MCP write permission — not on OQ-042):
- n28 + n27: URL path `/v2/instructions/{id}` → `/v2/tasks/instructions/{id}`.
- n27 only: image is a **separate** call — split `update_image`/`image` out of the verbiage PATCH
  into `PUT /v2/tasks/instructions/{id}/image` (support-confirmed image route).

A6 EHS Create WO suite is no longer OQ-042-blocked; it needs these two node fixes plus the
`Create Deficiency Task` (n21) fixes (due→epoch, `metadata`→top-level `String(meta1)` per OQ-024,
`@EHS;`→`@EHSWO;` per OQ-038).
