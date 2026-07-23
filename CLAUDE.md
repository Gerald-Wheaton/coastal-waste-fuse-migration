# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

This is **not a software codebase** — there is no build system, package manager, or test suite. Do
not invent `npm`/`bun`/`make` commands; none apply.

It is a **migration analysis & design project**: porting **Coastal Waste** (referred to as "Coastal"
throughout workflow names and docs)'s **Limble (CMMS) ⇄ Coupa (procurement)** and **Limble ⇄ EHS
Insight (safety inspections)** integrations off **Fuse** (Coastal's white-labeled **Make.com /
Integromat** platform, using private/custom Make apps — see "Working with the blueprint exports"
below) onto **n8n**. There are two related integrations, seven scenarios total. The work here is
reverse-engineering the existing Make.com scenarios and producing a build-ready design before
touching n8n.

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

No `docs/workflows/` vs. `docs/build-specs/` split exists yet. When flow-analysis docs and
build-ready n8n specs start getting written, keep them separate on purpose — do not co-mingle
reverse-engineering notes with build specs. Naming convention: `<workflow>-build-spec.md`.

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
  Coastal before go-live, tracked in `DEPLOYMENT.md` §0 (Credentials). Do not re-run the
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

A confirmed reliable full-graph walk (flow → routes[].flow → onerror, recursively) has already been
run once across all 7 files this session — see `open-questions.md` for what it found. Re-run it
whenever blueprints are updated rather than trusting this snapshot.

The cross-module data model: Make passes _bundles_ down a linear flow with
Aggregator/Feeder/Repeater + roundtrip variables. n8n passes _arrays of items_. These do **not**
map node-for-node — document the translation rules as you discover them (e.g. a
`docs/01-module-translation.md`), don't assume a 1:1 node swap.

A shared, cross-engagement translation-patterns reference is planned at
`../fuse-migrations/_template/module-translation-reference.md` (currently a placeholder, not yet
populated), covering common Fuse→n8n patterns pulled from past *completed* migrations. Once
populated, consult it as a starting point — it's advisory, not authoritative. Where it conflicts
with what Coastal's actual blueprints do, trust the blueprint.

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

No authoritative API reference material (Swagger/OpenAPI, Postman collection, or equivalent) has
been located in this repo for Limble, Coupa, or EHS Insight — tracked as **OQ-009** in
`open-questions.md`. The only material found so far:

- `docs/Coastal - Limble Integration Review - Coupa Integration (v1.2.0).docx` — narrative design
  doc (not an API reference), describes intended Coupa PR/PO field mapping (Account segments:
  entity/location/line-of-business/GLAccount/department/commodity).
- `docs/Coastal - Limble Integration Review - EHS Integration (v1.3.2).docx` — narrative design doc
  for the EHS side.
- The blueprint JSONs themselves are the closest thing to a live API reference right now — actual
  request shapes are visible in each `http:ActionSendData` / `coupa:makeApiCall` module's `mapper`.

Until OQ-009 resolves, treat field-level facts (e.g. exact Coupa Account segment codes, Limble
instruction schema) as reverse-engineered from the blueprint mappers and docx docs only — not
independently verified against an API spec.

## Constraints for this work (from the project owner)

- **Migration posture:** 1:1 + a sanctioned list of fixes (see `open-questions.md` OQ-001). Fixes
  must be individually proposed and approved — no unilateral improvements beyond the sanctioned
  list. Sanctioned so far: OQ-005 (isolated n8n credential instead of shared datastore), OQ-006
  (fix the Error Log Export delete-all race). Do not "improve" beyond the sanctioned list without
  asking — this is the single most common scope-creep failure mode in these engagements.
- **Decomposition:** 7 Make scenarios → 7 n8n workflows, 1:1, same trigger boundaries
  (webhook/schedule) preserved exactly (OQ-002).
- **API access boundaries:** this phase is **design/spec only** — no live API calls against
  Limble, Coupa, or EHS Insight (OQ-003).
- **Target n8n workflow IDs:** none assigned yet — **blocked**, tracked as **OQ-007**. Get one per
  workflow from the owner as each is built; write only to the named ID. Track superseded/old IDs
  explicitly so they don't get reused by accident.
- **Secrets:** Limble/Coupa credentials are datastore-referenced, not inlined — but the EHS Insight
  API key IS hardcoded in plaintext in both EHS blueprint exports (see "Key facts" above). Treat it
  as exposed; get it rotated before go-live. Re-verify (actually grep, don't assume) as new files
  are added. Coastal's real Coupa client_id/secret and the rotated EHS API key are not to be written
  into any repo file; they belong only in n8n's credential store (OQ-005).

## Tooling

- An **n8n MCP server** is connected. **Current authorization (OQ-003):** read-only use only —
  `search_nodes`, `get_node`, `validate_workflow` etc. to ground specs in real node schemas. Do
  **not** use `n8n_create_workflow` / write tools yet — the target n8n workspace is still being
  built out by the owner. Do not proactively look into the n8n instance until asked.
- No Limble, Coupa, or EHS Insight MCP server is connected. All source-system facts must currently
  come from the blueprint exports, `docs/functions.js`, and the two docx review docs.

## Open Questions

There is an open questions file tracking unresolved questions, blockers, and pending
decisions for this project. Review it when making decisions or before starting new work.

File: open-questions.md
