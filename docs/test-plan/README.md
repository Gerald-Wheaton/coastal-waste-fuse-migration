# Test Plan — Coastal Fuse→n8n Migration (design only)

Test strategy and data for exercising all **7 migrated n8n workflows without touching the live
Coupa or EHS Insight APIs**. Coupa and EHS are **mocked** (each as one n8n webhook workflow that
returns canned responses and captures inbound payloads). Limble is the one system we may exercise
for real, against **Gerald's Limble sandbox** — not production.

This phase is **design + data only**. Nothing here has been written to the n8n instance or the
Limble sandbox yet. The "Write/test phase" section below is the checklist that needs owner
sign-off before anything is deployed or run (per `open-questions.md` OQ-003, which is read-only
today).

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

## Cross-cutting findings the agents surfaced (need owner attention)

1. **EHS loop tag mismatch — RESOLVED (OQ-038).** "Create WO From EHS Inspection" stamped the WO
   description with **`@EHS;`** while "Update EHS Inspection From Limble WO" filters on **`@EHSWO;`**
   — disjoint literals, so Create's output could never trigger Update. It is a **pre-existing defect
   in the source Make blueprints** (`@EHS;` ×3 vs `@EHSWO;` ×1), faithfully ported. The EHS review
   docx specifies `@EHSWO;` on both sides, so the sanctioned fix (owner-approved 2026-07-08) corrects
   **Create → `@EHSWO;`**. Applied in the specs/test-plan; the one-line live edit to
   `isLUx7cUjkmKggD2` is **queued for the write phase** (n8n writes on hold).
2. **Step 2 points at the PROD Limble credential — DECISION: swap to sandbox for test.** Step 2
   (`WYJyHdQGcdeD8wEr`) uses "Coastal Waste Limble" (`qn6u8jEK085DoHT8`) on both Limble nodes, unlike
   Step 1/3 which use the sandbox credential. Running it as-built would **read and PATCH real
   production tasks.** Owner-confirmed 2026-07-08: swap Step 2's Limble credential to the sandbox for
   the test window and revert at teardown.
3. **EHS-Create locations don't match the sandbox.** The mock EHS inspections map (via
   `EHSLimbleLocationMapping`) to Coastal 10/12/23/24/30/"Corporate Office" — none is the sandbox's
   only location "Coastal 99" (98472). EHS-Create has no error handling, so a `listLocations` miss
   halts the run. Two options in `limble-sandbox-fixtures.md` §4a: **(A)** retarget one mock
   inspection to Coastal 99 and drop the rest before `listLocations` (minimal, recommended), or
   **(B)** seed all 6 locations in the sandbox.
4. **EHS-Create credential is a placeholder.** The 5 EHS nodes on `isLUx7cUjkmKggD2` carry
   `__EHS_INSIGHT_CREDENTIAL_ID__`; Update uses a real one (`ZEf4C1rpYSbBgLbX`). Must be resolved
   before EHS-Create can run (mocked auth still needs a credential object attached).
5. **Step 2 error paths are untestable (OQ-029).** No error subgraph is built, so the mock's
   `getreq`/`getpo` failModes have nothing to assert against — a documented coverage hole, not a test.
6. **Child-task fetch shape is the top EHS risk (OQ-009).** Update's built Code node reads
   `childTasks[i].completionNotes` flat, but Make read `body[0].completionNotes`. If Limble returns
   `{body:[…]}`, the write-back writes literal `"undefined"`. First thing to watch in the Update test.
7. **No Limble access this session.** `.env` (`ENCODED_AUTH`) and `.mcp.json` are gitignored and
   absent from this fresh clone — no live Limble calls were possible. Sandbox seeding/testing is
   blocked until the owner restores the sandbox credential and/or reconnects the Limble MCP.
8. **Mocks must be (re)built.** The OQ-028 Coupa mock was torn down 2026-07-06; the EHS mock never
   existed. Both are designed here but not deployed.

## Write/test phase — permission checklist (nothing below done yet)

> **Owner decisions — 2026-07-08.** The whole section below is **on HOLD (design-only)**: do not
> deploy mocks, seed n8n, or run any workflow yet. When greenlit: (a) Limble sandbox fixtures will
> be seeded either **manually by the owner** from the `limble-sandbox-fixtures.md` §4 checklist or
> via a **dedicated n8n seeder workflow** (recommended — uses the stored "Gerald Limble Sandbox"
> credential, so no local `.env`/MCP needed). **Guardrail:** all seeding targets the FM360 Sandbox
> via credential **"Gerald Limble Sandbox"**, and every seeded object lives under location **`98472`
> "Coastal 99 - Sandbox Test"** — never prod, never another location; (b) **Step 2's Limble
> credential is swapped to the sandbox** for the test window, reverted at teardown; (c) the
> **EHS tag fix (OQ-038)** is applied to `isLUx7cUjkmKggD2` before any real Create→Update loop test;
> (d) EHS-Create location mismatch defaults to **Option A** (retarget one mock inspection to Coastal
> 99) unless the owner directs otherwise.

**n8n (extends OQ-003 read-only → write for the test window):**
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
- Seed the consolidated minimal fixture set (`limble-sandbox-fixtures.md` §4) via any of: an **n8n
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
