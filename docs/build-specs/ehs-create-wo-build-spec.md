# Build Spec — Coastal - Create WO From EHS Inspection (PROD)

Status: **built + as-deployed corrections applied** (spec written 2026-07-08; built 2026-07-08
to n8n workflow ID `isLUx7cUjkmKggD2`, "Create WO from EHS Inspection", deployed **inactive**;
live-API corrections applied 2026-07-20 — see **§12**, which supersedes the guessed
`updateAnInstruction`/image handling in §3/§6/§7 below). 30 nodes, validates clean.

Source blueprint: `docs/OG-workflows/Coastal - Create WO From EHS Inspection (PROD).json`
(full flow → routes → onerror walk run 2026-07-08: **0 onerror chains anywhere** — the source
has no error handling, consistent with OQ-004). Custom functions used:
`CoastalEHSFormFilter`, `EHSLimbleLocationMapping` (bodies in `docs/functions.js`).

---

## 1. Purpose

Once daily, pull EHS Insight audit inspections from the last 24h, keep only completed
"Facility Inspection Checklist" inspections (latest per site), and for each site whose latest
inspection has a deficient (unacceptable) answer, create a Limble work order assigned to that
location's EHS approver team, with the deficiency text (and image, if attached) written into
the task's first instruction.

## 2. Trigger

| | Source (Make) | n8n target |
| --- | --- | --- |
| Type | Scheduled, daily @ 4:00 PM MST per `docs/workflow-list.md` | **Schedule Trigger**, Cron `0 16 * * *` |
| Timezone | "MST" per workflow-list — not verifiable from the export (schedules live in Make's scenario settings) | **`America/Denver`** (DST-aware), per OQ-011. Still subject to OQ-014 (confirm real TZ with Coastal). |

## 3. Source flow (Make, as-is)

The source is a nested loop: **question sets × inspections**, then dedupe, then a per-site
task-creation branch split across 3 identical region routes.

1. `http:ActionSendData` (id 24) — `GET https://coastalwasteinc.ehsinsight.com/api/v4/entity/AuditInspection/list?CreatedAfter={{addHours(now; -24)}}`. `X-ApiKey` header (hardcoded, see §4.1). `handleErrors: true`.
2. `http:ActionSendData` (id 47) — `GET .../entity/AuditInspectionQuestions/list?fields=Title,RowUID`. Gated by filter "There are Forms To Check": `24.data.List` length > 0.
3. `builtin:BasicFeeder` (id 49) — iterates `47.data.List` (the question sets).
4. `builtin:BasicFeeder` (id 65) — iterates `24.data.List` (the inspections), gated by filter "Only the \"Facility Inspection Checklist\" Question Set Allowed": `49.Title == "Facility Inspection Checklist"`. (So the inner loop only runs when the outer question set is the Facility Inspection Checklist.)
5. `http:ActionSendData` (id 64) — `GET .../entity/AuditInspection/fetch/{{65.RowUID}}` — full inspection detail.
6. `builtin:BasicAggregator` (id 66, feeder 65) — collects `64.data` into `66.array`.
7. `util:SetVariable2` (id 26) — `filteredFormList = CoastalEHSFormFilter(66.array; 49.RowUID)`. See §5 for the function's behavior (dedupe to the latest *completed* inspection per `BusinessEntity` whose `QuestionsSelector` matches the Facility Inspection Checklist question-set RowUID).
8. `builtin:BasicFeeder` (id 28) — iterates `26.filteredFormList`, gated by "Has Forms to Process?": `filteredFormList` length > 0. Each item is a fetched inspection `Entity` (`RowUID`, `FormNumber`, `BusinessEntity`, `Questions`, etc.).
9. `http:ActionSendData` (id 54) — `GET .../hierarchy/fetch/{{28.BusinessEntity}}` — site hierarchy; `54.data.Hierarchy.Title` is the EHS site name.
10. `util:SetVariable2` (id 50) — `questionList = last(28.Questions)`. **Only the last question in the inspection is examined** (see OQ-035).
11. `util:SetVariable2` (id 58) — `limbleLocation = EHSLimbleLocationMapping(54.data.Hierarchy.Title)`. Gated by "Question Unacceptable?": `50.questionList.Answer == "0"` (answer value `"0"` = unacceptable). If the last question is acceptable, nothing is created for that site.
12. `fuse-limble-app:listLocations` (id 60) — `name = "{{58.limbleLocation}}%"`, `limit 1` → `60.locationID`, `60.regionID`. (`%` wildcard suffix — Limble quirk, see project memory.)
13. `fuse-limble-app:universalModule` (id 71) — `GET /v2/regions?regions={{60.regionID}}` → `71.body[1].regionName` (Make 1-indexed).
14. `builtin:BasicRouter` (id 70) — **3 routes, no `else`** (regions outside the allowlist drop silently). See §6 — the three routes are functionally identical; this spec consolidates them (OQ-034).

Per route (routes shown are byte-identical except the region filter and a dead `var`):

| Route | Region filter (`71.body[1].regionName ==`) | dead var | nodes |
| --- | --- | --- | --- |
| 1 (id 73) | `Central Florida` OR `Southwest Florida` | 1 | 88/89/90/91, 44, 45, 52→(21,57 / 56) |
| 2 (id 74) | `Coastal Materials Management` OR `South Florida` | 2 | 92/93/94/95, 76, 77, 78→(79,80 / 81) |
| 3 (id 75) | `South Atlantic` | 3 | 96/97/98/99, 82, 83, 84→(85,86 / 87) |

The `var` (`util:SetVariable2` set to 1/2/3, roundtrip scope) is **written and never read** — dead.

Per-route body (using route 1 ids; routes 2/3 identical):

- `fuse-limble-app:listTeams` (88) — `name = "EHS Approver Assignee"`, `limit 500`.
- Aggregator→Feeder→Aggregator (89/90/91) with filter "Grab Location's Team": `team.locationID == 60.locationID` → `91.array[1].teamID` (Make 1-indexed). (The feeder/aggregator round-trip here is a Make idiom to filter the team list down to the one matching the location; in n8n this is a plain filter — see §7.)
- `fuse-limble-app:createATask` (44):
  - `name` = `EHS Facility Inspection Checklist Deficiencies - {{28.FormNumber}}`
  - `type` = `2`, `priority` = `2`
  - `metadata.meta1` = `{{28.RowUID}}` (EHS inspection RowUID — the idempotency/traceback key back to EHS)
  - `assignmentType` = `team`, `assignment` = `{{91.array[1].teamID}}`
  - `locationID` = `{{60.locationID}}`
  - `templateID` = `"842"` (hardcoded Limble task template)
  - `description` = `Deficiencies were found in the latest Facility Inspection Checklist for {{54.data.Hierarchy.Title}} @EHSWO;` — **OQ-038 sanctioned fix (2026-07-08):** source stamps `@EHS;`; corrected to `@EHSWO;` to match the EHS review docx and "Update EHS Inspection"'s `@EHSWO;` gate (source's `@EHS;` is a pre-existing typo that stops the EHS loop from closing). **Applied to the live workflow 2026-07-20** (§12).
  - `due` = `{{addDays(now; 7)}}`
