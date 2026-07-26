# Build Spec — Coastal - Coupa Integration Error Log Export

Status: **built in n8n** (2026-07-01), workflow ID `hR5YnDixecDz9HzJ` ("Coupa - Integration
Error Log Export"), inactive, validated 0 errors (3 expected warnings — no error handling,
tracked as OQ-013). Built after explicit owner go-ahead, scoped to this workflow only — the
other 5 remaining scenarios stay design-only until each gets its own go-ahead (OQ-007).

Source blueprint: `docs/OG-workflows/Coastal - Coupa Integration Error Log Export.json`
(9 modules, 0 `onerror` chains — this workflow has no self-monitoring, same asymmetric gap
noted elsewhere in CLAUDE.md/OQ-004/OQ-008).

---

## 1. Purpose

Every 15 minutes, drain the shared Coupa error-log store, email a report, then clear only the
rows that were actually reported (fixing the current delete-all race — OQ-006). The writers
into this store — "Create Requisition in Coupa" (Step 1) and "WO Completed" (Step 3) — are not
built yet. This spec creates the shared Data Table those two will eventually write to.

## 2. Trigger

Schedule Trigger, **Interval mode, every 15 minutes**. No timezone dependency — pure interval,
not clock-aligned to a day boundary, so OQ-011's DST question doesn't apply here.

## 3. Source flow (Make, as-is)

1. `datastore:Stats` (14) on datastore 326 → record count.
2. Filter "Errors Exist": count > 0 gates the next step.
3. `datastore:SearchRecord` (16) on 326, filter `timestamp exists`, no limit.
4. `builtin:BasicAggregator` (17) — collects Search's bundles into one array.
5. `builtin:BasicFeeder` (19) — re-splits that array back into individual bundles.
6. `util:SetVariable2` (20) — builds one formatted line per record (roundtrip var
   `recordString`): `Error#: N || LimbleWO: X || errorCode: Y || errorMsg: Z || timestamp: T`.
7. `builtin:BasicAggregator` (21) — collects `recordString`s into an array again.
8. `util:SetVariable2` (24) — joins all `recordString`s with newline → `allRecordsString`.
9. `email:ActionSendEmail` (15) — plain text, To `ethan@fm360consulting.com`, subject
   "Coastal Limble Integration: Error Report", priority high, body = `allRecordsString`.
10. `datastore:DeleteAllRecords` (25) — filter: only if step 9's `messageId` exists (send
    succeeded) → wipes the **entire** datastore 326, not just the exported rows (OQ-006).

Confirmed schema of what's written to datastore 326 (read from Step 1/3's `onerror` handlers,
since this workflow only reads): `data: { limbleWONum, errorCode, errorMsg, timestamp }`,
`overwrite: false`. No explicit `key` field — Make auto-assigns one. `timestamp` is written as
a **pre-formatted display string**, inconsistently: `"MM/DD/YYYY hh:mm A"` in some handlers,
`"MM/DD/YY hh:mm A"` in others, one long-form `"Eastern Standard Time"` — all hardcoded EST
(not DST-aware).

## 4. Design decisions locked in for this spec

