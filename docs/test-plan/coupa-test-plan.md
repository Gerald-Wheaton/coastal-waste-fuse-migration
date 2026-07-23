# Coupa-side Test Plan & Mock Harness (5 workflows)

Status: **design only** (2026-07-08). No live Coupa/Limble/EHS calls; no n8n writes performed here.
This document specifies the test data + a mock-based harness so the already-built n8n Coupa
workflows can be exercised WITHOUT touching the real Coupa API. It extends the prior Step-1-only
rig (OQ-028, deployed 2026-07-05 / torn down 2026-07-06) to all four API-calling workflows plus
the email-only Error Log Export.

Companion fixtures live in `docs/test-plan/fixtures/coupa/`:
- `mock-responses.json` — canned response body per endpoint (field-by-field).
- `failmode-config.json` — error-injection config table + every failMode value.
- `datatable-seed-rows.json` — token-table + error-log seed rows, mock config/capture tables.
- `webhook-payloads.json` — Step 1 / Step 3 webhook trigger payloads.

## 0. Workflows in scope

| # | Workflow | n8n ID | Trigger | Coupa HTTP nodes to mock |
|---|---|---|---|---|
| 1 | Coupa Token Regeneration | `oCAl4h0SZenEtbNs` | Schedule (daily) | 1 (`Refresh Coupa OAuth Token`) |
| 2 | Create Requisition (Step 1) | `WJSs6apAdVH5yKkq` | Limble webhook | 6 (Get User/Address/Account/Supplier, Create Req, Attach Quote) |
| 3 | Check For New PRs (Step 2) | `WYJyHdQGcdeD8wEr` | Schedule (5 min) | 2 (Get Associated Requisition, Get PO Created From Req.) |
| 4 | WO Completed (Step 3) | `NH1giNups8iICMZe` | Limble webhook | 4 (Get PO, Attach Invoice, Post Comment ×2) |
| 5 | Error Log Export | `hR5YnDixecDz9HzJ` | Schedule (15 min) | 0 — **no Coupa mock needed** (Ionos email only) |

All 5 are built and **inactive**. Coupa base URLs are currently the real
`coastalwasteinc.coupahost.com` (restored at OQ-028 teardown).

## 1. How the workflows are pointed at the mock

Follow OQ-028's approach: swap the **host prefix only** on each Coupa HTTP node's URL
(`https://coastalwasteinc.coupahost.com` → `https://fm360.n8n.fm360consulting.com/webhook/mock-coupa`),
leaving path, query params, headers, and Bearer auth untouched. That yields, e.g.,
`.../webhook/mock-coupa/api/users`, `.../webhook/mock-coupa/oauth2/token`.

Node-level URL swaps required (13 nodes across 4 workflows):

| Workflow | Nodes to re-point |
|---|---|
| Token Regen | `Refresh Coupa OAuth Token` |
| Step 1 | `Coupa: Get User`, `Coupa: Get Address`, `Coupa: Get Account`, `Coupa: Get Supplier`, `Coupa: Create Requisition`, `Coupa: Attach Quote` |
| Step 2 | `Get Associated Requisition`, `Get PO Created From Req.` |
| Step 3 | `Coupa: Get PO`, `Coupa: Attach Invoice`, `Coupa: Post Comment (Invoice)`, `Coupa: Post Comment (No Invoice)` |

Every Coupa node also carries `Authorization: Bearer {{ Get Coupa Token.oauth_token }}` and reads
the token from the `Coastal - Coupa OAuth Token` Data Table (`QAj62weJaWmRBJ76`). The mock ignores
auth; a placeholder token row (`client=coastal_waste`, `oauth_token=MOCK-TOKEN-COUPA`) must be
seeded so the token read returns a row (else the run halts). See `datatable-seed-rows.json`.

## 2. Mock Coupa API design — "Coastal - Mock Coupa API (TEST)"

A single new n8n workflow (needs its own workflow ID from the owner per OQ-007) that answers every
Coupa endpoint across Token Regen + Step 1/2/3 with canned responses, captures every inbound
payload, and injects errors driven by a config Data Table.

