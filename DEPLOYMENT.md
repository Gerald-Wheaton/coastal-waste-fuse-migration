# DEPLOYMENT — Coastal Waste, Fuse → n8n cutover

Personal checklist. Modeled on `../deer-valley/DEPLOYMENT.md` (see also
`DEPLOYMENT-REFERENCE-DOC.md` in this repo, which is that file copied over as a reference).
Coastal is bigger — 7 scenarios across 2 integrations (Limble⇄Coupa, Limble⇄EHS Insight) — so
this doc has one section per workflow instead of one flat list.

**Do not use this doc to build workflows.** It's the pre-publish gate: everything here is stuff
that must be true right before you flip a workflow live, not part of the build spec itself. Build
specs live in `docs/build-specs/`.

Status as of 2026-07-23: build complete; Phase A (pre-go-live) testing nearly done. All 7 target
workflows exist and are **deployed inactive** (5 confirmed inactive via live read 2026-07-23 —
Token Regen, Step 3, Error Log Export, EHS-Create, EHS-Update; Step 1/Step 2 not re-listed this
pass, last known inactive after suite-end deactivation). The live test scoreboard is
`docs/test-plan/test-sequence.md`; this doc is only the pre-publish cutover gate.

Phase A suite status: **A1 Step 2 ✅** (incl. S2-2 team-comment — PASS 2026-07-24, exec 127081,
OQ-040 resolved) · **A2 Token Regen ✅** · **A3 Error Log Export ✅** · **A4 Step 1 ✅** (team
contractor-comment variant unblocked by OQ-040, not separately re-run — optional) · **A5
Step 3 ✅** · **A6 EHS Create WO ✅** (exec 126934, 2026-07-21) · **A7 EHS Update ✅ PASSED
2026-07-25** (U1–U4 + regression, execs 127253–127262 — see `test-sequence.md` A7) ·
**A8 wrap-up ☐**. All Phase
A runs against mock Coupa + mock EHS + live Limble sandbox (loc 98472) — **no workflow has been
tested against the real Coupa/EHS APIs yet** (that is Phase C, post-cutover). Test rigs live:
Mock Coupa (`F05TiUurpc2kqxe0`), Mock EHS (`EBIzCJ0XJaJ5jUpp`), Limble seeder (`qyMChP0DKfI04r4a`).

---

## 0. Cross-cutting items (apply to more than one workflow)

### Credentials to create/swap on the n8n instance

| Credential | Used by | Sandbox → Prod swap needed |
| --- | --- | --- |
| **Limble** (HTTP Header/Bearer auth against Limble API) | Step 1, Step 2, Step 3, EHS-Create, EHS-Update | **✅ Loaded into n8n credential store 2026-07-03 (OQ-015 resolved); `.env` scrubbed.** Build/test runs on the sandbox credential (`MX0lwgfyFiGUBh5W`); before go-live, repoint every Limble-calling node's credential to Coastal's prod credential (`qn6u8jEK085DoHT8`) — tracked per-workflow below. |
| **Coastal Coupa OAuth Client Credentials** (`httpCustomAuth`, per OQ-005) | Token Regeneration, Step 1, Step 2, Step 3 | **✅ Loaded into n8n credential store 2026-07-03 (OQ-015 resolved)** — client_id/secret sourced from Make datastore `324` (client `coastal_waste (PROD)`). The `oauth_token`/`access_token` is ephemeral, minted daily by Token Regeneration. Target host `coastalwasteinc.coupahost.com`. Never write the real values into this repo — n8n credential store only. |
| **EHS Insight API key** (`X-ApiKey` header) | EHS-Create, EHS-Update | **✅ Rotated key loaded into n8n credential store 2026-07-03 (OQ-015 resolved).** Note: EHS-Create workflow nodes still carry placeholder `__EHS_INSIGHT_CREDENTIAL_ID__` (see §5) — attach the credential at cutover. The old exposed key (`apikey-160448cf-...`, 9 plaintext occurrences in the blueprint exports — see flag below) is superseded; do not reuse it. |
| **Integrations Ionos** (email sending, per OQ-010) | Token Regeneration (failure alert), Coupa Integration Error Log Export | **✅ Loaded into n8n credential store 2026-07-03 (OQ-015 resolved).** No sandbox/prod split — same credential throughout. |

