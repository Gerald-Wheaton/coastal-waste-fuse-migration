# Workflow Overview

Summary-level index of the 7 Coastal Waste Make.com (Fuse) scenarios ahead of n8n build specs.
Grounded in `docs/OG-workflows/*.json` (module lists, `onerror` counts, datastore refs, custom
function calls) and the two docx review docs. Depth here is intentionally summary-only — full
module/route/onerror walks belong in the per-workflow build-spec docs (`<workflow>-build-spec.md`),
not here.

## Index

| # | Workflow | Trigger | Purpose | Integration |
| - | -------- | ------- | ------- | ------------ |
| 1 | [Coupa Token Regeneration](#1-coastal---coupa-token-regeneration-prod) | Daily @ 12:00AM MST | Refresh Coupa OAuth token, store for other scenarios | Coupa (shared) |
| 2 | [Create Requisition in Coupa (Step 1)](#2-coastal---create-requisition-in-coupa-step-1-prod) | Limble webhook: new task comment | Parse a Limble task comment into a Coupa PR | Coupa |
| 3 | [Check For New PRs Ordered & Update Limble WO (Step 2)](#3-coastal---check-for-new-prs-ordered--update-limble-wo-step-2-prod) | Every 5 min | Poll Coupa for PR→PO conversion, update the Limble WO | Coupa |
| 4 | [WO Completed; Update Coupa PO (Step 3)](#4-coastal---wo-completed-update-coupa-po-step-3-prod) | Limble webhook: task completed | Push invoice/completion data to the Coupa PO | Coupa |
| 5 | [Create WO From EHS Inspection](#5-coastal---create-wo-from-ehs-inspection-prod) | Daily @ 4:00PM MST | Poll EHS Insight for new inspections, create Limble WOs | EHS Insight |
| 6 | [Update EHS Inspection From Limble WO](#6-coastal---update-ehs-inspection-from-limble-wo-prod) | Limble webhook: task completed | Write Limble WO completion notes back to EHS Insight | EHS Insight |
| 7 | [Coupa Integration Error Log Export](#7-coastal---coupa-integration-error-log-export) | Every 15 min | Drain shared Coupa error-log datastore, email report | Coupa (shared) |

## How these connect

Two independent integrations share nothing at the trigger level but do share Coupa-side plumbing:

- **Coupa PR→PO→invoice chain (#2 → #3 → #4).** A single Limble WO/task flows through all three
  in sequence: #2 creates the PR from a task comment, #3 polls until Coupa converts it to a PO and
  writes that back onto the same Limble WO, #4 fires later when the WO is marked complete and pushes
  the invoice to that PO. They're linked by Limble WO/task ID, not by a direct Make-to-Make call —
  each is its own scenario with its own trigger.
- **Coupa credential lifecycle (#1 feeds #2, #3, #4).** #1 refreshes the OAuth token daily and writes
  it to datastore `324`; #2/#3/#4 each read `324` to authenticate their `coupa:makeApiCall` calls.
  Per OQ-005, the n8n port replaces this shared datastore with an isolated n8n credential — so this
  fan-out collapses to "one credential, read by three workflows" rather than a datastore dependency.
- **Coupa error log (#2, #4 write → #7 drains).** #2 and #4 write failures to datastore `326`
  (found via the `onerror` walk — not visible from a flat read); #7 runs independently every 15 min,
  emails a report, and deletes the drained records. Per OQ-006, the n8n port fixes #7 to delete only
  the rows it exported, not the whole table (current Make behavior has a race). Note: #3 (the
  5-minute Coupa poller) has **zero** `onerror` chains and does not write to `326` — see OQ-008,
  still open on whether that's faithfully ported or fixed.
- **EHS chain (#5, #6) is fully separate** from the Coupa side — no shared datastore, no onerror
  writes at all (OQ-004: ported as-is, no error logging added). #5 creates the Limble WO from an EHS
  inspection; #6 is triggered independently later when that WO is completed and writes notes back to
  EHS Insight. Linked only by Limble WO ID, same pattern as the Coupa chain.
- **No workflow calls another workflow directly.** All linkage is via shared external state (Limble
  WO/task records, the two Coupa datastores) — never a Make "execute scenario" call. This matters
  for the n8n port: OQ-002 already decided 7 scenarios → 7 n8n workflows, trigger boundaries
  preserved exactly, so this indirect-linkage pattern carries over unchanged.

| Shared state | Written by | Read by | n8n target |
| --- | --- | --- | --- |
| Datastore 324 (Coupa OAuth) | #1 | #2, #3, #4 | Isolated n8n credential (OQ-005) |
| Datastore 326 (Coupa error log) | #2 *(none found)*, #4 *(confirmed)* — see note | #7 | n8n Data Table, fixed drain (OQ-006) |
| Limble WO/task record | #2 creates comment trail, #3 updates WO, #4 reads on completion | #3, #4 | n/a (external system, not a Make/n8n artifact) |

Note: CLAUDE.md's persistence-model section lists both "Create Requisition" (#2) and "WO Completed"
(#4) as datastore-326 writers per the prior `onerror` walk; this session's grep only matched a
literal `"datastore": 326` on #4's top-level modules — #2's write path is inside a deeply nested
`onerror` chain that doesn't literally repeat the datastore ID as plainly as #4's. Trust the prior
walk (documented in CLAUDE.md / open-questions.md), not this session's shallow grep, for #2.

---

## 1. Coastal - Coupa Token Regeneration (PROD)

**Trigger:** Daily @ 12:00AM MST

**Purpose:** Refresh the Coupa OAuth token and persist it for the other Coupa-side scenarios to
consume.

**Key steps:** Look up current client credentials in datastore 324 → call Coupa's token endpoint
(`http:ActionSendData`) → write the refreshed token back to datastore 324 (`AddRecord`).

**Systems touched:** Coupa (`coastalwasteinc.coupahost.com`), Make datastore 324.

**Custom functions:** none.

**Persistence:** Writes datastore 324. No error-log writes (0 `onerror` chains) — a token-refresh
failure here is currently silent.

**Open questions:** OQ-005 (credential store replacement), OQ-009 (no Coupa API reference material).

---

## 2. Coastal - Create Requisition in Coupa (Step 1) (PROD)

**Trigger:** Limble webhook (Task Endpoint) — Event: New Task Comment

**Purpose:** Parse a new Limble task comment for a purchase request and create the corresponding
Coupa Purchase Requisition (PR). The largest and most complex scenario — deeply nested routers
handle multiple comment formats/approval paths.

**Key steps:** Webhook receives the comment → pull the parent task, its comments, users, and
locations from Limble (`listTasks`, `listUsers`, `listInstructions`, `listLocations`) → run several
`util:Switcher` gates to classify the comment/request type → build the Coupa PR payload (line items,
account segments) → `coupa:makeApiCall` to create the PR → branch further (nested routers, up to 5
levels deep) to handle response variants, retries (`util:FunctionSleep`), and write results back
onto the Limble task via `updateATask`.

**Systems touched:** Limble (private app), Coupa (`coupa:makeApiCall`), datastore 324 (read token),
datastore 326 (error log, inside `onerror` chains).

**Custom functions:** `CoastalSiteManagerExtract`, `CoastalCoupaWOInstResponses`,
`LimbleGrabLatestTaskComment`, `NumberToSpelledNumberConverter` (see `docs/functions.js`).

**Persistence:** Reads 324, writes 326 on error (3 `onerror` chains present).

**Open questions:** OQ-009 (Coupa Account segment structure not independently verified against an
API spec — reverse-engineered from mapper + docx only).

---

## 3. Coastal - Check For New PRs Ordered & Update Limble WO (Step 2) (PROD)

**Trigger:** Every 5 minutes (poll)

**Purpose:** Poll Coupa for PRs that have progressed to a PO, then update the originating Limble WO
with the PO details.

**Key steps:** Pull open/pending items from Limble (`universalModule`) → `coupa:makeApiCall` (×2) to
check PR/PO status → route on result (`BasicRouter`, 2 routes) → depending on branch, pull Limble
users or teams for assignment → `updateATask` to write the PO reference back onto the Limble WO.

**Systems touched:** Limble (private app), Coupa (`coupa:makeApiCall`).

**Custom functions:** none.

**Persistence:** None — 0 `onerror` chains, no datastore reads/writes found. This is the one Coupa
API-calling scenario with no token-store read match either; worth confirming during build-spec how
it authenticates.

**Open questions:** OQ-008 (no error handling — faithful port vs. add to shared error-log pattern,
still open).

---

## 4. Coastal - WO Completed; Update Coupa PO (Step 3) (PROD)

**Trigger:** Limble webhook (Task Endpoint) — Event: Task Completed

**Purpose:** When a Limble WO/task is marked complete, push the invoice/completion data to the
matching Coupa PO.

**Key steps:** Webhook receives completed task → pull the task and its instructions from Limble
(`listTasks`, `listInstructions`) → look up the stored Coupa token (datastore 324 `SearchRecord`) →
`coupa:makeApiCall` to fetch the PO → route on outcome (`BasicRouter`, 2 routes): one path builds
and submits the invoice (`json:CreateJSON` + 2× `coupa:makeApiCall`), the other makes a single
follow-up API call.

**Systems touched:** Limble (private app), Coupa (`coupa:makeApiCall`), datastore 324 (read token),
datastore 326 (error log).

**Custom functions:** `CoastalGetInvoiceInstResponse` (see `docs/functions.js`).

**Persistence:** Reads 324, writes 326 on error (3 `onerror` chains present).

**Open questions:** OQ-009 (invoice/PO field mapping reverse-engineered from mapper + docx only).

---

## 5. Coastal - Create WO From EHS Inspection (PROD)

**Trigger:** Daily @ 4:00PM MST

**Purpose:** Poll EHS Insight for inspection results and create the corresponding Limble work
orders, including sub-instructions per finding.

**Key steps:** `http:ActionSendData` (×2+) to pull inspections/forms from EHS Insight → filter via
custom function → map EHS location to a Limble location (`listLocations` + mapping function) → route
by inspection/form type (`BasicRouter`, 3 routes, structurally identical) → each route: pull the
Limble team, create the Limble task (`createATask`), list/update its instructions
(`listInstructions`, `updateAnInstruction`), with a further 2-way branch on whether an extra HTTP
call is needed per instruction.

**Systems touched:** EHS Insight (`http:ActionSendData`), Limble (private app).

**Custom functions:** `CoastalEHSFormFilter`, `EHSLimbleLocationMapping` (see `docs/functions.js`).

**Persistence:** None — 0 `onerror` chains, no datastore use (EHS side has no error-log datastore at
all, per OQ-004).

**Open questions:** OQ-004 (no error logging — decided: port as-is), OQ-009 (no EHS Insight API
reference material).

---

## 6. Coastal - Update EHS Inspection From Limble WO (PROD)

**Trigger:** Limble webhook (Task Endpoint) — Event: Task Completed

**Purpose:** When the Limble WO created by #5 is completed, write the completion notes/results back
to the originating EHS Insight inspection.

**Key steps:** Webhook receives completed task → pull the task and its instructions from Limble
(`listTasks`, `listInstructions`) → aggregate child WO notes via custom function → build the update
payload (`SetVariable2`/`SetVariables`, `json:TransformToJSON`) → `http:ActionSendData` (×2) to
update EHS Insight.

**Systems touched:** Limble (private app), EHS Insight (`http:ActionSendData`).

**Custom functions:** `CoastalGetChildWONotes`, `CoastalEHSInspectFormUpdate` (see
`docs/functions.js`).

**Persistence:** None — 0 `onerror` chains, no datastore use.

**Open questions:** OQ-004 (no error logging — decided: port as-is).

---

## 7. Coastal - Coupa Integration Error Log Export

**Trigger:** Every 15 minutes

**Purpose:** Drain the shared Coupa error-log datastore (326) and email a report of recent
integration failures.

**Key steps:** `datastore:Stats` + `SearchRecord` (filtered on `timestamp exists`) → aggregate
results → `email:ActionSendEmail` to `ethan@fm360consulting.com` → `datastore:DeleteAllRecords`
(wipes the **entire** table, not just the exported rows — see OQ-006).

**Systems touched:** Make datastore 326, email.

**Custom functions:** none.

**Persistence:** Reads and fully clears 326 every run.

**Open questions:** OQ-006 (drain race — decided: fix to delete only exported records in the n8n
port).
