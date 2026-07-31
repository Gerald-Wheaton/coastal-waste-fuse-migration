# A6 sandbox seed record — EHS Create WO fixtures (2026-07-20)

Teardown ledger for everything created in the Limble **sandbox instance** for the A6 test suite
(ehs-test-plan section 5.1). Owner authorized API seeding 2026-07-20 with the sandbox Basic
credential. **Every object below must be removed after deployment** (A8 wrap-up / post-cutover
teardown), except where marked.

Companion staging (n8n side, tracked in DEPLOYMENT.md section 5, not here): 5 EHS node URLs →
mock host, `templateID: "842"` → `"4189"` on `Create Deficiency Task` — both revert at cutover.

> ⚠️ **Tag literals below are stale where they say `@EHSWO;` (OQ-038 reversed 2026-07-27).** The
> EHS gate now matches **`@EHS;`**; `"@EHSWO;"` does not contain `"@EHS;"`, so any parent still
> carrying the old literal drops at `WO is an EHS WO?`. Re-seeded since this ledger was written:
> **4218** and **4202** → `@EHS;` (`customTags` `['@EHS']`). **NOT re-seeded: 4223**, the fixture
> that actually produced the U4 pass — it still carries `@EHSWO;` and needs a PATCH before U4 is
> re-fired. Treat the rows below as the historical seed record, not current fixture state; the
> live state is in `test-sequence.md`'s A7 block.

## Created via API (this session)

### Regions — `DELETE /v2/regions/{id}`

| regionID | name | assigned to location |
| --- | --- | --- |
| 7944 | Central Florida | 98872 Coastal 10 |
| 7946 | Southwest Florida | 98873 Coastal 12 |
| 7947 | South Florida | 98876 Coastal 23 - Miami Hauling East |
| 7948 | Coastal Materials Management | 98875 Coastal 24 - Lake Worth Hauling |
| 7949 | South Atlantic | 98877 Coastal 30 |
| 7950 | Corporate Services | 98878 Corporate Office |

(A probe region 7945 "Central Florida TEST-PROBE" was created and deleted same-session — already gone.)

### Teams — delete route unverified; try `DELETE /v2/teams/{id}`, else UI

| teamID | name | locationID |
| --- | --- | --- |
| ~~602733~~ **605957** | EHS Approver Assignee | 98872 Coastal 10 (602733 deleted in OQ-043 test 2026-07-25; 605957 is the live replacement) |
| 602734 | EHS Approver Assignee | 98873 Coastal 12 |
| 602735 | EHS Approver Assignee | 98876 Coastal 23 - Miami Hauling East |
| 602736 | EHS Approver Assignee | 98875 Coastal 24 - Lake Worth Hauling |
| 602737 | EHS Approver Assignee | 98877 Coastal 30 |

Verified: `GET /v2/teams?name=EHS Approver Assignee&limit=500` returns exactly these 5 (real
teams, not OQ-040-style role-teams).

### Template task — `DELETE /v2/tasks/4189`

| taskID | name | locationID | instructionID |
| --- | --- | --- | --- |
| 4189 | EHS WO Template (Sandbox A6 TEST) | 98472 | 14933 — text: `Work that Needs to be Done (from the EHS Inspection)` (type 3) |

Sandbox stand-in for prod template **842**. Cloning proven: probe task 4190 created with
`templateID:"4189"` inherited instruction 14933's text as new instruction 14934; probe task
deleted same-session (already gone).

## Created by owner (UI, 2026-07-20) — owner deletes at teardown

| locationID | name |
| --- | --- |
| 98872 | Coastal 10 |
| 98873 | Coastal 12 |
| 98875 | Coastal 24 - Lake Worth Hauling |
| 98876 | Coastal 23 - Miami Hauling East |
| 98877 | Coastal 30 |
| 98878 | Corporate Office |

Note: locations must be deleted AFTER their teams/regions/tasks; regions after unassigning
(or deleting) their locations.

## Will be created by the A6 run itself (record as they appear)

The A6 execution creates up to 5 deficiency tasks (scenarios A1/B/C/D/E) at the fixture
locations, each with cloned + patched instructions and (B only) an uploaded image. Append their
taskIDs here after the run; delete at teardown (`DELETE /v2/tasks/{id}`).

