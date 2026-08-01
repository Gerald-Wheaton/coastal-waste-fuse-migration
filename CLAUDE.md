# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

This is **not a software codebase** — there is no build system, package manager, or test suite. Do
not invent `npm`/`bun`/`make` commands; none apply.

It is a **migration analysis & design project**: porting **Coastal Waste** (referred to as "Coastal"
throughout workflow names and docs)'s **Limble (CMMS) ⇄ Coupa (procurement)** and **Limble ⇄ EHS
Insight (safety inspections)** integrations off **Fuse** (Coastal's white-labeled **Make.com /
Integromat** platform, using private/custom Make apps — see "Working with the blueprint exports"
below) onto **n8n**. There are two related integrations, seven scenarios total. The work started
as reverse-engineering the existing Make.com scenarios into build-ready designs; as of 2026-07-26
**all 7 n8n workflows are built** (inactive, test phase) — the workflow-ID table lives in OQ-007's
entry in `open-questions.md`.

Two kinds of artifact live here:

- **Source of truth for the _current_ system:** the Make.com blueprint exports in
  `docs/OG-workflows/` (`*.json` files — one per scenario/workflow, 7 total, see
  `docs/workflow-list.md` for the trigger/schedule of each).
- **Source of truth for the _migration_:** the design scaffold in `docs/`, plus
  `open-questions.md` at the repo root (see "Open Questions" section below). Start every task by
  reading through the included project documentation under `docs/` and `open-questions.md`. The
  decisions and gaps are recorded in these documents, not in code.
- Two narrative review docs describe the intended behavior (written before this migration, by the
  original build team): `docs/Coastal - Limble Integration Review - Coupa Integration (v1.2.0).docx`
  and `docs/Coastal - Limble Integration Review - EHS Integration (v1.3.2).docx`. Both are real
  `.docx` binaries — extract text via `python3 -c "import zipfile; ..."` reading `word/document.xml`
  (Read tool cannot open them directly). Treat these as the *intended* design; the blueprint JSON is
  the *actual* implementation — verify against the JSON before trusting the docx on any specific
  behavior, since docs can drift from what shipped.
- `docs/functions.js` holds the bodies of every custom IML/JS function referenced by name in the
  blueprint mappers (e.g. `CoastalCoupaWOInstResponses`, `CoastalSiteManagerExtract`,
  `EHSLimbleLocationMapping`). Read this before porting any `function:CoastalX` call to an n8n Code
  node — this is the one place their real logic lives, not the blueprint export.

`docs/build-specs/` holds the build-ready n8n specs — one per workflow,
`<workflow>-build-spec.md`, all 7 written. Keep reverse-engineering notes and build specs
separate on purpose — do not co-mingle them. Post-build sanctioned-fix change sets are appended
as sections 8/9 of the affected spec.

Other artifacts to know about:

- `docs/test-plan/` — mock-rig test strategy, fixtures, and **`test-sequence.md`, the live test
  scoreboard**. For test status, trust `test-sequence.md` + actual n8n execution history — never
  `DEPLOYMENT.md` status lines alone; parallel sessions outdate those within hours.
- `DEPLOYMENT.md` — the pre-publish gate checklist (one section per workflow). Not a build doc.
  `DEPLOYMENT-REFERENCE-DOC.md` is the deer-valley equivalent, copied in as a model only.
- `oq-resolution-plan.md` — 2026-07-17 plan for closing the remaining open questions, grouped by
  who can answer.
- `tools/sandbox-seed/` — scripts that seed the Limble sandbox (location 98472) for tests.
- `handoffs/` — session handoff docs (`handoff-*.md`), written/consumed by the handoff/hand-in
  skills.

## Key facts that override surface impressions

