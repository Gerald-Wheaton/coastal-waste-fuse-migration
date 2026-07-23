# Step 1 test rig — sandbox seeding (OQ-028)

Seeds Gerald's Limble sandbox for testing "Coastal - Create Requisition in Coupa (Step 1)"
against the mock Coupa API. Design: `docs/build-specs/coupa-create-requisition-step1-build-spec.md`
§7 and `open-questions.md` OQ-028.

## Order of operations

1. `python3 tools/sandbox-seed/seed.py` — verifies location 98472, attempts statuses + Site
   Manager user via API, prints UI checklist for whatever the API refuses.
2. Create the **template** in the sandbox UI (below) — no API endpoint for this.
3. `python3 tools/sandbox-seed/seed.py --template-id <ID>` — spawns the 9 scenario tasks,
   sets status, posts trigger comments, verifies instruction texts/order.
4. Fill instruction responses + quote upload per the scenario table (UI).
5. Fire: `./tools/sandbox-seed/fire.sh <taskID> <step1-webhook-url>`.
6. Inspect: n8n execution log, "Coastal - Coupa Mock Capture (TEST)" data table,
   `seed.py --verify <taskID>`.

Auth comes from the repo `.env` (`ENCODED_AUTH`, Basic). Never committed, never printed.

## Template (UI, once)

Name: `Main WO Template (Sandbox)` — any name works; Step 1 never reads the template name.
17 instructions to mirror prod template 965's shape (verified live 2026-07-06 via Limble MCP);
only these 6 are load-bearing, the other 11 are filler. Texts must be VERBATIM (Step 1 matches
on exact text):

| Pos | Instruction text | Type |
|---|---|---|
| any | `Describe the Work that Needs to be Done` | text response |
| any | `Is this a Capex Work Order?` | dropdown: `Yes`, `No` |
| any | `Select the Contractor who will Complete the Work` | dropdown: `Sandbox Contractor LLC`, `A & B Services`, `FAIL-SUPPLIER Corp` |
| any | `Insert Estimated Dollar Amount for Work (Amount from Quote, if Applicable). NOTE: Set to $500 if Estimate is Less than $500` | number |
| **5** | `Upload the Contractor's Quote Here for Coupa` | **file upload — must be the 5th instruction (1-indexed), positional read** |
| any | `Select Which Type of Capex Work This Is` | dropdown, real prod options: `Building Improvement`, `Construction Projects`, `Furniture and Fixtures`, `Land Improvement`, `MRF Equipment`, `Shop Equipment` |

Note: "Other Operating" is NOT a dropdown option — it is the code's fallback when the
capex-type question is left unanswered (commodity defaults to "Facility Repairs", accSeg6 to
"Other Operating"). Leave it blank on one scenario task to exercise that branch.

Filler 7-17, real prod texts (flat, order among fillers irrelevant): `Quoting Process`,
`Will this Work Cost More than $500?` (radio Yes/No), `Generate WO for Contractor to Evaluate
and Quote the Work`, `Set the Status of this WO to "PO Create", Check this Box, and Exit this
WO. Wait Until the PO has been Approved (i.e. Status = "PO Approved") Before Continuing in
this WO.` (checkbox), `Perform Work Process`, `Generate WO for Contractor to Perform the
Work`, `Check the Box if the Work has been Verified Completed` (checkbox), `Check the Box when
Contractor's Invoice is Uploaded in Below Instruction` (checkbox), `Upload Invoice Here`
(file), `Capex Work Type`, `Contractor Select`.

## Scenario table (instruction responses, UI)

| Task | Capex | Contractor | Amount | Quote file | Expected |
|---|---|---|---|---|---|
| s1-happy-gt500-capex | Yes | Sandbox Contractor LLC | 1200 | attach any PDF | full route 1: create-req, attach, status→PO Requested, meta1=424242, SM notify |
| s2-le500 | Yes | Sandbox Contractor LLC | 400 | none | route 2, no attachment call |
| s3-capex-no | No | Sandbox Contractor LLC | 1200 | any | GL 612200 in captured account query (s1 shows 160999) |
| s4-ampersand-contractor | Yes | A & B Services | 1200 | any | supplier query captures `A %26 B Services` |
| s5-fail-supplier | Yes | FAIL-SUPPLIER Corp | 1200 | any | supplier-missing path: comments only, NO error-log row |
| s6a/b/c-fail-* | Yes | Sandbox Contractor LLC | 1200 | any | error paths A/B/C: error-log row + admin comment (set failMode first, see below) |
| s7-fail-createreq | Yes | Sandbox Contractor LLC | 1200 | any | create-req onerror: error-log row + admin comment (failMode=createreq) |
| re-fire s1 | — | — | — | — | idempotency guard blocks duplicate |

## Error injection (failMode)

The users/addresses lookups carry only fixed inputs (site-manager email, location name), so
those failures can't ride on task data. Instead the mock reads a config row before every
response. Data table **"Coastal - Coupa Mock Config (TEST)"** (`bZ78rLHH8sJfDbtN`), row
`key=default`:

| failMode | Effect |
|---|---|
| `` (empty) | all routes answer normally |
| `user` | GET users returns `[]` (error path A) |
| `addr` | GET addresses returns `[]` (error path B) |
| `acct` | GET accounts returns `[]` (error path C) |
| `createreq` | POST create-requisition returns 500 (onerror path) |

Set the value in the n8n UI (or via MCP) before firing scenarios 6a/6b/6c/7, reset to empty
after. Supplier failure needs no toggle: any queried contractor name containing
`FAIL-SUPPLIER` returns `[]`.

## Deployed rig (created 2026-07-05 — TORN DOWN 2026-07-06, IDs below are historical)

Test phase closed: all 8 scenarios passed (see OQ-028 results table). Mock workflow + both
TEST tables deleted, Step 1 URLs restored to real Coupa, dummy token + test error rows purged,
Step 1 deactivated pending go-ahead. Limble sandbox fixtures left in place.

| Piece | ID / URL |
|---|---|
| Mock workflow "Coastal - Mock Coupa API (TEST)" | `mSiLCsvOVdiSWOZP` (ACTIVE) |
| Mock base URL (swapped into Step 1's 6 Coupa nodes) | `https://fm360.n8n.fm360consulting.com/webhook/mock-coupa/api/...` |
| Capture table "Coastal - Coupa Mock Capture (TEST)" | `u7iAudMydWyhl7BJ` |
| Config table "Coastal - Coupa Mock Config (TEST)" | `bZ78rLHH8sJfDbtN` |
| Dummy token row in "Coastal - Coupa OAuth Token" | row id 2, `client=coastal_waste`, token `MOCK-TOKEN-OQ028-DELETE-AT-CUTOVER` |
| Step 1 webhook (fire.sh default) | `https://fm360.n8n.fm360consulting.com/webhook/coastal-coupa-create-requisition-step1` |

## Statuses (UI, if API create refused)

Instance-wide: `PO Create`, `PO Requested`. Exact spelling — Step 1 looks both up by name
(`%...%` wildcard). This doubles as the OQ-025 rehearsal; prod spelling still needs its own
UI check before cutover.

## Teardown

Tracked in OQ-028 — do not delete pieces ad hoc; the cutover checklist covers mock workflow,
capture table, dummy token row, base-URL revert, credential swap, error-log purge.