**Flag:** `docs/OG-workflows/Coastal - Create WO From EHS Inspection (PROD).json` and
`.../Coastal - Update EHS Inspection From Limble WO (PROD).json` both contain a literal EHS
Insight API key in plaintext (9 occurrences total). This contradicts CLAUDE.md's "no literal
secrets found" note — that note was only ever true for Limble/Coupa (datastore-referenced), not
EHS. Because the value is already in-hand, testing does not wait on it — but get the key rotated
before go-live regardless of what else changes.

### Data Tables to create and record the ID of

| Table | Replaces | Used by |
| --- | --- | --- |
| Coastal Coupa OAuth Token | Datastore 324 (scoped to Coastal only, not shared — OQ-005) | Token Regeneration (write), Step 1/2/3 (read) |
| Coastal Coupa Error Log | Datastore 326 | Step 1 (write), Step 3 (write), Error Log Export (read + delete) |

Record both table IDs here once created — later build specs and the workflows themselves need
to agree on the same ID:

- Coastal Coupa OAuth Token: `QAj62weJaWmRBJ76` (Token Regen writes; Step 1/2/3 read)
- Coastal Coupa Error Log: `6GbR5Rxezl7hqk9i` (Step 1 + Step 3 write; Error Log Export drains)

### Workflow IDs (OQ-007 — resolved)

All 7 target n8n workflow IDs assigned (owner-provisioned shells). Write only to the named ID.
Write authorization is still granted one scenario at a time per OQ-003.

| Workflow | n8n Workflow ID | Active? |
| --- | --- | --- |
| Coupa Token Regeneration | `oCAl4h0SZenEtbNs` | ☐ |
| Create Requisition in Coupa (Step 1) | `WJSs6apAdVH5yKkq` | ☐ |
| Check For New PRs Ordered & Update Limble WO (Step 2) | `WYJyHdQGcdeD8wEr` | ☐ |
| WO Completed; Update Coupa PO (Step 3) | `NH1giNups8iICMZe` | ☐ |
| Create WO From EHS Inspection | `isLUx7cUjkmKggD2` | ☐ |
| Update EHS Inspection From Limble WO | `8JvtesynrYtZbw7U` | ☐ |
| Coupa Integration Error Log Export | `hR5YnDixecDz9HzJ` | ☐ |

### Email recipients (OQ-010 — dev override, restore before go-live)

Every email-sending node currently routes to `gerald@fm360consulting.com` only, via the
**Integrations Ionos** credential. Before go-live, restore real recipients:

| Node / Workflow | Real recipient(s) | Status |
| --- | --- | --- |
| "Token Refresh Failed" — Coupa Token Regeneration | `integrations@fm360consulting.com` (owner decision 2026-07-25; also the from-address — self-addressed on purpose) | ☐ pending restore |
| Coupa Integration Error Log Export report | `ethan@fm360consulting.com` (confirmed — matches source Make blueprint) | ☐ pending restore |

If any additional error/failure-alert emails get added while building Step 1/2/3 or the EHS
workflows (none exist in the source blueprints today — confirmed via full-repo scan for embedded
email addresses), add a row here before they ship.

### Limble webhook subscriptions

Step 1 (New Task Comment), Step 3 (Task Completed), and Update EHS Inspection From Limble WO
(Task Completed) are all triggered by Limble webhooks currently pointed at Fuse/Make. The Make
export doesn't carry the webhook URL (hook IDs are Make-internal, not in the JSON) — at deploy
time:

1. Activate each n8n webhook node, copy its production URL.
2. In Limble's webhook/integration settings, update the subscription for that event type to the
   new n8n URL.
3. Confirm old Fuse subscriptions are removed/disabled so Limble doesn't fire both.

