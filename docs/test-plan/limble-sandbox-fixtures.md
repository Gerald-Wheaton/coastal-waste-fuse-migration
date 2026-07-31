# Limble Sandbox Test-Data Plan (all 7 n8n workflows)

**Status:** DESIGN ONLY (2026-07-08). This is a seeding *plan* + script *design*. Nothing here
was executed — see "Hard constraints" below.

Purpose: define the **smallest sufficient** set of Limble sandbox fixtures to drive all 7 n8n
workflows end-to-end in test, and the approach to create them, extending the existing Step-1-only
seeder (`tools/sandbox-seed/`). Owner has approved populating Gerald's Limble sandbox in principle
(OQ-028); Coupa and EHS Insight must still be **mocked** (they are not owner-approved for live
test writes, and the EHS side has no mock yet — see Blockers §8).

## 0. Hard constraints in force this session

- **No live API calls** to Limble, Coupa, or EHS were made. This phase is design/spec only
  (OQ-003). Every "verify"/"create" below is an instruction for a *future* seeding run, not
  something done here.
- **Sandbox-only, one location, one credential — owner directive (2026-07-08).** All Limble seeding
  MUST target the **FM360 Sandbox** via the n8n credential **"Gerald Limble Sandbox"**
  (`MX0lwgfyFiGUBh5W`), and **every** seeded object MUST be created under location **`98472`
  "Coastal 99 - Sandbox Test"**. Never seed
  against a production Limble credential or any other location. This binds all three seeding
  mechanisms in §5 — in particular the n8n seeder workflow hardcodes `locationID = 98472` on every
  create so nothing can escape the sandbox location.
- **This fresh clone has no *local* Limble access.** `.env` (holds `ENCODED_AUTH`) and `.mcp.json`
  (the Limble MCP registration) are git-ignored and **absent** from this checkout, so the local
  `seed.py` can't authenticate and the Limble MCP isn't connected. **Mitigation:** seeding can run
  from an **n8n seeder workflow** that uses the already-stored "Gerald Limble Sandbox" credential
  (§5, option 1) — no local secret needed. Otherwise live seeding is *blocked* on the owner
  restoring `.env`/MCP (§8).
- **No writes to the n8n instance** (no workflow create/update/activate/test, no Data Table
  writes). The workflow read/write field lists below are taken from the seven `docs/build-specs/*`
  documents (recently authored against the live blueprints), not from live n8n reads, to stay
  within the design-only posture. A read-only `n8n_get_workflow` (mode=structure) pass could
  reconfirm exact field mappings later if desired; it was not needed here.
- **Only repo files were written** (this doc + `docs/test-plan/seed/`).
- **No secrets** are written to any repo file. Sandbox credentials belong in `.env` (git-ignored)
  and n8n's credential store only.

---

## 1. Baseline inventory — what already exists (OQ-028)

The prior Step-1 test rig (deployed 2026-07-05, torn down 2026-07-06) left the **Limble sandbox
fixtures in place** after teardown. Per OQ-028 and `tools/sandbox-seed/README.md`:

| Fixture | Identity | Notes |
|---|---|---|
| **Location** | `98472` — **"Coastal 99 - Sandbox Test"** | Name deliberately embeds `99`; Step 1's location transform spells it → **"Coastal Ninety Nine"** (exercises `NumberToSpelledNumberConverter`, incl. the two-word compound). Verified 2026-07-06 (test scenario s6b). |
| **Template** | `4041` — 17-instruction CoupaWO shape | Mirrors prod template 965. Load-bearing: quote-upload instruction at **position 5** (positional read); plus the 5 text/dropdown/number instructions Step 1 matches by verbatim text; plus filler incl. **"Upload Invoice Here"** (used by Step 3). Created in UI (no template API). |
| **Tasks** | `4052`–`4060` (9) | The Step-1 scenario matrix `s1-happy-gt500-capex` … `s7-fail-createreq`. Each spawned from template 4041, put in **"PO Create"**, with `@CoupaWO;` in the description and a trigger comment. Instruction responses + the s1 quote file were set in the UI. |
| **Site Manager user** | firstName **"Site Manager"**, lastName "Sandbox NinetyNine", email `gerald+sm99@fm360consulting.com` | Role **"View Only"** (sandbox `roleID 37676`) at location 98472, active. Matches `CoastalSiteManagerExtract`'s convention (`active` + role "View Only" at the location + `firstName == "Site Manager"`). |
| **Statuses** | **"PO Create"**, **"PO Requested"** | Instance-wide, exact spelling (Step 1 looks both up by `%name%` wildcard). "PO Approved" was **not** seeded — Step 1 never needed it. |