- **No hidden/stale backend found (so far)**: unlike the generic template's cautionary example,
  spot-checking the blueprints did not turn up a backend that contradicts surface naming. Limble
  really is the CMMS hub, Coupa really is the procurement backend (real hostname
  `coastalwasteinc.coupahost.com`), and EHS Insight really is the safety-inspection system. Still
  verify base URL/auth for each API against the actual `http:ActionSendData` / `coupa:makeApiCall`
  modules as you go — this is a "so far, nothing found" note, not a guarantee.
- **Private/custom Make apps in play**: `fuse-limble-app:*` (e.g. `universalModule`, `listTasks`,
  `listUsers`, `listInstructions`, `updateATask`, `createATask`, `listLocations`, `listTeams`) is
  Limble's private-labeled connector under Fuse. `coupa:makeApiCall` is a custom/generic Coupa app
  module (not a stock Make.com Coupa app) — both need translation to plain **HTTP Request** nodes
  against the underlying REST APIs, since neither exists as a first-class n8n node.
- **Limble/Coupa credentials are not inlined** — referenced via datastore lookups (e.g.
  `{{2.data.client_secret}}`), not literal values in the export. The Make datastore that holds the
  actual Coupa OAuth client_id/secret (id `324`) is not itself exported to JSON — its records live
  in Make's cloud only.
- **EHS Insight is the exception — a literal secret IS embedded in the JSON.** Both
  `Coastal - Create WO From EHS Inspection (PROD).json` and
  `Coastal - Update EHS Inspection From Limble WO (PROD).json` hardcode the same `X-ApiKey` header
  value (`apikey-160448cf-4e25-4a16-a7b3-170a56743a37`) in plaintext, 9 occurrences total (a
  2026-07-02 recount of the literal key string across both EHS exports returned 9; the original
  2026-07-01 note said 8). Found 2026-07-01 via `grep` across all `*.json` for header/value fields
  matching key/token/secret/password patterns. Because the value is already in-hand, testing does
  not wait on it — but treat this key as already exposed: it must be rotated by
  Coastal before go-live, tracked in `DEPLOYMENT.md` section 0 (Credentials). Do not re-run the
  "no secrets found" spot-check claim for new blueprints without actually grepping — this file
  slipped through the original check.
- **Custom IML/JS functions** referenced in mappers (`function:CoastalX`) have their real bodies in
  `docs/functions.js` — **not** in the blueprint export. Confirmed present: `CoastalContractorExtraction`,
  `CoastalCoupaWOInstResponses`, `CoastalEHSFormFilter`, `CoastalEHSInspectFormUpdate`,
  `CoastalGetChildWONotes`, `CoastalGetInvoiceInstResponse`, `CoastalSiteManagerExtract`,
  `EHSLimbleLocationMapping`, `LimbleGrabLatestTaskComment`, `NumberToSpelledNumberConverter`. Read
  `functions.js` before porting any of these to an n8n Code node — this is where 1-indexing bugs,
  off-by-one math, and Make-bundle-vs-n8n-item mismatches get caught.
- **Error-handling is asymmetric across the 7 scenarios** — not a uniform pattern. See "Persistence
  model" below and `open-questions.md` (OQ-004, OQ-008) for exactly which workflows log errors and
  which are silent; do not assume all scenarios follow the same error-handling shape.

## Working with the blueprint exports

The files in `docs/OG-workflows/` are Make.com blueprints, one per scenario:

- `Coastal - Coupa Token Regeneration (PROD).json` — daily OAuth token refresh for Coupa.
- `Coastal - Create Requisition in Coupa (Step 1) (PROD).json` — Limble webhook (new task comment)
  → creates a Coupa PR. The largest/most complex file (844KB, deeply nested routers).
- `Coastal - Check For New PRs Ordered & Update Limble WO (Step 2) (PROD).json` — polls every 5 min
  for PR→PO conversion, updates the Limble WO.
- `Coastal - WO Completed; Update Coupa PO (Step 3) (PROD).json` — Limble webhook (task completed)
  → pushes invoice to the Coupa PO.