- `fuse-limble-app:listInstructions` (45) — `taskID = {{44.taskID}}`.
- `builtin:BasicRouter` (52, `else: 1`) — filter "Grab Instruction ID of 1st Instruction": `45.instruction` contains `"Work that Needs to be Done (from the EHS Inspection)"` → `45.instructionID`. (This is the template-842 instruction the deficiency text lands in.)
  - **If image present** — filter "Need to Add an Image?": `50.questionList.FileAttachments` length > 0, AND "Attachment is image file": `FileAttachments[1].FileName` contains `.jpeg`/`.png`/`.jpg`/`.gif`:
    - `http:ActionSendData` (21) — `GET .../attachment/fetch/{{50.questionList.FileAttachments[1].AttachmentUID}}` → `21.data` (file bytes).
    - `fuse-limble-app:updateAnInstruction` (57) — `instructionID = {{45.instructionID}}`, `instruction = "Deficiencies from Inspection:  {{50.questionList.Verification}}"`, `update_image = true`, `image = {file_data: {{21.data}}, file_name: {{...FileName}}}`.
  - **Else** (`else: 1`): `fuse-limble-app:updateAnInstruction` (56) — same `instruction`/`instructionID`, `update_image = false`.

Only `FileAttachments[1]` (the first attachment, Make 1-indexed) is ever considered.

## 4. Design decisions locked in for this spec

Confirmed with the owner 2026-07-08 (see §11 for the interview).

1. **EHS `X-ApiKey` moves to an n8n credential — not hardcoded.** The source embeds
   `apikey-160448cf-...` in plaintext in all 5 EHS HTTP nodes (24, 47, 64, 54, 21). Per
   CLAUDE.md's Secrets constraint and DEPLOYMENT §0, this key is **already exposed and must be
   rotated by Coastal before go-live**. In n8n: one **httpHeaderAuth** credential (header name
   `X-ApiKey`, value = the *rotated* key), wired to every EHS HTTP Request node. The literal
   key never gets written into any repo file or this spec.