| taskID | scenario | location | notes |
| --- | --- | --- | --- |
| 4191 | A1 (partial run 126921) | 98872 Coastal 10 | orphan from errored 2026-07-21 run (n28 body-expression bug); **deleted same-session** — already gone |
| 4192 | A1 | 98872 Coastal 10 | meta1 EHS-INSP-A1; instr 14936 verbiage patched |
| 4193 | B | 98873 Coastal 12 | meta1 EHS-INSP-B; instr 14937 verbiage patched + image `178460441194564-deficiency-photo.png` |
| 4194 | C | 98876 Coastal 23 - Miami Hauling East | meta1 EHS-INSP-C; instr 14938 verbiage patched |
| 4195 | D | 98875 Coastal 24 - Lake Worth Hauling | meta1 EHS-INSP-D; instr 14939 verbiage patched |
| 4196 | E | 98877 Coastal 30 | meta1 EHS-INSP-E; instr 14940 verbiage patched |

All five from the PASSING A6 run (execution 126934, 2026-07-21). Delete at teardown
(`DELETE /v2/tasks/{id}`; 4193's image goes with the task).

## A7 fixtures (EHS Update suite) — SCRAPPED + REBUILD PLAN (revised 2026-07-24)

### Original API skeletons — SCRAPPED (delete at teardown, `DELETE /v2/tasks/{id}`)

The 2026-07-21 skeletons (spec-plan IDs 9001/9101/9102/9002/9003) are **not usable for U1**. Live
sandbox read 2026-07-24 (`limble-mcp-SANDBOX` → FM 360 Consulting) found them broken:

| taskID | role | actual state (2026-07-24) | disposition |
| --- | --- | --- | --- |
| 4198 | U1 parent | `@EHSWO;` + `meta1=EHS-INSP-UPD-1` OK, but **0 instructions**, `associatedTaskID:0`, **not completed** (status 0, dateCompleted 0), completionNotes null | **DELETE — rebuild** |
| 4199 | U1 child 1 | not completed; completionNotes wrongly = `"Parent WO: replaced handrail bolts."` (parent's line) | **DELETE** |
| 4200 | U1 child 2 | not completed; completionNotes null | **DELETE** |
| 4201 | U3 non-EHS | no `@EHSWO;`/no meta1 (gate-drop fixture OK); not completed | keep; complete in UI for faithfulness |
| 4202 | U4 parent | `@EHSWO;` + `meta1=EHS-INSP-UPD-1` OK, 0 instructions, not completed | salvageable: add 1 text instruction via API + complete in UI (no child spawn) |

(Probe task 4197 + instructions 14941/14942 were created and deleted 2026-07-21 — already gone.)

**`type:2` is NOT the problem** (corrected 2026-07-24): the real EHS-Create output 4192 is also
`type:2, template:false` and is an ordinary completable WO. EHS WOs are type-2 by design. The
skeletons failed only because they were never completed and never child-linked — not because of
their type.

**Root cause the U1 skeletons can't be salvaged:** the fields U1 needs are **UI-only** (all → 400
"`X` is not allowed" via API, probed 2026-07-21): task `completionNotes`, task `dateCompleted`,
and instruction `meta`/`associatedTask`. And Limble has **no "attach existing WO as child"**
action — a parent's `instruction.meta.associatedTask` is stamped **only** when a child WO is
**spawned from an instruction on the parent** in the UI. Standalone 4199/4200 can never be
retro-linked.

**`meta1` is API-set, not UI-editable** (2026-07-24): both 4192 (real EHS output) and 4198
received `meta1` via the API; it is Limble integration metadata, not surfaced in the standard WO
editor. So a rebuilt parent's shell (name + `@EHSWO;` description + `meta1` + the text
instruction) is created via **API**; only the child-spawn + completions happen in the UI.

### Child-WO mechanism — CONFIRMED from prod template 842 (2026-07-24)