**Ending state after the 2026-07-06 test run (must be re-verified):** task `4052` was driven all
the way through Step 1 — flipped to **"PO Requested"** with **`meta1 = 424242`** stamped and a
quote attached. That makes 4052 a ready-made **Step 2 input** if it is still in that state. The
other scenario tasks ended in their respective terminal states (error paths, supplier-miss, etc.).

**Known baseline gaps (from OQ-028 residual surface R1/R2):**
- Admin user **`317887`** (Brandon Ray Freckleton, the error-escalation @-mention used by
  Step 1 & Step 2) **does not exist in the sandbox** — "Get Admin User" returns 0 items and
  admin error comments no-op in test (R2). Fine for prod (user exists there, OQ-019).
  **Since 2026-07-26 the ID is no longer a node literal** — both workflows read it from row
  `escalation_admin_user_id` in Data Table `Coastal - Integration Config` (`L0npQPPEXQI9JRzX`),
  currently holding the sandbox stand-in `398783`. Change the stand-in there, not in the nodes.
- No team, no EHS template, no EHS/CoupaWO-completed task states were ever seeded (Step-1 rig
  only).

> **RE-VERIFY BEFORE REUSE.** All of the above was confirmed in a *prior* session with live MCP
> access. This session has none. The first action of any future seeding run must be to re-verify
> the baseline (the seeder's `verify_location`, `ensure_statuses`, `ensure_site_manager` already
> do lookup-before-create, so a plain re-run reports drift without duplicating).

---

## 2. What each workflow reads from Limble (the input side that fixtures must satisfy)

Grounded in the build specs. Only the **read/trigger** side dictates fixtures; the write side is
listed to show what a passing run should produce.

| # | Workflow | Trigger | Reads from Limble | Writes to Limble | Needs Limble fixtures? |
|---|---|---|---|---|---|
| 1 | Coupa Token Regeneration | Schedule (daily) | — nothing — | — nothing — | **No** (Coupa + Data Table only) |
| 2 | Create Requisition (Step 1) | Webhook: new comment `status="ADDED COMMENT TO TASK"` | task (`meta1`,`statusID`,`description @CoupaWO;`,`locationID`,`teamID`/`userID`,`due`); instructions (17, load-bearing 6); users (scan for Site Manager); location (name→spelled); statuses `%PO Create%`/`%PO Requested%`; comments (latest-comment tiebreak); admin `317887` | `meta1`, status→PO Requested, comments | **Yes** (baseline covers it) |
| 3 | Check For New PRs (Step 2) | Schedule (every 5 min) | statuses `%PO Requested%` → all tasks in it (`meta1`,`description @CoupaWO;`,`teamID`,`userID`,`taskID`); statuses `%PO Approved%`; team (`teamID`) / user (`userID`) for mention; admin `317887` (error path) | `meta2`, description append, status→**PO Approved**, comment @assignee | **Yes** (+ "PO Approved" status, assignments) |
| 4 | WO Completed (Step 3) | Webhook: task completed `status="COMPLETE"` | task (`meta1`+`meta2`,`description @CoupaWO;`,`taskID`); instructions (find **"Upload Invoice Here"** → `response[0].link`) | — nothing (Coupa only) — | **Yes** (completed CoupaWO w/ meta1+meta2+invoice) |
| 5 | Create WO From EHS Inspection | Schedule (daily) | `listLocations name="Coastal 99%"` → `locationID`,`regionID`; `GET /v2/regions?regions={regionID}` → `regionName` (must be in allowlist); `listTeams name="EHS Approver Assignee"` filtered by `locationID` → `teamID`; instructions on the created task (find "Work that Needs to be Done (from the EHS Inspection)") | **createATask** (template 842, `meta1`=EHS RowUID, `@EHS;` desc — OQ-038 fix REVERSED 2026-07-27, tag stays source-faithful), updateAnInstruction | **Yes** (region on location, team, EHS template) — EHS side mocked |
| 6 | Update EHS Inspection From Limble WO | Webhook: task completed `status="COMPLETE"` | task (`meta1`=EHS RowUID, `description @EHS;` — gate literal changed 2026-07-27, `dateCompleted`, `completionNotes`); instructions (filter `meta.associatedTask` exists → child WOs); each child task (`completionNotes`) | — nothing (EHS only) — | **Yes** (completed @EHS; parent + optional child) — EHS side mocked |
| 7 | Coupa Integration Error Log Export | Schedule (every 15 min) | — nothing — | — nothing — | **No** (Data Table + email only; R3 = insert a synthetic error row) |