2. **Consolidate the 3 identical region routes to 1 branch + a region allowlist guard**
   (sanctioned fix, **OQ-034**). One create-task branch, gated by an IF that allowlists the 5
   region names (`Central Florida`, `Southwest Florida`, `Coastal Materials Management`,
   `South Florida`, `South Atlantic`); regions outside drop, preserving the source's no-`else`
   behavior exactly. The dead `var` is dropped. Net behavior is identical to the source; node
   count drops ~2/3.
3. **No error handling — faithful silent port** (OQ-004, already resolved for both EHS-side
   workflows). The source has zero `onerror` chains; the n8n port adds none. HTTP nodes keep
   their default failure behavior (no retry loop, no alert email — unlike Token Regen, which
   got a sanctioned alert; the EHS side deliberately does not).
4. **`last(Questions)` ported faithfully, flagged** (**OQ-035**). Only the last question's
   answer/attachment drives the WO — multi-deficiency inspections capture only the last
   question. This is what shipped; not changed here. Flagged for the owner to decide whether
   iterating all unacceptable questions is a wanted fix later.
5. **Limble custom-app modules → HTTP Request** against the Limble REST API, using the same
   Limble credential wired on the other built workflows: **"Gerald Limble Sandbox"**
   (`MX0lwgfyFiGUBh5W`, httpHeaderAuth) for the test phase, swapped to the **"Coastal Waste
   Limble"** prod credential (`qn6u8jEK085DoHT8`, from OQ-015) before cutover. Applies to
   `listLocations`, `universalModule` (regions), `listTeams`, `createATask`, `listInstructions`,
   `updateAnInstruction`.
6. **Custom functions → Code nodes**, ported bit-for-bit from `docs/functions.js`:
   `CoastalEHSFormFilter`, `EHSLimbleLocationMapping` (see §5). Watch the Make-1-indexed array
   accesses when translating (§7).

## 5. Custom function behavior (from `docs/functions.js`)

**`CoastalEHSFormFilter(formList, questionSetID)`** — dedupe to the latest completed
inspection per site:
- Iterates `formList` (each element is a fetched inspection; the body reads `formList[i].data.Entity`).
- Keeps only forms where `form.QuestionsSelector == questionSetID`.
- Groups by `form.BusinessEntity`; for a site already in the list, replaces the kept form only
  if the candidate has a newer `UpdatedDtm` **and** a non-empty `RecurringTaskCompleteDtm`
  (i.e. the inspection is actually completed). First-seen sites are pushed unconditionally.
- Returns an array of `form` (`Entity`) objects.
- **Translation note:** the input shape matters — in Make, `66.array` is an array of
  `{data: {Entity: {...}}}` (the aggregator collected `64.data`). In the n8n port, feed the
  Code node the fetched-inspection items in a shape whose `[i].data.Entity` resolves, OR adapt
  the function's indexing to the n8n item shape. Port the logic, not the wrapper — verify the
  `.data.Entity` access against whatever the n8n HTTP node actually returns.

**`EHSLimbleLocationMapping(ehsSite)`** — map EHS site name → Limble location name:
- Splits on space, takes the first token, extracts digits (`\d+`).
- If digits found → `"Coastal " + siteNum`, with special cases:
  - `Coastal 23` → `Miami Hauling East` / `Miami East Weld Shop` / (default) `Miami East Container Yard`, chosen by substring match in `ehsSite`.
  - `Coastal 24` → `Lake Worth Hauling` (if "Lake Worth") else `Palm Beach Hauling`.
- If no digits → returns `ehsSite` unchanged.
- Pure string logic, no external calls — direct port to a Code node.

## 6. Consolidated node graph (n8n target)