### Schedule timezone — RESOLVED (OQ-014, owner decision 2026-07-25): America/New_York

Owner decided **America/New_York** (Eastern), superseding OQ-011's Denver convention — matches
Limble recon (all ~49 Coastal locations Eastern) and the source blueprints' hardcoded "EST"
error-timestamp formatting. **All flips applied to the live workflows 2026-07-25:**

- Token Regeneration (`oCAl4h0SZenEtbNs`): `settings.timezone` → America/New_York (verified by
  read-back; daily @ 12:00AM cron now fires Eastern midnight).
- EHS Create (`isLUx7cUjkmKggD2`): `settings.timezone` → America/New_York (daily @ 4:00PM
  Eastern).
- EHS Update (`8JvtesynrYtZbw7U`): `settings.timezone` → America/New_York AND the
  `Prepare Update Payload` completion-note formatting `.setZone('America/Denver')` →
  `'America/New_York'`.
- Error Log Export (`hR5YnDixecDz9HzJ`): `Build Report` `timeZone: 'America/Denver'` →
  `'America/New_York'` (no settings tz; 15-min interval is tz-agnostic).
- Step 2 (`WYJyHdQGcdeD8wEr`): no timezone setting and no tz-formatting — nothing to flip
  (5-min interval tz-agnostic). Step 1/Step 3: webhook-triggered, no tz settings or display
  formatting; `$now` error-row timestamps store as UTC instants and are formatted only at
  Error Log Export.

Residual: EHS Update's Eastern-rendered completion note and the Error Log Export Eastern
report display have not been re-executed since the flip (A7/A3 proved the Denver rendering);
re-verify at each workflow's cutover manual-test row.

---

## 1. Coupa Token Regeneration

- [ ] Coastal Coupa OAuth Client Credentials populated with real client_id/secret
- [ ] Coastal Coupa OAuth Token Data Table ID confirmed correct
- [ ] "Token Refresh Failed" email recipient restored to `integrations@fm360consulting.com`
      (decided 2026-07-25; node currently gerald@ dev-only per OQ-010 — swap at cutover)
- [x] Schedule timezone resolved (OQ-014, 2026-07-25) — cron daily @ 12:00AM **America/New_York**,
      `settings.timezone` flipped + verified by read-back
- [ ] Manual test run — confirm token written to Data Table
- [ ] Workflow ID assigned (OQ-007) and activated

**Test-only staging applied 2026-07-13 — MUST be reverted before cutover:**
- [ ] **Token URL:** `Refresh Coupa OAuth Token` repointed to mock
      `https://fm360.n8n.fm360consulting.com/webhook/mock-coupa/oauth2/token` — revert to
      `https://coastalwasteinc.coupahost.com/oauth2/token`.
- [ ] Mock token value (`MOCK-TOKEN-COUPA-REFRESHED`) purged from Coupa OAuth Token table
      `QAj62weJaWmRBJ76` (shared with Step 2 §3 mock-row cleanup).
- [ ] Stale `Coastal_Waste (TEST)` row (id 1, expired test-instance JWT) deleted from the same
      table (OQ-039 resolved 2026-07-25: no test-instance pass; Coupa shapes examined at
      go-live under the C4 first-shepherd watch — OQ-028 is the tracking item).

## 2. Create Requisition in Coupa (Step 1)

- [ ] Limble credential swapped sandbox → Coastal prod
- [ ] Coupa credential confirmed reading from Coastal Coupa OAuth Token table
- [ ] Coastal Coupa Error Log table ID confirmed correct
- [ ] Limble webhook subscription (New Task Comment) repointed to this workflow's n8n URL
- [ ] Manual test run against a real (or realistic) Limble task comment
- [ ] Workflow ID assigned (OQ-007) and activated

