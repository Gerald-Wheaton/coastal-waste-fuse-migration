# Build Spec — Coastal - Create Requisition in Coupa (Step 1) (PROD)

Status: **BUILT 2026-07-03** into `WJSs6apAdVH5yKkq` ("Coupa - Create Requisition (Step 1)"),
49 nodes, left **inactive** until cutover (OQ-020). Owner lifted the 2026-07-03 Hold same day and
authorized the deploy (OQ-003 one-at-a-time pattern). Deployed workflow body archived at
`docs/build-specs/coupa-create-requisition-step1.n8n.json`. Limble credential wired 2026-07-04
per owner: **"Gerald Limble Sandbox"** (`MX0lwgfyFiGUBh5W`, httpHeaderAuth) on all 16 Limble
HTTP nodes. That is a **sandbox** credential — test runs hit Gerald's Limble sandbox, not
Coastal's instance. Swap to the Coastal prod Limble credential before cutover (a "Coastal Waste
Limble" credential, `qn6u8jEK085DoHT8`, already exists in n8n from OQ-015).

Source blueprint: `docs/OG-workflows/Coastal - Create Requisition in Coupa (Step 1) (PROD).json`
(79 modules incl. routers/onerror — recounted 2026-07-03 via the recursive walk; the largest of
the 7 scenarios; 3 `onerror` chains, 3 in-flow error routes; custom functions `CoastalCoupaWOInstResponses`, `CoastalSiteManagerExtract`,
`LimbleGrabLatestTaskComment`, `NumberToSpelledNumberConverter` — bodies in `docs/functions.js`).

§4's consolidations and the Add-Quote onerror fix are **approved** (OQ-021 and OQ-017, both
resolved 2026-07-03). Credentials are loaded in n8n (OQ-015 resolved 2026-07-03). Coupa auth
is settled: Bearer-for-all on all 7 calls (OQ-016 resolved 2026-07-03, confirm at first live
test). OQ-022 resolved 2026-07-03: idempotency guard + GET-lookup retries sanctioned (§4 items
12/13), rest faithful. The build go-ahead landed 2026-07-03 (Hold lifted, deployed same day).
Remaining gate is go-live only: verifying the "PO Requested" status name in Limble — see §7.

---

## 1. Purpose

When a Limble task whose description tags it `@CoupaWO;` is moved to status **"PO Create"**,
parse its instruction responses into a purchase request and create a Coupa Purchase
Requisition (PR), attach the quote file if the amount is over $500, then flip the task to
**"PO Requested"** and stamp the Coupa requisition ID onto the task (`meta1`) so Step 2 can
poll for PR→PO conversion. Every missing-prerequisite case (site manager / location / account
/ supplier not found in Coupa) posts an explanatory comment back onto the Limble task; most
also write to the shared error log.

## 2. Trigger

| | Source (Make) | n8n target |
| --- | --- | --- |
| Type | Limble webhook (hook `776`, `maxResults: 1`) — fires on task events; flow gates on event text `ADDED COMMENT TO TASK` | **Webhook** node, POST, Respond Immediately |
| Registration | Hook lives in Limble's webhook config pointing at Make; each scenario has its own hook (Step 1 = 776, Step 3 = 777, EHS-update = 775) | New n8n production URL must be registered in Limble at cutover — deployment step, not a node (OQ-020) |

Payload fields consumed: `status` (event name), `taskID`. Nothing else from the webhook body
is referenced.

**Effective trigger semantics:** the webhook fires on every new task comment, but the gate
chain (§3 modules 19/136/137/3) means the workflow only proceeds when the comment is Limble's
auto-comment for a status change **to "PO Create"** on a `@CoupaWO;`-tagged task. Re-fires
from this workflow's own writes (status→"PO Requested", success/error comments) fail the
`statusID == PO Create` gate and exit — that's the built-in loop guard. Preserve it exactly.

## 3. Source flow (Make, as-is)

Gate chain:
1. `gateway:CustomWebHook` (1).
2. `universalModule` (19) `GET /v2/statuses?name=%PO Create%&limit=1` — **filter before it:**
   `{{1.status}} == "ADDED COMMENT TO TASK"`.
3. `listTasks` (2) — `tasks={{1.taskID}}, status=0, limit=1`.
4. `universalModule` (136) `GET /v2/tasks/{id}/comments` — **filter:** task `description`
   contains `@CoupaWO;` AND task `statusID == {{19.body[1].statusID}}`.
5. `SetVariable` (137) `latestComment = stripHTML(LimbleGrabLatestTaskComment(136.body))`.
6. `SetVariable` (3) — **filter "WO Needs a Req?":** `latestComment` contains
   `"Status was changed"` (case-insens.) AND contains `"to PO Create"`. (Sets a
   `Task Due Date` var that nothing downstream reads — dead, see §4.4.)

Gather:
7. `universalModule` (79) GET comments again → `BasicFeeder` (80) → `BasicAggregator` (81) —
   **aggregate output never consumed** (dead chain, §4.4).
8. `listUsers` (40) `limit=500` → `BasicAggregator` (44) → `SetVariable` (43)
   `siteManager = CoastalSiteManagerExtract(44.array, 2.locationID)` — finds the active user
   with role "View Only" at the task's location whose `firstName == "Site Manager"`; returns
   `{userEmail, userName(lastName)}`.