```
[Schedule Trigger 0 16 * * *]
        |
        v
[HTTP: EHS AuditInspection/list?CreatedAfter=now-24h]
        |
   [IF List length > 0] --no--> (stop)
        | yes
        v
[HTTP: EHS AuditInspectionQuestions/list (Title,RowUID)]
        |
        v
[Code/Set: pick RowUID where Title == "Facility Inspection Checklist"]  --> questionSetID
        |
        v
[Loop inspections] -> [HTTP: AuditInspection/fetch/{RowUID}] -> aggregate fetched inspections
        |
        v
[Code: CoastalEHSFormFilter(fetched, questionSetID)]  --> filteredFormList
        |
   [IF filteredFormList length > 0] --no--> (stop)
        | yes
        v
[Loop each filtered form]
        |
        +-> [Set: questionList = last(form.Questions)]
        +-> [HTTP: hierarchy/fetch/{form.BusinessEntity}]
        |
   [IF questionList.Answer == "0"] --no--> (skip this form)
        | yes
        v
[Code: EHSLimbleLocationMapping(hierarchy.Title)]  --> limbleLocation
        v
[HTTP L: listLocations name=limbleLocation+"%" limit 1]  --> locationID, regionID
        v
[HTTP L: GET /v2/regions?regions={regionID}]  --> regionName
        v
[IF regionName IN {Central Florida, Southwest Florida, Coastal Materials Management,
                   South Florida, South Atlantic}] --no--> (drop, mirrors no-else)
        | yes
        v
[HTTP L: listTeams name="EHS Approver Assignee" limit 500]
        v
[Filter: team.locationID == locationID]  --> teamID  (first match)
        v
[HTTP L: createATask (template 842, type 2, priority 2, meta1=form.RowUID,
         assignment=teamID team, locationID, name/description per §3)]  --> taskID
        v
[HTTP L: listInstructions(taskID)]
        v
[Filter: instruction contains "Work that Needs to be Done (from the EHS Inspection)"]
        v
   [IF FileAttachments length>0 AND FileAttachments[0].FileName is image]
        | yes                                            | no
        v                                                v
[HTTP: attachment/fetch/{AttachmentUID}          [HTTP L: PATCH /v2/tasks/instructions/{id}
 responseFormat=file -> binary 'data']             body { instruction: deficiency text }]
        v
[HTTP L: PUT /v2/tasks/instructions/{id}/image
 multipart/form-data, form field 'image' = binary]
        v
[HTTP L: PATCH /v2/tasks/instructions/{id}
 body { instruction: deficiency text }]
```

*(Graph tail shown as-deployed 2026-07-20, §12 — the Make module's `update_image`/`image`
fields do not exist on the real API; image upload is a separate PUT.)*

`HTTP` = EHS Insight (httpHeaderAuth `X-ApiKey`, rotated). `HTTP L` = Limble (credential per §4.5).

## 7. Make → n8n translation notes

- **1-indexing:** Make `FileAttachments[1]` → n8n `[0]`; `71.body[1]` → `body[0]`;
  `91.array[1]` → first item of the filtered team list. `last(28.Questions)` →
  `Questions[Questions.length - 1]`.
- **Nested question-set × inspection loop** collapses in n8n: there is exactly one target
  question set ("Facility Inspection Checklist"), so resolve its RowUID once, then loop
  inspections once. No need to replicate the outer Feeder over all question sets.
- **Feeder→Aggregator→Feeder→Aggregator team filter** (88–91) is a Make idiom for "filter the
  team list to the entry matching this location." In n8n this is a single **Filter** (or IF
  inside a small loop) on `team.locationID == locationID` — do not replicate the double
  round-trip.
- **`listLocations` `%` suffix wildcard** is a Limble API quirk (project memory,
  OQ-024-adjacent recon) — preserve it in the HTTP query.
- **`createATask` / `updateAnInstruction` payloads** — RESOLVED (live contract, §12): create is
  `POST /v2/tasks` with `due` as **epoch seconds** (not the Make `addDays()` datetime) and
  **top-level `meta1` as a String** (the API rejects a `metadata` object and numeric metaN —
  OQ-024); instruction update is `PATCH /v2/tasks/instructions/{id}` with a verbiage-only
  `{ instruction }` body (the route rejects `response`/answer fields — OQ-042).
- **Image bytes** — RESOLVED (live-proven, §12): the Make module's `image.file_data`/`file_name`
  shape does not exist on the real API. Image upload is a **separate**
  `PUT /v2/tasks/instructions/{id}/image`, multipart/form-data, file in form field `image`.
  The EHS `attachment/fetch` node runs with `responseFormat: file` so n8n binary `data` feeds
  the multipart field directly. Remaining verify-at-A6: the EHS endpoint (and mock) actually
  return raw bytes with a usable filename.

## 8. Hardcoded values carried as literals

| Value | Where | Notes |
| --- | --- | --- |
| `842` | createATask `templateID` | Limble task template for these deficiency WOs |
| `"EHS Approver Assignee"` | listTeams `name` | team-name lookup |
| `type 2`, `priority 2` | createATask | Limble task type/priority codes |
| `"Facility Inspection Checklist"` | question-set title filter | the only inspection type processed |
| `"Work that Needs to be Done (from the EHS Inspection)"` | instruction match | the instruction the deficiency text targets |
| 5 region names | allowlist guard (§6) | Central Florida, Southwest Florida, Coastal Materials Management, South Florida, South Atlantic |
| deficiency text / description templates | §3 | reproduce the double space in `"Deficiencies from Inspection:  "` verbatim; trailing tag corrected `@EHS;`→`@EHSWO;` (OQ-038 sanctioned fix) |

