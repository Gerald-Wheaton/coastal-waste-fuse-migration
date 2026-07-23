# Build Spec — Coastal - WO Completed; Update Coupa PO (Step 3) (PROD)

Status: **Built in n8n** (2026-07-07), workflow ID `NH1giNups8iICMZe`
("Coupa - Update PO on WO Created (Step 3)"), 13 nodes, inactive, `n8n_validate_workflow`
clean (0 errors/0 warnings). Deployed on owner go-ahead. Ready-to-deploy body archived at
`docs/build-specs/coupa-wo-completed-step3.n8n.json`. Limble cred = "Gerald Limble Sandbox"
(`MX0lwgfyFiGUBh5W`) for test; swap to prod (`qn6u8jEK085DoHT8`) at cutover.

Source blueprint: `docs/OG-workflows/Coastal - WO Completed; Update Coupa PO (Step 3) (PROD).json`
(13 modules incl. 1 router with 2 routes and **3 `onerror` chains** — confirmed via recursive
walk; one custom function `CoastalGetInvoiceInstResponse`, body in `docs/functions.js`).

Design-truth note: the narrative review doc `docs/Coastal - Limble Integration Review - Coupa
Integration (v1.2.0).docx` §"Step 5: Soft Closing the Coupa PO" is the design source for this
blueprint (docx "Step 5" == this scenario; the docx numbers the Coupa lifecycle 1-5, the Make
scenarios collapse it to 3). Owner directive 2026-07-03: docx is source of truth where it and
the blueprint disagree. It disagrees on two points, both handled below (§4.1 meta2 key, §4.5
@-mention).

