# Build Spec — Coastal - Update EHS Inspection From Limble WO (PROD)

Status: **design / spec-only** (2026-07-08). Target n8n workflow ID `8JvtesynrYtZbw7U`
("Update EHS Inspection From Limble WO") — currently an empty shell (OQ-007). Not built yet;
build awaits explicit per-workflow go-ahead per the design-phase posture (OQ-003).

Source blueprint: `docs/OG-workflows/Coastal - Update EHS Inspection From Limble WO (PROD).json`
(full flow walk run 2026-07-08: **linear, no routers, 0 `onerror` chains anywhere** —
consistent with OQ-004). Custom functions used: `CoastalGetChildWONotes`,
`CoastalEHSInspectFormUpdate` (bodies in `docs/functions.js`).

---

## 1. Purpose

When a Limble WO tagged `@EHS;` (carrying `meta1` = the source EHS inspection's `RowUID`,
written by "Create WO From EHS Inspection") is **completed**, write the WO's completion notes
— plus the completion notes of any child WOs spawned from it — back into that EHS Insight
inspection's `UDFLimbleWOCompletionNotes` field. This is the return leg of the EHS↔Limble loop:
EHS creates the Limble WO (EHS1), Limble reports the remediation back to EHS (this workflow).

## 2. Trigger

| | Source (Make) | n8n target |
| --- | --- | --- |
| Type | Limble webhook (hook `775`, `maxResults: 1`) — fires on task events; flow gates on event text `COMPLETE` | **Webhook** node, POST, Respond Immediately |
| Registration | Hook 775 lives in Limble's webhook config pointing at Make (cf. Step 1 = 776, Step 3 = 777) — one of the 3 registrations tracked in OQ-020 | New n8n production URL registered in Limble at cutover — deployment step, not a node (OQ-020) |

Payload fields consumed: `status` (event name), `taskID`. Nothing else from the webhook body
is referenced.

**Effective trigger semantics:** fires on any task event; proceeds only when the event is a
**completion** (`status == "COMPLETE"`) of a task whose description contains `@EHS;` and
which already carries `meta1`. A completion of any non-EHS or not-yet-tagged WO exits at the
gate. Same two-gate shape as Step 3 (§3 of that spec) — completion check first, integration-tag
check second, after the task detail fetch. Preserve exactly.

## 3. Source flow (Make, as-is)

Linear chain, no branching, no error handling:

1. `gateway:CustomWebHook` (58) — hook 775.
2. `universalModule` (63) — `GET /v2/tasks/{{58.taskID}}/comments`. **Filter "WO Completed?":**
   `{{58.status}} == "COMPLETE"`. Connection 2106.
3. `SetVariable2` (64) — `lastComment = last(63.body)`.
4. `listTasks` (59) — `tasks={{58.taskID}}, limit=1`. Returns the task incl. `meta1`,
   `description`, `dateCompleted`, `completionNotes`. Connection 2106.
5. `listInstructions` (68) — `taskID={{59.taskID}}`. **Filter "WO is an EHS WO":**
   `{{59.description}}` contains `"@EHSWO;"` AND `{{59.meta1}}` exists. Connection 2106.
   **Built gate changed 2026-07-27 to `"@EHS;"`** (OQ-038 reversal) — the source literal above is
   preserved for provenance; the live n8n node `n04` now tests `@EHS;`.
6. Aggregator→Feeder→Aggregator (70/69/71), the latter gated by filter **"Grab Child WOs"**:
   `{{69.meta.associatedTask}} exists` — filters the instruction list down to instructions that
   carry a linked child-task reference (the "generate child WO" button instruction from the
   EHS1-created template, per the EHS docx §"child WOs" — see §8).
7. `Feeder` (74) over `71.array` → `universalModule` (76) — `GET {{74.meta.associatedTask}}`
   (fetches each linked child task by its full URL) → `Aggregator` (77, feeder=74) collects
   `{body: 76.body}` per child task.
8. `SetVariable2` (73) — `childWOCompNotes = CoastalGetChildWONotes(77.array)`.
9. `SetVariables` (60) — two roundtrip vars:
   - `inspectionID = {{59.meta1}}`
   - `completionNotes` = `"(Completed {{formatDate(59.dateCompleted; \"MM/DD/YYYY hh:mm A\")}}){{newline}}All discrepancies listed in the last question have been resolved. Here are the completion notes from Limble:{{newline}}{{59.completionNotes}}{{newline}}{{73.childWOCompNotes}}"`
