# Test Plan — EHS-side n8n Workflows (mock-based, design only)

Status: **design / spec-only** (2026-07-08). No live EHS Insight / Limble / Coupa calls; no writes
to n8n from this document. Deliverable is the test design + fixtures only. Execution (creating the
mock workflow, capture table, Limble sandbox fixtures, and running the workflows) is a later,
separately-authorized step — see the "Test-time artifacts to create (needs permission)" and
"Teardown" sections.

Covers the two EHS-side workflows:

| Workflow | n8n ID | Trigger | Nodes | Source blueprint |
| --- | --- | --- | --- | --- |
| Create WO From EHS Inspection | `isLUx7cUjkmKggD2` | Schedule (daily) | 29 (built, inactive) | `Coastal - Create WO From EHS Inspection (PROD).json` |
| Update EHS Inspection From Limble WO | `8JvtesynrYtZbw7U` | Limble webhook (task completed) | 13 (built, inactive) | `Coastal - Update EHS Inspection From Limble WO (PROD).json` |

Both were confirmed **built and inactive** by a read-only `n8n_get_workflow` on 2026-07-08 (the
build-spec headers still say "empty shell" — stale; the OQ-007 table and this plan reflect Built).

**Goal:** exercise every branch, both sanctioned fixes (OQ-034 region consolidation, OQ-036 dead-node
drop), and the two open-question behaviors (OQ-035 last-question-only, OQ-037 dedupe typo) **without
touching real EHS Insight**. The EHS Insight API is replaced by a mock n8n workflow; the Limble side
of "Create WO" runs against the Limble sandbox (a separate agent owns Limble seeding — this plan only
**enumerates** the Limble inputs needed).

---

## 0. Guardrails and scope notes carried into this plan

- **No real EHS calls.** Both workflows' 7 EHS HTTP nodes get their base host repointed at the mock at
  test time (host-substring swap only, mirroring the OQ-028 Coupa-mock approach). See §1.4.
- **EHS API key is never used against anything real and never written to any file.** The mock ignores
  the `X-ApiKey` header. Fixtures and this doc use the placeholder `MOCK-EHS-APIKEY`; the real
  (exposed, being-rotated) key `apikey-160448cf-…` appears in no repo file. (OQ-015.)
- **Correction to the task brief:** `NumberToSpelledNumberConverter` and `CoastalContractorExtraction`
  are **not** referenced by either EHS workflow — verified by grepping both blueprints (only
  `CoastalEHSFormFilter` + `EHSLimbleLocationMapping` in Create WO; only `CoastalEHSInspectFormUpdate`
  + `CoastalGetChildWONotes` in Update). Both of the other functions are Coupa-side
  (`NumberToSpelledNumberConverter` does the "Coastal Ninety Nine" location spelling in Step 1). No
  fixtures exercise them here. Location resolution in Create WO is purely `EHSLimbleLocationMapping`.

---

## 1. Mock EHS Insight API design

New n8n workflow **"Coastal - Mock EHS Insight API (TEST)"** (webhook-based). It answers every EHS
Insight endpoint the two workflows call, returns canned fixture responses, and captures the
write-back payload into a Data Table for verification.

### 1.1 Endpoint inventory (reverse-engineered from the live built HTTP nodes + blueprint mappers)

Base path on the real API: `https://coastalwasteinc.ehsinsight.com/api/v4`. Mock base:
`https://<n8n-host>/webhook/mock-ehs/api/v4` (so a host-only swap preserves every path/query).

