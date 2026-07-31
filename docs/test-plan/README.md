# Test Plan — Coastal Fuse→n8n Migration

Test strategy and data for exercising all **7 migrated n8n workflows without touching the live
Coupa or EHS Insight APIs**. Coupa and EHS are **mocked** (each as one n8n webhook workflow that
returns canned responses and captures inbound payloads). Limble is the one system we may exercise
for real, against **Gerald's Limble sandbox** — not production.

**Status (2026-07-26): the write/test phase has been executed.** Owner greenlit writes 2026-07-09
(OQ-003 addendum; n8n writes and live Limble-sandbox writes are sanctioned). Mocks were deployed,
the sandbox seeded, and **Phase A suites A1–A7 have all passed** — see `test-sequence.md`, the
**live execution scoreboard and single source of test status** (this README is orientation and
design record only; do not read status from it). Remaining: A8 wrap-up gates, Phase B cutover
mechanics, Phase C live observations. Node/credential swaps made for the test window are tracked
in `DEPLOYMENT.md`'s revert ledger.

## Documents

| File | Scope |
| --- | --- |
| `test-sequence.md` | **Execution-order master checklist** — remaining test grind sequenced (Phase A pre-go-live mock/sandbox → Phase B cutover reverts → Phase C live-only observations) |
| `coupa-test-plan.md` | Token Regen, Step 1, Step 2, Step 3, Error Log Export — mock Coupa API (11 endpoints), scenarios, assertions |
| `ehs-test-plan.md` | Create WO From EHS Inspection, Update EHS Inspection From Limble WO — mock EHS Insight API (6 endpoints), scenarios, assertions |
| `limble-sandbox-fixtures.md` | Cross-cutting: the consolidated minimal Limble sandbox fixture set for all 7, plus the seeding plan |
| `fixtures/coupa/` | Canned mock responses, failMode config, data-table seed rows, webhook payloads |
| `fixtures/ehs/` | Canned mock EHS responses (7 payloads incl. multi-site/multi-question inspection) |
| `seed/seed_ext.py`, `seed/fire.sh` | Extended sandbox seeder design + generic webhook trigger helper (extend `tools/sandbox-seed/`) |
| `generated/mock-coupa.workflow.json` | Importable n8n definition of the Mock Coupa API (TEST) workflow — 27 nodes, placeholders only |
| `generated/mock-ehs.workflow.json` | Importable n8n definition of the Mock EHS Insight API (TEST) workflow — 46 nodes, placeholders only |

## Test architecture

```
        ┌─────────────────────────┐         ┌──────────────────────────────┐
        │  Limble SANDBOX (real)  │         │  n8n instance (FM360_Account) │
        │  loc 98472 "Coastal 99" │◄───────►│  7 built workflows (inactive) │
        │  seeded fixtures        │  reads/ │                               │
        └─────────────────────────┘  writes │  Coupa nodes ─┐  EHS nodes ─┐ │
                                             │   (URL swap)  ▼   (URL swap)▼ │
                                             │  ┌─────────────┐ ┌──────────┐│
                                             │  │Mock Coupa   │ │Mock EHS  ││
                                             │  │API (TEST)   │ │API (TEST)││
                                             │  │+capture tbl │ │+capture  ││
                                             │  │+config tbl  │ │ tbl      ││
                                             │  └─────────────┘ └──────────┘│
                                             └──────────────────────────────┘
```

- **Mock = n8n webhook workflow.** Coupa/EHS HTTP nodes in the real workflows are host-swapped to
  the mock's base URL for the test window, then reverted at teardown (the proven OQ-028 approach).
- **Capture tables** record every inbound payload so we assert on request *shape/content*, not just
  on a 200. Error branches are driven by a **failMode config row**, not by request data.
- **Deterministic IDs are a hard contract** between the mock and the Limble fixtures: the mock
  always returns **requisition `424242`** and **PO `555001`** (n8n can't match mid-path route
  params, so routes are literal — an OQ-028 finding). Therefore the seeded Limble tasks must carry
  **`meta1=424242`** (Step 2 input) and **`meta2=555001`** (Step 3 input) to line up.

## Cross-cutting findings the agents surfaced (all since addressed — historical record)

1. **EHS loop tag mismatch — RESOLVED, then REVERSED; both sides now `@EHS;` (OQ-038).** "Create WO
   From EHS Inspection" stamped the WO description with **`@EHS;`** while "Update EHS Inspection
   From Limble WO" filtered on **`@EHSWO;`** — disjoint literals, so Create's output could never
   trigger Update. A **pre-existing defect in the source Make blueprints** (`@EHS;` ×3 vs
   `@EHSWO;` ×1), faithfully ported. The first fix (owner-approved 2026-07-08, applied live
   2026-07-20) corrected **Create → `@EHSWO;`** per the review docx. **Ethan reversed that on
   2026-07-27:** Create keeps `@EHS;` and **Update's gate moved to `@EHS;`**, because prod holds
   10 EHS WOs all tagged `@EHS;` with **5 still open** that a `@EHSWO;` gate would orphan at
   cutover. Both live nodes changed (`isLUx7cUjkmKggD2` n21, `8JvtesynrYtZbw7U` n04) and read
   back. A7 U1 re-validated post-flip (exec 127376); **A6's description assertion is still owed a
   run.** The A6/A7 passes that predate 2026-07-27 assert the old literal.
2. **Step 2 pointed at the PROD Limble credential — swapped to sandbox for test.** Step 2
   (`WYJyHdQGcdeD8wEr`) used "Coastal Waste Limble" (`qn6u8jEK085DoHT8`) on both Limble nodes, unlike
   Step 1/3 which use the sandbox credential. Running it as-built would have **read and PATCHed real
   production tasks.** Owner-confirmed 2026-07-08; swap applied for the test window (A1 suite ran
   against the sandbox). Revert at cutover — tracked in `DEPLOYMENT.md` and Phase B of
   `test-sequence.md`.