1. **Data Table created here** — first build in the shared-error-log family (Step 1/3 aren't
   built yet). Name: **"Coastal - Coupa Integration Error Log"** (matches the source
   datastore's Make label). Columns:

   | Column | Type | Notes |
   | --- | --- | --- |
   | `limbleWONum` | string | unchanged from source |
   | `errorCode` | string | unchanged from source |
   | `errorMsg` | string | unchanged from source |
   | `timestamp` | **Date** | sanctioned fix — see below |
   | `id` | built-in, auto | not user-defined; used for delete-by-id (§4.6) |

2. **`timestamp` becomes a native Date column, not a pre-formatted string** (sanctioned fix,
   logged as **OQ-012**). Source wrote 3 inconsistent formats, always hardcoded EST. Since
   this workflow provisions the table before Step 1/3 exist, **their future build specs must
   write a real ISO/date value to `timestamp`, not a formatted string** — carried forward as a
   dependency, same pattern as Token Regen's `scope` note.
3. **Report email displays `timestamp` in `America/Denver` (Mountain), not EST** — second
   fix riding the same OQ-012 entry. Source's hardcoded EST looks like a dev mistake, not
   intentional design, given Coastal's own schedules use Mountain Time elsewhere (OQ-011).
4. **Stats→Search gate replaced by n8n's default empty-input behavior.** `Get rows` with
   `returnAll: true` simply returns 0 items when the table is empty, and 0 items means nothing
   downstream executes — no explicit "count > 0" / IF-gate node needed. Functionally
   equivalent to the source's `datastore:Stats` + filter pair.
5. **Record-string build collapses 5 Make modules into 1 Code node.** Source's
   Aggregate→Feeder→SetVariable→Aggregate→SetVariable chain (modules 17/19/20/21/24) exists
   only because Make bundles are linear; n8n already hands the Code node all rows as an array
   in one step, so one "Run Once for All Items" Code node replaces the whole chain.
6. **Delete-only-exported (OQ-006):** Data Table **Delete** operation, resource `row`,
   condition `id = {{ $json.id }}`, run once per row (fed from a Split Out step after the
   email succeeds) — not `DeleteAllRecords`. Confirmed via the n8n Data Table node schema:
   the auto-generated `id` is a valid delete/update match column even though it isn't part of
   the user-defined schema.
7. **"Only delete if send succeeded" gate:** relies on n8n's default stop-on-error behavior
   (Send Email node's failure halts its branch, so nothing downstream runs) rather than an
   explicit IF/filter node checking `messageId exists` like the source. No `continueOnFail` on
   the Send Email node. Functionally equivalent.
8. **Email delivery:** "Integrations Ionos" credential (same one Token Regen uses, per
   OQ-010). Real recipient `ethan@fm360consulting.com` preserved in config; **To** overridden
   to `gerald@fm360consulting.com` until go-live (OQ-010).
9. **No error handling added to this workflow's own failures.** Faithful port — source has
   zero `onerror` chains. This is a **third** instance of the asymmetric-error-handling pattern
   (alongside the two EHS workflows, OQ-004, and Step 2, OQ-008) — flagged as **OQ-013**, not
   fixed here, since it hasn't been individually sanctioned like OQ-004/008 covered the others.
   **Superseded 2026-07-26 — OQ-013 resolved:** owner sanctioned the basic fix (Token Regen
   alert pattern). Change set in section 8; applied to n8n 2026-07-26, validated clean.

## 5. Target n8n node graph

```
[Schedule Trigger: every 15 min]
        |
        v
[Data Table: Get rows — "Coastal - Coupa Integration Error Log", returnAll=true]
        |   (0 items -> nothing below runs; replicates source's count>0 gate)
        v
[Code: aggregate all rows -> ONE item {reportBody, rowIds[]}]
        |
        v
[Send Email: "Coastal Limble Integration: Error Report"]  --(error)--> [stop; no alert, faithful]
        |
   (success)
        v
[Split Out: rowIds[] -> one item per id]
        |
        v
[Data Table: Delete rows — condition id = {{ $json.rowIds }}, one delete per item]
```

### 5.1 Schedule Trigger
- Interval, every 15 minutes.

### 5.2 Data Table — Get rows
- Node: `n8n-nodes-base.dataTable`, resource `row`, operation `get`
- Table: **"Coastal - Coupa Integration Error Log"** (to be created — does not exist yet,
  unlike Token Regen's table)
- Filters: none. Source's `timestamp exists` filter is vestigial once `timestamp` is a
  required Date column — no row can lack one by construction.
- `returnAll`: true

### 5.3 Code — build report body + carry row IDs
- Mode: Run Once for All Items
- For each input row (1-indexed, matching source's `__IMTINDEX__`), build:
  `Error#: {i} || LimbleWO: {limbleWONum} || errorCode: {errorCode} || errorMsg: {errorMsg} || timestamp: {formatted}`
- `timestamp` formatted via Luxon in `America/Denver`, format `MM/dd/yyyy hh:mm a` (closest
  Mountain-time equivalent to the source's EST display format).
- Join all lines with `\n` → `reportBody`.
- Output **one item**: `{ reportBody, rowIds: [<id for each input row>] }`.

### 5.4 Send Email — "Coastal Limble Integration: Error Report"
- Node: `n8n-nodes-base.emailSend`, credential: **Integrations Ionos** (same as Token Regen)
- To: `gerald@fm360consulting.com` (dev/pre-launch only — OQ-010). Real recipient
  `ethan@fm360consulting.com` documented here, not deleted; swap when owner confirms go-live.
- Subject: `Coastal Limble Integration: Error Report`
- Priority: High
- Content type: Plaintext
- Body: `Errors have occured for the Coastal Limble Integration. See the following Error Logs:\n\n{{ $json.reportBody }}`
- On error: default (halt branch, no retry configured — matches source having no retry logic
  around the email step either)

### 5.5 Split Out — rowIds
- Node: Item Lists / Split Out, field `rowIds`, one item per array entry.

### 5.6 Data Table — Delete rows
- Node: `n8n-nodes-base.dataTable`, resource `row`, operation `deleteRows`
- Table: "Coastal - Coupa Integration Error Log"
- Condition: `id` equals `{{ $json.rowIds }}` (the exploded per-item value from §5.5)
- Runs once per exported row — never a full-table wipe.

## 6. Cross-workflow dependency this creates

Step 1 ("Create Requisition in Coupa") and Step 3 ("WO Completed; Update Coupa PO") — neither
built yet — must, when their specs are written:
- Write to the **"Coastal - Coupa Integration Error Log"** Data Table instead of datastore 326.
- Write `timestamp` as a real ISO date value, not a pre-formatted EST string (OQ-012).

## 7. What's actually built vs. still open

**Built (2026-07-01):**
- Workflow `hR5YnDixecDz9HzJ` ("Coupa - Integration Error Log Export") — 6 nodes (Schedule
  Trigger → Get rows → Code (Build Report) → Send Email → Split Out → Delete rows), validated
  0 errors, inactive.
- Data Table `6GbR5Rxezl7hqk9i` ("Coastal - Coupa Integration Error Log") — 4 columns
  (`limbleWONum` string, `errorCode` string, `errorMsg` string, `timestamp` date), empty
  (no writers exist yet — Step 1/3 aren't built).
- Send Email node uses the existing **Integrations Ionos** credential (`vPXcXvRpktLu49Vr`),
  same one Token Regen uses. From: `integrations@fm360consulting.com` (matches Token Regen's
  convention). To: `gerald@fm360consulting.com` (dev override, OQ-010) — real recipient
  `ethan@fm360consulting.com` documented here (§5.4), not entered into the live node yet.
- `appendAttribution` set to `false` on the Send Email node — source email has no n8n
  boilerplate, kept faithful.
- Source's `priority: high` header has **no equivalent property** on n8n's Send Email node
  (`n8n-nodes-base.emailSend` v2.1 has no priority/custom-header field) — dropped, flagged
  here as an untranslatable minor field, not a functional gap.

**Still open:**
- Table is empty until Step 1/3 are built — nothing to test end-to-end yet. A manual test row
  can be inserted via `n8n_manage_datatable` to dry-run this workflow before then.
- Step 1 / Step 3 specs (not written) inherit the OQ-012 timestamp obligation from this spec.
- **OQ-013** (resolved 2026-07-26): sanctioned fix approved — self-error-handling via the
  Token Regen alert pattern. **Applied to n8n 2026-07-26** (see section 8 for the change set
  and validation results).
- **Activation** — built but left inactive, matching Token Regen's precedent; turning it on is
  a separate decision.
- Real recipient swap (`ethan@fm360consulting.com`) — held back until owner confirms go-live
  (OQ-010).

## 8. OQ-013 sanctioned fix (2026-07-26) — APPLIED to n8n same day

Owner approved the **basic** sanctioned fix (Token Regen alert pattern; the "second alert
channel" variant was explicitly not chosen). The write was briefly deferred behind a
multi-instance-MCP hold, then applied later on 2026-07-26: all 7 operations below landed in
one atomic partial-update on workflow `hR5YnDixecDz9HzJ`. Post-apply validation (runtime
profile): valid, 0 errors, 0 warnings — the 3 pre-fix "no error handling" warnings are gone.
Final graph: 8 nodes, alert node fed by exactly the three error outputs, success path
unchanged, workflow still **inactive** (activation remains a separate owner decision).

Note: the live workflow now has **7 nodes**, not the 6 listed in section 7's build note — a
"Reattach Row IDs" Code node sits between Send Email and Split Out (added in a later build
session; versionCounter was 8 on 2026-07-26).

Change set (mirrors `oCAl4h0SZenEtbNs` "Coupa - Token Refresh" node 4 exactly):

1. **Add node** `Alert: Error Log Export Failed` — `n8n-nodes-base.emailSend` v2.1,
   position ~`[1120, 260]`, credential **Integrations Ionos** (`vPXcXvRpktLu49Vr`):
   - From: `integrations@fm360consulting.com`
   - To: `gerald@fm360consulting.com` (dev override, OQ-010 — real go-live recipient TBD
     same as the report email)
   - Subject: `Coastal Coupa Error Log Export failed`
   - Format: plain text. Body:
     ```
     The Coupa Integration Error Log Export workflow failed for Coastal Waste.

     Failed node: {{ $prevNode.name }}
     Error: {{ $json.error && $json.error.message ? $json.error.message : ($json.error || 'unknown') }}

     Error-log rows are not lost: rows are only deleted after a successful report send, so
     unexported rows remain in the "Coastal - Coupa Integration Error Log" Data Table and
     will be retried on the next 15-minute run. If the failed node is "Delete Reported Rows",
     already-emailed rows may be re-reported next run.
     ```
2. **Update 3 nodes** — `Get Error Log Rows`, `Send Error Report Email`,
   `Delete Reported Rows`: set `onError: continueErrorOutput`, `retryOnFail: true`,
   `maxTries: 3` (exact Token Regen settings).
3. **Add 3 connections** — each of those nodes' error output (main, index 1) →
   `Alert: Error Log Export Failed`.

Decisions locked in with the fix:

- **Accepted blind spot:** the alert uses the same Ionos SMTP as the report itself — a hard
  SMTP outage stays silent either way. Retry (3x) + alert covers transient failures only.
  The "second channel" (global Error Workflow / Slack) option was offered and declined.
- **No data-loss change:** deletes stay on the success path. Failed report send = rows remain
  and re-export next run (same as pre-fix). Failed delete = duplicate report next run, now
  alerted instead of silent.
- Section 4 decision 7's "no `continueOnFail` on the Send Email node" and decision 9's
  faithful-port stance are both superseded by this section.