| # | Method | Path (after `/api/v4`) | Used by | n8n node | Canned response shape (fixture) |
| --- | --- | --- | --- | --- | --- |
| E1 | GET | `/entity/AuditInspection/list?CreatedAfter=<iso>` | Create WO | `EHS: List Inspections` | `{ "List": [ {RowUID, …} ] }` — `ehs-auditinspection-list.json` |
| E2 | GET | `/entity/AuditInspectionQuestions/list?fields=Title,RowUID` | Create WO | `EHS: List Question Sets` | `{ "List": [ {Title, RowUID} ] }` — `ehs-auditinspectionquestions-list.json` |
| E3 | GET | `/entity/AuditInspection/fetch/{RowUID}` | Create WO **and** Update | `EHS: Fetch Inspection Detail` / `EHS: Fetch Inspection` | `{ "Entity": {…} }` keyed by RowUID — `ehs-inspection-fetch.json` |
| E4 | GET | `/hierarchy/fetch/{BusinessEntity}` | Create WO | `EHS: Get Hierarchy` | `{ "Hierarchy": { "Title": "…" } }` keyed by BusinessEntity — `ehs-hierarchy-fetch.json` |
| E5 | GET | `/attachment/fetch/{AttachmentUID}` | Create WO | `EHS: Fetch Attachment` | ~~`{ "data": "<base64>" }`~~ **Superseded 2026-07-20:** raw **binary PNG** + `Content-Disposition: attachment; filename="deficiency-photo.png"` (mock's dedicated binary branch; consuming node uses `responseFormat: file`) |
| E6 | POST | `/entity/AuditInspection/update` (body = full Entity) | Update | `EHS: Update Inspection` | `{ "Success": true }` + **capture inbound body** — `ehs-update-response.json` |

**Response-shape provenance (all OQ-009 — no EHS API spec exists, shapes are reverse-engineered):**
The built nodes strip Make's bundle-level `.data` wrapper and read the response body as `$json`
directly (`$json.List`, `$json.Entity`, `$json.Hierarchy.Title`). So the mock returns `List` /
`Entity` / `Hierarchy` at the **top level**, matching the built expectation. Each is flagged
"verify against a live response at first test" in the node notes.
**Attachment shape updated 2026-07-20:** the old `$json.data || $json` base64 guess is gone — the
node now uses `responseFormat: file` (binary out), feeding the new `Attach Instruction Image` PUT
(multipart field `image`, Limble-support-confirmed route, proven live). The mock's E5 route serves
real binary accordingly. Whether the **real** EHS endpoint returns raw bytes (vs JSON/base64)
remains the one unverified piece — Phase C6 watch item. E6 request/response shapes remain guesses.

### 1.2 Mock routing (n8n implementation note)

The task frames this as "Switch on path," but n8n cannot register **one** static webhook path that
matches all six distinct EHS paths. Two buildable options:

- **Preferred — one webhook trigger node per endpoint** (n8n allows multiple triggers in a single
  workflow). Six Webhook nodes with paths `mock-ehs/api/v4/entity/AuditInspection/list`,
  `…/AuditInspectionQuestions/list`, `…/AuditInspection/fetch/:rowuid`,
  `…/hierarchy/fetch/:businessentity`, `…/attachment/fetch/:attachmentuid`,
  `…/AuditInspection/update` (POST). E1/E2/E6 are static paths; E3/E4/E5 use a **trailing** `:param`.
  Each webhook → a small Code/Set node that looks up the keyed fixture by the path param → **Respond
  to Webhook**. E6's webhook additionally inserts a capture row (§1.3) before responding.
- **Fallback if the instance rejects the trailing `:param`** — OQ-028 found this n8n instance did
  **not** match a *mid-path* route param (`/requisitions/:reqId/attachments`); trailing params are
  more likely to work but are unverified here. If they fail, register the E3/E4/E5 paths as
  **literal deterministic paths** per fixture ID (e.g. `…/AuditInspection/fetch/EHS-INSP-A1`), exactly
  the OQ-028 workaround. All fixture IDs in §3 are deterministic, so this is viable if tedious.

A single "Switch on `$json.path`" node behind one webhook is **not** viable unless the workflows'
EHS node URLs are also rewritten to a single flat path with the resource as a query param — a larger
edit than the host swap, so not recommended.

### 1.3 Write-payload capture (for verifying the write-back workflow)

Create Data Table **"Coastal - Mock EHS Capture (TEST)"** (a new table; no existing table matches —
confirmed via read-only `listTables`, 2026-07-08):

| Column | Type | Contents |
| --- | --- | --- |
| `endpoint` | string | e.g. `AuditInspection/update` |
| `method` | string | `POST` |
| `inspectionID` | string | `body.Entity.RowUID` (or the fetched id) parsed from the inbound body |
| `udfCompletionNotes` | string | `body.Entity.UDFLimbleWOCompletionNotes` — the primary assertion target |
| `rawBody` | string | `JSON.stringify(inbound body)` — full round-trip for diffing |
| `receivedAt` | date | `$now` |

E6's mock branch: parse inbound body → insert one row → respond `ehs-update-response.json`. The
Update-Inspection assertions read this row. (E1–E5 are reads; capturing them is optional debug only.)

### 1.4 Pointing the workflows at the mock (test-setup edit, needs authorization)

For **both** workflows, in each EHS HTTP node, swap the host substring
`coastalwasteinc.ehsinsight.com` → `<n8n-host>/webhook/mock-ehs` (paths, queries, headers, auth
untouched). Nodes to edit: Create WO — `EHS: List Inspections`, `EHS: List Question Sets`,
`EHS: Fetch Inspection Detail`, `EHS: Get Hierarchy`, `EHS: Fetch Attachment`; Update —
`EHS: Fetch Inspection`, `EHS: Update Inspection`. This is a temporary test edit; restore the real
host at teardown (§7). It requires write access to the two workflows — request per OQ-003/OQ-007.

**Credential note:** Create WO's EHS nodes currently reference a **placeholder credential id**
(`__EHS_INSIGHT_CREDENTIAL_ID__`, name "EHS Insight API Key") — it will not resolve as-is. Update's
EHS nodes reference the real `ZEf4C1rpYSbBgLbX` ("Coastal Waste - EHS API Key"). Before testing,
either point Create WO's five EHS nodes at `ZEf4C1rpYSbBgLbX` or create the placeholder credential
(any dummy header value — the mock ignores it). Flag: the two workflows should share **one** EHS
credential per the specs; the placeholder is a build gap to close regardless of testing.

---

## 2. How assertions are observed

- **Create WO** writes to **Limble** (create task, update instruction), not to the EHS mock. Its
  assertions are read from (a) the n8n **execution view** — each HTTP node's request body/response is
  inspectable (e.g. the `Create Deficiency Task` node's outgoing JSON body); and (b) the **Limble
  sandbox** (the created tasks/instructions). The EHS mock only feeds it reads.
- **Update Inspection** writes back to **EHS** — its assertion is the **capture table** row (§1.3),
  chiefly `udfCompletionNotes`.
- Branch/gate drops are observed as the absence of a downstream node execution in the execution view.

---

## 3. Create-WO test section (`isLUx7cUjkmKggD2`)

### 3.1 Trigger

Manual **"Execute Workflow"** (the Schedule Trigger fires once on manual execution — no pinned data
needed). The workflow then calls the mock for E1/E2, loops, and writes to the Limble sandbox. The
`CreatedAfter=now-24h` query is ignored by the mock; all fixture inspections are treated as in-window.

### 3.2 One fixture set drives every branch

The single `ehs-auditinspection-list.json` (9 inspections across 8 sites) + `ehs-inspection-fetch.json`
+ `ehs-hierarchy-fetch.json` + `ehs-attachment-fetch.json` cover the whole matrix in one run. Site →
Limble location → region mapping is produced by `EHSLimbleLocationMapping` (site name) then the Limble
sandbox (location's regionID → region name).

### 3.3 Scenario matrix

| Inspection(s) | EHS site Title → Limble location → Region | Branch(es) exercised | Expected result |
| --- | --- | --- | --- |
| **A1 + A2** (both `BE-10`) | `10 Fort Lauderdale` → `Coastal 10` → **Central Florida** (allow) | `CoastalEHSFormFilter` dedupe, **OQ-037** typo | Exactly **one** task for Coastal 10. Its name must contain **`FIC-1001`** (A1, first-seen), **not** `FIC-1002` (A2). A2 is discarded even though it has a newer `UpdatedDtm` + completed — proving the `UpdateDtm`/`UpdatedDtm` typo makes the replace branch never fire. `meta1 = EHS-INSP-A1`. No image → verbiage-only PATCH, image PUT not reached. |
| **B** (`BE-12`) | `12 Naples` → `Coastal 12` → **Southwest Florida** (allow) | **OQ-035** last-question-only + **image** attachment path | One task. Instruction text = `Deficiencies from Inspection:  B-Q3: Exit sign not illuminated` (last question only; `B-Q1: Spill kit missing` must be **absent**). `EHS: Fetch Attachment` **called** for `ATT-B-1` (capture row via mock's `Att Capture`); `Attach Instruction Image` PUT fires — instruction's `instructionFiles[]` gains `<serverPrefix>-deficiency-photo.png` (upload response `{"filename": ...}`). |
| **C** (`BE-23`) | `23 East Miami Hauling` → `Coastal 23 - Miami Hauling East` → **South Florida** (allow) | `EHSLimbleLocationMapping` **Coastal 23 special case** + attachment-present-but-**not-image** | One task. `EHS: Fetch Attachment` **not** called (`.pdf` fails the `.jpeg/.png/.jpg/.gif` filter). Verbiage-only PATCH, no image PUT. Text `…C: Guardrail corroded`. |
| **D** (`BE-24`) | `24 Lake Worth Facility` → `Coastal 24 - Lake Worth Hauling` → **Coastal Materials Management** (allow) | `EHSLimbleLocationMapping` **Coastal 24 special case** + no attachment | One task. Verbiage-only PATCH, no image PUT. Text `…D: Broken ladder rung`. |
| **E** (`BE-30`) | `30 Savannah` → `Coastal 30` → **South Atlantic** (allow) | 5th allowlisted region | One task. Verbiage-only PATCH, no image PUT. Text `…E: Blocked emergency exit`. |
| **F** (`BE-99`) | `Corporate Office` → `Corporate Office` → **Corporate Services** (NOT in allowlist) | `EHSLimbleLocationMapping` **no-digit passthrough** + **OQ-034** region-drop (negative) | **No task.** Passes the Answer gate (last Q deficient), resolves location + region, then **drops at `Region In Allowlist?`**. `List EHS Approver Teams` / `Create Deficiency Task` do **not** run. |
| **G** (`BE-40`) | `40 Orlando` (hierarchy fetched; Limble never queried) | acceptable last answer (`Answer != "0"`) + OQ-035 reinforcement | **No task.** Drops at `Question Unacceptable?`. The earlier deficient question (`G-Q1`) is **ignored** (last-only). No Limble location lookup. |
| **H** (`BE-50`) | n/a | wrong `QuestionsSelector` + question-set Title filter | **Dropped** inside `Filter To Latest Completed` (`QuestionsSelector = QS-VEH-002 ≠ QS-FIC-001`). Never enters the per-form loop; hierarchy never fetched. |

**Net:** exactly **5** tasks created (A1, B, C, D, E); F/G/H create nothing. Region allowlist coverage:
all 5 names appear as *proceeding* cases (A1/B/C/D/E) + one *dropping* case (F) — full OQ-034 coverage.

### 3.4 Per-created-task assertions (Limble side, from the `Create Deficiency Task` node body)

For each of A1/B/C/D/E, the outgoing `POST /v2/tasks` JSON body must have:
`name = "EHS Facility Inspection Checklist Deficiencies - {FormNumber}"`, `type: 2`, `priority: 2`,
`metadata.meta1 = {inspection RowUID}`, `assignmentType: "team"`, `assignment = {teamID matched to the
location}`, `locationID = {matched location}`, `templateID: "842"`,
`description = "Deficiencies were found in the latest Facility Inspection Checklist for {site Title} @EHSWO;"` (**OQ-038:** tag corrected from source's `@EHS;` to `@EHSWO;` so the created WO matches "Update EHS Inspection"'s gate),
`due = now+7d`. Then `Get Task Instructions` → `Deficiency Instruction` filter selects the instruction
containing `Work that Needs to be Done (from the EHS Inspection)`, and one `updateAnInstruction` PATCH
fires (image or no-image branch per the table). Note the **double space** in
`"Deficiencies from Inspection:  "` — assert it verbatim.

### 3.5 Branches deliberately NOT covered (and why)

- Multiple images / multiple attachments: source only ever reads `FileAttachments[0]` (Make `[1]`), so
  one image + one non-image + none is full coverage.
- `Any Deficient Forms?` false (empty filtered list): implicitly covered if you also run with an
  empty `List` fixture; optional negative run — low value, the IF is a length check.

---

## 4. Update-Inspection test section (`8JvtesynrYtZbw7U`)

### 4.1 Trigger

Manual curl replay of the Limble task-completed webhook (webhook delivery itself is not exercised until
cutover, OQ-020). n8n wraps the POST body under `$json.body`.

```
curl -X POST 'https://<n8n-host>/webhook/coastal-ehs-update-inspection' \
     -H 'Content-Type: application/json' \
     -d '{"status":"COMPLETE","taskID":9001}'
```

Payloads for all three scenarios are in `update-inspection-webhook.json` (post the `body` object).

### 4.2 Scenario matrix

| Scenario | Payload | Exercises | Expected |
| --- | --- | --- | --- |
| **U1 — parent completed w/ 2 children** | `{status:"COMPLETE", taskID:9001}` | Main path: `@EHSWO;` gate passes, child WO collection, `CoastalGetChildWONotes` concat, `CoastalEHSInspectFormUpdate`, write-back | Capture-table row: `inspectionID = EHS-INSP-UPD-1`; `udfCompletionNotes` = parent notes **and** both child notes concatenated (per spec §7): see §4.3 for the exact expected string. |
| **U2 — not a completion** | `{status:"ADDED COMMENT TO TASK", taskID:9001}` | `Is Completed?` gate | Drops immediately. No Limble/EHS calls, **no** capture row. |
| **U3 — completed, not an EHS WO** | `{status:"COMPLETE", taskID:9002}` | `WO is an EHS WO?` gate (`@EHSWO;` + `meta1 exists`) | `Get Task` runs; gate fails (task 9002 has no `@EHSWO;` / no `meta1`); drops. **No** EHS fetch/update, no capture row. |

### 4.3 U1 expected write-back string (exact)

`Prepare Update Payload` builds, and `Apply Completion Notes` stores into
`Entity.UDFLimbleWOCompletionNotes`:

```
(Completed <MM/dd/yyyy hh:mm a in America/Denver>)
All discrepancies listed in the last question have been resolved. Here are the completion notes from Limble:
Parent WO: replaced handrail bolts.
 Child 1: guardrail welded. Child 2: lighting fixed.
```

Assert (from `rawBody` / `udfCompletionNotes` in the capture row):
- The parent's `completionNotes` line is present.
- **Both** children's notes are appended, space-separated, on the final line — proving
  `CoastalGetChildWONotes` iterated all child WOs.
- The **leading space** before `Child 1` is real (the function concatenates `" " + note`) — assert
  verbatim; it is a faithful-port artifact, not a bug to fix.
- The timestamp renders in **America/Denver** (spec §4.4). **Flag:** `dateCompleted` is assumed
  unix-epoch-seconds; if the live Limble task carries an ISO string, the built `DateTime.fromSeconds`
  yields a wrong/epoch-0 date — observe the rendered date and confirm the assumption (build note /
  OQ-009).
- **No-null-guard flag:** if a child task returns no `completionNotes`, the literal string
  `"undefined"` is concatenated (faithful, OQ-001). U1's children both have notes, so `undefined` must
  **not** appear — a good regression signal.

### 4.4 OQ-036 assertion — dropped dead nodes confirmed absent

The built workflow (13 nodes, verified) has **no** comments-fetch node and **no** `lastComment`
variable — source modules 63/64 were dropped per OQ-036. Assert by structure: node list contains no
`/comments` GET; the `Is Completed?` gate feeds `Get Task` directly. (Already confirmed in the
read-only structure pull; re-confirm after any rebuild.)

### 4.5 Known shape risks to watch during U1 (OQ-009)

- **Child-task fetch shape mismatch (highest risk).** Make's `CoastalGetChildWONotes` read
  `childWOs[i].body[0].completionNotes`; the built n8n Code reads `childTasks[i].completionNotes`
  directly (flattened). This assumes the Limble child-task GET (`GET {meta.associatedTask}`) yields
  items whose `completionNotes` is at the top level after n8n's array handling. If the real response is
  `{ body: [ {…task} ] }`, `childTasks[i].completionNotes` is `undefined` and every child note becomes
  `"undefined"`. The Limble sandbox response settles this — watch U1's output closely; this is the
  single most likely place the port misbehaves.
- **`Get Instructions` has no `limit`** on this workflow (faithful to source module 68), colliding with
  Limble's known instructions default page size of 2. If the parent WO template's child-link
  instructions sit past the first page, `Has Child WO?` sees none and child notes silently drop. The
  Limble parent fixture (§5) must keep child-link instructions within the returned page, or the test
  must confirm the full instruction list returns.
- **`Aggregate Child Tasks` with 0 children.** The build assumes it still emits one item (empty array)
  when no child WOs pass the filter. Add a fourth optional scenario **U4** (an `@EHSWO;` parent with
  **no** child-linked instructions) to confirm the write-back still runs with `childWOCompNotes = ""`;
  if Aggregate emits nothing, the workflow would silently stop before updating EHS — an important
  negative check. (Requires one more Limble parent fixture; listed optional in §5.)

---

## 5. Limble fixtures required (INPUT — enumerated, not designed here)

These are the **inputs** the two EHS workflows read. Limble credential in use on all Limble nodes is
**"Gerald Limble Sandbox"** (`MX0lwgfyFiGUBh5W`). Seeding mechanics live in
`limble-sandbox-fixtures.md` §5 — a dedicated **n8n seeder workflow** using that same credential
(recommended when there's no local `.env`), the local `tools/sandbox-seed/` script, or the Limble
UI. **All seeded data goes under sandbox location `98472` "Coastal 99 - Sandbox Test".**

### 5.1 For Create WO (`isLUx7cUjkmKggD2`)

**Locations** (queried by `GET /v2/locations?name={limbleLocation}%&limit=1`; each must return
`locationID` + `regionID`). Names must match the `EHSLimbleLocationMapping` output exactly (prefix
match with trailing `%`):

| Limble location name (starts-with) | regionID → region name (via `GET /v2/regions?regions={id}` → `regionName`) | Needed because |
| --- | --- | --- |
| `Coastal 10` | → **Central Florida** (allowlisted) | A1 proceeds |
| `Coastal 12` | → **Southwest Florida** (allowlisted) | B proceeds |
| `Coastal 23 - Miami Hauling East` | → **South Florida** (allowlisted) | C proceeds |
| `Coastal 24 - Lake Worth Hauling` | → **Coastal Materials Management** (allowlisted) | D proceeds |
| `Coastal 30` | → **South Atlantic** (allowlisted) | E proceeds |
| `Corporate Office` | → any name **not** in the 5-name allowlist (e.g. `Corporate Services`) | F must drop at region gate |

(No `Coastal 40` needed — G drops at the Answer gate before the location lookup.)

**Regions:** the `regionID` on each of the 6 locations must resolve through `GET /v2/regions` to the
region name above. The mock does **not** cover regions — this is real Limble sandbox config. The
allowlist match is on `regionName` returned as the **first** element (built node auto-splits the array
→ `$json.regionName`).

**Teams:** for each of the 5 allowlisted locations, a team named **`EHS Approver Assignee`** whose
`locationID` equals that location's `locationID` (the `Team At Location` filter matches on it, then
`First Matching Team` takes the first). `GET /v2/teams?name=EHS Approver Assignee&limit=500` must return
these. (Corporate Office needs no team — F drops before the team lookup.) *Note: the docx calls this
team "EHS Assignees"; the blueprint and built workflow both use `EHS Approver Assignee` — trust the
built literal.*

**Task template `842`:** the create-task uses `templateID:"842"`. The created task's instruction list
(via `GET /v2/tasks/{id}/instructions`) must include one instruction whose text contains
**`Work that Needs to be Done (from the EHS Inspection)`** (the `Deficiency Instruction` filter target,
which `updateAnInstruction` then patches). Template 842 must exist in the sandbox and carry that
instruction.

**Auth/credential:** the Limble sandbox key must be able to create tasks, list instructions, and patch
instructions at these locations.

**Outputs to assert (not inputs):** the 5 created sandbox tasks + their patched instructions — clean
up at teardown (§7).

### 5.2 For Update Inspection (`8JvtesynrYtZbw7U`)

Queried by `GET /v2/tasks?tasks={taskID}&limit=1` and `GET /v2/tasks/{taskID}/instructions`, plus
child fetches by the instructions' `meta.associatedTask` URL.

| Fixture | Requirement |
| --- | --- |
| **Parent WO `9001`** | `description` contains `@EHSWO;`; `meta1 = "EHS-INSP-UPD-1"` (matches the mock's E3 key); `dateCompleted` set (epoch seconds — see §4.3 flag); `completionNotes = "Parent WO: replaced handrail bolts."`; status Complete. |
| **Parent 9001 instructions** | At least two instructions carrying `meta.associatedTask` = a fetchable URL to a child task (e.g. `https://api.limblecmms.com/v2/tasks/9101` and `…/9102`), plus optionally a plain (no-`associatedTask`) label instruction. **Keep child-link instructions within the first returned page** given the no-`limit` page-size-2 risk (§4.5). |
| **Child WO `9101`** | Completed, `completionNotes = "Child 1: guardrail welded."` |
| **Child WO `9102`** | Completed, `completionNotes = "Child 2: lighting fixed."` |
| **Non-EHS WO `9002`** | Completed but `description` without `@EHSWO;` and/or `meta1` empty — drives U3's gate drop. |
| *(optional)* **Parent WO `9003`** | `@EHSWO;` + `meta1 = "EHS-INSP-UPD-1"` but **no** child-linked instructions — drives optional U4 (§4.5, zero-children Aggregate check). |

**Cross-check at seed time:** the `@EHSWO;` tag literal and `meta1` must match what "Create WO"
writes. Per **OQ-038** both sides are now `@EHSWO;` (Create corrected from `@EHS;`, aligned to the
docx + Update's gate). Confirm the queued live edit to `isLUx7cUjkmKggD2` has been applied before
running a real Create→Update closed-loop test; until then the parent fixture supplies `@EHSWO;`
directly.

---

## 6. Test-time artifacts to create (needs permission before executing)

Nothing below is created by this plan. Each needs explicit go-ahead (OQ-003/OQ-007 posture):

1. **n8n workflow** "Coastal - Mock EHS Insight API (TEST)" — a new workflow (needs an ID/shell, per
   the OQ-007 one-at-a-time pattern; the Coupa mock used shell `mSiLCsvOVdiSWOZP`). ~6 webhook triggers
   + responders + one Data Table insert. Set **active** for the test window.
2. **Data Table** "Coastal - Mock EHS Capture (TEST)" — schema in §1.3. New table (none exists today).
3. **Two workflow edits** (temporary): host-swap the 7 EHS HTTP nodes to the mock (§1.4), and resolve
   Create WO's placeholder EHS credential (§1.4).
4. **Limble sandbox fixtures** — everything in §5 (owned by the separate Limble agent).
5. **Capture-table rows** — written by the mock during U1 (one row per write-back). Not pre-seeded.

No dummy tokens or credentials are needed (EHS auth is mocked; Limble uses the existing sandbox
credential). Nothing is written to prod EHS or prod Limble.

---

## 7. Teardown checklist

After the test window:

- [ ] **Restore EHS host** on all 7 EHS nodes in both workflows (`<n8n-host>/webhook/mock-ehs` →
      `coastalwasteinc.ehsinsight.com`). Verify by node read.
- [ ] **Re-resolve Create WO's EHS credential** to the intended shared EHS credential (or leave the
      placeholder if that's the pre-build state to preserve) — record which.
- [ ] **Deactivate + delete** the "Coastal - Mock EHS Insight API (TEST)" workflow.
- [ ] **Delete** the "Coastal - Mock EHS Capture (TEST)" Data Table (after exporting rows if the write
      payloads are worth keeping as evidence).
- [ ] **Delete the created sandbox tasks** from Create WO (the 5 deficiency tasks + patched
      instructions) and the Update fixtures (parent/child/non-EHS tasks), or hand them to the Limble
      agent for reuse.
- [ ] **Confirm both workflows remain INACTIVE** (they were built inactive; testing must not activate
      them). No Limble webhook was registered for Update, so nothing to de-register (OQ-020 unchanged).
- [ ] **EHS key** — no rotation triggered by testing (mock never used a real key); the pre-go-live
      rotation obligation (DEPLOYMENT §0 / OQ-015) is unchanged and independent of this test.

---

## 8. Open questions / assumptions surfaced by this plan

- **OQ-009 (mock shapes are guesses)** — E1–E6 response shapes, the attachment `data` encoding, and
  especially the **child-task fetch shape** (§4.5) are reverse-engineered, not spec-confirmed. First
  live/sandbox run is the real confirmation.
- **OQ-035 / OQ-037** — deliberately made observable (B/G for last-only; A1/A2 for the dedupe typo) so
  the owner can see the shipped behavior in test before deciding whether to sanction a fix.
- **`dateCompleted` epoch-vs-ISO** (§4.3) and **`Get Instructions` pagination** (§4.5) are build-note
  flags that testing can now settle.
- **Create WO EHS credential placeholder** (§1.4) — a build gap independent of testing.
- **Region names are Limble-side config**, not in the EHS mock — full OQ-034 allowlist coverage depends
  on the six sandbox locations resolving to the six intended region names (§5.1).
- **`@EHSWO;` tag literal — RESOLVED (OQ-038, 2026-07-08):** owner sanctioned correcting "Create
  WO" to stamp `@EHSWO;` (was `@EHS;`), matching the docx and "Update"'s gate. Design applied; the
  live `isLUx7cUjkmKggD2` edit is queued for the write phase. Fixtures stamp `@EHSWO;` as the
  *correct* Create output (no longer a workaround).
```