Decisions locked 2026-07-07 (this session):
- **§4.1 PO lookup key → SANCTIONED FIX** (OQ-030): blueprint queries `?po-number={{meta2}}`
  but `meta2` holds the PO **id** (Step 2's write + docx both say so) — query by id instead.
- **§4.2 Coupa auth → Bearer-for-all** (OQ-031): all 3 Coupa calls use the Bearer token from
  the "Coastal - Coupa OAuth Token" Data Table, matching Step 1 (OQ-016) / Step 2 (OQ-027).
  Drops the datastore-324 read; fixes the attachment POST's missing `Bearer ` prefix.
- **§4.3 Error handling → FAITHFUL log-only** (OQ-032): port the 3 `onerror` writes to the
  shared error-log Data Table (ISO timestamp per OQ-012). **No** admin @-mention comment
  (source has none; Step 3's comments go to Coupa, not Limble). Coverage = the 3 POSTs only.
- **§4.4 Dead comment Feeder/Aggregator (8/9) → DROP** (OQ-033): unreferenced downstream;
  docx Step 5 asks for no comment/note compilation (verified). Consolidation, behavior-neutral.
- **§4.5 PO comment @-mention → FAITHFUL**: `@<PO created-by fullname>`, as the blueprint
  sends it. Docx "site manager" is doc drift.
- Deliverable this session = this spec only; Step 3 stays design-only/Hold.

---

## 1. Purpose

When a `@CoupaWO;`-tagged Limble WO that already carries both `meta1` (Coupa requisition id,
from Step 1) and `meta2` (Coupa PO id, from Step 2) is **completed**, push the WO's invoice to
its Coupa PO and notify the PO owner. Concretely: look up the PO by `meta2`, read the WO's
"Upload Invoice Here" instruction; if an invoice file is present, attach it to the PO; then
post a comment on the PO @-mentioning the PO's creator that the PO is ready for receiving. This
is the terminal Coupa-side handshake — the accounting team/Site Manager then manually receive
and close the PO in Coupa.

Nothing is written back to Limble. The WO is already complete; Step 3 only touches Coupa.

## 2. Trigger

| | Source (Make) | n8n target |
| --- | --- | --- |
| Type | Limble webhook (hook `777`, `maxResults: 1`) — fires on task events; flow gates on event text `COMPLETE` | **Webhook** node, POST, Respond Immediately |
| Registration | Hook lives in Limble's webhook config pointing at Make (Step 3 = hook 777; cf. Step 1 = 776, EHS-update = 775) | New n8n production URL registered in Limble at cutover — deployment step, not a node (OQ-020) |

Payload fields consumed: `status` (event name), `taskID`. Nothing else from the webhook body
is referenced.

**Effective trigger semantics:** the webhook fires on task events; the gate chain (§3 modules
2/6) proceeds only when the event is a **completion** (`status == "COMPLETE"`) of a
`@CoupaWO;`-tagged task that already has `meta1` **and** `meta2`. A completion of any
non-Coupa or not-yet-processed WO exits at the gate. Preserve this exactly.

## 3. Source flow (Make, as-is)

Linear gate chain, then a two-route router at the tail:

1. `gateway:CustomWebHook` (1) — hook 777.
2. `listTasks` (2) — `tasks={{1.taskID}}, limit=1`. **Filter "Is Completed?":** `{{1.status}}
   == "COMPLETE"`. Connection 2106 (Limble). Returns the task incl. `meta1`, `meta2`,
   `description`, `taskID`, `locationID`.
3. `universalModule` (6) — `GET /v2/tasks/{{2.taskID}}/comments`. **Filter "WO is Coupa
   related":** `2.meta1` exists AND `2.meta2` exists AND `2.description` contains `@CoupaWO;`.
   Connection 2106.
4. `BasicFeeder` (8) — `array={{6.body}}` → `BasicAggregator` (9) `comment={{8.comment}}`.
   **Dead:** module 9's aggregate is referenced by no downstream mapper. Drops in the port
   (§4.4).
5. `listInstructions` (3) — `taskID={{2.taskID}}, limit=50`. Connection 2106.
6. `BasicAggregator` (12) — `array` of `{instruction, response}` over the listInstructions
   feed (feeder=3).
7. `datastore:SearchRecord` (18) — datastore `324`, filter `client == "coastal_waste (PROD)"`
   → the Coupa creds/token record. **Replaced** in the port (§4.2).
8. `coupa:makeApiCall` (25) — `GET /api/purchase_orders?po-number={{2.meta2}}`. Connection
   1766, **no auth header**. **Bug (§4.1):** `meta2` is the PO id, so this should query by id.
9. `util:SetVariable2` (11) — `invoiceResponse = CoastalGetInvoiceInstResponse(12.array)`
   (roundtrip). The function scans the instruction array for `instruction == "Upload Invoice
   Here"` and returns that instruction's `response[0]` (`{fileName, link}`); empty object if
   not found. Body in `docs/functions.js`.
10. `BasicRouter` (10), `else: 1` — two routes evaluated for the task:
    - **Route 0 — invoice present:** first module `json:CreateJSON` (14) carries **filter
      "Contains Invoice File":** `{{11.invoiceResponse.link}}` exists. It builds
      `{"attachment": {"file": "{{11.invoiceResponse.link}}", "type": "file"}}`. Then:
      - `coupa:makeApiCall` (15) — `POST /api/purchase_orders/{{25.body[1].id}}/attachments`,
        body `{{14.json}}`, header `Authorization: {{18.data.oauth_token}}` (**raw token, no
        `Bearer ` prefix** — §4.2 fix). `onerror` → `datastore:AddRecord` (16) → datastore
        `326` `{errorMsg: 15.error.message, errorCode: 15.error.type, timestamp: formatDate(now,
        "MM/DD/YY hh:mm A", "EST"), limbleWONum: 2.taskID}`.
      - `coupa:makeApiCall` (28) — `POST /api/purchase_orders/{{25.body[1].id}}/comments`, body
        `{"comments": "@{{25.body[1].`created-by`.fullname}}: PO is ready for receiving. Please
        review the invoice, update the PO (if necessary), and finish it out."}`, header
        `Authorization: Bearer {{18.data.oauth_token}}`. `onerror` → `AddRecord` (21) → 326
        (same schema, `errorMsg` = `28.error.message: 28.error.detail`).
    - **Route 1 — else (no invoice):** `coupa:makeApiCall` (29) — identical comment POST to
      (28). `onerror` → `AddRecord` (20) → 326 (same schema as 21, references `29.error`).

Notes on the as-is graph:
- **Error handling covers only the 3 Coupa POSTs** (15/28/29). GET purchase_orders (25), the
  datastore read (18), and all Limble reads have **no** `onerror` — a failure there aborts the
  run silently (Make `maxErrors` then stop). Faithful port keeps this coverage boundary (§4.3).
- Make `body[1]` (1-indexed) → n8n `body[0]`.
- `25.body[1].`created-by`.fullname` — hyphenated Coupa field, bracket/quote access in n8n.
- The two routes' comment POSTs are byte-identical; the only route-0-exclusive work is the
  attachment. (Optional collapse to one comment node after an IF is possible but not taken —
  faithful posture on this workflow; noted, not done.)

## 4. Design decisions

### 4.1 PO lookup by id, not po-number — SANCTIONED FIX (OQ-030)

Module 25 does `GET /api/purchase_orders?po-number={{2.meta2}}`. But `meta2` holds the Coupa PO
**id**, not its po-number:
- Step 2 build spec §4.7 writes `meta2 = purchase_orders[0].id`.
- The docx (§"Soft Closing the Coupa PO") states: *"using the saved PO ID in the meta2 field,
  the invoice file will be attached to the PO in Coupa."*

So querying the po-number endpoint with an id value returns no PO, and every downstream call
(`{{25.body[1].id}}`) dereferences an empty result. This never surfaced in prod because the
Coupa integration has essentially never produced a PO (`meta2` null on every real task —
OQ-024). Docx is source of truth on disagreements; the id is the correct key.

**The n8n port fetches the PO by id:** `GET /api/purchase_orders/{{meta2}}` (direct-id path;
fall back to `?id={{meta2}}` if the direct path isn't exposed — verify at build against the
Coupa API). Joins the sanctioned-fixes list. Tracked as **OQ-030**.

Reciprocal dependency: this fix binds Step 3's read key to Step 2's write key. If Step 2 is
ever changed to store po-number in `meta2` instead of id, Step 3 must change with it (§6).

### 4.2 Coupa auth — Bearer-for-all from token Data Table (OQ-031)

The source is inconsistent: GET po (25) sends **no** auth header; the attachment POST (15)
sends `Authorization: {{18.data.oauth_token}}` (**no `Bearer ` prefix** — a likely bug); the
comment POSTs (28/29) send `Authorization: Bearer {{18.data.oauth_token}}`. All read the token
from the datastore-324 record (18.data.oauth_token).

Per the OQ-005 credential model and the OQ-016 (Step 1) / OQ-027 (Step 2) resolutions, **the
n8n port uses Bearer-for-all**: drop the datastore-324 read entirely; every Coupa call
(GET po, attachment POST, comment POST) sends `Authorization: Bearer <token>` where `<token>`
is read from the **"Coastal - Coupa OAuth Token"** Data Table (`QAj62weJaWmRBJ76`, written by
the built Token Regen workflow). This fixes the attachment POST's missing prefix as a side
effect. Confirmation point is the first live test — a 401/403 on any Coupa call = revisit.
Tracked as **OQ-031**.

### 4.3 Error handling — FAITHFUL log-only (OQ-032)

Unlike Step 2 (which had zero error handling and got a sanctioned add), Step 3 already logs its
3 Coupa POST failures to the shared error datastore. Owner decision: **port this faithfully,
do not upgrade it to the Step 1/2 converged subgraph.** Specifically:

- **Covered calls (On Error → error output → log write):** attachment POST (15), comment POST
  route-0 (28), comment POST route-1 (29). These are the exact 3 the source wraps.
- **Not covered (faithful):** GET purchase_orders (25), the token read, and all Limble reads.
  A failure there aborts the run unlogged, as today. (If desired later, adding coverage to GET
  po is a one-node deviation — flagged, not taken.)
- **Log target:** the shared **"Coastal - Coupa Integration Error Log"** Data Table
  (`6GbR5Rxezl7hqk9i`), the same table Step 1 writes and the Error Log Export drains. Step 3
  becomes the (already-intended) writer alongside Step 1; do **not** create a second table.
- **Row schema:** `{ limbleWONum: <2.taskID>, errorCode: <node error.type/name>, errorMsg:
  <node error.message (+ ": " + error.detail where the source concatenates it, i.e. the comment
  POSTs)>, timestamp: <now, native Date/ISO> }`. The `timestamp` is a **native Date/ISO** value,
  not the source's `formatDate(..., "EST")` string — mandated by OQ-012 (the shared table's
  column is a Date type; the report email does the Mountain/Eastern display formatting). This is
  the one non-faithful detail, and it's forced by the shared table's schema, not a Step 3 choice.
- **No admin comment.** The source posts nothing to Limble on error (its only comments go to
  Coupa). Do not add the `@317887` admin Limble comment that Step 1/2 use — that would be a
  call the source lacks. Admin user 317887 (OQ-019) is **not** referenced by Step 3.
- **Per-iteration isolation:** Step 3 processes a single webhook task (no Feeder over tasks), so
  "Continue (using error output)" on the 3 covered nodes just routes to the log write and lets
  the run finish; there is no sibling task to protect.

### 4.4 Drop dead comment Feeder/Aggregator (8/9) — CONSOLIDATION (OQ-033)

`BasicFeeder` (8) over `6.body` → `BasicAggregator` (9) `comment` produces a comment list that
**no downstream mapper references**. Verified against the docx: §"Soft Closing the Coupa PO"
specifies only invoice-attach + a single PO notification comment — no compilation of WO
comments/notes onto the PO (keyword scan of the section: note/completion/compile/list/summary =
0). The related `CoastalGetChildWONotes` function exists in `functions.js` but is wired to
nothing in Step 3 — an abandoned scaffold from an earlier design, not a forgotten requirement.
**The port omits modules 8 and 9** (and the comments GET at module 6 is retained only for its
gate filter — the "WO is Coupa related" check reads task fields, so if that filter is moved onto
the task fetch the comments GET can go too; see §5). Behavior-neutral. Tracked as **OQ-033**.

### 4.5 PO comment @-mention — FAITHFUL (PO created-by)

The comment @-mentions `{{25.body[1].`created-by`.fullname}}` — the Coupa PO's creator. The
docx says "@<name of site manager>". Blueprint is the actual impl and there is no site-manager
lookup anywhere in this scenario; port the created-by mention exactly. (Doc drift; noted.)

### 4.6 Instruction extraction (faithful)

Port `CoastalGetInvoiceInstResponse` bit-for-bit into a **Code** node: scan the instruction
array for `instruction == "Upload Invoice Here"`; return that instruction's `response[0]`
(`{fileName, link}`); return the empty `{fileName:"", link:""}` if not found. The router's
route-0 gate is then `invoiceResponse.link` truthy. Verify the instruction text "Upload Invoice
Here" exists on the live Coupa WO template at build (cf. Step 1's positional-quote quirk;
recon can confirm the exact instruction label). Note the function returns only the **last**
matching instruction's response (loop has no early break) — faithful; matters only if the
template ever has two "Upload Invoice Here" instructions.