### 2.1 Endpoint table (the full mock surface)

Deterministic IDs baked in: **requisition id `424242`**, **PO id `555001`**. These make the
mid-path routes registerable as literal webhook paths and let the Limble meta fields be seeded to
match (Step 2 WO `meta1=424242`, Step 3 WO `meta2=555001`).

| # | Method | Mock path (after `/webhook/`) | Stands in for | Used by | Canned response (raw body) | fullResp? | Consumer reads |
|---|---|---|---|---|---|---|---|
| 1 | POST | `mock-coupa/oauth2/token` | `/oauth2/token` | Token Regen | `{access_token:"MOCK-TOKEN-COUPA-REFRESHED", token_type,expires_in,scope}` | no | `$json.access_token` |
| 2 | GET | `mock-coupa/api/users` | `/api/users?login=` | Step 1 | `[{id:1001, login, email, active:true}]` | yes | `body.length>0` (content unused) |
| 3 | GET | `mock-coupa/api/addresses` | `/api/addresses?name=` | Step 1 | `[{id:2001, custom-fields:{entity:{external-ref-code:"CWR"}, location:{external-ref-code:"099"}}}]` | yes | `body.length>0`, `body[0].id`, `body[0].custom-fields.entity/location.external-ref-code` |
| 4 | GET | `mock-coupa/api/accounts` | `/api/accounts?segment-…` | Step 1 | `[{id:3001, account-type:{name:"Coastal Waste COA"}}]` | yes | `body.length>0`, `body[0].id`, **`body[0].account-type.name`** |
| 5 | GET | `mock-coupa/api/suppliers` | `/api/suppliers?display-name=` | Step 1 | `[{id:4001, display-name}]` — `[]` when name contains `FAIL-SUPPLIER` | yes | `body.length>0`, `body[0].id` |
| 6 | POST | `mock-coupa/api/requisitions/new/submit_for_approval` | create requisition | Step 1 | `{id:424242, status:"pending_approval"}` | yes | `body.id` |
| 7 | POST | `mock-coupa/api/requisitions/424242/attachments` | `/api/requisitions/{id}/attachments` | Step 1 | `{id:500001, type:"file"}` | yes | (not read) |
| 8 | GET | `mock-coupa/api/requisitions/424242` | `/api/requisitions/{meta1}` | Step 2 | `{id:424242, status:"ordered"}` | no | `$json.status`, `$json.id` |
| 9 | GET | `mock-coupa/api/purchase_orders` | `/api/purchase_orders?…` | Step 2, Step 3 | `[{id:555001, po-number:"PO-555001", requisition-header:{id:424242}, created-by:{fullname:"Jordan Buyer"}}]` | Step 2 no / Step 3 yes | S2: `[0].id`,`[0].po-number`; S3: `body[0].id`,`body[0].created-by.fullname` |
| 10 | POST | `mock-coupa/api/purchase_orders/555001/attachments` | `/api/purchase_orders/{poId}/attachments` | Step 3 | `{id:500002, type:"file"}` | yes | (not read) |
| 11 | POST | `mock-coupa/api/purchase_orders/555001/comments` | `/api/purchase_orders/{poId}/comments` | Step 3 | `{id:600001, comments:"posted"}` | yes | (not read) — serves both invoice & no-invoice comment POSTs |

Exact bodies and per-field rationale are in `mock-responses.json`.

**Additions beyond the OQ-028 Step-1-only rig** (which had only #2–#7): **#1** (`/oauth2/token`,
Token Regen), **#8** (`GET /api/requisitions/{id}`, Step 2), **#9** (`GET /api/purchase_orders`,
Step 2 + Step 3), **#10** (PO attachments, Step 3), **#11** (PO comments, Step 3).

### 2.2 n8n routing constraint (carried from OQ-028)

n8n does **not** match mid-path webhook route params (`/requisitions/:reqId/attachments` fails).
So routes #7/#8/#10/#11 are registered as **literal** paths using the deterministic IDs
(`424242`, `555001`). Because n8n also cannot multiplex all 11 paths under one dynamic webhook,
the mock uses **one Webhook trigger node per path** (11 total), each tagged with its logical
endpoint name, all funnelling into ONE shared handler chain. This is still a single mock workflow
and behaves as "one base path (`mock-coupa`) + a Switch on the endpoint."

