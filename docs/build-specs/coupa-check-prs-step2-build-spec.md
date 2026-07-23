# Build Spec — Coastal - Check For New PRs Ordered & Update Limble WO (Step 2) (PROD)

Status: **Built** (confirmed 2026-07-07 via direct n8n read; workflow `updatedAt` 2026-07-06),
into `WYJyHdQGcdeD8wEr` ("Update Limble WO on New PRs (Step 2)"), inactive. §4.1 status-flip
fix and §4.3 Bearer-auth fix are both present in the built graph. **§4.2 error-log subgraph
(OQ-008) added 2026-07-09 — OQ-029 resolved** (26 nodes; mirrors Step 1 §4.9; see OQ-029 for
the node list). This doc previously said
"design only, not built (2026-07-03)"; corrected after the build was found already done in a
prior session that wasn't reflected back into the tracker.

Source blueprint: `docs/OG-workflows/Coastal - Check For New PRs Ordered & Update Limble WO
(Step 2) (PROD).json` (9 modules incl. 1 router with 2 routes; **zero `onerror` chains** —
confirmed via recursive walk; no custom `function:Coastal*` calls). This is the smallest and
simplest of the three Coupa steps.

Design-truth note: the narrative review doc `docs/Coastal - Limble Integration Review - Coupa
Integration (v1.2.0).docx` §"Step 3: Checking for PR Ordering" (its Step 3 == this blueprint)
is the **source of truth** for intended behavior where it and the blueprint disagree — owner
directive 2026-07-03. It disagrees on one material point (the status flip, §4.1).

Decisions locked 2026-07-03 (this session):
- **§4.1 status flip → SANCTIONED FIX** (docx-mandated; the blueprint omits it — a bug).
- **§4.2 error handling → SANCTIONED FIX** (add error-log table + admin comment; OQ-008 resolved).
- **§4.3 Coupa auth → RESOLVED 2026-07-06 (OQ-027): Bearer-for-all**, same pattern as Step 1
  (OQ-016) — Bearer token from the "Coastal - Coupa OAuth Token" Data Table on both Coupa
  calls. Confirmation point stays the first live test (401/403 = revisit).
- Deliverable this session = this spec only; Step 2 stays design-only/Hold (like Step 1).

---

## 1. Purpose

Every 5 minutes, find all Limble WOs sitting in the **"PO Requested"** sub-status (the status
Step 1 leaves a WO in after creating its Coupa requisition), and for each one check whether its
Coupa requisition has been approved/ordered and converted into a PO. When it has: save the PO
id to the WO's `meta2`, append the PO number to the WO description, flip the WO to **"PO
Approved"**, and post a comment @-mentioning the assignee so they get notified that work may
begin. WOs whose requisition is not yet ordered are left untouched and re-checked next run.

This is the Coupa correlation-poll half of the Step 1 → Step 2 handshake: Step 1 writes `meta1`
(requisition id) + status "PO Requested"; Step 2 reads `meta1`, writes `meta2` (PO id) + status
"PO Approved".

## 2. Trigger

| | Source (Make) | n8n target |
| --- | --- | --- |
| Type | Scheduled poll, **every 5 minutes** (per `docs/workflow-list.md`; Make schedule config is not in the JSON export) | **Schedule Trigger** node, interval = 5 minutes |
| Timezone | N/A — a fixed 5-minute interval has no wall-clock anchor, so the Eastern-vs-Mountain question (OQ-014) does not affect this trigger | no timezone setting needed |

No webhook, no inbound payload. The workflow discovers its own work each run via the status
query (§3 module 10/11).

## 3. Source flow (Make, as-is)

Linear, single router at the tail:

1. `universalModule` (10) — `GET /v2/statuses?name=%PO Requested%&limit=1` → the "PO Requested"
   statusID. Connection 2106 (Limble).
2. `universalModule` (11) — `GET /v2/tasks/?statusIDs={{10.body[1].statusID}}` → **all** tasks
   currently in that status.