10. `http:ActionSendData` (4) — `GET https://coastalwasteinc.ehsinsight.com/api/v4/entity/AuditInspection/fetch/{{60.inspectionID}}`. `X-ApiKey` header (hardcoded, see §4.1). `handleErrors: true`.
11. `SetVariable2` (65) — `updatedInspectRecord = CoastalEHSInspectFormUpdate(4.data.Entity; 60.completionNotes)`.
12. `json:TransformToJSON` (67) — `{{65.updatedInspectRecord}}` → `67.json`.
13. `http:ActionSendData` (54) — `POST .../entity/AuditInspection/update`, body `{{67.json}}`,
    same `X-ApiKey` header. `handleErrors: true`.

**Dead nodes (63/64) — confirmed, see §4.2.** Grep for `{{63.` / `{{64.` across the full export
returns zero hits: nothing downstream ever reads `63.body` or `64.lastComment`. The docx
review (`Coastal - Limble Integration Review - EHS Integration (v1.3.2).docx`) describes the
completion-notes payload as "the completion notes typed in the EHS WO as well as the
completion notes of all of its child WOs" (line 88) — no mention of a Limble task *comment*
being part of the payload anywhere in the doc. Cross-checked; these two nodes are scaffolding
with no documented purpose and no live consumer.

## 4. Design decisions locked in for this spec

Confirmed with the owner 2026-07-08 (see §11 for the interview).

1. **Drop dead comments-fetch (63) and lastComment var (64) — SANCTIONED FIX (new, see §10).**
   Verified two ways before dropping: (a) grep across the full blueprint export for any
   downstream reference to `63.` or `64.` — zero hits; (b) cross-checked against the EHS docx
   review doc, which specifies the completion-notes payload as WO completion notes + child-WO
   completion notes only, no task-comment content. Same dead-code shape as OQ-033 (Step 3) and
   the EHS1 daily-poll spec. The n8n port omits both nodes entirely — the "WO Completed?" gate
   (`58.status == "COMPLETE"`) moves onto the task fetch (59) directly, same consolidation
   pattern Step 3 used when it dropped its own dead comments GET (§4.4 of that spec).
2. **EHS `X-ApiKey` moves to an n8n credential — not hardcoded.** Same treatment as EHS1 (its
   spec §4.1) and per CLAUDE.md's Secrets constraint: the source embeds
   `apikey-160448cf-...` in plaintext in both EHS HTTP nodes (4, 54) here. Already-exposed key,
   must be rotated by Coastal before go-live (DEPLOYMENT §0). One **httpHeaderAuth** credential
   (header name `X-ApiKey`, value = the *rotated* key), wired to both EHS HTTP Request nodes.
   Same credential entry EHS1 uses — do not create a second one.
3. **No error handling — faithful silent port** (OQ-004, already resolved for both EHS-side
   workflows). Zero `onerror` chains in the source; the n8n port adds none.
