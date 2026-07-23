# A6 sandbox seed record — EHS Create WO fixtures (2026-07-20)

Teardown ledger for everything created in the Limble **sandbox instance** for the A6 test suite
(ehs-test-plan section 5.1). Owner authorized API seeding 2026-07-20 with the sandbox Basic
credential. **Every object below must be removed after deployment** (A8 wrap-up / post-cutover
teardown), except where marked.

Companion staging (n8n side, tracked in DEPLOYMENT.md section 5, not here): 5 EHS node URLs →
mock host, `templateID: "842"` → `"4189"` on `Create Deficiency Task` — both revert at cutover.

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
| 602733 | EHS Approver Assignee | 98872 Coastal 10 |
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

## A7 fixtures (EHS Update suite, seeded 2026-07-21) — `DELETE /v2/tasks/{id}` at teardown

Skeletons created via API (spec-plan IDs 9001/9101/9102/9002/9003 → real sandbox IDs):

| taskID | role | notes |
| --- | --- | --- |
| 4198 | U1 parent | `@EHSWO;` desc + `meta1 = EHS-INSP-UPD-1` set via API; needs owner UI completion (see checklist) |
| 4199 | U1 child 1 | needs owner UI completion w/ exact note |
| 4200 | U1 child 2 | needs owner UI completion w/ exact note |
| 4201 | U3 non-EHS | complete as-is (no `@EHSWO;`, no meta1) — no owner action needed |
| 4202 | U4 parent (optional) | `@EHSWO;` + meta1, zero child links — owner completion optional |

(A probe task 4197 + probe instructions 14941/14942 were created and deleted same-session — already gone.)

**Owner UI checklist before A7 runs** (none of these fields are writable via the public API —
`completionNotes`, `dateCompleted`, and instruction `meta.associatedTask` all return
"`X` is not allowed"):

1. On parent **4198**: link two child WOs via the Limble UI child-work-order feature so the
   parent's instructions carry `meta.associatedTask`. If the UI spawns new child tasks instead of
   linking existing ones, use those, delete 4199/4200, and record the new IDs here.
2. Complete child 1 with completion notes exactly: `Child 1: guardrail welded.`
3. Complete child 2 with completion notes exactly: `Child 2: lighting fixed.`
4. Complete parent 4198 with completion notes exactly: `Parent WO: replaced handrail bolts.`
5. *(optional, U4)* Complete 4202 with any note.

After step 1, verify `GET /v2/tasks/4198/instructions` returns `meta.associatedTask` — sandbox
API-created instructions carry **no `meta` key at all**, which is also an open A7 run risk: the
workflow's `Has Child WO?` filter reads `$json.meta.associatedTask` and may error (not just
filter) on meta-less instructions.

## API contracts discovered while seeding (OQ-009 additions)

- `POST /v2/regions` — body `{name, parentRegionID}`; **parentRegionID is required in practice**
  (omitting it → opaque 400/500). Returns `{"regionID":"<id>"}`.
- `DELETE /v2/regions/{id}` — 200.
- `PATCH /v2/locations/{id}` — `{regionID}` accepted, 200.
- `POST /v2/teams` — body `{name, locationID}`. Returns `{"teamID":"<id>"}`.
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