**Trigger note:** only **3** workflows are webhook-triggered (Step 1, Step 3, EHS-Update) and are
fired via the trigger helper (§7 deliverable, `docs/test-plan/seed/fire.sh`). Step 2, EHS-Create,
Token Regen and Error Log Export are **schedule-triggered** — they are exercised by executing /
activating the workflow in n8n; they self-discover their work (no payload).

### 2a. Tag mismatch — RESOLVED as OQ-038 (2026-07-08), then **REVERSED 2026-07-27**

> ⚠️ **Read this first — the direction below is superseded.** On **2026-07-27 Ethan reversed
> OQ-038**: the created WO keeps the source-faithful **`@EHS;`** and **EHS-Update's gate moved to
> `@EHS;`** instead. Reason: Coastal's prod Limble holds 10 EHS WOs all tagged `@EHS;` with **5
> still open**, which a `@EHSWO;` gate would orphan when they complete after cutover. Applied to
> both live nodes (`isLUx7cUjkmKggD2` n21, `8JvtesynrYtZbw7U` n04).
> **Fixture consequence, inverted:** EHS-Update parent fixtures must carry **`@EHS;`**, not
> `@EHSWO;`. Sandbox parents **4218** and **4202** were re-PATCHed 2026-07-27; **4223** was not
> (see the A7 block in `test-sequence.md`). `"@EHSWO;"` does not contain `"@EHS;"`, so a
> stale-literal parent now drops at the gate.

EHS-Create's `createATask` stamped the description with **`@EHS;`** (3 occurrences in
`Coastal - Create WO From EHS Inspection (PROD).json`, one per region route) while EHS-Update
**filters on `description contains "@EHSWO;"`** (1 occurrence in the Update blueprint). `"@EHS;"`
is not a substring of `"@EHSWO;"`, so an EHS-Create WO could never satisfy EHS-Update's gate — a
**pre-existing defect in the shipped Make blueprints** (faithfully ported into n8n), meaning the
EHS closed loop has never worked in production. ~~**Owner decision (OQ-038):** sanctioned fix —
EHS-Create is corrected to stamp **`@EHSWO;`**, matching the EHS review docx (which specifies
`@EHSWO;` on both the created WO and the Update gate). Design is applied in the specs/plan; the
one-line live edit to `isLUx7cUjkmKggD2` is **queued for the write phase** (n8n writes on hold).
**Fixture consequence:** the EHS-Update parent-task fixture is stamped **`@EHSWO;`** — now the
*correct* Create output, not a workaround.~~ **(Struck 2026-07-27 — reversed; see the block above.
Both sides are `@EHS;`.)**

---

## 3. Fixtures-by-workflow matrix (before consolidation)