4. **Completion-note timestamp → `America/Denver`.** The source's `formatDate(59.dateCompleted;
   "MM/DD/YYYY hh:mm A")` carries no explicit timezone literal (Make would apply the
   account/org default). The n8n port sets this formatDate call to `America/Denver`, matching
   the Mountain-time convention already locked in for schedule triggers (OQ-011) and the
   error-log display (OQ-012). Non-faithful in the strict sense (source had no literal tz to
   copy), but consistent with the project's established Mountain-time default rather than an
   arbitrary pick.
5. **Limble custom-app modules → HTTP Request** against the Limble REST API, using the same
   Limble credential wired on the other built workflows: **"Gerald Limble Sandbox"**
   (`MX0lwgfyFiGUBh5W`) for test, swapped to **"Coastal Waste Limble"** (`qn6u8jEK085DoHT8`)
   before cutover. Applies to `listTasks`, `listInstructions`, and the child-task
   `universalModule` GET.
6. **Custom functions → Code nodes**, ported bit-for-bit from `docs/functions.js`:
   `CoastalGetChildWONotes`, `CoastalEHSInspectFormUpdate`.

## 5. Custom function behavior (from `docs/functions.js`)

**`CoastalGetChildWONotes(childWOs)`** — concatenate child-WO completion notes:
- `childWOs` is an array of `{body: [...]}` — each element's `body[0].completionNotes` is
  appended, space-separated, into one running string. Returns the concatenated string
  (`""` if `childWOs` is empty).
- **No null-guard**: if a child task's `body[0].completionNotes` is `undefined` (task not
  actually completed, or a shape mismatch), the literal string `"undefined"` gets concatenated
  in. Faithful port — flagged, not fixed (matches the project's fix-only-what's-sanctioned
  posture).
- **Translation note:** in Make, `77.array` is `[{body: [<task>]}, ...]` (aggregator wrapping
  each `76.body` response). Port the `[i].body[0].completionNotes` indexing exactly, adapting
  only to whatever shape the n8n HTTP node's response actually takes for the child-task fetch.

**`CoastalEHSInspectFormUpdate(inspectionRecord, completionNotes)`** — trivial mutator:
sets `inspectionRecord.UDFLimbleWOCompletionNotes = completionNotes` and returns the whole
record (read-modify-write — the POST sends the full inspection entity back, not a partial
patch). Direct port to a Code node; no external calls.

## 6. Target n8n node graph

```
[Webhook: POST hook-775]
  → [IF: status == "COMPLETE"]                                    (63's filter, moved; false → end)
  → [HTTP L: GET /v2/tasks/?tasks={taskID}&limit=1]               (59)
  → [IF: description contains "@EHS;" AND meta1 exists]           (68 filter; false → end)
  → [HTTP L: GET /v2/tasks/{taskID}/instructions]                 (68)
  → [Filter: instruction.meta.associatedTask exists]              (70/69/71 collapsed, §7)
  → [Loop each matching instruction]
       → [HTTP L: GET {instruction.meta.associatedTask}]          (76, child task fetch)
  → [Aggregate child task bodies into array]                      (77)
  → [Code: CoastalGetChildWONotes(childBodies) → childWOCompNotes] (73)
  → [Set: inspectionID = meta1;
          completionNotes = "(Completed {dateCompleted, America/Denver})…"]  (60)
  → [HTTP E: GET AuditInspection/fetch/{inspectionID}]            (4)
  → [Code: CoastalEHSInspectFormUpdate(entity, completionNotes) → updatedInspectRecord]  (65)
  → [HTTP E: POST AuditInspection/update  body=updatedInspectRecord]  (54)
```

`HTTP L` = Limble (credential per §4.5). `HTTP E` = EHS Insight (httpHeaderAuth `X-ApiKey`,
rotated, per §4.2).

## 7. Make → n8n translation notes

- **Dropped Aggregator→Feeder→Aggregator idiom (70/69/71) → single Filter.** Same pattern
  called out in the EHS1 spec §7 for the team-lookup round-trip: Make's
  aggregate-then-refeed-then-aggregate-with-filter is just "filter this list," expressed once
  in n8n as a Filter node on `meta.associatedTask exists`. Do not replicate the double
  round-trip.
- **`last(63.body)`** — moot; module dropped entirely (§4.1).
- **`childWOBody[0]`** (Make 1-indexed-equivalent array access inside the function body, `[0]`
  in JS already) — the function itself uses 0-based JS indexing already since it's a literal
  JS function body, not a Make mapper expression; no reindexing needed when porting the
  function verbatim. Only the *Make-side* aggregator wrapper shape (`{body: [...]}` per item)
  needs to match on the n8n side — verify against the actual n8n HTTP node output at build.
- **`59.meta1`** is the EHS inspection `RowUID`, written by EHS1's `createATask` at WO creation
  (that spec's `metadata.meta1 = {{28.RowUID}}`). This workflow is the read side of that
  contract — if EHS1's `meta1` field ever changes, this workflow's `inspectionID` lookup breaks
  with it (cross-workflow dependency, §9).
- **Child-task fetch URL** (`74.meta.associatedTask`) is a **full URL**, not a bare ID — the
  Make `universalModule` GET uses it directly. Confirm at build whether it's a Limble API path
  or a full `https://` URL; either way, wire it directly into the HTTP node's URL field rather
  than reconstructing it.

## 8. Design-truth cross-check (docx)

`Coastal - Limble Integration Review - EHS Integration (v1.3.2).docx` describes the completion
side of this integration (lines 87-94):
- "The integration will grab the details of the WO — including the hidden meta1 field... the
  completion date, and the completion notes (if written)... to prepare the data sent back to
  the EHS inspection."
- "The completion notes sent back to EHS will be the completion notes typed in the EHS WO as
  well as the completion notes of all of its child WOs."
- Exact template text confirmed matching the blueprint's `completionNotes` string almost
  verbatim: *"All discrepancies listed in the last question have been remedied. Here are the
  completion notes from Limble: <Completion Notes Grabbed from Limble>"* (docx says
  "remedied," blueprint says "resolved" — trivial word-choice drift, not a behavior
  difference; port the blueprint's literal wording, it's the shipped text).