3. `BasicFeeder` (13) — `array = {{11.body}}` — iterate one task at a time.
4. `coupa:makeApiCall` (14) — `GET api/requisitions/{{13.meta1}}`. Connection 1766, **no auth
   header** (OQ-016/§4.3). **Filter "WO is Coupa related?":** `13.meta1` exists AND
   `13.description` contains `@CoupaWO;`.
5. `coupa:makeApiCall` (21) — `GET api/purchase_orders?requisition-header[id]={{14.body.id}}`.
   Connection 1766, **no auth header**. **Filter "Is Requisition Ordered?":** `14.body.status`
   == `"ordered"` (text:equal, i.e. case-insensitive per Make semantics).
6. `universalModule` (20) — `GET /v2/statuses?name=%PO Approved%&limit=1` → the "PO Approved"
   statusID. Connection 2106. **⚠ Its result is never referenced by any downstream mapper —
   see §4.1.**
7. `updateATask` (15) — `taskID={{13.taskID}}`, `metadata.meta2={{21.body[1].id}}`,
   `description="{{13.description}} || Coupa PO# {{21.body[1].`po-number`}}"`, `work_request={}`.
   Connection 2106. **Does NOT set `statusID`** (the bug — §4.1).
8. `BasicRouter` (22) — two routes, evaluated for the same task:
   - **Route 0 — team-assigned:** `listTeams` (25) `teams={{13.teamID}}, limit=1` (**filter:**
     `13.teamID` exists AND `!= 0`) → `universalModule` (19) `POST /v2/tasks/{{13.taskID}}/
     comments` body `@{{25.name}} The Coupa PO has been approved for this WO. Work may now be
     conducted.` (blue font).
   - **Route 1 — user-assigned:** `listUsers` (24) `users={{13.userID}}, limit=1` (**filter:**
     `13.userID` exists AND `!= 0`) → `universalModule` (23) `POST .../comments` body
     `@{{24.firstName}} {{24.lastName}} The Coupa PO has been approved...`.
   - **No "neither assigned" route** — a WO with neither `teamID` nor `userID` gets no comment
     (faithful; §4.5).

Notes on the as-is graph:
- **Zero error handling** anywhere (OQ-008) — any failed Coupa/Limble call aborts that
  Feeder iteration (Make `maxErrors: 3` at scenario level, then the run stops); nothing is
  logged or surfaced.
- `meta1` is read off the task object returned by the tasks-list call (11) — it must be present
  inline in that response (Step 1 writes it there). `13.description`, `13.teamID`, `13.userID`,
  `13.taskID` likewise come from the task list item.
- Make `body[1]` (1-indexed first element) → n8n `body[0]`.

## 4. Design decisions

### 4.1 Status flip to "PO Approved" — SANCTIONED FIX (docx source of truth)

The blueprint fetches the "PO Approved" statusID (module 20) but **never writes it** — module
15's `updateATask` sets `meta2` + `description` + `work_request` only, no `statusID`. The docx
(v1.2.0, final pre-go-live) explicitly requires the flip:

> "The integration will then set the status of the Limble WO to the 'PO Approved' sub-status
> and a comment will also be inserted... NOTE: the comment is needed as it generates a
> notification... changing the status does not send out a notification."

So the status change and the comment are **both** load-bearing and serve different ends (status
= progression to Step 4; comment = assignee notification). Owner directive: docx is source of
truth on disagreements. **The n8n port sets `statusID = <PO Approved id>` (from module 20's
lookup) in the same task-update call.**

Why it also matters mechanically: without the flip, the processed WO stays in "PO Requested",
so the **next 5-minute poll re-selects it** (module 11), re-appends `|| Coupa PO# X` to the
description, and re-posts the approval comment — indefinitely. The flip is therefore also the
natural idempotency guard: once flipped, the WO drops out of the polled set. (This never
manifested in prod because Step 1 has essentially never succeeded there — no WO ever reached
"PO Requested"; OQ-024.)