| Workflow | Object | State / key fields | Source | Create via |
|---|---|---|---|---|
| **Step 1** | location 98472 | name "Coastal 99 - Sandbox Test" | baseline | exists |
| | template 4041 | 17 instr, quote@5, verbatim texts | baseline | UI (exists) |
| | tasks 4052-4060 | PO Create, `@CoupaWO;`, responses set, s1 quote file | baseline | API + UI (exist) |
| | Site Manager user | View Only @98472, active | baseline | API/UI (exists) |
| | statuses PO Create, PO Requested | exact spelling | baseline | UI (exist) |
| **Step 2** | task in **PO Requested** | `meta1` non-empty, `@CoupaWO;`, **teamID** set | reuse 4052 (team-assign it) | stamp meta + assign (API/UI) |
| | task in **PO Requested** | `meta1` non-empty, `@CoupaWO;`, **userID** set | reuse 4053 (user-assign it) | stamp meta + assign (API/UI) |
| | status **PO Approved** | exact spelling (write target) | **NEW** | API attempt → UI fallback |
| **Step 3** | completed `@CoupaWO;` task | `meta1`+`meta2` set, **invoice file** on "Upload Invoice Here" | reuse 4052 (chain from Step 2) or new | stamp meta2 + complete + file (API + UI) |
| | completed `@CoupaWO;` task | `meta1`+`meta2` set, **no** invoice file | reuse 4054 | stamp meta2 + complete (API) |
| **EHS-Create** | Limble location(s) matching the EHS mock's mapped site(s) | see §4a — the mock currently maps to Coastal 10/12/23/24/30/"Corporate Office", NOT the sandbox "Coastal 99" | **coordination needed** | reuse 98472 (option A) or seed 6 (option B) |
| | region on the create-target location | `regionName` ∈ allowlist (e.g. **"South Florida"**) | **NEW / verify** | UI (region admin) |
| | team **"EHS Approver Assignee"** @ that location | `locationID`==that location | **NEW** | API attempt → UI fallback |
| | EHS deficiency template (prod 842 analog) | has instruction "Work that Needs to be Done (from the EHS Inspection)" + a "generate child WO" button instruction | **NEW** | UI (no template API) |
| **EHS-Update** | completed **`@EHS;`** parent task (was `@EHSWO;` before the 2026-07-27 reversal) | `meta1`=**`EHS-INSP-UPD-1`** (matches the mock), `completionNotes` set, `dateCompleted` set; taskID wired into the mock's `update-inspection-webhook.json` | **NEW** | create + stamp meta1 (API) + complete (API, via `status` — see below) + **UI for `completionNotes`, which the API cannot set at all**. Contract proven 2026-07-27 on 4237: `PATCH /v2/tasks` **rejects built-in statuses on `statusID`** (`2` and `0` both 400 `` `statusID` contains an invalid value ``; custom statuses like 8054 are fine). Completion works via `{"status":1,"assignmentType":"team","assignment":<teamID>}`, which sets `statusID:2` + `dateCompleted` as side effects. `completionNotes` and `dateCompleted` are both `is not allowed` on PATCH, and a completed task cannot be PATCHed back to Open. |
| | 2 completed child WOs (mock scenario U1) | linked from parent instructions' `meta.associatedTask`, each with `completionNotes` | **NEW** | UI (button-spawned links) |

Allowlist region names (EHS-Create §4.2 / OQ-034): **Central Florida, Southwest Florida, Coastal
Materials Management, South Florida, South Atlantic.** Any one satisfies the guard; pick **"South
Florida"** for the sandbox location.

---

## 4. Consolidated minimal fixture set (the smallest union)

Reuse the single sandbox location (98472) and the single CoupaWO template (4041) everywhere the
logic allows. Only add distinct objects where a workflow genuinely needs a different task **state**
or a genuinely different object (EHS team/template). IDs shown as `<assign>` are allocated by
Limble at create time and recorded back into `tools/sandbox-seed/` on the real run.

**Shared / reused (already exist, re-verify):**
1. Location **98472** "Coastal 99 - Sandbox Test".
2. Template **4041** (CoupaWO 17-instr, quote@5, "Upload Invoice Here" filler).
3. Site Manager user (View Only @98472).
4. Statuses **"PO Create"**, **"PO Requested"**.

**New Limble objects to add (the whole delta for the other 6 workflows):**
5. Status **"PO Approved"** (exact spelling) — Step 2 flip target.
6. Assign location 98472 to a region named **"South Florida"** (regionName in allowlist) — EHS-Create.
7. Team **"EHS Approver Assignee"** at location 98472 — EHS-Create.
8. EHS deficiency template (sandbox analog of prod 842) with the instruction **"Work that Needs to
   be Done (from the EHS Inspection)"** and a "generate child WO" button instruction — EHS-Create
   output + EHS-Update child structure. *(Record its sandbox templateID; the built EHS-Create
   workflow's hardcoded `templateID:"842"` must be pointed at this sandbox ID for the test run,
   analogous to the Step-1 Coupa base-URL swap.)*

**Task states (the minimal 5, favouring the Step 1→2→3 chain):**
- **A (chain):** reuse/confirm **4052** — happy CoupaWO. After Step 1 it is PO Requested + `meta1`.
  **Team-assign it** → covers Step 2's *team* comment branch → after Step 2 it is PO Approved +
  `meta2` → **complete it with an invoice file** → covers Step 3's *invoice-present* branch. One
  task exercises the whole Coupa handshake.