### 4.7 Attachment payload (faithful, verify at test)

`json:CreateJSON` (14) → `{"attachment": {"file": <invoiceResponse.link>, "type": "file"}}`,
POST to `/api/purchase_orders/{poId}/attachments`. The `file` value is a Limble file **URL**,
sent with `type: "file"`. Whether Coupa's attachment endpoint accepts a remote URL under
`type: "file"` (vs. a multipart upload or `type: "url"`) is unverified — port faithfully and
confirm at first live test. This is the most likely test-time surprise in the workflow.

## 5. Target n8n node graph

```
[Webhook: POST hook-777]
  → [IF: status == "COMPLETE"]                                    (2 filter; false → end)
  → [HTTP L: GET /v2/tasks/?tasks={taskID}&limit=1]               (2)
  → [IF: meta1 exists AND meta2 exists AND description contains "@CoupaWO;"]   (6 filter; false → end)
  → [HTTP L: GET /v2/tasks/{taskID}/instructions?limit=50]        (3)
  → [Code: aggregate → array of {instruction, response}]          (12)
  → [Code: CoastalGetInvoiceInstResponse → invoiceResponse]       (11)
  → [Data Table: read Coupa OAuth token]  "Coastal - Coupa OAuth Token" QAj62weJaWmRBJ76   (§4.2)
  → [HTTP C: GET /api/purchase_orders/{meta2}]                    (25 + §4.1 by-id fix)
  → [IF: invoiceResponse.link exists]                             (10 router / 14 filter)
       true  → [Set: attachment JSON {file: link, type: "file"}]  (14)
             → [HTTP C: POST /api/purchase_orders/{poId}/attachments] ──err──▶(log)   (15)
             → [HTTP C: POST /api/purchase_orders/{poId}/comments @created-by] ──err──▶(log)  (28)
       false → [HTTP C: POST /api/purchase_orders/{poId}/comments @created-by] ──err──▶(log)  (29)

(error log write: [Data Table: Insert row {limbleWONum: taskID, errorCode, errorMsg,
 timestamp = now ISO} → "Coastal - Coupa Integration Error Log" 6GbR5Rxezl7hqk9i])
```