Joins the sanctioned-fixes list (OQ-005/006/012/017/021/022 + Step 2's OQ-008 fix below).
Tracked as **OQ-026**.

### 4.2 Error handling — SANCTIONED FIX (OQ-008 resolved: add logging)

Step 2 ships with no error handling; the sanctioned fix brings it in line with Step 1/Step 3:
failures write to the shared **"Coastal - Coupa Integration Error Log"** Data Table
(`6GbR5Rxezl7hqk9i`, drained by the built Error Log Export) and @-mention the admin on the WO.

Since the source has no error branches to port literally, the n8n design adds them at the
failure-prone calls, converging on one shared error subgraph (same shape as Step 1 §4.9):

- **Covered calls (On Error → error output → shared subgraph):** Coupa `GET requisition` (14),
  Coupa `GET purchase_orders` (21), `updateATask` (15), and the two comment POSTs (19/23). The
  two status lookups (10/20) failing aborts the whole run before any per-task work — log once at
  workflow level (see below), not per task.
- **Shared error subgraph** emits/writes a Data Table row:
  `{ limbleWONum: <13.taskID>, errorCode: <http status or "Step2 error">, errorMsg: <node
  error.message>, timestamp: <now, native Date/ISO> }` (matches OQ-012's ISO obligation and the
  Step 1 error-log schema) → `GET` admin user `317887` → `POST` a comment on the WO (admin id
  hardcoded, faithful to Step 1's convention; identity = Brandon Ray Freckleton per OQ-019).
- **Per-iteration isolation:** an error on one task must not abort the remaining tasks in the
  poll. Use "Continue (using error output)" on the covered nodes so the Feeder/loop proceeds to
  the next task after logging.

**Comment wording — SIGNED OFF 2026-07-06 (owner): distinct message per covered call.** All
share the frame `@<admin>, Task# {N}: An unexpected error occurred while <clause>. Please
reach out to FM360 to resolve.` with the middle clause per failing node:

| Covered call | Middle clause |
|---|---|
| Coupa `GET requisition` (14) | "fetching the Coupa requisition" |
| Coupa `GET purchase_orders` (21) | "checking the Coupa PO status" |
| Limble `updateATask` (15) | "updating the Limble WO" |
| Comment POSTs (19/23) | "posting the notification comment" |

The error-log row schema above is unchanged (one shape for all calls; the distinct wording
lives in the comment only, and `errorMsg` carries the raw node error regardless).

### 4.3 Coupa auth — RESOLVED (OQ-027, 2026-07-06): Bearer-for-all

Both Coupa calls (14 GET requisition, 21 GET purchase_orders) use Make connection `1766` and
send **no `Authorization` header** in the export — same shape as Step 1's 3 unauthenticated
lookups. OQ-016 resolved *Step 1's* calls to "Bearer-for-all" (daily token from the "Coastal -
Coupa OAuth Token" Data Table); owner initially declined to auto-extend that to Step 2
(tracked as OQ-027), then **resolved it the same way on 2026-07-06: Bearer-from-Data-Table on
both calls.** Confirmation point is the first live test — a 401/403 on either call means
revisit. No other part of the spec depends on the outcome.

### 4.4 Token + error-log plumbing inherit prior specs

- Coupa Bearer token (§4.3/OQ-027, resolved) read from Data Table **"Coastal - Coupa OAuth
  Token"** (`QAj62weJaWmRBJ76`) — same source as Step 1 §4.1, written by the built Token Regen
  workflow.
- Error-log writes → Data Table **"Coastal - Coupa Integration Error Log"**
  (`6GbR5Rxezl7hqk9i`), `timestamp` native Date/ISO (OQ-012).
- Limble via HTTP Request nodes against `https://api.limblecmms.com`, credential **"Coastal
  Limble API"** (OQ-015). Coupa host `https://coastalwasteinc.coupahost.com`.

### 4.5 Router — faithful two-route, no "neither" fallback

Port router 22 as-is: an IF/Switch producing a team branch (teamID exists and != 0) and a user
branch (userID exists and != 0). A WO assigned to neither posts no comment. This is faithful —
do not add a fallback comment. (Consequence with the §4.1 fix: such a WO still advances to "PO
Approved" and gets `meta2`/description; it just isn't notified. Matches source intent, which
tied the comment to an assignee.)

### 4.6 Feeder → n8n items

`BasicFeeder` (13) over `11.body` → the tasks-list HTTP node already returns items; split/loop
so each task flows independently (needed for §4.2 per-iteration error isolation). If using a
Loop Over Items node, keep the Coupa filters (§3.4/§3.5) as IF gates inside the loop:
- "WO is Coupa related?": `meta1` truthy AND `description` contains `@CoupaWO;` — tasks failing
  this are skipped (no requisition lookup).
- "Is Requisition Ordered?": `requisition.status` == `"ordered"` (case-insensitive) — tasks
  failing this are left untouched for the next poll (the documented not-yet-ordered path).

### 4.7 Description append + field notes (faithful)

- Description becomes `"{original} || Coupa PO# {po-number}"` — note the ` || ` separator and
  Coupa's hyphenated field name `po-number` (bracket/quote access in n8n).
- `meta2 = purchase_orders[0].id`; PO number for the description = `purchase_orders[0]["po-number"]`.
- `work_request: {}` in the source updateATask is an empty object — carry as a no-op or omit if
  the Limble PATCH tolerates its absence (verify at build).
- The merged task update (§4.1) sets `meta2` + `description` + `statusID` in one PATCH (Step 1
  §4.5 precedent of collapsing sequential updateATask calls into one).

## 5. Target n8n node graph

```
[Schedule Trigger: every 5 min]
  → [HTTP L: GET /v2/statuses?name=%PO Requested%]          (10)
  → [HTTP L: GET /v2/tasks/?statusIDs={PO-Requested id}]    (11)
  → [HTTP L: GET /v2/statuses?name=%PO Approved%]           (20 — moved up; result used in §4.1 flip)
  → [Loop Over Items: tasks]                                 (13 Feeder)
       → [IF: meta1 exists AND description contains "@CoupaWO;"]      (14 filter)
       → [HTTP C: GET api/requisitions/{meta1}]  ──err──▶ (shared error subgraph)   (14)
       → [IF: requisition.status == "ordered"]   (21 filter; false → skip, retry next poll)
       → [HTTP C: GET api/purchase_orders?requisition-header[id]={reqId}] ──err──▶ (err)  (21)
       → [HTTP L: PATCH task {meta2: PO.id, description: "{desc} || Coupa PO# {po-number}",
                             statusID: {PO-Approved id}}]  ──err──▶ (err)            (15 + §4.1)
       → [Switch/IF: assignee]                                                        (22)
            team (teamID exists & !=0)  → [HTTP L: listTeams {teamID}] → [HTTP L: POST comment @team] ──err──▶(err)
            user (userID exists & !=0)  → [HTTP L: listUsers {userID}] → [HTTP L: POST comment @user] ──err──▶(err)
            neither                      → (no comment; faithful)

(shared error subgraph: [Data Table: Insert row {limbleWONum, errorCode, errorMsg,
 timestamp=now ISO} → "Coastal - Coupa Integration Error Log" 6GbR5Rxezl7hqk9i]
 → [HTTP L: GET user 317887] → [HTTP L: POST @admin comment] → continue loop)
```

`HTTP L` = Limble (credential "Coastal Limble API"), `HTTP C` = Coupa
(`https://coastalwasteinc.coupahost.com`; Bearer-from-Data-Table auth per §4.3/OQ-027).

Node notes beyond §3/§4:
- **"PO Approved" status lookup (20)** is hoisted above the loop (fetch once per run, not per
  task) since its value is now consumed by every iteration's task update (§4.1). Faithful to the
  source's single fetch; just repositioned for efficiency.
- **All "found?" gates:** Make `body[1]`/`array:greater 0` → n8n `[0]` / `.length > 0`.
- **On Error = "Continue (using error output)"** on the 5 covered calls (§4.2), wired to the
  shared subgraph, so one task's failure logs and the loop moves on.
- **No retries** specified in the source; unlike Step 1, OQ-022's GET-retry sanction was
  Step-1-scoped — do not add retries here without a separate sanction (flag if desired).

## 6. Cross-workflow dependencies

- **Reads `meta1`** (Coupa requisition id) + **status "PO Requested"** — both written by Step 1.
  Any change to how Step 1 writes `meta1` or names that status breaks Step 2's poll. (Step 1
  spec §6 already flags the reciprocal.)
- **Writes `meta2`** (Coupa PO id) + **status "PO Approved"** — consumed by Step 3/Step 4 (WO
  Completed → Update Coupa PO). Carry `meta2` semantics forward into the Step 3 spec.
- **Reads** "Coastal - Coupa OAuth Token" (`QAj62weJaWmRBJ76`) — written by the built Token
  Regen workflow; both Step 2 Coupa calls use it (§4.3/OQ-027, resolved Bearer-for-all).
- **Writes** "Coastal - Coupa Integration Error Log" (`6GbR5Rxezl7hqk9i`) — drained by the built
  Error Log Export. Step 2 becomes a **third writer** (with Step 1 and Step 3) under the OQ-008
  fix; all three must point at this same table (no second error log).
- **Status names** "PO Requested" (read) and "PO Approved" (write) are looked up by name at
  runtime (`%...%` wildcard, limit 1) — both confirmed 2026-07-06 (OQ-025 resolved — see §7).

## 7. Open items gating the build

- **Owner go-ahead** to build into `WYJyHdQGcdeD8wEr` — not yet given (design-only, mirrors
  Step 1's Hold).
- **OQ-027: RESOLVED 2026-07-06 — Bearer-for-all** (owner decision, matches OQ-016). Both
  Coupa HTTP nodes use the Bearer token from the "Coastal - Coupa OAuth Token" Data Table.
  Confirmed at first live test (401/403 = revisit).
- **OQ-025: RESOLVED 2026-07-06 — both status names confirmed via owner's direct API pull**
  of the full Coastal status list: `PO Requested` = statusID 5782 (read, module 10),
  `PO Approved` = statusID 5783 (write, module 20 + §4.1 flip), `PO Create` = 5784. Spellings
  match the runtime `%...%` lookups exactly; the docx's "PO Request Submitted" variant was
  just doc drift. No longer gates the build. (Do not re-verify via the MCP `get_statuses`
  tool — it returns only "In Progress" even against Coastal; use the real `/v2/statuses`
  endpoint or the UI.)
- **OQ-024 (no working prod baseline)** — Step 2 has never processed a real WO. No regression
  history; validate against synthetic WOs driven to "PO Requested" with a real (or stubbed)
  ordered Coupa requisition through every path (ordered / not-ordered / team / user / neither /
  error).
- **§4.2 error-message wording — SIGNED OFF 2026-07-06**: distinct per-call middle clauses
  (table in §4.2); shared frame and log-row schema unchanged.

## 8. Relationship to recon (2026-07-03, OQ-023) and to the Step 1 spec

- Status-name risk (OQ-025) and the null-`meta1`/no-baseline facts (OQ-024) carry over directly
  from the Step 1 spec §8 — Step 2 sits downstream of the same never-succeeded path.
- Admin escalation user `317887` = Brandon Ray Freckleton, active (OQ-019) — reused here for the
  §4.2 error comments.
- Limble API quirks apply: name filters need explicit `%` wildcards (already present in modules
  10/20); pass explicit `limit` (source does). The tasks-list call (11) has no explicit limit —
  verify Limble's default page size for `/v2/tasks/` and add a limit if the PO-Requested set
  could exceed it (low risk given tiny Coupa volume, but note it; cf. the instructions-endpoint
  default-2 surprise).