- **B:** reuse **4053** — **user-assign it** and stamp `meta1`, set to PO Requested → covers Step
  2's *user* comment branch. (An unassigned PO-Requested task covers the "neither" no-comment
  branch — reuse any other 405x task, no new fixture.)
- **C:** reuse **4054** — completed CoupaWO with `meta1`+`meta2` but **no** invoice file → covers
  Step 3's *no-invoice* branch.
- **D:** **NEW** `TEST EHSUpdate parent` — completed task, `@EHS;` in description (post-2026-07-27 reversal),
  `meta1`=**`EHS-INSP-UPD-1`** (the RowUID the concurrent EHS mock defines for the update path),
  `completionNotes` typed → EHS-Update core. This parent's Limble taskID must be written back into
  the mock's `update-inspection-webhook.json` (scenario U1) so `fire.sh` replays the right id.
- **E (mock scenario U1 = 2 children):** **NEW** two child WOs linked from D's "generate child WO"
  instructions, each completed with its own `completionNotes` → EHS-Update child-notes
  concatenation. If skipped, D still runs (empty child list → `CoastalGetChildWONotes` returns
  `""`) — a valid lighter fixture that also de-risks the EHS-Update spec's flagged "does the
  Aggregate node emit one item with 0 children?" concern, but it is *not* the mock's U1 scenario.

EHS-Create (#5) needs **no pre-seeded task** — it *creates* the task; you verify the created WO
(assigned to the EHS Approver team, `meta1`=RowUID, deficiency text in instruction 1). Its inputs
are the region+team+template fixtures (5–8) plus the EHS mock's inspection payload — but which
**location(s)** must exist depends on a cross-worker decision (§4a).

### 4a. Cross-worker coordination — the EHS mock's site mapping vs. the sandbox location

An EHS Insight **mock** is being built concurrently (fixtures landing in
`docs/test-plan/fixtures/ehs/`). Its `AuditInspection/list` + `hierarchy/fetch` drive **six**
sites all the way to `createATask`, mapping (via `EHSLimbleLocationMapping`) to Limble location
names: **Coastal 10, Coastal 12, Coastal 23 - Miami Hauling East, Coastal 24 - Lake Worth Hauling,
Coastal 30**, and **"Corporate Office"** (the no-digit passthrough branch). **None of these is the
sandbox's only location, "Coastal 99" (98472).** EHS-Create has no error handling (faithful silent
port, OQ-004), so a `listLocations` miss on the first unmatched site will most likely halt the run
before any WO is created.

Resolve **before** running EHS-Create, with the EHS-mock worker + owner — two options:

- **Option A — minimal Limble (recommended):** ask the EHS-mock worker to retarget exactly **one**
  inspection's `hierarchy.Title` so it maps to the existing sandbox location (e.g. Title
  `"99 Sandbox"` → first token `99` → `"Coastal 99"` → `listLocations name="Coastal 99%"` hits
  98472), and make the other inspections **drop before `listLocations`** (acceptable last answer,
  or a non-`Facility Inspection Checklist` question set — the mock already demonstrates both drops
  for BE-40 and BE-50). Then the Limble side needs **only** location 98472 (+ its region + EHS
  team). Keeps the fixture set minimal.
- **Option B — full Limble coverage:** seed all six mapped locations in the sandbox, each with an
  allowlisted region and an "EHS Approver Assignee" team, to exercise the special-case mappings
  (Coastal 23/24) and the image path (Coastal 12/23). Heavier; take it only if in-sandbox branch
  coverage of `EHSLimbleLocationMapping` is explicitly wanted.

**EHS-Update is unaffected by this mismatch:** it reads its task by `taskID` and uses `meta1` to
fetch the EHS inspection — it never calls `listLocations`, so its parent task can live at 98472
regardless of the EHS site. The mock already provides the matching update inspection
(`EHS-INSP-UPD-1`) and the U1 trigger payload.

Total new Limble objects: **1 status, 1 region assignment, 1 team, 1 template, 1–2 tasks** on top
of the untouched baseline. Everything else is reuse.

---

## 5. Seeding approach (API vs UI), reusing the proven seed.py patterns