3. **EHS-Create locations didn't match the sandbox — resolved by seeding.** The mock EHS inspections
   map (via `EHSLimbleLocationMapping`) to Coastal 10/12/23/24/30/"Corporate Office" — none was the
   sandbox's original sole location "Coastal 99" (98472). Resolved 2026-07-20: sandbox
   locations/regions/teams seeded (owner-created locations + API-seeded rest); teardown ledger in
   `sandbox-seed-record-a6.md`.
4. **EHS-Create credential was a placeholder — resolved.** The 5 EHS nodes on `isLUx7cUjkmKggD2`
   carried `__EHS_INSIGHT_CREDENTIAL_ID__`; credential `ZEf4C1rpYSbBgLbX` (same as Update) attached
   during A6 staging 2026-07-20.
5. **Step 2 error paths were untestable — RESOLVED (OQ-029, 2026-07-09).** The OQ-008 error-log
   subgraph was built into Step 2 (now 26 nodes); the mock's `getreq`/`getpo` failModes were then
   exercised and passed in A1 (S2-err-getreq / S2-err-getpo).
6. **Child-task fetch shape was the top EHS risk — confirmed real, fixed in A7.** Update's Code node
   read `childTasks[i].completionNotes` flat, but the actual fetch shape differed. A7 scenario U4's
   first run hit exactly this; sanctioned rewire applied 2026-07-25 (`Get Child Task` now reads
   `$json.childLinks`), re-run passed with no `undefined` write-back. Real-Limble shape remains a
   Phase C watch item (OQ-009 still open).
7. **No Limble access (session-relative, 2026-07-08 clone) — since restored.** Both Limble MCP
   servers (`limble-mcp-CLIENT` prod, `limble-mcp-SANDBOX`) are connected and local `.env`
   credentials are in place; sandbox seeding and live-sandbox tests ran throughout Phase A.
8. **Mocks rebuilt and deployed.** The OQ-028 Coupa mock (torn down 2026-07-06) and the new EHS mock
   were both deployed and used across A1–A7. OQ-028's cutover **teardown checklist is still open**,
   as is its core caveat: mock response shapes are reverse-engineered guesses — passing the mock
   suite proves our logic, not the real APIs.

## Write/test phase — permission checklist (EXECUTED — kept as historical record)

> **Status.** Owner greenlit 2026-07-09 (OQ-003 addendum) and the checklist below was executed
> across 2026-07-09 → 2026-07-25; Phase A suites A1–A7 all passed. Per-scenario results and the
> remaining grind (A8 wrap-up, Phase B cutover, Phase C live watches) live in `test-sequence.md`;
> every swap's revert row lives in `DEPLOYMENT.md`. The standing guardrail held throughout and
> still applies to any further sandbox work: all Limble writes target the FM360 Sandbox via
> credential **"Gerald Limble Sandbox"**, every seeded object under location **`98472`
> "Coastal 99 - Sandbox Test"** — never prod. One deviation from the original plan: the EHS-Create
> location mismatch was resolved by **seeding sandbox locations** (finding 3 above), not Option A.

**n8n (OQ-003 addendum: writes authorized for the test window):**
- Create **"Coastal - Mock Coupa API (TEST)"** workflow (11 endpoints) — needs a workflow ID (OQ-007).
- Create **"Coastal - Mock EHS Insight API (TEST)"** workflow (6 endpoints) — needs a workflow ID.
- *(Optional, recommended)* Create **"Coastal - Seed Limble Sandbox (TEST)"** workflow to seed the
  sandbox via the **"Gerald Limble Sandbox"** credential (all creates pinned to location `98472`) —
  needs a workflow ID; the API-only alternative to manual UI seeding when there's no local `.env`.
- Create **3 Data Tables**: Coupa capture, Coupa failMode config, EHS capture.
- Seed rows: 1 dummy token row (`MOCK-TOKEN-COUPA`) into `QAj62weJaWmRBJ76`; error-log seed rows
  (9001/9002 + a mid-run 9003 to prove the OQ-006 partial-delete) into `6GbR5Rxezl7hqk9i`; the
  failMode config row.
- Host-swap **13 Coupa nodes** (Token ×1, Step 1 ×6, Step 2 ×2, Step 3 ×4) and **7 EHS nodes** to
  the mock base URLs; resolve EHS-Create's placeholder credential; swap Step 2's Limble credential
  to sandbox.

**Limble sandbox (real writes — FM360 Sandbox only, credential "Gerald Limble Sandbox", everything
under location `98472`):**
- Seed the consolidated minimal fixture set (`limble-sandbox-fixtures.md` section 4) via any of: an **n8n
  seeder workflow** using the "Gerald Limble Sandbox" credential (recommended — no local secret
  needed); the local `seed.py`/`seed_ext.py` if `.env`/MCP is restored; or the **Limble UI** for the
  API-uncreatable fixtures (templates, file uploads, region assignment, child-WO links). Whichever
  path, every created object is pinned to location `98472`.

**Run + observe:**
- Fire each workflow (webhook curl for Step 1/3/EHS-Update; manual execution for the scheduled
  Token/Step 2/EHS-Create/Error Log Export); assert against capture tables, Limble writes, and
  data-table end state. Emails are observed via the dev-routed Ionos recipient gerald@ (OQ-010).

**Teardown** (per each plan's checklist): revert all node URLs, delete mock workflows + capture/
config tables, purge dummy token + test error rows, revert Step 2 credential, deactivate.