### 2.3 Shared handler chain (per inbound request)

```
[Webhook (one of 11, literal path)]
  → [Set: endpoint=<name>, method]                  (identifies the route)
  → [Data Table: Insert capture row]                 "Coastal - Coupa Mock Capture (TEST)"
        {endpoint, method, query=JSON($json.query), body=JSON($json.body), receivedAt=now}
  → [Data Table: Get failMode row]                   "Coastal - Coupa Mock Config (TEST)" key=default
  → [Switch: endpoint]  ──▶ per-endpoint branch:
        [IF: failMode matches this endpoint's trigger?  (suppliers: OR query.display-name contains FAIL-SUPPLIER)]
             true  → [Respond to Webhook: error body + errorVariants.httpStatus (500 / [])]
             false → [Respond to Webhook: normalResponse (200)]
```

- **Capture**: every call writes one row for payload diffing against the build specs (§5/§7 of each
  spec). This is the primary assertion source for scheduled workflows and for confirming query
  encoding (e.g. the OQ-028 `A & B Services` single-encode check).
- **failMode**: read once per request from the config table; see `failmode-config.json` for all 12
  values and what each exercises. Set with `updateRows` before an error scenario, reset to `''` after.
- **Supplier failure** is payload-driven (contractor name contains `FAIL-SUPPLIER`), not a failMode.

## 3. Per-workflow test sections

Common assertions abbreviations: **CAP** = capture-table rows; **DT** = n8n Data Table end state;
**LMB** = Limble write expected; **EXEC** = execution status.

### 3.1 Coupa Token Regeneration (`oCAl4h0SZenEtbNs`)

- **Trigger**: Schedule → run via editor **Execute Workflow** (manual).
- **Pre**: token row `client=coastal_waste` seeded with a `scope` value; `Refresh Coupa OAuth Token`
  URL swapped to `mock-coupa/oauth2/token`. (The `httpCustomAuth` credential holds placeholder
  client_id/secret — fine, mock ignores them.)

| # | Scenario | failMode | Assertions |
|---|---|---|---|
| T1 | Happy refresh | `` | CAP: 1 row `oauth2/token`, body carries `grant_type=client_credentials` + `scope`. DT: token row `oauth_token` = `MOCK-TOKEN-COUPA-REFRESHED`, `refreshed_at`≈now, `scope` unchanged. EXEC success. |
| T2 | Token endpoint 500 | `token` | HTTP node retries 3× then takes error output → Ionos alert email "Coastal Coupa Token Regeneration failed" **to gerald@fm360consulting.com** (OQ-010). DT: token row `oauth_token` **unchanged**. EXEC: error branch taken (upsert not reached). |

Email in T2: real Ionos send, dev-routed to gerald@ — **observe** the inbox. (Do not disable the
email node; that is the failure path under test.)

### 3.2 Create Requisition — Step 1 (`WJSs6apAdVH5yKkq`)

- **Trigger**: curl the webhook (`webhook-payloads.json` → step1), `{status:"ADDED COMMENT TO TASK",
  taskID}`.
- **Pre**: 6 Coupa URLs swapped to mock; token row seeded; Limble credential = "Gerald Limble
  Sandbox" (already wired); sandbox tasks seeded per §4. Reuses OQ-028's proven s1–s7 + idempotency;
  **s8 added** to exercise the Add-Quote onerror (OQ-017) with a real quote file present.