**Three mechanisms are available; pick per fixture (all bound by the §0 guardrail — credential
"Gerald Limble Sandbox", everything under location 98472):**

1. **n8n seeder workflow(s) — recommended, and the only API path available this session.** Build a
   dedicated TEST workflow (e.g. **"Coastal - Seed Limble Sandbox (TEST)"**) whose HTTP Request
   nodes call the Limble API using the stored **"Gerald Limble Sandbox"** credential. Because that
   credential already lives in n8n, this needs no local `.env`/MCP (clears blocker §8.1 without
   passing secrets around), runs in the same environment as the workflows under test, and is
   re-runnable. Mirror `seed.py` node-for-node: lookup-before-create per object, custom `User-Agent`
   (Limble WAF), `locationID`+`roleID` on user create, verbatim instruction text, quote instruction
   positionally 5th, and a **hardcoded `locationID = 98472`** on every create so nothing can escape
   the sandbox location. Anything the API refuses (templates, uploads, region/child-WO links) still
   routes to the UI checklist. It is itself a TEST artifact — delete it at teardown, and it needs
   its own workflow ID (OQ-007) like the mocks. It can be one workflow with a Switch over a "what to
   seed" input, or a few small per-scenario workflows.
2. **Local `tools/sandbox-seed/seed.py` (+ `seed_ext.py`)** — the proven script path; usable only
   once the owner restores `.env` (`ENCODED_AUTH`) or the Limble MCP.
3. **Limble UI** — for the fixtures no API can create (templates, file uploads, region assignment,
   child-WO links; likely status and team creation).

The API-driven patterns below are reused verbatim across mechanisms 1 and 2 (already proven in the
base `seed.py`; the n8n seeder must replicate them, do not re-invent):
- **Custom `User-Agent`** on every request — Limble's WAF 403s the default `Python-urllib` UA.
- **`Authorization: Basic <ENCODED_AUTH>`** from `.env`, never printed.
- **Lookup-before-create** idempotency on every object (`find_task_by_name`, `ensure_*`).
- **User create requires `locationID` + `roleID`** (View Only = 37676 in this sandbox).
- **Status create is unreliable via API** → attempt POST, fall back to a printed UI checklist line
  (the base `ensure_statuses` already does this).
- **Instruction text is matched verbatim** and the **quote instruction must be positionally 5th**
  — the base `verify_template_task` already asserts this.