9. `datastore:SearchRecord` (13) — datastore 324, `client = "coastal_waste (PROD)"` → token.
10. `listInstructions` (4) `taskID, limit=100` → `BasicAggregator` (6) → `SetVariable` (52)
    `instResponses = CoastalCoupaWOInstResponses(6.array)` → `SetVariables` (5) unpacks the
    returned 6-tuple (1-indexed): `description, designatedContractorFull, dollarAmount, capex,
    commodity, accSeg6`. The function matches instructions **by exact instruction text** (HTML
    stripped) and resolves option-type responses via `itemOptionID → itemOptionText`.
11. `SetVariable` (138) `designatedContractor = replace(designatedContractorFull, "&", "%26")`
    — manual URL-escape for the supplier query (§4.7).
12. `listLocations` (50) by `2.locationID` → (107) `locationLimbleNum = trim(replace(first(
    split(name, " -")), "Coastal", ""))` → `Switcher` (108): if the remainder is a bare number,
    output `"Coastal " + NumberToSpelledNumberConverter(n)` (e.g. "Coastal 23" → "Coastal
    Twenty Three"), else the raw location name → `Switcher` (110) special-cases:
    `"Coastal - Corporate Overhead"` → `"Corporate Office"`, `"Coastal - Southwest Florida
    Overhead"` → `"Southwest Area Office"`, else passthrough.

Coupa lookups (each gated by the previous one's "found" filter; each miss takes an error route):
13. `coupa:makeApiCall` (89) `GET api/users?login={siteManager.userEmail}` — **no Authorization
    header** (connection-level auth, §4.2 / OQ-016). Router (90): route 2 (miss) = error path A.
14. (51) `GET api/addresses?name={110.output}` — filter `89.body length > 0`. **No auth
    header.** Router (130): route 2 = error path B.
15. GL code `Switcher` (113) — filter `51.body length > 0`: `capex == "true"` → `160999`,
    else `612200`. `Switcher` (140) derives `capexField = (113.output == "160999")` back to
    `"true"`/`"false"`. `SetVariables` (116) account segments: seg1 =
    `51.body[1].custom-fields.entity.external-ref-code`, seg2 =
    `51.body[1].custom-fields.location.external-ref-code`, seg3 = literal `"999"`, seg4 =
    GL code, seg6 = `accSeg6`. (No seg5.)
16. (115) `GET /api/accounts?segment-1..4,6=...` — **no auth header.** Router (119): route 2 =
    error path C.
17. (18) `GET /api/suppliers?display-name={designatedContractor}` — filter `115.body length >
    0`. **Explicit `Authorization: Bearer {{13.data.oauth_token}}`.** Router (58): route 2 =
    supplier-missing path (comments only, **no error-log write** — preserve this asymmetry).

Create + finalize (router 7 on `dollarAmount`, filter `18.body length > 0` on the router):
18. **Route 1 (`> 500`):** (8) `attachmentInfo = 6.array[5].response` (5th instruction,
    1-indexed, positional — the quote-file instruction) → `json:CreateJSON` (45) requisition
    payload (§5.9) → `coupa:makeApiCall` (17) `POST api/requisitions/new/submit_for_approval`,
    Bearer, **onerror:** AddRecord 326 (`{{17.error.message}}`/`type`) + admin comment + Ignore
    → (25) attachment payload `{attachment: {file: {{8.attachmentInfo[1].link}}, type:
    "file"}}` → Sleep 2s (134) → (24) `POST /api/requisitions/{{17.body.id}}/attachments`,
    Bearer, **onerror:** AddRecord 326 — but it logs `{{17.error.message}}`, the *Create Req*
    module's error, not module 24's own (source bug, §4.5 / OQ-017) + admin comment ("error
    attaching quote") + Ignore → (28) `GET /v2/statuses?name=%PO Requested%&limit=1` →
    `updateATask` (142) `metadata.meta1 = {{17.body.id}}` → `updateATask` (11) `statusID =
    PO Requested` → (61) POST comment `"Coupa Requisition successfully created!"`.
19. **Route 2 (`<= 500`):** same minus the attachment: CreateJSON (36, identical payload) →
    Sleep 2s (135) → Create Req (15, same endpoint/auth, **onerror** logs `{{15.error...}}`
    correctly) → Sleep 1s (139) → status lookup (27) → `updateATask` (141) `meta1 =
    {{15.body.id}}` → (12) statusID → (62) comment `"Coupa Requisition successfully created"`
    (no `!` — trivial source inconsistency).

Error paths (in-flow route-2s):
- **A — site manager miss (104/105/106):** AddRecord 326 `{errorCode: "400", errorMsg:
  "Location's Site Manager for Task# N was not found in Coupa."}` → `listUsers` for hardcoded
  admin `317887` → task comment @admin naming the location + site manager, "change the status
  of the Task from and then back to 'PO Create'".
- **B — location miss (131/132/133):** AddRecord `{errorCode: "Missing Account", errorMsg:
  "Selected Location (X) does not have a Coupa counterpart."}` → same admin mention, "reach
  out to FM360".
- **C — account miss (126/127/128):** AddRecord `{errorCode: "Missing Account", errorMsg:
  "Selected Account (s1-s2-s3-s4-###-s6) does not exist in Coupa."}` → same admin pattern.
- **Supplier miss (64/65/60/68/69/78):** 3-way router — user assigned → `listUsers` → comment
  @user; team assigned → `listTeams` → comment @team; else plain comment. Message: "Error:
  Selected Contractor does not exist in Coupa. Select a different Contractor and change the
  status of the Task from and then back to 'PO Create'." **No error-log write.**

All 5 error-log writes: `data: {limbleWONum, errorCode, errorMsg, timestamp}`, timestamp as
formatted EST string (3 inconsistent formats — superseded by OQ-012's native-Date fix).

## 4. Design decisions (all resolved except where noted)

1. **Token + error-log plumbing inherit prior specs (resolved).** Coupa Bearer token read from
   Data Table **"Coastal - Coupa OAuth Token"** (`QAj62weJaWmRBJ76`), replacing datastore 324
   (Token Regen spec §6). Error-log writes go to Data Table **"Coastal - Coupa Integration
   Error Log"** (`6GbR5Rxezl7hqk9i`), `timestamp` as a **native Date/ISO value** (OQ-012
   obligation), replacing datastore 326. If the token row is missing, the Get-row step returns
   0 items and the run dies there — matches source (`continueWhenNoRes: false`, no onerror on
   module 13).
2. **Bearer token on every Coupa call (resolved — OQ-016, owner call 2026-07-03).** Source
   sends the Bearer header on only 4 of 7 Coupa calls; the other 3 (users/addresses/accounts
   lookups) authenticated via Make connection `1766`, whose contents aren't in the export.
   Decision: uniform `Authorization: Bearer <token>` on all 7, using the daily token from the
   "Coastal - Coupa OAuth Token" Data Table. This is a build-on assumption, not a verification
   — connection 1766 wasn't opened and the historical logs are erased (OQ-024). Residual risk:
   if 1766 carried a broader-permission credential, the 3 lookups 401/403 at first live test;
   that test is the confirmation point, fallback is whatever auth 1766 turns out to hold.
3. **Limble via HTTP Request nodes** against `https://api.limblecmms.com` (base inferred from
   the fuse app's `/v2/...` paths). Credential (updated 2026-07-04, owner direction): **"Gerald
   Limble Sandbox"** (`MX0lwgfyFiGUBh5W`, httpHeaderAuth) for the test phase — swap to the
   Coastal prod credential ("Coastal Waste Limble", `qn6u8jEK085DoHT8`, from OQ-015) before
   cutover. The `listInstructions` endpoint shape (`GET /v2/tasks/{id}/instructions` assumed)
   still verifies at first live test.
4. **Dead modules dropped (resolved — OQ-021).** The comments Feeder→Aggregator chain (79/80/81 —
   aggregate never referenced) and module 3's `Task Due Date` roundtrip var (payloads use
   `2.due` directly) have no consumers; module 3's **filter** ("WO Needs a Req?") is
   load-bearing and stays. Behavior-neutral removal, same spirit as the error-log-export
   spec's 5→1 collapse.
5. **The two dollar branches merge into one tail (resolved — OQ-021).** Payloads 45 and 36 are
   byte-identical; the branches differ only in (a) quote attachment, (b) sleeps, (c) a `!`.
   Port as: one Create Requisition node → IF `dollarAmount > 500` → attach path → shared
   finalize (status lookup → task update → success comment, text normalized to
   `"Coupa Requisition successfully created!"`). Sleeps: keep **Wait 2s** between create and
   attach (source 134 — plausibly waits out Coupa indexing before the sub-resource POST);
   drop 135/139 as branch-duplication artifacts. Consequence: the source's wrong-module
   onerror reference (§4.6) becomes unreproducible — the merged Create node's error is just
   "the Create error", and the Add Quote node logs its own.
6. **Add Quote onerror logs its own error (resolved — sanctioned fix, OQ-017 approved
   2026-07-03).** Source logs
   module 17's error (already-succeeded Create Req) from module 24's onerror — a copy-paste
   bug producing an empty/wrong log line in prod. Fix: the n8n Add Quote error branch logs the
   Add Quote node's actual `error.message`/`error.name`. (Faithful alternative rejected with
   the approval; §4.5's consolidation made literal replication awkward anyway.)
7. **Manual `&`→`%26` replace dropped; use n8n query-parameter encoding (resolved as
   translation rule).** Source escaped only `&` in the contractor name before splicing it into
   the supplier query string (any other reserved char breaks in prod today). n8n HTTP Request
   query parameters URL-encode the whole value; keeping the manual replace would double-encode
   `&`. Same rule for `110.output` in the addresses lookup and the site-manager email.
8. **Custom functions port to Code nodes bit-for-bit** from `docs/functions.js`:
   `CoastalCoupaWOInstResponses` (keep the exact instruction-text cases, incl. the long
   estimated-dollar one and the Capex-default `commodity="Facility Repairs"` /
   `accSeg6="Other Operating"` else-branch), `CoastalSiteManagerExtract`,
   `LimbleGrabLatestTaskComment` (+ HTML strip), `NumberToSpelledNumberConverter`. Watch
   1-indexing: the function returns a plain array consumed 1-indexed in Make (`[1]`..`[6]`);
   in n8n return named fields instead.
9. **Error-path convergence (resolved — OQ-021).** Five near-identical "log + fetch admin + @comment"
   chains become one shared subgraph: each error route emits `{errorCode, errorMsg, adminMsg,
   writeLog: bool}` and feeds a common chain (IF writeLog → Data Table insert) → GET admin
   user `317887` → POST comment. Supplier-miss sets `writeLog: false` and keeps its own 3-way
   user/team/none mention logic. Admin ID stays a hardcoded literal (faithful) — identity
   unconfirmed, OQ-019.
10. **`listUsers limit=500` kept faithful** — single page, no pagination, silently misses the
    site manager past 500 users (OQ-018 tracks whether to sanction a paginate fix).
    **Superseded 2026-07-26 — OQ-018 resolved:** owner sanctioned the paginate fix
    (future-proofing). Cursor-based change set in section 9; applied to n8n 2026-07-26.
11. **No email in this workflow** — error visibility is the shared error-log table (drained by
    the already-built Error Log Export) plus Limble comments. Ionos/OQ-010 not applicable here.
12. **Idempotency guard (sanctioned fix — OQ-022 item 1, approved 2026-07-03).** After the task
    fetch (module 2 equivalent), an IF node exits early if `task.meta1` is already populated —
    the requisition already exists for this task. n8n runs webhook executions concurrently
    (Make serialized them), so two rapid PO-Create flips or a webhook redelivery could both
    clear the `statusID == PO Create` gate before either stamps `meta1`, creating **duplicate
    Coupa requisitions**. The guard closes that window. Not in the source (Make's serialization
    made it unnecessary) — a migration-specific fix, not a behavior change to prod semantics.
    Placement: after the task/status gates, before the Coupa lookups.
13. **Retries on the 4 Coupa GET lookups only (sanctioned fix — OQ-022 item 2, approved
    2026-07-03).** Retry On Fail (3 attempts) on the users / addresses / accounts / suppliers
    GET nodes — transient 5xx no longer ends the run and forces a human status re-toggle.
    **Never** on the Create Requisition or Add Attachment POSTs: a retry after a timeout that
    actually succeeded server-side would double-create. Source had no retries anywhere.
    OQ-022 items 3/4/5/6 stay faithful/rejected (see OQ-022 resolution) — attachment stays a
    positional `[5]` read, status names stay runtime `%...%` lookups.

## 5. Target n8n node graph

```
[Webhook (Limble task events)]
  → [IF: status == "ADDED COMMENT TO TASK"]
  → [HTTP L: GET statuses ?name=%PO Create%]
  → [HTTP L: GET tasks ?tasks={taskID}&status=0]
  → [IF: description contains "@CoupaWO;" AND statusID == PO-Create ID]
  → [HTTP L: GET task comments] → [Code: latest comment] 
  → [IF: contains "Status was changed" (ci) AND "to PO Create"]
  → [IF: task.meta1 already populated → EXIT]  [OQ-022 #1 idempotency guard]
  → [HTTP L: GET users limit=500] → [Code: CoastalSiteManagerExtract]
  → [Data Table: Get row — Coastal - Coupa OAuth Token]
  → [HTTP L: GET instructions] → [Code: CoastalCoupaWOInstResponses → named fields
      + attachmentInfo = instructions[5th].response]
  → [HTTP L: GET location] → [Code: location name → Coupa address name
      (number→spelled, special cases)]
  → [HTTP C: GET users?login=...] ──miss──> (ERR A: log + admin comment)
  → [HTTP C: GET addresses?name=...] ──miss──> (ERR B)
  → [Code/Set: GL code (capex→160999|612200), capexField, segments 1/2/3/4/6]
  → [HTTP C: GET accounts?segment-...] ──miss──> (ERR C)
  → [HTTP C: GET suppliers?display-name=...] ──miss──> (supplier path: IF user→@user /
      team→@team / else plain comment; NO log write)
  → [Set/Code: requisition JSON]
  → [HTTP C: POST requisitions/new/submit_for_approval] ──error──> (ERR D: log Create error
      + admin comment)
  → [IF: dollarAmount > 500]
       true → [Wait 2s] → [HTTP C: POST /requisitions/{id}/attachments {file: link}]
                ──error──> (ERR E: log Add-Quote's OWN error + admin comment)  [OQ-017]
                → join
       false → join
  → [HTTP L: GET statuses ?name=%PO Requested%]
  → [HTTP L: PATCH task {meta1: reqID, statusID: PO-Requested ID}]
  → [HTTP L: POST comment "Coupa Requisition successfully created!"]

(shared error subgraph: [IF writeLog → Data Table: Insert row (limbleWONum, errorCode,
 errorMsg, timestamp=now ISO)] → [HTTP L: GET user 317887] → [HTTP L: POST @admin comment])
```

`HTTP L` = Limble (credential "Gerald Limble Sandbox" for test; Coastal prod credential at
cutover), `HTTP C` = Coupa
(`https://coastalwasteinc.coupahost.com`, Bearer from the token Data Table — §4.2).

Node notes beyond §3/§4:
- **Webhook:** respond immediately (Make acked before processing; nothing downstream depends
  on the response body).
- **All "found?" IF gates:** `{{ $json.body.length > 0 }}` equivalents on the Coupa lookup
  responses (source filters are `array:greater 0`), and Make's `body[1]` reads become `[0]`.
- **Coupa GET lookups (users/addresses/accounts/suppliers):** Retry On Fail = 3 (OQ-022 #2).
  The two POSTs (Create Requisition, Add Attachment) get **no** retry — double-create risk.
- **Create Req / Add Quote nodes:** On Error = "Continue (using error output)" wired to the
  shared error subgraph; after the error branch completes, the run ends (source `Ignore`
  terminator — nothing downstream of the failure runs; the task is NOT flipped to
  "PO Requested" on failure).
- **Requisition payload** (both source copies identical): `pcard: ""`, `approvals: []`,
  `department: ""`, `requested-by.login = siteManager.userEmail`, `justification = "Limble
  WO#{taskID}"`, `ship-to-address.id = addresses[0].id`, one `requisition-line`: `account.id =
  accounts[0].id`, `account.account-type.name`, `currency.code = "USD"`, `line-num: "1"`,
  `supplier.id = suppliers[0].id`, `commodity.name`, `unit-price = dollarAmount`,
  `description`, `need-by-date = task.due` (raw Limble value passed through, faithful),
  `payment-term: ""`, `custom-fields.capex = capexField`.
- **Task finalize:** source used two PATCHes (metadata then status); merged into one PATCH
  setting `meta1` + `statusID` together (§4.5). `meta1` is the Step 2 correlation key —
  verified: Step 2 reads `task.meta1` to poll `api/requisitions/{id}` and writes `meta2` =
  PO id.

## 6. Cross-workflow dependencies

- **Reads** "Coastal - Coupa OAuth Token" (`QAj62weJaWmRBJ76`) — written by the built Token
  Regen workflow. Credentials are loaded (OQ-015 resolved 2026-07-03); Step 1 still cannot
  succeed live until Token Regen has run once and seeded the table.
- **Writes** "Coastal - Coupa Integration Error Log" (`6GbR5Rxezl7hqk9i`) — drained by the
  built Error Log Export workflow. First real writer; OQ-012's ISO-timestamp obligation lands
  here.
- **Writes `meta1`** (Coupa requisition ID) onto the Limble task — Step 2's poll key. Any
  change to how `meta1` is written must be mirrored in Step 2's spec.
- **Status names** "PO Create" / "PO Requested" are looked up by name at runtime (`%...%`
  wildcard, limit 1) — renaming either status in Limble breaks Steps 1 and 2.

## 7. Open items gating go-live (build done 2026-07-03)

Still open:

- **Swap Limble credential to Coastal prod before cutover.** All 16 Limble nodes carry "Gerald
  Limble Sandbox" (2026-07-04, owner direction) for the test phase; go-live needs the Coastal
  prod Limble credential ("Coastal Waste Limble", `qn6u8jEK085DoHT8`).
- **OQ-028: test phase CLOSED, rig torn down (2026-07-06).** All 8 scenarios passed (results
  table in OQ-028); Step 1 itself needed zero changes. n8n reset for deployment: Coupa URLs
  restored to `coastalwasteinc.coupahost.com`, dummy token + test error rows purged, mock
  workflow and TEST tables deleted, Step 1 left INACTIVE. Remaining go-live gates, in order:
  (1) swap Limble credential to "Coastal Waste Limble" (`qn6u8jEK085DoHT8`) — owner deferred
  to go-ahead; (2) activate + run Token Refresh once; (3) activate Step 1; (4) OQ-020 webhook
  registration; (5) OQ-025 status-name check. Real Coupa acceptance still confirms only at
  first live call (OQ-016/OQ-024) — or earlier against the discovered Coupa TEST instance
  (OQ-028 side discovery) if sanctioned.
- **Residual untested surface — R1-R4 table in OQ-028 (2026-07-06).** Four items the rig
  never exercised: contractor-comment User/Team variants (all test tasks were unassigned),
  the Post Admin Comment node (admin 317887 absent from sandbox), Error Log Export
  end-to-end, and real-Coupa acceptance. Each has a pre-launch mitigation and a
  watch-at-hotswap signal in the OQ-028 table; R1/R2 now require live prod-Coupa GETs
  (mock torn down) and double as the OQ-016 lookup-auth probe.
- **OQ-025: RESOLVED 2026-07-06 — status names confirmed via direct API pull.** Owner
  fetched the full status list from Coastal Limble (direct API call, outside the MCP):
  `PO Create` = statusID 5784, `PO Requested` = 5782, `PO Approved` = 5783, `Pending ` = 4766
  (trailing space is in the official config). Spellings match the runtime `%...%` lookups
  exactly — no build change needed; go-live gate (5) in the OQ-028 list above is done.
  Caveat that stays: the MCP `get_statuses` tool shows only "In Progress" (statusID 1) even
  against Coastal — an MCP visibility artifact, not API truth; never use it for status
  verification.
- OQ-018 (listUsers pagination), OQ-019 (admin 317887 identity), OQ-020 (webhook registration
  at cutover) — non-blocking for build, needed before go-live. All three have live-recon data
  now (§8): 79 users, admin = Brandon Ray Freckleton (active), 3 Limble-side task webhooks.
- **OQ-024: `meta1` null on every real CoupaWO task — root-caused (§8).** The integration has
  essentially never succeeded in prod: 7 of 8 tagged tasks never entered the flow, the 1 that
  did failed at the Coupa create-requisition POST twice. Not blocking the *build* (the port is
  spec-driven), but means there's no working baseline to test against and the known real-world
  failure is Coupa-side. ~~Get the task-1953 Make error before go-live~~ — dead end: Fuse
  execution logs erased (recon 2026-07-03; owner re-searched 2026-07-06 — no log for 1953,
  and neighboring runs 1955-1959 also unreadable). The `meta1` write side is now PROVEN via
  the OQ-028 synthetic run. Coupa-acceptance side confirms only at first live call, or
  earlier via the Coupa TEST instance (OQ-028 side discovery, unsanctioned).

Resolved 2026-07-03 (no longer gating):

- OQ-022: idempotency guard (#1) and GET-lookup retries (#2) sanctioned and folded into §4
  (items 12/13); attachment-by-text (#3) faithful/positional, server-side filter (#4) dropped
  as infeasible, status-ID handling (#5) faithful runtime lookups, native OAuth2 (#6) rejected.
- OQ-021: §4 consolidations approved as-is (dead-module drop, branch merge, error-path
  convergence, single PATCH).
- OQ-017: Add-Quote onerror fix approved — sanctioned.
- OQ-016: Coupa auth = Bearer-for-all on all 7 calls (owner call; confirm at first live test).
- OQ-015: all credentials loaded in n8n (Limble moved from `.env` and scrubbed, Coupa
  client_id/secret, rotated EHS key, Ionos SMTP).

## 8. Live-instance recon findings (2026-07-03, sanctioned under OQ-023)

Read-only Limble MCP sweep of Coastal's instance (Coastal Waste & Recycling, enterprise).
Full task sweep: 504 incomplete + 1,335 completed-since-2025-07-01 tasks.

Verified (spec assumptions that now stand on live data, not just blueprint reads):
- **Instruction texts match `functions.js` verbatim** — all 5 `CoastalCoupaWOInstResponses`
  match cases confirmed against live template 965 ("Main WO Template (Limble-to-Coupa)",
  17 instructions; 46 template copies exist, one per location).
- **Quote-upload instruction is at position 5** on the live template ("Upload the
  Contractor's Quote Here for Coupa", type 9) — the positional `[5]` read works today.
- **Site-manager convention holds**: 38 accounts with `firstName == "Site Manager"`,
  View Only role per location. 16 of 38 are inactive (as-is prod failure mode for those
  locations, not a migration concern). 79 users total — OQ-018's 500 cap is a non-issue.
- **Admin 317887** = Brandon Ray Freckleton, active, Super User (OQ-019).
- **`task.due` is a unix epoch**, consistently 11:59:59 PM local — pins down what
  `need-by-date` receives.
- **Location names** fit the `"Coastal NN - X"` transform incl. leading zeros ("Coastal 04"
  → converter yields "Four"); both §3 special-case names exist verbatim ("Coastal -
  Corporate Overhead", "Coastal - Southwest Florida Overhead").
- **3 Limble task webhooks** (webhookIDs 1742/1743/1744, all enabled) point at
  `hook.fuse.limblecmms.com` — the cutover surface for OQ-020.

New risks surfaced:
- **OQ-024 (resolved to root cause via comment sweep): `meta1` null because the requisition
  path has ~never succeeded here, not an API-mapping trap.** 7 of 8 `@CoupaWO;` tasks never
  entered the flow (used as plain WOs); the 1 that did (task 1953) failed **at the Coupa
  create-requisition POST**, twice (2025-09-12 + 2025-09-15), posting the generic create-req
  `onerror` comment after all Limble lookups had passed. Consequences: (a) no working prod
  baseline — validate against synthetic tasks through every path, not against history; (b) the
  real failure was Coupa-side at create-req, which sharpens OQ-016 (auth) / the PR payload as
  the thing to get right. The updateATask `meta1` write itself is unproven-but-probably-fine
  (EHS's createATask `meta1` surfaces via the API); confirm by observing `meta1` populated
  after the first successful synthetic run.
- **Status names — ALL confirmed 2026-07-06 (OQ-025 resolved)**: owner's direct API pull of
  the full Coastal status list confirms `PO Create` (5784), `PO Requested` (5782),
  `PO Approved` (5783), and `Pending ` (4766, trailing space in the official config) — every
  spelling matches the blueprint lookups exactly. Earlier partial evidence (1953's
  status-change comments) is superseded. The MCP `get_statuses` tool remains unreliable
  (returns only "In Progress" even against Coastal — it can't even resolve the statusID 2
  its own task `meta.status` links reference); the real `/v2/statuses` endpoint returns all
  9 rows. Never verify statuses through the MCP tool.
- **Only ~8 real CoupaWO tasks in a year** — prod volume is tiny; regression-testing against
  real history is barely possible, so cutover testing must exercise synthetic tasks through
  every path (§3's error routes included).
- **All Limble locations are `America/New_York`** — feeds OQ-014; the Mountain-time
  assumption behind OQ-011/OQ-012 is likely wrong (Eastern looks intentional).

Limble API quirks for the build (apply to the n8n HTTP nodes):
- Name filters require explicit `%` wildcards ("PO" matches nothing, "%PO%" matches).
- The instructions endpoint's **default page size is 2** — always pass an explicit limit
  (source's `limit=100` is load-bearing, not decorative).
- Instruction option field names differ by endpoint: inline options use `itemOptionID`/
  `itemOptionText`; the options sub-endpoint uses `instructionOptionID`/`instruction`.
  `CoastalCoupaWOInstResponses` consumes the inline shape — keep it that way.

## 9. OQ-018 sanctioned fix (2026-07-26) — APPLIED to n8n same day

Owner approved paginating the main `GET users` fetch (future-proofing). Applied 2026-07-26
to workflow `WJSs6apAdVH5yKkq`, node **`Get Limble Users`** (`n10`, httpRequest v4.4 — the
spec graph's `[HTTP L: GET users limit=500]` placeholder). Round-trip read confirmed the
pagination options landed exactly as designed; `limit=500`, URL, auth, headers untouched;
node `notes` updated. **`Extract Site Manager` (`n11`) needed NO patch** — item 2's predicted
flatMap tweak proved unnecessary: n8n's HTTP Request node splits the bare-array response into
one item per user, and the Code node already iterates `$input.all()` per-user, so pagination
just appends items. Post-apply validation: 5 errors, all pre-existing validator-heuristic
complaints about the intentional `Err: *` error-branch wiring (present before this change,
none touch `n10`/`n11`); 0 new issues, 79 expressions validated. Workflow still **inactive**.

**Activation gate CLEARED (2026-07-26, same day):** raw-REST probe via curl against
`api.limblecmms.com` (sandbox credential from local `.env`): `GET /v2/users/?limit=2` →
userIDs `[220593, 224202]`; `GET /v2/users/?limit=2&cursor=224202` → `[224203, 231029]`.
Confirms on the raw API (not just the MCP wrapper): param name is `cursor`, exclusive-after,
ascending — exactly the contract the node's pagination expression assumes. The node's n8n
`notes` field was updated 2026-07-26 (same day) to record the verification — no stale
caveat remains.

**Probe findings this design rests on (2026-07-26, read-only via Limble CLIENT MCP, prod):**
- Coastal prod still has **79 users** (matches 2026-07-03 recon) — `limit=500` returns all in
  one call today. No live truncation; this fix changes nothing at runtime until users > 500.
- **Limble user pagination is cursor-based, not page-based**: `cursor` = a userID, results
  resume strictly AFTER it (exclusive), ordered ascending by userID. Response is a bare JSON
  array — no `nextCursor`/`hasMore`/envelope; the client must carry the last userID forward.
- The Fuse wrapper (`fuse-limble-app:listUsers`) exposes **no pagination parameter at all**
  (param surface: limit/name/users/teams/roles) — the original could never have paginated.
  This fix is additive, with no source behavior to imitate.
- Caveat: the probe ran through the Limble MCP wrapper. The raw `/v2/users` REST param is
  presumably also `cursor` (pass-through), but **confirm with one live call at apply time**
  before wiring the expression below.

**Change set (workflow node `[HTTP L: GET users limit=500]`, section 5 graph — confirm the
live node's exact name at apply time):**

1. HTTP Request node → Options → **Pagination**:
   - Mode: **Update a Parameter in Each Request**
   - Parameter: type Query, name `cursor`,
     value `{{ $response.body.last().userID }}`
   - Complete When: **Other** — expression `{{ $response.body.length < 500 }}`
     (a short page is the last page; empty page also terminates)
   - Keep `limit=500` unchanged. First request carries no cursor; n8n adds it from page 2 on.
2. **Downstream `CoastalSiteManagerExtract` Code node**: with pagination on, the HTTP node
   emits one item per page (each body an array). The user array must be built across ALL
   items — `$input.all().flatMap(i => i.json)` or equivalent — not from a single item's body.
   Confirm the built node's current input handling at apply time; worst case a 2-line tweak.
3. **No change** to the other 7 `listUsers` calls (limit=1 targeted lookups — error-path
   admin fetch and @mention lookups are unaffected by any cap).

**Out of scope, flagged:** EHS Create WO has the same pattern (`listTeams limit=500`,
ehs-create-wo-build-spec.md) — filed and resolved as **OQ-046 (2026-07-26): no change**,
faithful single call stands (45 of 500 teams today, name-filtered server-side).

### 9.1 Runtime failure of the as-applied expression — corrected 2026-07-26 (same day)

The fix above was verified two ways that both looked convincing and neither of which ran the
node: a **config round-trip read** (proves what n8n stored) and a **raw-REST cursor probe**
(proves what Limble accepts). Its first actual execution — 2026-07-26, exec **127324**, fired
during the R1-team run — failed:

```
NodeApiError: last can't be used on undefined value
node: Get Limble Users (n10)
```

**Root cause:** n8n evaluates the pagination parameter expression on the **first** request as
well as subsequent ones. On request 1 there is no `$response` body yet, so
`{{ $response.body.last().userID }}` throws before any HTTP call is made. Step 1 died at n10
on every run, ahead of all Coupa traffic — the design note above ("First request carries no
cursor; n8n adds it from page 2 on") was wrong about n8n's evaluation order.

**Probes establishing the corrected value** (sandbox credential, read-only):
- `GET /v2/users?limit=2&cursor=` → **HTTP 400**, `` `cursor` must be a number `` — an
  empty-string guard is not viable.
- `GET /v2/users?limit=2&cursor=0` → **200**, `[220593, 224202]` — identical to omitting the
  param. `0` is a safe "start from the beginning" sentinel.

**Applied (2026-07-26):** cursor value changed to

```
={{ $response?.body?.last()?.userID ?? 0 }}
```

`completeExpression` left unchanged at `{{ $response.body.length < 500 }}` (it only evaluates
after a real response). The whole `parameters.options` object was replaced in one update — dot
paths do not index array elements — and the node was read back to confirm no sibling-key
corruption. Re-fired as exec **127325: PASS**, `Get Limble Users` → **54 items** from the
sandbox in a single page, run completed through to the team-comment tail.

**Residual:** only the single-page path has executed. The multi-page branch (>500 users, where
the cursor actually advances) is still unproven at runtime — sandbox has 54 users, prod 79.
The cursor contract itself is probe-verified; what is untested is n8n's page-2 request
assembly. Watch at go-live, or prove it by temporarily setting `limit` low on a sandbox run.

**Lesson for the rest of this build:** a config round-trip plus an API-contract probe is not
execution proof. Any node change lands unverified until the node has actually run once.

## 10. OQ-019 sanctioned fix (2026-07-26) — APPLIED to n8n same day

Owner approved hoisting the error-path escalation admin userID out of the workflow. Applied
2026-07-26 to `WJSs6apAdVH5yKkq` (49 → **50 nodes**), and to Step 2 `WYJyHdQGcdeD8wEr` the same
day (26 → 27 nodes) — the two are deliberately kept in lockstep on this.

**What was wrong (and what wasn't).** The Make source hardcodes `317887` **6 times** across
Step 1's error paths. This spec's port had already collapsed that to **one** literal, because
all five `Err: *` Set nodes funnel into a single
`Insert Error Log Row → Get Admin User → Merge Error Context → Post Admin Comment` chain — so
the "6 hardcodes" framing in OQ-019 never described the n8n build. What remained was still one
literal per workflow, two across the build, and the escalation contact is a person who can
leave the company.

**Change set:**

1. New Data Table **`Coastal - Integration Config`** (`L0npQPPEXQI9JRzX`), columns
   `key` / `value` / `notes`. Seeded with one row:
   `escalation_admin_user_id = 398783` (test value; sandbox Site Manager) with a note naming
   `317887` as the cutover value. Deliberately Coastal-scoped rather than reusing the instance's
   cross-client `Project Settings` table — same isolation reasoning as OQ-005.
2. New node **`Get Escalation Admin ID`** (`n8n-nodes-base.dataTable` v1.1, operation `get`,
   `returnAll: true`, filter `key = escalation_admin_user_id`), inserted between
   `Insert Error Log Row` and `Get Admin User`.
3. **`Get Admin User`** (`n40`) query param `users`: literal `398783` → `={{ $json.value }}`.
   URL, `limit=1`, auth, headers unchanged. Moved to `[4784, 248]` to make room.
4. Nothing else in the error subgraph moved. `Merge Error Context` still combines by position,
   `Get Admin User` on input 0 and the originating `Err: *` Set node on input 1, one item each.
   `Post Admin Comment` still reads `firstName`/`lastName` off the user lookup and
   `adminMsgBody` off the merge, and still targets `$('Get Task').first().json.taskID`.

**Apply-time gotcha worth recording.** The first patch attempt used the n8n-MCP `updateNode`
dot path `parameters.queryParameters.parameters[0].value`. That path does **not** index into
the array — it created a literal sibling key `"parameters[0]"` next to the real `parameters`
array and left `398783` live in the request. Caught by reading the node back. Fix: replace the
whole `parameters.queryParameters` object in one update. **Always read the node back after an
array-element patch.**

**Deliberately not done:** no `|| '317887'` fallback in the expression. A fallback is a second
place the value can drift, which defeats the fix. Trade-off accepted: if the config row is
missing or renamed, `Get Escalation Admin ID` returns 0 items and the admin comment is skipped.
The error row is written to the error log *before* this node, so the failure is not silent —
but it is a new (small) failure point inside the error path, gated by a DEPLOYMENT.md check
rather than by code.

**Re-test: DONE — PASS 2026-07-26, exec `127330`.** Fired `{status:"ADDED COMMENT TO TASK",
taskID:4059}` at `failMode=acct` after the owner posted a fresh `Status was changed from Open to
PO Create` comment on 4059 (required — the prior latest comment was A4's admin comment, which
would have bounced the n08 gate). Result: `Err: Account Missing` → error-log row **23** with a
message byte-identical to A4's row 18 → `Get Escalation Admin ID` returned `value="398783"` →
`Get Admin User` resolved userID 398783 → `Post Admin Comment` posted **commentID 7140**. Fixture
unmutated (4059 still statusID 8054, meta1 null). Workflow deactivated, `failMode` reset to `""`.