**Test-only staging applied 2026-07-13 — MUST be reverted before cutover:**
- [ ] **Coupa URLs:** 6 nodes (`Coupa: Get User`, `Coupa: Get Address`, `Coupa: Get Account`,
      `Coupa: Get Supplier`, `Coupa: Create Requisition`, `Coupa: Attach Quote`) point at mock
      host `https://fm360.n8n.fm360consulting.com/webhook/mock-coupa` — revert host to
      `https://coastalwasteinc.coupahost.com` (paths unchanged).
- [ ] **Admin-comment target:** `Get Admin User` query retargeted from real admin **317887
      (Brandon Ray Freckleton)** to sandbox Site Manager **398783** — **revert to 317887**
      on deploy (OQ-019). Same pattern as Step 2 §3.
- [ ] Mock token row cleanup shared with §1/§3 (`client=coastal_waste` in `QAj62weJaWmRBJ76`).

**Permanent (do NOT revert) — sanctioned fix under OQ-045 (applied + tested 2026-07-25):**
`Get Instructions` (n13) has `alwaysOutputData: true` so a zero-instruction WO still reaches
`Parse Instruction Responses`, which emits source-faithful defaults and lets the error surface
downstream (source Make continued via empty aggregator bundle; unguarded n8n silently stopped).
Zero-instruction exec 127289 + regression exec 127295 both PASS. Keep at go-live.
- [ ] Teardown: delete OQ-045 fixture task **4228** (`DELETE /v2/tasks/4228`) with the other
      sandbox fixtures.

## 3. Check For New PRs Ordered & Update Limble WO (Step 2)

- [ ] Limble credential swapped sandbox → Coastal prod (all 10 Limble nodes: currently
      sandbox `MX0lwgfyFiGUBh5W`, revert to PROD `qn6u8jEK085DoHT8`)
- [ ] Coupa credential confirmed reading from Coastal Coupa OAuth Token table
- [x] OQ-008 resolved — error-log subgraph built into `WYJyHdQGcdeD8wEr` 2026-07-09 (OQ-029)
- [ ] Manual test run
- [ ] Workflow ID assigned (OQ-007) and activated (5-minute schedule)

**Test-only staging applied 2026-07-09 — MUST be reverted before cutover:**
- [ ] **Coupa URLs:** 2 nodes (`Get Associated Requisition`, `Get PO Created From Req.`)
      point at mock host `https://fm360.n8n.fm360consulting.com/webhook/mock-coupa` — revert to
      `https://coastalwasteinc.coupahost.com`.
- [ ] **Admin-comment target:** `Get Admin User` query retargeted from real admin **317887
      (Brandon Ray Freckleton)** to sandbox Site Manager **398783** so test error-paths don't
      ping a real user — **revert to 317887** on deploy (OQ-019).
- [ ] **Mock token row** purged from Coupa OAuth Token table `QAj62weJaWmRBJ76` (row
      `client=coastal_waste` / `oauth_token=MOCK-TOKEN-COUPA`).
- [ ] Sandbox test fixtures/dud tasks removed from loc 98472 (4080–4083 etc.; S2-2 fixtures added
      2026-07-24: task **4213** `DELETE /v2/tasks/4213` + team **605550** `DELETE /v2/teams/605550`).
- [ ] Remove the `coastal-seed-team` branch (3 nodes) added to seeder `qyMChP0DKfI04r4a` 2026-07-24
      (or drop it with the whole seeder at cutover teardown).

**Permanent (do NOT revert) — sanctioned fixes under OQ-024:** the write node
`Set 'PO Approved' Status and Save PO ID` now writes **top-level `meta2`** (not `metadata.meta2`)
and wraps it as **`String(...)`** (Limble rejects the `metadata` object and rejects a numeric
`meta2`). These are correctness fixes, not test scaffolding — keep them at go-live.

## 4. WO Completed; Update Coupa PO (Step 3)

- [ ] Limble credential swapped sandbox → Coastal prod
- [ ] Coupa credential confirmed reading from Coastal Coupa OAuth Token table
- [ ] Coastal Coupa Error Log table ID confirmed correct (same table as Step 1)
- [ ] Limble webhook subscription (Task Completed) repointed to this workflow's n8n URL
- [ ] Manual test run
- [ ] Workflow ID assigned (OQ-007) and activated