- "A new text box field called 'Limble WO Completion Notes' has been created for the Audit
  Inspection Forms" — confirms `UDFLimbleWOCompletionNotes` is the intended target field
  (matches `CoastalEHSInspectFormUpdate`'s hardcoded key).
- Docx confirms the "generate child WO" button instruction is where `meta.associatedTask`
  comes from (lines 97-106: child WOs are spawned per-deficiency from a button instruction on
  the parent WO) — this is what module 71's "Grab Child WOs" filter is selecting for.
- No mention anywhere of pulling Limble task *comments* into this payload — supports dropping
  63/64 (§4.1).

## 9. Cross-workflow dependencies

- **Reads `meta1`** — written by "Create WO From EHS Inspection" (`createATask.metadata.meta1
  = {{28.RowUID}}`, that spec §3 step 13). If EHS1's meta1 write changes, this workflow's
  inspection lookup breaks with it — keep in lockstep, same pattern as Step 2/Step 3's
  `meta1`/`meta2` coupling (Step 3 spec §6).
- **Reads `@EHS;` tag** (changed from `@EHSWO;` 2026-07-27, OQ-038 reversal) — written into the WO's `description` by EHS1's `createATask`
  (verify the literal tag string against EHS1's `description` field at build; EHS1's spec §3
  step 13 shows the description template but doesn't show the `@EHSWO;` tag literal itself —
  cross-check both specs' descriptions against each other at build time, flag if they diverge).
- **No Coupa-side interaction** — this workflow and EHS1 are a closed loop between Limble and
  EHS Insight; neither touches Coupa or the shared Coupa error-log table.
- **Child-WO structure** depends on EHS1's task template (`842`) having the "generate child WO"
  button instruction described in the docx (§8) — not independently verified against the live
  Limble template in this session (OQ-009 applies).

## 10. Open items / dependencies

- **New OQ (this session)** — sanction dropping dead comments-fetch (63) / lastComment (64).
  Owner approved 2026-07-08 after the docx cross-check found no documented use; recorded here
  for the audit trail (see §11). Track as **OQ-036**.
- **OQ-009** — no EHS/Limble API reference; request shapes reverse-engineered from mappers.
- **OQ-020** — this workflow is one of the 3 webhook re-registrations at cutover (hook 775).
- **EHS API key rotation** — must happen before go-live (DEPLOYMENT §0); shares the credential
  entry with EHS1, not a separate one.
- **`@EHS;` tag literal** (was `@EHSWO;` until the 2026-07-27 OQ-038 reversal) — confirm exact string against EHS1's `description` template at
  build (§9).
- **Child-task fetch shape** — confirm `meta.associatedTask` resolves to a fetchable URL/ID and
  that the response shape matches `body[0].completionNotes` at build (§7).
- **Built + pushed 2026-07-08** — `docs/build-specs/ehs-update-inspection.n8n.json` is the
  artifact (13 nodes, `validate_workflow` clean: 0 errors/warnings besides the expected "no
  error handling" suggestion, which is correct per OQ-004). Pushed to the `8JvtesynrYtZbw7U`
  shell via `n8n_update_full_workflow` on owner authorization; on-instance structure verified
  matching the file, deployed INACTIVE. EHS credential resolved to the existing
  **`ZEf4C1rpYSbBgLbX`** ("Coastal Waste - EHS API Key") — the placeholder is gone. New flags
  surfaced while building, tracked in the file's `__readme`:
  (1) child-task fetch assumes `meta.associatedTask` is a directly-fetchable full URL, per §7;
  (2) `dateCompleted` assumed unix-epoch-seconds by analogy to the confirmed-epoch Limble `due`
  field — not independently confirmed for this field; (3) "Get Instructions" carries no `limit`
  query param (faithful to source module 68), collides with the known Limble instructions
  page-size-2 default — verify at build; (4) the n8n Aggregate node is assumed to still emit
  one item when 0 child WOs reach it (the common case) — if false, every completion with no
  child WOs would silently stop short of updating EHS, verify at first live test.

## 11. Interview record (2026-07-08)

Decisions via `/collaborate` AskUserQuestion round:
1. **Dead nodes 63/64:** owner asked for a docx cross-check before approving the drop (not a
   blind "yes drop it"). Cross-check done (§8) — docx describes the completion-notes payload
   with no task-comment component anywhere. Confirmed as pure dead scaffolding, not an
   under-configured intended feature. Drop approved, tracked as OQ-036.
2. **Completion-note timestamp tz:** `America/Denver`, matching OQ-011/OQ-012 convention.
3. **Deliverable:** spec doc only (this file). Build later on go-ahead.