| # | Scenario | failMode / input | Assertions |
|---|---|---|---|
| s1 | Happy, >$500, capex=Yes | `` , contractor OK, qty 1200, quote file at instr 5 | CAP: users, addresses, accounts (seg-4=`160999`), suppliers, create-req, **attachments**. LMB: status→"PO Requested" (5782), **meta1=424242**, success comment "Coupa Requisition successfully created!". DT error-log: 0 new rows. EXEC success. |
| s2 | ≤$500 | `` , amount 400, no quote | CAP: no attachments call. LMB: flip + meta1 + comment. |
| s3 | capex=No | `` , capex No, amount 1200 | CAP accounts query seg-4=`612200` (vs s1's 160999). Otherwise as s1. |
| s4 | Ampersand contractor | `` , contractor `A & B Services` | CAP suppliers query `display-name=A & B Services` **single-encoded** (no `%2526` double-escape — n8n query encoding, spec §4.7). |
| s5 | Supplier missing | contractor contains `FAIL-SUPPLIER` | CAP: suppliers → `[]`; no create-req. LMB: contractor-missing comment; **NO error-log row** (asymmetry). No status flip. |
| s6a | Site-manager miss | `user` | LMB error path A: error-log row `{errorCode:"400", errorMsg:"…Site Manager…not found in Coupa."}` + admin @-comment. No flip. |
| s6b | Location miss | `addr` | error path B: `errorMsg` names "Coastal Ninety Nine" (proves NumberToSpelled transform). |
| s6c | Account miss | `acct` | error path C: `errorMsg` shows the `s1-s2-999-glCode-Other Operating` segment string (capex-blank fallback if capex-type left blank). |
| s7 | Create-req 500 | `createreq` | error path D: error-log row with the mock's 500 body in `errorMsg`; no flip. |
| s8 | Attach-quote 500 | `attachq`, >$500 + quote present | error path E: error-log row logs the **Attach Quote node's own** error (OQ-017), not create-req's; create-req already succeeded (id 424242) but status is **not** flipped (run ends on error). |
| idem | Re-fire s1 | task meta1 already set, back in PO Create | "No Existing Requisition?" exits early; **zero Coupa traffic** (CAP: no new rows); no duplicate requisition. |

Admin comment caveat (R1/R2 from OQ-028): sandbox lacks admin 317887 and the test tasks are
unassigned, so the admin-comment node and the User/Team contractor-comment variants only no-op /
run the Plain variant unless you seed an assignee + point "Get Admin User" at a sandbox userID.
To close R1/R2: assign one sandbox task to a user and one to a team, re-fire s5; temporarily point
"Get Admin User" at a sandbox userID, re-fire one s6 scenario.

### 3.3 Check For New PRs — Step 2 (`WYJyHdQGcdeD8wEr`)

- **Trigger**: Schedule (5 min) → **Execute Workflow** (manual).
- **Pre**: 2 Coupa URLs swapped to mock; token row seeded. **Credential caveat (finding):** Step 2's
  Limble nodes (`Get 'PO Requested' WOs`, `Set 'PO Approved' Status…`) are wired to the **PROD**
  credential "Coastal Waste Limble" (`qn6u8jEK085DoHT8`), unlike Step 1/3 which use the sandbox
  credential. **Swap Step 2's Limble credential to "Gerald Limble Sandbox" (`MX0lwgfyFiGUBh5W`) for
  the test phase** — otherwise Step 2 reads/patches PROD Limble tasks. Swap back at cutover.
- **Pre-Limble**: ≥1 sandbox WO in status "PO Requested" (5782), `meta1=424242`, description contains
  `@CoupaWO;`, with team / user / neither assignment variants.

| # | Scenario | failMode | Assertions |
|---|---|---|---|
| S2-1 | No PR yet | `reqpending` | CAP: `getRequisition` only (status `requisition_pending`); "Is Requisition Ordered?" false → no `purchase_orders` call. LMB: WO **untouched** (no meta2, no flip, no comment). EXEC success. Re-poll would re-select it (expected). |
| S2-2 | Ordered → PO, team-assigned | `` | CAP: getRequisition (ordered), purchase_orders. LMB PATCH: `statusID`=**"PO Approved" (5783)** (OQ-026 fix), `meta2=555001`, description appended ` \|\| Coupa PO# PO-555001`; **team** comment `@<team>` posted. EXEC success. |
| S2-3 | Ordered → PO, user-assigned | `` | As S2-2 but **user** branch, comment `@<user first last>`. |
| S2-4 | Ordered, neither assigned | `` | PATCH still flips status + writes meta2/desc; **no comment** (faithful no-fallback, spec §4.5). |
| S2-idem | Re-run after S2-2 | `` | The flipped WO now sits in "PO Approved", so `Get 'PO Requested' WOs` no longer returns it → not reprocessed (the flip is the idempotency guard). |

**OQ-029 gap (document, don't test):** Step 2's built graph has **no error subgraph** — no
error-output wiring, no error-log write, no admin comment. A `getreq`/`getpo`/PATCH/comment failure
currently aborts silently. The `getreq`/`getpo` failModes exist in the config but there is nothing
to assert until the OQ-008/OQ-029 fix is added. Note this as a known coverage hole.

### 3.4 WO Completed — Step 3 (`NH1giNups8iICMZe`)

- **Trigger**: curl the webhook (`webhook-payloads.json` → step3), `{status:"COMPLETE", taskID}`.
- **Pre**: 4 Coupa URLs swapped to mock; token row seeded; Limble cred = "Gerald Limble Sandbox"
  (already wired). Sandbox completed WO with `meta1` populated, **`meta2=555001`**, description
  contains `@CoupaWO;`, "Upload Invoice Here" instruction (with/without a file per scenario).

| # | Scenario | failMode / input | Assertions |
|---|---|---|---|
| S3-1 | Invoice present (happy) | `` , "Upload Invoice Here" has file link | CAP: `Coupa: Get PO` with `?id=555001` (**OQ-030 by-id fix**) → body[0].id=555001; PO attachments POST; PO comment POST body `@Jordan Buyer: PO is ready for receiving…`. DT error-log: 0 rows. EXEC success. |
| S3-2 | No invoice | `` , no file on the instruction | invoiceResponse.link empty → "Has Invoice?" false → **no attach**; comment (No Invoice) posted (same body). CAP: PO get + comment only. Error-log 0 rows. |
| S3-3 | Attach fails | `poattach`, invoice present | attach POST 500 → error output → **Insert Error Log Row**: `{limbleWONum=taskID, errorCode, errorMsg, timestamp=now}`. Comment (Invoice) **not** posted. DT error-log: +1 row. |
| S3-4 | Comment fails | `pocomment`, no invoice (simplest path) | comment (No Invoice) POST 500 → error output → error-log +1 row. |

Note Step 3 is faithful log-only (OQ-032): **no** admin @-mention, and GET-PO / reads are uncovered
— a `getpo` failure aborts before the covered POSTs and writes nothing (expected).

### 3.5 Coupa Integration Error Log Export (`hR5YnDixecDz9HzJ`)

- **Trigger**: Schedule (15 min) → **Execute Workflow** (manual). **No Coupa mock needed** — the only
  external call is the Ionos email.
- **Pre**: seed the error-log table (`6GbR5Rxezl7hqk9i`) per `datatable-seed-rows.json`.

| # | Scenario | Setup | Assertions |
|---|---|---|---|
| E1 | Drain + email + OQ-006 partial delete | seed rows 9001, 9002; trigger; during the Ionos send window `insertRows` a 3rd row 9003 | Email (dev-routed to gerald@, OQ-010) lists **only 9001+9002** (Mountain-time formatted timestamps). After run: rows 9001/9002 **deleted**, row **9003 SURVIVES** (delete targets only the reported row IDs, not the whole table — race closed). EXEC success. |
| E2 | Empty table | 0 rows | `Get Error Log Rows` returns 0 items → nothing downstream runs → **no email**, no delete. EXEC success (no-op). |

Email: real Ionos send, dev-routed — **observe** gerald@. Fallback proof for E1 if the mid-send
insertion window is hard to hit: inspect that `Delete Reported Rows` filters `id = <reported id>`
(per exploded row), never a full-table wipe — confirmed in the built node. Insert 9003 anytime
before Delete runs; it must remain.

## 4. Limble sandbox fixtures required (hand-off to the Limble agent — enumerate only)

These are the Limble inputs each Coupa workflow needs. Seeding mechanics live in
`limble-sandbox-fixtures.md` §5 — either a dedicated **n8n seeder workflow** using the
**"Gerald Limble Sandbox"** credential (`MX0lwgfyFiGUBh5W`, recommended when there's no local
`.env`), the local `tools/sandbox-seed/` script (already covers most of Step 1), or the Limble UI.
**All seeded data goes under sandbox location `98472` "Coastal 99 - Sandbox Test".** The
deterministic-ID constraints below are **hard requirements** for the mock to line up.

**Instance-wide (all steps):**
- **Statuses**, exact spelling: `PO Create`, `PO Requested`, `PO Approved` (Step 1 gate/flip, Step 2
  read/flip). Prod IDs are 5784 / 5782 / 5783 (OQ-025); sandbox IDs may differ — the workflows look
  them up by `%…%` name, so only spelling matters.
- **Location**: `Coastal 99 - Sandbox Test` (locationID `98472`) — already seeded (OQ-028); its name
  drives the `Coastal Ninety Nine` address transform.

**Step 1:**
- **Site Manager user**: firstName `Site Manager`, a lastName, an email, role `View Only` at 98472,
  **active** (drives `CoastalSiteManagerExtract`).
- **Template + 9 scenario tasks** (s1–s7 + idempotency) from the 17-instruction template (quote-upload
  at position 5), with the 6 load-bearing instruction texts VERBATIM and responses per the OQ-028
  scenario table (README in `tools/sandbox-seed/`). Each task: status `PO Create`, description
  contains `@CoupaWO;`, trigger comment `Status was changed from Open to PO Create`, `meta1` EMPTY.
- **Idempotency task**: same as s1 but with `meta1` pre-populated.
- **(R1)** one task **assigned to a user** and one **assigned to a team** (for the contractor-comment
  User/Team variants on supplier-miss).
- **(R2)** one sandbox **userID** to temporarily stand in for admin `317887` (absent in sandbox) if
  exercising the admin-comment node.

**Step 2:**
- ≥1 WO in status **`PO Requested`**, **`meta1=424242`** (must equal the mock's requisition id),
  description contains `@CoupaWO;`. Assignment variants: one with a **teamID** (≠0), one with a
  **userID** (≠0), one with **neither** (for S2-1..S2-4).

**Step 3:**
- 1 **completed** WO (status Complete), `meta1` populated, **`meta2=555001`** (must equal the mock's
  PO id), description contains `@CoupaWO;`, and an **`Upload Invoice Here`** instruction — with a
  file/link for S3-1/S3-3/S3-4, without a file for S3-2. (Verify the exact instruction label on the
  live template — Step 3 spec §4.6.)

**Meta-field summary (deterministic-ID contract):** Step 2 WO `meta1 = 424242`; Step 3 WO
`meta2 = 555001`. If Steps 1→2→3 are chained on one task, these flow automatically (s1 stamps
meta1=424242; Step 2 writes meta2=555001). For isolated per-step tests, seed them directly.

## 5. n8n writes / data-table rows needed at test time (permission list — OQ-003 is read-only today)

Every item below is a WRITE; none are performed in this design phase. Grouped so the owner can grant
scoped permission:

**New workflow (needs an ID per OQ-007):**
- Create `Coastal - Mock Coupa API (TEST)` (11 webhook nodes + shared handler), set ACTIVE.

**New Data Tables (`createTable`):**
- `Coastal - Coupa Mock Capture (TEST)` — cols endpoint/method/query/body/receivedAt.
- `Coastal - Coupa Mock Config (TEST)` — cols key/failMode; seed `{key:default, failMode:''}`.

**Data-table rows (`insertRows`/`upsertRows`/`updateRows`):**
- Token table `QAj62weJaWmRBJ76`: upsert `client=coastal_waste` row (token `MOCK-TOKEN-COUPA`, a
  scope value). 1 row.
- Config table: update `failMode` before/after each error scenario (many `updateRows`, single row).
- Error-log table `6GbR5Rxezl7hqk9i`: seed 9001/9002 (+9003 mid-run) for E1. 2–3 rows.
- Runtime (auto, by the workflows): capture rows (one per Coupa call), error-log rows (Step 1 s6/s7/s8,
  Step 3 S3-3/S3-4).

**Workflow edits (`n8n_update_partial_workflow`):**
- Swap 13 Coupa node URLs to the mock (Token 1, Step 1 ×6, Step 2 ×2, Step 3 ×4).
- Swap Step 2's Limble credential (2 nodes) from PROD `qn6u8jEK085DoHT8` → sandbox `MX0lwgfyFiGUBh5W`.

**Activation:** set the mock workflow ACTIVE; the 4 target workflows can run via manual/execute or
`/webhook-test/` without activating (except Step 1/Step 3 if firing the production `/webhook/` path).

## 6. Teardown checklist (mirrors OQ-028 cutover teardown)

1. **Revert base URLs** on all 13 Coupa nodes back to `https://coastalwasteinc.coupahost.com`
   (Token 1, Step 1 ×6, Step 2 ×2, Step 3 ×4). Verify by node read.
2. **Revert Step 2's Limble credential** to PROD `qn6u8jEK085DoHT8` ("Coastal Waste Limble").
3. **Delete** the mock workflow + `Coastal - Coupa Mock Capture (TEST)` + `Coastal - Coupa Mock
   Config (TEST)` tables.
4. **Purge the dummy token row** (`client=coastal_waste`) from `QAj62weJaWmRBJ76`, leaving only the
   real `Coastal_Waste (TEST)` row.
5. **Purge test error rows** from `6GbR5Rxezl7hqk9i` (table back to empty).
6. **Deactivate** any workflow left active; confirm all 5 targets inactive.
7. **`n8n_validate_workflow`** each of the 4 edited workflows — expect clean (Step 2 will still show
   the OQ-029 no-error-handling warnings; that is pre-existing, not from testing).
8. Limble sandbox fixtures may be left in place or cleaned (owner's call). Credential swap
   sandbox→prod for Step 1/3 is a **go-live** step, not test teardown.

## 7. Assumptions & open questions hit

- **A1 — Step 2 Limble credential points at PROD.** The built Step 2 uses "Coastal Waste Limble"
  (prod) on both Limble nodes, unlike Step 1/3 (sandbox). Testing Step 2 as-is would read/patch prod
  tasks. Plan assumes it is swapped to sandbox for the test phase (§3.3 pre) and swapped back at
  teardown. **Confirm with owner.**
- **A2 — deterministic IDs must match Limble meta seeding.** The mock's literal mid-path routes force
  Step 2 WO `meta1=424242` and Step 3 WO `meta2=555001`. If the Limble agent seeds different ids, the
  mock routes must be renamed to match (or vice-versa). Coordinate.
- **A3 — Step 2 error paths are untestable now (OQ-029).** No error subgraph is built, so `getreq`/
  `getpo` failModes have nothing to assert. Testing the Step 2 error path is blocked until OQ-008/
  OQ-029 lands.
- **A4 — email verification is observational.** T2 (Token alert) and E1/E2 (export report) send real
  Ionos email dev-routed to gerald@ (OQ-010). No SMTP stub is specified; observe the inbox. If a stub
  is preferred, it must not break the export's "delete only if send succeeded" gate.
- **A5 — mock response shapes are still reverse-engineered (OQ-009/OQ-028 item 1).** The rig proves
  the workflows handle *expected* Coupa responses, not that expectations match Coupa reality. Real
  acceptance (auth, payload, account segments, the `{file:<URL>,type:"file"}` attachment shape) stays
  unverified until a live call — OQ-016/OQ-024/OQ-030 confirmation points unchanged. Step 3's
  attachment payload (spec §4.7) is the highest live-test risk.
- **A6 — R1/R2/R4 residual surface** from OQ-028 persists: contractor User/Team comment variants and
  the admin-comment node need assigned tasks + a sandbox admin stand-in; real-Coupa acceptance (R4) is
  out of scope for a mock. The plan closes R3 (Error Log Export end-to-end) via §3.5.
- **A7 — `meta1`/`meta2` write shape unverified against real Limble API** (OQ-024 hyp. 2). The mock
  proves the n8n side; observing meta1=424242 on the sandbox task after s1 is the synthetic proof
  (already achieved once in OQ-028 for Step 1).