**Test-only staging applied 2026-07-13 — MUST be reverted before cutover:**
- [ ] **Coupa URLs:** 4 nodes (`Coupa: Get PO`, `Coupa: Attach Invoice`, `Coupa: Post Comment
      (Invoice)`, `Coupa: Post Comment (No Invoice)`) point at mock host
      `https://fm360.n8n.fm360consulting.com/webhook/mock-coupa` — revert host to
      `https://coastalwasteinc.coupahost.com` (paths unchanged).
- [ ] Mock token row cleanup shared with §1/§2/§3 (`client=coastal_waste` in `QAj62weJaWmRBJ76`).

**Permanent (do NOT revert) — sanctioned fix under OQ-045 (applied + tested 2026-07-25):**
`Get Instructions` (n05) has `alwaysOutputData: true` so a zero-instruction WO still reaches
`Extract Invoice Response`, which emits the empty-invoice default and posts the no-invoice
"@Jordan Buyer" comment — matching source Make (unguarded n8n silently stopped). Zero-instruction
exec 127286 + regression exec 127296 both PASS. Keep at go-live.
- [ ] Teardown: delete OQ-045 fixture task **4229** (`DELETE /v2/tasks/4229`) with the other
      sandbox fixtures.

## 5. Create WO From EHS Inspection

Built 2026-07-08, deployed inactive to `isLUx7cUjkmKggD2` (**30 nodes** after the 2026-07-20
fixes below, re-validated clean — 0 errors/warnings). See
`docs/build-specs/ehs-create-wo-build-spec.md` (section 12 for the as-deployed corrections).

**Test status: A6 suite PASSED 2026-07-21** (exec 126934) — 5 deficiency tasks created at correct
locations/teams, `meta1`=RowUID (top-level string), epoch `due`, `@EHSWO;` tag, verbiage PATCH on
all 5, image PUT on the image scenario; negative scenarios all held. Detail in test-sequence.md A6.

**Permanent (do NOT revert) — fixes applied to the live workflow 2026-07-20:**
- `Create Deficiency Task`: `due` → epoch seconds (`Math.round(...toSeconds())`; API 400s on
  ISO), `metadata.meta1` → top-level `meta1: String(...)` (OQ-024 sanctioned fix), description
  tag `@EHS;` → `@EHSWO;` (OQ-038 sanctioned fix).
- Both instruction-update nodes: URL fixed to `PATCH /v2/tasks/instructions/{id}` (old guessed
  `/v2/instructions/{id}` 404s — Limble-support-confirmed route), bodies now verbiage-only
  (`{ instruction }`; the PATCH rejects answer/`response` fields, which this workflow never
  needed — OQ-042 resolved 2026-07-20, no longer a blocker).
- Image upload split into new node `Attach Instruction Image`:
  `PUT /v2/tasks/instructions/{id}/image`, multipart/form-data, file in form field `image` —
  **proven live on sandbox 2026-07-20** (200, response `{"filename":"<serverPrefix>-<name>"}`,
  populates `instructionFiles[]`; `DELETE .../image?filename=` removes). Wired
  `EHS: Fetch Attachment` → PUT image → verbiage PATCH → loop.
- `EHS: Fetch Attachment`: `responseFormat: file` (emits n8n binary `data` for the multipart
  upload — replaces the guessed JSON `file_data` mapping).

- [x] "Coastal Waste - EHS API Key" n8n credential (`ZEf4C1rpYSbBgLbX`, httpHeaderAuth,
      rotated key) attached to all 5 EHS HTTP nodes 2026-07-20 — placeholder
      `__EHS_INSIGHT_CREDENTIAL_ID__` gone. Credential is already the prod one; no swap
      needed at cutover (host swap only, see staging block below)
- [ ] EHS Insight API key rotated (see flag above)
- [ ] Limble credential swapped sandbox → Coastal prod
- [x] Schedule timezone resolved (OQ-014, 2026-07-25) — cron `0 16 * * *` daily @ 4:00PM
      **America/New_York**, `settings.timezone` flipped