- `Coastal - Create WO From EHS Inspection (PROD).json` — daily EHS Insight poll → creates Limble WOs.
- `Coastal - Update EHS Inspection From Limble WO (PROD).json` — Limble webhook (task completed) →
  writes completion notes back to EHS Insight.
- `Coastal - Coupa Integration Error Log Export.json` — every 15 min, drains the shared error-log
  datastore (see "Persistence model" below) and emails a report.

Structure to know before parsing them:

- Top level: `name`, `flow` (ordered array of modules), `metadata`.
- Each module: `id`, `module` (e.g. `datastore:SearchRecord`, `http:ActionSendData`,
  `fuse-limble-app:universalModule`, `builtin:BasicRouter`), `mapper` (the data bindings, using
  `{{N.field}}` references to module #N), `parameters`, optional link `filter` (`{"a","b","o"}`
  conditions — the routing/gating logic).
- **Branching, iteration, and error handling nest recursively**: routers carry `routes[].flow[]`,
  some modules carry a nested `flow[]`, and **most modules carry an `onerror[]` chain that holds
  real logic** — error-log writes, alerting, cleanup often live there, not in the main flow. A flat
  read (or even a `flow`+`routes` walk) misses it. `jq` and `python3` are available; a recursive
  walk over `flow` → `routes[].flow` → **`onerror`** is the reliable way to see the full graph and
  every filter/mapper/handler. **Do not report "nothing writes to X" until you've done this walk —
  it is the single most common false negative in this kind of analysis.**

For large blueprints, parse structurally instead of reading top to bottom, e.g.:

```bash
python3 -c "import json; d=json.load(open('docs/OG-workflows/[file].json')); print([m['module'] for m in d['flow']])"
```

A confirmed reliable full-graph walk (flow → routes[].flow → onerror, recursively) was run once
across all 7 files during the initial analysis (2026-07-01) — its findings are recorded in
`open-questions.md`. Re-run it whenever blueprints are updated rather than trusting that snapshot.

The cross-module data model: Make passes _bundles_ down a linear flow with
Aggregator/Feeder/Repeater + roundtrip variables. n8n passes _arrays of items_. These do **not**
map node-for-node — don't assume a 1:1 node swap.

The cross-engagement translation-patterns reference is populated and lives at
`docs/module-translation-reference.md` (an identical copy sits in `../_template/`), covering
common Fuse→n8n patterns confirmed across past migrations (deer-valley, drink-pak). Consult it
as a starting point — it's advisory, not authoritative. Where it conflicts with what Coastal's
actual blueprints do, trust the blueprint.

Common Make → n8n node mappings to start from (verify each against the actual blueprint, don't
assume):

- `builtin:BasicRepeater` / `BasicAggregator` → **Loop Over Items** / aggregation
- `builtin:BasicRouter` → **Switch / IF**; `BasicFeeder` → item splitting
- `datastore:*` → see "Persistence model" below — the two datastores in this engagement map to
  two different targets, not one uniform rule
- `fuse-limble-app:*` / `coupa:makeApiCall` (custom/private apps) → **HTTP Request** against the
  underlying REST API (Limble API, Coupa API respectively)
- `http:ActionSendData` → **HTTP Request**; `util:SetVariable(s)` / `util:Switcher` → **Set / Edit
  Fields** / **Switch**
- `json:CreateJSON` / `json:TransformToJSON` → **Set** (JSON mode) or a small **Code** node
- `util:FunctionSleep` → n8n **Wait** node
- custom JS/IML functions (`function:CoastalX`) → **Code** nodes, bodies in `docs/functions.js`
  (port logic bit-for-bit; flag, don't guess, if a referenced function's source is missing)

## Persistence model (Make datastores → n8n)

Two Make datastores carry cross-run state, and they map to **different** n8n targets — do not
treat `datastore:*` as one uniform node-swap rule:

- **Datastore `324`** ("CLIENTS - API Acct Information and Key") — holds the Coupa OAuth
  client_id/secret, filtered by a `client` field (`"coastal_waste (PROD)"`). This looks like a
  **shared, multi-tenant** datastore across FM360's other clients, not Coastal-exclusive — n8n has
  no equivalent multi-tenant credential store. **Decision (see `open-questions.md` OQ-005):** do
  not replicate the shared-datastore pattern; use an **isolated n8n credential** scoped to this
  instance, populated with Coastal's Coupa client_id/secret. Read by "Coupa Token Regeneration"
  (which also writes the refreshed token back via `AddRecord`), and by "Create Requisition" /
  "Check For New PRs Ordered" / "WO Completed" (read the current token to call Coupa).
- **Datastore `326`** (Coupa error log) → n8n **Data Table**. This is a **log**, not a work queue —
  no workflow dequeues individual rows to act on them; "Coupa Integration Error Log Export" simply
  drains and reports the whole thing every 15 minutes. **Writers:** "Create Requisition in Coupa"
  (Step 1) and "WO Completed; Update Coupa PO" (Step 3) — found via the `onerror` walk, not obvious
  from a flat read. A faithful port must have both writers point at the **same** n8n Data Table —
  do not add a second error log. **Reader/drainer:** "Coupa Integration Error Log Export" does
  Search (filtered on `timestamp exists`) → email `ethan@fm360consulting.com` → `DeleteAllRecords`
  (wipes the **entire** table, not just the searched/exported rows — a race window). **Decision
  (OQ-006):** sanctioned fix — the n8n port should delete only the records actually exported in
  that run, not the whole table.
- **EHS-side and Step 2 have no equivalent error datastore** — see "Key facts" above and
  `open-questions.md` OQ-004/OQ-008 for the as-is-vs-fix decisions on each.

## Reference material

No authoritative API reference (Swagger/OpenAPI, Postman collection, or equivalent) exists in this
repo for Limble, Coupa, or EHS Insight — tracked as **OQ-009** (still open). What exists instead,
and how far to trust each system's facts:

- **Limble** — field-level facts are now **live-verified**: extensive sandbox/prod recon and raw
  API probes during the test phase (create-task contract, cursor pagination, status IDs,
  instruction writes — see the resolved OQ entries and build-spec sections 8/9). Vendor doc sites
  are JS-rendered shells (unfetchable); raw-contract questions need a live probe, not WebFetch.
- **Coupa / EHS Insight** — still reverse-engineered only, from the blueprint mappers (request
  shapes in each `http:ActionSendData` / `coupa:makeApiCall` module) and the two narrative docx
  review docs in `docs/`. Test-phase calls hit **mock rigs** whose response shapes are guessed
  from the blueprints — no live verification against either API yet, and none is coming before
  cutover: OQ-039/OQ-028 (both resolved) settled that real shapes get examined at go-live under
  the C4 first-shepherd watch (`docs/test-plan/test-sequence.md` Phase C), with Fuse
  disabled-not-deleted as the rollback lever.

## Constraints for this work (from the project owner)

- **Migration posture:** 1:1 + a sanctioned list of fixes (see `open-questions.md` OQ-001). Fixes
  must be individually proposed and approved — no unilateral improvements beyond the sanctioned
  list. The list has grown far past the initial OQ-005/OQ-006 — the authoritative record is the
  resolved entries in `open-questions.md`; check there, not this file. Do not "improve" beyond
  the sanctioned list without asking — this is the single most common scope-creep failure mode
  in these engagements.
- **Decomposition:** 7 Make scenarios → 7 n8n workflows, 1:1, same trigger boundaries
  (webhook/schedule) preserved exactly (OQ-002).
- **API access boundaries (OQ-003, relaxed in stages — its addenda in `open-questions.md` are
  the current line):** read-only Limble calls are sanctioned, and live writes against the Limble
  **sandbox** (test location 98472) are sanctioned for test-phase work. No live calls to Coupa
  or EHS Insight (mock rigs only), and no writes to Coastal's Limble **prod**.