`HTTP L` = Limble (credential per §6), `HTTP C` = Coupa (`https://coastalwasteinc.coupahost.com`;
Bearer-from-Data-Table auth per §4.2).

Node notes beyond §3/§4:
- **Dead comment Feeder/Aggregator (8/9) dropped** (§4.4). The "WO is Coupa related" gate
  reads task fields (`meta1`/`meta2`/`description`) — put it as an IF **on the task fetch (2)**;
  the source's comments GET (6) existed only to host that filter, so it can be dropped with 8/9.
- **`body[1]` → `[0]`** everywhere (PO lookup result, etc.).
- **On Error = "Continue (using error output)"** on the 3 covered POSTs (§4.3), each wired to
  the error-log write. GET po and reads left uncovered (faithful).
- **No retries** — source has none; OQ-022's GET-retry sanction was Step-1-scoped. Do not add
  retries here without separate sanction (flag if desired — the GET po lookup is the candidate).
- **Two identical comment POSTs** kept per-route (faithful). Optional single-node collapse noted
  in §3; not taken.

## 6. Cross-workflow dependencies

- **Reads `meta1` + `meta2`** — both written upstream (Step 1 writes `meta1`; Step 2 writes
  `meta2` = PO **id**). §4.1's by-id fix binds Step 3's PO lookup to Step 2's `meta2` = id
  contract. If Step 2 ever changes what `meta2` holds, Step 3 breaks — keep them in lockstep.