- [x] `createATask` field names verified against live Limble API — `due` epoch seconds +
      top-level `String(metaN)` confirmed via live sandbox contract (2026-07-09/2026-07-20);
      remaining fields exercised at A6
- [x] `updateAnInstruction` endpoint/method verified — real routes are
      `PATCH /v2/tasks/instructions/{id}` (verbiage) + `PUT .../image` (multipart), both
      support-confirmed and deployed 2026-07-20 (image PUT proven live)
- [ ] EHS attachment-fetch response shape verified — node now expects a **binary file**
      response (`responseFormat: file`); **mock half done 2026-07-20** (serves raw PNG +
      `Content-Disposition` filename, live-curled); the **real** EHS endpoint's byte shape
      remains a Phase-C6 unknown (if it returns JSON/base64, add a decode step)
- [ ] Manual test run
- [ ] Workflow ID assigned (OQ-007) and activated

**Test-only staging applied 2026-07-20 — MUST be reverted before cutover:**
- [ ] **EHS URLs:** all 5 EHS nodes (`EHS: List Inspections`, `EHS: List Question Sets`,
      `EHS: Fetch Inspection Detail`, `EHS: Get Hierarchy`, `EHS: Fetch Attachment`) point at
      mock host `https://fm360.n8n.fm360consulting.com/webhook/mock-ehs` — revert host to
      `https://coastalwasteinc.ehsinsight.com` (paths unchanged).
- [ ] **templateID:** `Create Deficiency Task` retargeted `"842"` → sandbox template `"4189"`
      2026-07-20 — **revert to `842`** at cutover.
- [ ] Sandbox A6 fixtures removed at teardown — full ledger (regions 7944/7946–7950, teams
      602733–602737, template task 4189, owner-created locations 98872–98878, plus the A6 run's
      created tasks) in `docs/test-plan/sandbox-seed-record-a6.md`.

## 6. Update EHS Inspection From Limble WO

Built 2026-07-08, deployed inactive to `8JvtesynrYtZbw7U` (**15 nodes** after the approved
Collect Child Links fix; confirmed live 2026-07-25). See
`docs/build-specs/ehs-update-inspection-build-spec.md`.

**Test status: A7 suite ✅ PASSED 2026-07-25** — U1 (exec 127255), U2 (127253), U3 (127254),
U4 (127259, after the owner-approved Collect Child Links rewire; first run 127258 exposed the
zero-children silent stop), U1 regression (127262, byte-identical write-back). The old
"blocked on owner UI checklist" story is dead: fixtures were rebuilt around **type-14 "Work
Order" instructions** (parent 4218, children 4220/4222) — the one API-reachable mechanism that
stamps `meta.associatedTask`. Three **permanent** port fixes applied 2026-07-25 (no cutover
revert): n05 `?limit=100` (page-size-2 clip), n06 `meta?.associatedTask` optional chaining,
n07 host-prepend (relative child link). Full detail in `docs/test-plan/test-sequence.md` A7.
**Run risk — RESOLVED (stale note removed 2026-07-25):** the 2026-07-23 note here described
`Has Child WO?` (Filter) and `Get Child Task` reading `{{ $json.meta.associatedTask }}` with no
optional chaining (throw on meta-less instructions). That graph is gone: the approved Collect
Child Links fix restructured the segment — `Has Child WO?` no longer exists, and `Get Child Task`
(n07) now reads `$json.childLinks` fed by the Collect node. Verified against the live workflow
2026-07-25. A7 has since run and PASSED (see test-status above); the checklist rows below are
cutover gates (credential swap, webhook repoint, real-EHS manual test), not suite re-runs.

**Test-only staging applied 2026-07-21 — MUST be reverted before cutover:**
- [ ] **EHS URLs:** 2 nodes (`EHS: Fetch Inspection`, `EHS: Update Inspection`) point at mock host
      `https://fm360.n8n.fm360consulting.com/webhook/mock-ehs` — revert host to
      `https://coastalwasteinc.ehsinsight.com` (paths unchanged). Verified applied 2026-07-23.