- **Target n8n workflow IDs (OQ-007 resolved):** all 7 assigned and built — the ID table lives
  in OQ-007's entry in `open-questions.md`. Write only to those IDs.
- **Secrets:** Limble/Coupa credentials are datastore-referenced, not inlined — but the EHS Insight
  API key IS hardcoded in plaintext in both EHS blueprint exports (see "Key facts" above). Treat it
  as exposed; get it rotated before go-live. Re-verify (actually grep, don't assume) as new files
  are added. Coastal's real Coupa client_id/secret and the rotated EHS API key are not to be written
  into any repo file; they belong only in n8n's credential store (OQ-005).

## Tooling

- An **n8n MCP server** is connected and **writes are authorized** — the original read-only rule
  belonged to OQ-003's design phase and is superseded; all 7 workflows are built, and
  owner-approved sanctioned fixes get applied directly via the write tools. Standing limits:
  **never activate a workflow without asking the owner**; ~100 MCP calls/day quota; and the
  server is **multi-instance with a binding shared across parallel sessions** — run
  `n8n_instances mode=list` before any call and confirm you are pointed at the right account,
  then never switch instances without checking whether another session is mid-use.
  **Match on the URL, not the name.** As of the **2026-07-30 owner ruling (OQ-048)** there are
  TWO Coastal-relevant hosts, with different roles:
  - **`https://fm360.n8n.fm360consulting.com`** — where all 7 workflows were built and tested
    (Phase A). After the OQ-048 port it remains the build/test sandbox + mock rigs. Display
    name unstable: has appeared as `FM360_Account` and `FM360` (renamed, new instance ID, by an
    MCP reconnect 2026-07-27) — same host either way.
  - **`https://coastal.n8n.fm360consulting.com`** (display name `Coastal-Waste`) — the **go-live
    target**. **Port EXECUTED 2026-08-01**: all 7 workflows exist here (inactive, cutover
    config — real hosts, placeholder credentials), plus 3 data tables and 4 placeholder
    credentials the owner still must populate. The authoritative new-ID table is
    `docs/oq-048-port-ledger.md`; OQ-048 stays open until credentials are populated.
    CREATE-verification rule learned the hard way: a create is verified only by a workflow
    LIST on the intended instance — ID-addressed read-backs succeed cross-instance
    (Step 1 initially strayed onto DrinkPak via a binding flip; deleted + redone).

  Other accounts are separate clients with their own names and URLs (e.g. `DrinkPak` →
  `https://drinkpak.n8n.fm360consulting.com`), so a name check alone can pass while you are on
  the wrong client, or fail on a rename that changed nothing. Verify the host.
- Two **Limble MCP servers** are connected, both read-only: `limble-mcp-CLIENT` → Coastal prod,
  `limble-mcp-SANDBOX` → the FM 360 sandbox (test location 98472). Confirm which instance a
  server actually points at (`get_current_customer_info`) before trusting or recording recon
  facts. Known blind spot: the MCP `get_statuses` tool returns only a subset — verify statuses
  via direct API or the UI, never the MCP tool.
- No Coupa or EHS Insight MCP server is connected — facts for those systems come from the
  blueprint exports, `docs/functions.js`, the two docx review docs, and the mock Coupa/EHS test
  rigs (Mock Coupa `F05TiUurpc2kqxe0`, Mock EHS `EBIzCJ0XJaJ5jUpp`, seeder `qyMChP0DKfI04r4a`).
- **A config round-trip read is not execution proof.** Reading a node back after an MCP write
  confirms what n8n stored, and an API-contract probe confirms what the vendor accepts — neither
  proves the node runs. The OQ-018 pagination fix passed both checks and still threw on its
  first execution (2026-07-26). Run the node once before calling any change verified.

## Open Questions

There is an open questions file tracking unresolved questions, blockers, and pending
decisions for this project. Review it when making decisions or before starting new work.

File: open-questions.md