- **Reads status "COMPLETE"** from the webhook event text (not a Limble status-name lookup) —
  it's the raw Limble webhook event string, same family as Step 1's "ADDED COMMENT TO TASK".
- **Reads** "Coastal - Coupa OAuth Token" (`QAj62weJaWmRBJ76`) — written by the built Token
  Regen workflow; all 3 Coupa calls use it (§4.2).
- **Writes** "Coastal - Coupa Integration Error Log" (`6GbR5Rxezl7hqk9i`) — drained by the built
  Error Log Export. Step 3 is a writer alongside Step 1 (and Step 2 once its OQ-008 fix lands —
  OQ-029); all must point at this same table (no second error log).
- **No Limble writeback** — Step 3 is terminal on the Limble side; it does not touch the WO.

## 7. Open items gating the build

- **Owner go-ahead** to build into `NH1giNups8iICMZe` — not yet given (design-only Hold, mirrors
  Step 1/2's pre-build posture).
- **OQ-030 (RESOLVED 2026-07-07): PO lookup by id** — confirm at build that Coupa exposes the
  direct-id path `GET /api/purchase_orders/{id}` (else use `?id=`). The fix is committed; only
  the exact endpoint shape is a build-time verification.
- **OQ-031 (RESOLVED 2026-07-07): Bearer-for-all** — confirm at first live test (401/403 on any
  Coupa call = revisit auth).
- **§4.7 attachment payload** — the `{file: <Limble URL>, type: "file"}` shape against Coupa's
  attachments endpoint is unverified. Highest-risk item at first live test.
- **§4.6 instruction label** — verify "Upload Invoice Here" is the exact instruction text on the
  live Coupa WO template (recon can confirm read-only, per OQ-023).
- **OQ-024 (no working prod baseline)** — Step 3 has never processed a real completed CoupaWO
  (no task ever reached `meta2`-populated). No regression history; validate against synthetic WOs
  driven all the way through Steps 1→2→3 (invoice-present / no-invoice / each error path).
- **Limble credential** — follow Step 1's precedent: wire the sandbox Limble credential
  ("Gerald Limble Sandbox", `MX0lwgfyFiGUBh5W`) for test runs, swap to the Coastal prod Limble
  credential (`qn6u8jEK085DoHT8`) at cutover.

## 8. Relationship to recon (OQ-023) and to the Step 1/2 specs

- The null-`meta2`/no-baseline facts (OQ-024) carry over directly — Step 3 sits at the far end
  of the same never-succeeded path; there is no live Step-3 execution to compare against.
- Admin escalation user `317887` (Brandon Ray Freckleton, OQ-019) is **not** used by Step 3 —
  its error handling is Coupa-log-only with no Limble admin comment (§4.3).
- Limble API quirks apply: name/text filters need explicit handling; the instructions call (3)
  passes `limit=50` (source) — verify Limble's `/instructions` default page size doesn't clip a
  long template (cf. the instructions-endpoint default-2 surprise in prior recon).
- Coupa host `https://coastalwasteinc.coupahost.com`; token source and error-log table are the
  same shared artifacts Step 1/Step 2 use.