- [ ] **A7 fixture teardown at loc 98472:** parent task **4218** (+ its type-14 child links),
      children **4220**/**4222**, U4 parent **4223**, non-EHS control **4201**, and the scrapped
      old-plan skeletons (4198–4200, 4202 if present). Dangling type-14 instruction **15056**
      (→ deleted task 4221) goes with 4218. Ledger: `docs/test-plan/sandbox-seed-record-a6.md`.

- [x] EHS Insight API key rotated and moved into an n8n credential (same rotated key as #5) —
      verified live 2026-07-25: both EHS nodes (n11 `EHS: Fetch Inspection`, n13
      `EHS: Update Inspection`) carry rotated credential `ZEf4C1rpYSbBgLbX`
      ("Coastal Waste - EHS API Key")
- [ ] Limble credential swapped sandbox → Coastal prod
- [ ] Limble webhook subscription (Task Completed) repointed to this workflow's n8n URL
- [x] Dead comments-fetch (module 63) / lastComment (module 64) confirmed dropped per OQ-036 —
      structure pull 2026-07-25 (A7): no comments-fetch node, no `lastComment` anywhere
- [ ] `@EHSWO;` tag literal on the Limble WO description verified to match what "Create WO From
      EHS Inspection" (#5) actually writes — cross-check both workflows, don't assume
- [x] Child-task fetch confirmed at A7 (U1, exec 127255): `meta.associatedTask` is a **relative
      path** (`/v2/tasks/?tasks=NNNN`) — host-prepend fix applied; fetched child notes matched
      `body[0].completionNotes` and landed in the write-back string
- [x] Completion-note timestamp mechanics proven at A7 U1: `(Completed 07/25/2026 12:17 PM)` from
      epoch 1785003479 (then-Denver rendering). OQ-014 resolved Eastern 2026-07-25: formatting
      flipped to `America/New_York` same day — **Eastern rendering not yet re-executed; re-check
      at the cutover manual test below**
- [ ] Manual test run — completed parent WO + at least one completed child WO, confirm
      `UDFLimbleWOCompletionNotes` on the EHS inspection gets both notes concatenated
- [ ] Workflow ID assigned (OQ-007) and activated

## 7. Coupa Integration Error Log Export

- [ ] Coastal Coupa Error Log table ID confirmed correct (same table Step 1/Step 3 write to)
- [ ] Delete-only-exported-records fix in place (OQ-006 — do not port the delete-all race)
- [ ] Email recipient restored to `ethan@fm360consulting.com` (currently gerald@ dev-only)
- [ ] Manual test run — confirm report contents match table state, confirm delete only removes
      exported rows
- [ ] Workflow ID assigned (OQ-007) and activated (15-minute schedule)

---

## Cutover sequence (once all 7 are individually ready)

1. Turn off the corresponding live Fuse/Make scenario for each workflow, one at a time — don't
   run both systems against the same Limble/Coupa/EHS account in parallel.
2. Confirm Limble webhook subscriptions point only at n8n (see §0 above).
3. Activate n8n schedules/webhooks in dependency order: Token Regeneration first (Step 1/2/3
   depend on its output table), then Step 1, then Step 2, then Step 3, then the EHS pair, then
   Error Log Export last.
4. Watch first live cycle of each before moving to the next.
5. Keep the Fuse scenarios disabled-not-deleted until n8n has run clean for a few cycles.

## Rollback

Per workflow: deactivate the n8n workflow, re-enable the corresponding Fuse/Make scenario, revert
the Limble webhook subscription back to the old Fuse URL if it was changed. Coupa OAuth token
state lives in the Data Table, not shared with Fuse's datastore — Fuse will re-mint its own token
on next scheduled run, no manual token copy needed (unlike Deer Valley's FuelCloud token, which is
single-holder/rotating).