## 9. Idempotency observation (not a decision — flag)

`meta1 = form.RowUID` (the EHS inspection RowUID) is written on every created task, but nothing
in this workflow reads it back to check for an existing WO before creating one. A daily re-poll
that re-sees the same still-recent inspection (the `CreatedAfter=now-24h` window vs. a 24h
schedule is a tight but not exact fit) could create duplicate WOs. The source has no dedupe
guard either. Noted for the owner; not changed under the faithful posture. Related to the
Coupa-side meta1 anomaly (OQ-024) only in that both rely on `meta1` — different workflows.

## 10. Open items / dependencies

- **OQ-034** (new) — sanction the 3-route → 1-branch consolidation (§4.2). Owner approved in
  the 2026-07-08 interview; recorded for the audit trail.
- **OQ-035** (new) — `last(Questions)` single-question behavior flagged (§4.4).
- **EHS API key rotation** — must happen before go-live (DEPLOYMENT §0); the n8n credential
  holds the rotated value, never the exposed one.
- **OQ-009** — no EHS/Limble API reference; request shapes reverse-engineered from mappers.
  The Limble-side shapes for this workflow are now live-verified (§12); EHS-side shapes
  (attachment fetch) remain unverified until A6.
- **OQ-014** — confirm the real trigger timezone with Coastal (MST vs EST).
- **OQ-020** — this workflow is schedule-triggered (no Limble webhook), so it's not part of the
  webhook re-registration at cutover.
- **Built** — deployed inactive to `isLUx7cUjkmKggD2` 2026-07-08; §12 corrections applied
  2026-07-20. A6 test suite (`docs/test-plan/test-sequence.md`) still to run.

## 12. As-deployed corrections (2026-07-20)

Applied to the live workflow `isLUx7cUjkmKggD2` after OQ-042's resolution (Limble support
answer + live sandbox probes/proof). These supersede the guessed shapes in §3/§6/§7. Workflow
is now **30 nodes** (was 29), re-validated clean.

1. **`Create Deficiency Task` (n21)** — three body fixes:
   - `due`: `.toISO()` → `Math.round($now.plus({ days: 7 }).toSeconds())` — `POST /v2/tasks`
     requires epoch **seconds**, 400s on ISO.
   - `metadata: { meta1: ... }` → top-level `meta1: String(...)` — the API rejects the
     `metadata` object and numeric metaN (OQ-024 sanctioned fix).
   - description tag `@EHS;` → `@EHSWO;` (OQ-038 sanctioned fix, per §3 note).
2. **Instruction-update URL fix (n27 + n28)** — `PATCH /v2/instructions/{id}` (guessed, 404s)
   → **`PATCH /v2/tasks/instructions/{id}`** (no taskID segment, `tasks/instructions`
   pluralized — Limble-support-confirmed). Bodies reduced to verbiage-only `{ instruction }`:
   the route rejects `update_image`/`image` and any answer/`response` field. (OQ-042 resolved
   2026-07-20: the public API cannot write an instruction's *answer* — irrelevant here, this
   workflow writes verbiage, which is supported.)
3. **New node `Attach Instruction Image`** — image upload is a separate call:
   `PUT /v2/tasks/instructions/{id}/image`, multipart/form-data, file in form field **`image`**.
   **Proven live** (sandbox instr 13200, 2026-07-20): 200, response
   `{"filename":"<serverPrefix>-<originalName>"}`, populates `instructionFiles[]` with a signed
   CDN link; `DELETE .../image?filename=<saved>` removes. Wiring:
   `EHS: Fetch Attachment` → `Attach Instruction Image` → verbiage PATCH (n27) → loop. The PUT
   sits directly after the fetch because n8n binary does not survive an intermediate HTTP
   node's response output.
4. **`EHS: Fetch Attachment` (n26)** — `responseFormat: file` so the response lands as n8n
   binary property `data` (feeds the multipart field). Replaces the guessed JSON
   `file_data` mapping. Still to verify at A6: EHS (and the mock) return raw bytes with a
   usable filename; node also still points at the real EHS host with the
   `__EHS_INSIGHT_CREDENTIAL_ID__` placeholder — mock-EHS staging is a separate A6 task.

## 11. Interview record (2026-07-08)

Decisions via `/collaborate` AskUserQuestion round:
1. **Deliverable:** spec doc only (this file). Build later on go-ahead.
2. **Region routes:** consolidate to 1 + allowlist guard (OQ-034).
3. **Error handling:** silent, faithful (OQ-004).
4. **`last(Questions)`:** faithful + flag (OQ-035).