| Fixture | Mechanism | Detail |
|---|---|---|
| Re-verify baseline (loc/status/SM/template) | **API (existing)** | Re-run `seed.py` (+ `--template-id 4041`) — reports drift, creates nothing that exists. |
| Status "PO Approved" | **API attempt → UI fallback** | New `ensure_status("PO Approved")` reusing the base status create/fallback. |
| `meta1`/`meta2` stamping | **API** (`PATCH /v2/tasks/{id}` `{"metadata":{"meta1":...}}`) → verify via GET → UI fallback | `updateATask` (what the workflows use) writes `metadata.meta*`; the same PATCH shape should let the seeder pre-stamp. `meta1=424242` was confirmed surfacing via GET in the OQ-028 run, so verify-after-write works. Flag if the tasks-API rejects a direct metadata PATCH → then meta must be produced by *running* Step 1/Step 2 (chain approach A) rather than pre-stamped. |
| Task → PO Requested / complete | **API** (`PATCH /v2/tasks/{id}` statusID / completion) → UI fallback | Reuse base's status PATCH; add `complete_task(id, notes)` (PATCH completed + `completionNotes`; UI fallback = mark complete + type notes). |
| Team/user **assignment** on a task | **API** (`PATCH /v2/tasks/{id}` `assignmentType`+`assignment`, as EHS-Create's createATask does) → UI fallback | Needed so Step 2 exercises team vs user comment branches. |
| Team "EHS Approver Assignee" @98472 | **API attempt → UI fallback** | `listTeams name=...` lookup first; create if the teams endpoint allows, else UI checklist (teams are often admin-UI only). |
| Region on location 98472 | **UI (verify via API)** | `GET /v2/regions?regions={regionID}` to *read* the location's current region; **assigning/creating** a region is an admin-UI operation — checklist line: "set location 98472's Region to a region named exactly 'South Florida'". |
| CoupaWO template 4041 | **UI (exists)** | No template create API (base README establishes this). |
| EHS deficiency template (842 analog) | **UI only** | Create in UI with the two named instructions; record its templateID for the workflow config swap. |
| Quote file (s1) / invoice file (Step 3) | **UI only** | File uploads onto an instruction response are UI actions (base README already lists the quote upload as UI). |
| Instruction responses (capex/contractor/amount/desc) | **UI** (API where exposed) | Base README scenario table; unchanged. |
| Child-WO link (`meta.associatedTask`) | **UI only** | The link is created by clicking the template's "generate child WO" button in the Limble UI; no direct seeding API assumed. Optional fixture E. |
| EHS-Update parent `@EHS;` task | **API** (create + stamp meta1 + complete) **+ UI** (completion notes if PATCH won't set them) | Description must contain `@EHS;` literally — **not** `@EHSWO;`, which no longer matches the gate (§2a, reversed 2026-07-27). `meta1` = a fixed RowUID string the EHS mock recognizes. |

### seed.py extensions required to go beyond Step 1
Designed in `docs/test-plan/seed/seed_ext.py` (imports and reuses the base seeder). New functions:
`ensure_status(name)`, `stamp_meta(task_id, meta1, meta2)`, `set_assignment(task_id, kind, id)`,
`set_status_by_name(task_id, status_name)`, `complete_task(task_id, notes)`,
`ensure_ehs_team(location_id)`, `verify_region_allowlisted(location_id, allow)`, and the
per-workflow fixture builders `seed_step2_fixtures()`, `seed_step3_fixtures()`,
`seed_ehs_update_parent()`. Anything the API refuses becomes a UI-checklist line, exactly like the
base seeder. The **n8n seeder workflow** (§5 option 1) implements this same function set as HTTP
Request nodes bound to the "Gerald Limble Sandbox" credential — it is the build target when there
is no local credential (this session's case).

---

## 6. Idempotency & teardown

- **Idempotency:** every builder does lookup-before-create (by task name / status name / team name
  / metadata presence). Re-running the extended seeder must not create duplicates — it reports
  existing fixtures and only fills gaps, matching the base seeder's contract. `stamp_meta` and
  `set_status_by_name` are naturally idempotent (writing the same value twice is a no-op-equivalent).
- **Leave in place (per OQ-028 precedent):** all Limble sandbox fixtures — location, template(s),
  team, statuses, users, tasks — are left after a test run so re-runs and future phases reuse them.
  Limble is a *long-lived sandbox*, not torn down like the Coupa mock.
- **Clean up (test-run hygiene, not fixtures):** after a run, reset mutated task *state* if you
  want a clean re-run of the chain (e.g. flip 4052 back to "PO Create", clear `meta1`/`meta2`) —
  the base rig's idempotency re-fire test did exactly this. The extended seeder should offer a
  `--reset <taskID>` that returns a chained task to PO Create with meta cleared (design stub
  included). Do **not** delete shared fixtures ad hoc.
- **What is NOT left behind (non-Limble):** the Coupa mock workflow + its Data Tables and the dummy
  token row were torn down 2026-07-06 (OQ-028); they must be **re-stood-up** for any Coupa-side
  re-test (§8). No EHS mock exists yet.

---

## 7. Deliverables in `docs/test-plan/seed/`

- **`seed_ext.py`** — extended seeder *design* (well-commented, runnable-shaped; imports the base
  `tools/sandbox-seed/seed.py`). Stubs the new API calls + UI-checklist fallbacks in the base
  seeder's style. Not run this session (no `.env`).
- **`fire.sh`** — generic webhook trigger helper for the **3** webhook workflows (Step 1, Step 3,
  EHS-Update). Maps an event preset to the Limble webhook `status` string and posts `{status,
  taskID}` (the only fields the gateways consume):
  - `comment`  → `status="ADDED COMMENT TO TASK"` (Step 1)
  - `complete` → `status="COMPLETE"` (Step 3 and EHS-Update)

  Generalizes the base `fire.sh` (which hardcoded Step 1's comment event and URL).

---

## 8. Blockers, assumptions & open questions

**Blockers (live seeding cannot start until these clear):**
1. **Local Limble credential absent — mitigated by the n8n seeder.** No `.env` (`ENCODED_AUTH`) and
   no Limble MCP in this clone, so the *local* `seed.py` can't authenticate. **Preferred path:**
   build the n8n seeder workflow (§5 option 1), which uses the stored **"Gerald Limble Sandbox"**
   credential and needs no local secret. Restoring `.env`/MCP is only required if the owner prefers
   the local script. *(Design/plan work — i.e. this document — needs neither.)*
2. **UI-only fixtures need a human in the Limble sandbox UI:** the EHS deficiency template (+ its
   two named instructions + "generate child WO" button), all file uploads (quote, invoice),
   region create/assignment, the child-WO link, and most likely status creation and team creation.
   The seeder emits these as a checklist; it cannot perform them.
3. **Non-Limble mocks are a prerequisite for the workflows that call out:**
   - Coupa mock (workflow `mSiLCsvOVdiSWOZP` + capture/config tables + dummy token row) was **torn
     down 2026-07-06** — must be **redeployed** to test Step 1/2/3 again (or run against the Coupa
     TEST instance `coastalwasteinc-test.coupahost.com` noted in OQ-028). Out of scope for this
     Limble plan, but gates Step 1/2/3 execution.
   - **EHS Insight mock — being built concurrently** (fixtures in `docs/test-plan/fixtures/ehs/`:
     `ehs-auditinspection*.json`, `ehs-inspection-fetch.json`, `ehs-hierarchy-fetch.json`,
     `ehs-attachment-fetch.json`, `ehs-update-response.json`, `update-inspection-webhook.json`).
     Two Limble⇄EHS handshakes must line up with it:
     - **EHS-Update:** the parent Limble task's `meta1` must equal the mock's update RowUID
       **`EHS-INSP-UPD-1`**, and the parent's Limble taskID must be written into the mock's
       `update-inspection-webhook.json` (scenario U1). EHS-Update webhook path:
       `/webhook/coastal-ehs-update-inspection`.
     - **EHS-Create:** the mock's mapped site names must resolve to Limble locations that exist in
       the sandbox — see §4a (currently they do **not** match 98472; needs the Option A/B decision).
4. **n8n workflow IDs / activation** remain owner-gated (OQ-007/OQ-003). Webhook delivery itself is
   untested until cutover (no sandbox webhook registered — OQ-020/OQ-028); test fires use the n8n
   editor's "Listen for test event" URL passed to `fire.sh`.

**Assumptions (verify at seed time):**
- `PATCH /v2/tasks/{id}` accepts `metadata.meta1/meta2`, `assignmentType/assignment`, and
  completion fields directly (the workflows' `updateATask`/`createATask` write these; direct
  pre-stamping is assumed to use the same shape). If it doesn't, produce meta by *running* the
  upstream workflow (chain approach A) instead of pre-stamping.
- "PO Approved" is spelled exactly `PO Approved` (prod statusID 5783, OQ-025) — sandbox uses the
  same spelling; only the string matters (workflows look it up by `%name%`, not ID).
- Team creation and region assignment are likely UI-only in Limble; the seeder attempts API and
  falls back — confirm at seed time.

**Open questions to raise with the owner:**
- **RESOLVED, then REVERSED — EHS tag mismatch (§2a → OQ-038):** the 2026-07-08 fix corrected
  EHS-Create to write `@EHSWO;` (applied live 2026-07-20). **Ethan reversed it 2026-07-27** — the
  WO keeps `@EHS;` and **EHS-Update's gate** moved to `@EHS;`, which also adopts the 5 prod EHS WOs
  still open. Both live nodes changed. Parent fixtures must carry **`@EHS;`**.
- **NEW — EHS-Create site→location mismatch (§4a):** the concurrent EHS mock maps its sites to
  Coastal 10/12/23/24/30/"Corporate Office", none matching the sandbox's Coastal 99 (98472). Pick
  Option A (retarget one mock inspection to Coastal 99 + drop the rest before `listLocations`) or
  Option B (seed the 6 mapped locations). Gates EHS-Create execution.
- Sandbox EHS template ID (842 analog) → the built EHS-Create workflow's `templateID:"842"` literal
  must be swapped to it for the sandbox test (a workflow-config step, like the Coupa base-URL swap).
- Whether to redeploy the Coupa mock vs. use the Coupa TEST instance for Step 1/2/3 re-test (feeds
  OQ-016/OQ-024 R4).