The link the workflow follows (`instruction.meta.associatedTask`, blueprint modules #68→#69→#71)
is created **only** by a Limble **type-14 "Work Order" instruction** — a button that spawns a
linked child WO. Prod template **842** carries two instructions:

| instr | text | type |
| --- | --- | --- |
| 2026 | `Work that Needs to be Done (from the EHS Inspection)` | **7** (label) |
| 2027 | `Create a WO for the Deficiencies (… "Start another WO" button …)` | **14** (WO generator) |

A **type-3/7 text instruction has NO create-WO action** (owner screenshot 2026-07-24: menu only
offers "Viewing Past Responses"). **Sandbox gap:** template 4189, the A6 outputs 4192–4196, and
the rebuilt parent 4218 all have only the text instruction — the **type-14 instruction was never
replicated**, so none of them could ever spawn children. (Instr 2027's `response` reads
`"This response type is not supported currently, please contact Limble…"` via API — the button is
UI-driven.)

### Rebuild plan (revised 2026-07-24 — type-14 required)

Parent **4218** already created via API: `@EHSWO;` + `meta1=EHS-INSP-UPD-1` + text instr 15052
(type 3), verified. Remaining:

1. **Add a type-14 "Work Order" instruction to 4218** (the child generator). Try via API:
   `POST /v2/tasks/4218/instructions` body `{"instruction":"Create a WO for the Deficiencies …","type":14}`.
   If POST rejects type 14, add it in the UI (edit WO instructions → add a "Work Order"-type step).
2. In the UI, open 4218 → the type-14 instruction renders a **button**; click it → child WO 1,
   then use **"Start another WO"** → child WO 2. This is what stamps `meta.associatedTask` on the
   type-14 instruction.
3. Complete **child 1** → completion notes exactly: `Child 1: guardrail welded.`
4. Complete **child 2** → completion notes exactly: `Child 2: lighting fixed.`
5. Complete the **parent 4218** → completion notes exactly: `Parent WO: replaced handrail bolts.`
6. *(optional U4)* rebuild 4202 with a text instruction only (no type-14, no children); complete
   with any note — exercises the zero-children + meta-less path.
7. **Delete** old 4198 / 4199 / 4200. Record child IDs in this file.

**Sandbox stand-in fix (broader):** template 4189 should also gain a type-14 instruction so future
A6 EHS-Create clones produce spawnable parents — track separately.

### 2026-07-25 finding — multi-child = multiple type-14 instructions + page-size-2 bug

Raw curl on `GET /v2/tasks/4218/instructions` (bypassing the MCP, which truncates to **2** — the
known instructions page-size-2 blind spot) shows parent **4218** actually has **four** instructions:

| instr | type | associatedTask |
| --- | --- | --- |
| 15052 | 3 (text) | — |
| 15054 | 14 | `?tasks=4220` (child 1) |
| 15056 | 14 | `?tasks=4221` — **DANGLING**, task 4221 was deleted |
| 15058 | 14 | `?tasks=4222` (child 2) |

- **Mechanism confirmed:** each **"Start another WO"** click creates a **new type-14 instruction**,
  each linking exactly one child. Multi-child is many type-14 instructions, NOT one comma-list.
  The workflow's design (iterate instructions → filter `meta.associatedTask` → fetch each) is right.
- **Child→parent link is UI/DB-only, invisible to MCP get_tasks:** children 4220/4222 show
  `Associated Task: #4218` in the UI, but `get_tasks` reports `associatedTaskID: 0` for both. Don't
  trust MCP for association state — use raw curl.
- **CONCRETE page-size-2 bug (was ehs-test-plan section 4.5 risk):** the EHS-Update **Get
  Instructions** node had no `limit` → Limble returns only the first **2** instructions (`15052`
  text + `15054`→4220) → children 4221/4222 silently dropped.
- **THREE port fixes approved by owner + applied 2026-07-25** (n8n writes authorized for these
  edits; verified in place by read-back). These are **permanent port-bug fixes, NOT test staging**
  — no cutover revert:
  1. `Get Instructions` (n05): URL now `…/instructions?limit=100` (page-size-2 fix).
  2. `Has Child WO?` (n06): `{{ $json.meta?.associatedTask }}` (optional chain — plain `.meta.`
     threw on the meta-less text instruction, killing the run).
  3. `Get Child Task` (n07): URL now `https://api.limblecmms.com{{ $json.meta.associatedTask }}`
     (raw meta value is a **relative path** `/v2/tasks/?tasks=NNNN`; without the host the request
     fails). Resolves that node's OQ-009 "directly-fetchable URL" assumption: it is NOT a full URL.
- **Shape check (n08/n09):** Aggregate outputs `childTasks`; n8n HTTP node splits the child GET's
  array response into flattened items, so n09's flat `childTasks[i].completionNotes` read is
  correct — the section 4.5 `body[]` worst case does not materialize in this port.
- **Cleanup owed:** delete dangling instruction **15056** (points at deleted 4221). Deleting a
  child task does NOT remove its generator instruction — a real gotcha.

Current valid children: **4220** (Child 1) + **4222** (Child 2). Old 4221 deleted (instruction
15056 still dangling).

### A7 run results (2026-07-25) — U1/U2/U3/U4 ALL PASS

Execs 127253 (U2), 127254 (U3), 127255 (U1), 127258 (U4 pre-fix, silent-stop proof),
127259 (U4 PASS post-rewire), 127262 (U1 regression PASS) — details in `test-sequence.md` A7.
Dangling instr 15056 left in deliberately and proved **harmless** both runs: fetching deleted
4221 returns empty → zero items → no `undefined` (deleted-child links degrade gracefully).
U4 exposed + closed a real fidelity gap (zero-children silent stop) via the owner-approved
`Collect Child Links`/`Any Child Links?`/`Split Child Links` rewire — permanent, no cutover
revert.

**Teardown adds** (`DELETE /v2/tasks/{id}`): parent **4218** + children **4220/4222** (instrs
15052/15054/15056/15058 go with 4218) and U4 parent **4223** (instr 15060). Workflow deactivated
after each test burst (owner-managed).

### OQ-043 batch-kill test (2026-07-25) — PASS; more teardown adds

Missing-team batch test on the guarded EHS Create workflow (exec 127265): team **602733**
(98872) deleted via `DELETE /v2/teams/{id}` — **delete route now verified** (was "unverified;
try DELETE, else UI" above). A1 skipped via `Team Missing?`→Loop, B/C/D/E still processed.

- **Teardown adds:** duplicate deficiency tasks **4224/4225/4226/4227** (B/C/D/E re-created;
  no cross-run dedupe — static mock re-serves same forms) → `DELETE /v2/tasks/{id}`.
- Team at 98872 recreated post-test via `POST /v2/teams` → **teamID 605957** (2026-07-25);
  supersedes 602733 in the teams table above — teardown deletes 605957, not 602733 (gone).
  Workflow deactivated post-test.

### Verification gate before U1 fires (I run these read-only)

- `GET /v2/tasks/<new parent>/instructions` returns **`meta.associatedTask`** = fetchable child
  URLs, **on the first page** (page-size-2 risk, ehs-test-plan section 4.5).
- Parent `dateCompleted` + `completionNotes` populated (else write-back gets epoch-0 date + null
  parent note — section 4.3 flag).

### Elevated run risk (was "may error", now confirmed likely)

Sandbox instructions start with **no `meta` key** (confirmed on 4192, 2026-07-24). `Has Child WO?`
reads `$json.meta.associatedTask`; on a meta-less instruction `meta` is `undefined` → `.associatedTask`
**throws** (not just filters). Affects U4's meta-less parent especially. Build likely needs
`$json.meta?.associatedTask` (optional-chain) before A7 runs — track as a workflow fix.

## API contracts discovered while seeding (OQ-009 additions)

- `POST /v2/regions` — body `{name, parentRegionID}`; **parentRegionID is required in practice**
  (omitting it → opaque 400/500). Returns `{"regionID":"<id>"}`.
- `DELETE /v2/regions/{id}` — 200.
- `PATCH /v2/locations/{id}` — `{regionID}` accepted, 200.
- `POST /v2/teams` — body `{name, locationID}`. Returns `{"teamID":"<id>"}`.
- `POST /v2/tasks` — **`type` is a required field** (2026-07-24: omitting it → 400
  `` `type` is required ``). Use `type: 2` for EHS-style WOs (matches real EHS-Create output 4192,
  which is `type:2, template:false`). `name`, `locationID`, `description`, `meta1` also accepted.
- `templateID` on `POST /v2/tasks` accepts any existing task's ID (as a **string**) and clones
  its instruction list onto the new task; "templates" are ordinary type-2 tasks (see sandbox
  4041 "Main WO Template (Sandbox)").
- `DELETE /v2/tasks/{id}` — 200.
- **`POST /v2/tasks/{taskID}/instructions`** — works (201, returns `{"instructionID":"<id>"}`);
  body `{instruction, type}`. Discovered 2026-07-21 during A7 seeding.
- **NOT API-writable** (all → 400 "`X` is not allowed", 2026-07-21): task `completionNotes`,
  task `dateCompleted` (PATCH /v2/tasks/{id}); instruction `meta`/`associatedTask` (PATCH and
  POST instruction routes). Task completion state and child-WO links are UI-only.
- `POST /v2/tasks/{id}/complete` — 404 route not found.
- Sandbox `GET /v2/tasks/{id}/instructions` items carry **no `meta` key** on API-created
  instructions (whether UI child-links add one is unverified — checklist above settles it).
