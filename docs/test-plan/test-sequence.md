# Test Execution Sequence — remaining grind, pre-go-live vs. post-go-live

Status date: 2026-07-13. Source docs: `coupa-test-plan.md`, `ehs-test-plan.md`,
`handoffs/handoff-6193.md`, `DEPLOYMENT.md`. Scenario IDs below refer to those plans.

Two hard boundaries shape this sequence:

1. **Pre-go-live testing = mock Coupa + mock EHS + live Limble sandbox (loc 98472) only.**
   Real Coupa and real EHS Insight are never called before cutover (OQ-003). Mock response
   shapes are reverse-engineered guesses (OQ-028, OQ-009) — passing the mock suite proves our
   logic, **not** the real APIs.
2. **Schedule-triggered workflows can't be fired headless via MCP** — Token Regen, Step 2,
   EHS Create WO, Error Log Export each need an owner **Execute Workflow** click per scenario.
   Webhook-triggered workflows (Step 1, Step 3, EHS Update) fire via `curl`, no clicks needed.

Legend: ☐ not run · ✅ passed · ◐ partial/awaiting-decision · each numbered block is sequenced —
do them in order unless noted.

---

## PHASE A — Pre-go-live (mock + sandbox; executable now)

### A1. Finish Step 2 suite (`WYJyHdQGcdeD8wEr`) — mid-flight, staged, resume here

Continues handoff-6193 "Next steps" exactly.

- ✅ S2-4 happy path, neither-assigned (exec 126546, 2026-07-09)
- ✅ **S2-idem** — Execute, `failMode=""`: poll returned 0 WOs, zero writes (exec 126645, 2026-07-13)
- ✅ **Re-seed** fresh PO-Requested fixture (`/webhook/coastal-seed-step2` → new 8055 +
  meta1=424242 WO 4097) — seeder extended to take optional `label`/`userID`/`teamID`
- ✅ **S2-1** `failMode=reqpending` → WO untouched, requisition not ordered (exec 126648)
- ✅ **S2-err-getreq** `failMode=getreq` → +1 row in error-log table `6GbR5Rxezl7hqk9i`,
  admin comment 7027 to sandbox user **398783** (exec 126650)
- ✅ **S2-err-getpo** `failMode=getpo` → +1 row + admin comment 7028 (exec 126652)
- ✅ Reset `failMode=""` in config table `YkCIlyx7lUUNs7vG`
- ✅ **S2-3 user-assigned** → "Post User Comment" 7038 to userID 398783 on WO 4101 (exec 126665)
- ☐ **S2-2 team-assigned — BLOCKED (OQ-040):** routing correct, but `Get Team` (`/v2/teams?teams=`)
  returns `[]` for sandbox team 107065 (a "View Only" role-team the endpoint won't list). Needs a
  real maintenance team at loc 98472 (also unlocks Step 1 R1/R2, A4) or defer to Phase C.

### A2. Token Regeneration suite (`oCAl4h0SZenEtbNs`) — small; do early, it's also the go-live canary

Staging needed first: swap `Refresh Coupa OAuth Token` URL → `mock-coupa/oauth2/token`; confirm
token row `client=coastal_waste` seeded with a `scope` value. Log the swap in `DEPLOYMENT.md` §
revert list.

- ✅ **Staged** — URL → `…/webhook/mock-coupa/oauth2/token`; revert row logged in `DEPLOYMENT.md` §1
- ✅ **T1** happy refresh: token row → `MOCK-TOKEN-COUPA-REFRESHED`, `refreshed_at`≈now,
  `grant_type=client_credentials` + scope sent (exec 126675, 2026-07-13)
- ✅ **T2** `failMode=token`: 3 retries → error branch → Ionos alert email landed at gerald@;
  token row unchanged (exec 126677)

### A3. Error Log Export suite (`hR5YnDixecDz9HzJ`) — no mock needed; run right after A1 error rows exist

- ✅ Cleared error-log table, seeded rows 9001 + 9002 per `datatable-seed-rows.json`
- ✅ **E1** drain + email + OQ-006 partial-delete proof: email to gerald@ listed only 9001+9002
  (Mountain-time 08:05/08:07 AM); delete scoped to reported ids [12,13] only, 9003 survived
  (exec 126681, 2026-07-13). Note: delete is ID-scoped, so 9003 survives regardless of insert timing
- ✅ **E2** empty table: clean no-op — only trigger + Get-rows ran, no email, no delete (exec 126682)

### A4. Step 1 suite (`WJSs6apAdVH5yKkq`) — largest block; webhook-fired, no owner clicks

Staging first: 6 Coupa URLs → mock host; token row present; Limble sandbox cred confirmed on all
Limble nodes; sandbox tasks seeded per coupa-test-plan §4. All scenarios fire via curl
(`{status:"ADDED COMMENT TO TASK", taskID}`).

**SUITE COMPLETE 2026-07-14** (all scenarios pass except R1-team, deferred on OQ-040). Staged
2026-07-13 (6 Coupa URLs→mock, admin 317887→398783 — DEPLOYMENT §2 revert rows); workflow was
activated for the webhook fires and **deactivated again at suite end**; failMode reset to `""`.
Fixture findings hit on the way: file responses on re-seeded tasks were `[]` (owner re-uploaded
PDFs to 4054/4057/4060 + set 4055 amount→400); `meta1` cannot be cleared via API (rejects `""`
and `null`); instruction responses are UI-only (OQ-042).

- ✅ **s1** happy, >$500, capex=Yes (2026-07-14, on 4057 after owner PDF upload): full capture
  chain users→addresses→accounts (seg-4=**160999**)→suppliers→create-req→**attachments POST w/
  real PDF link** (capture rows 52–57); 4057 → statusID 8055 + meta1="424242"
- ✅ **s2** ≤$500 — covered by the s4 combo fire (owner set 4055 amount→400): capture ends at
  create-req (unit-price 400), **no attachments call**, flip + meta1 still happen
- ✅ **s3** capex=No: seg-4=**612200** (exec 126688, row 30); full-chain re-run 2026-07-14 after
  PDF upload → 4054 flipped 8055 + meta1. (First run's quote-less attach error deleted; it
  pre-proved the OQ-017 own-error shape)
- ✅ **s4** `A & B Services` → captured query decoded clean (`display-name=A & B Services`,
  single-encoded, no `%2526`) — rows 31 (2026-07-13) + 67 (combo fire 2026-07-14)
- ✅ **s5** supplier missing (exec 126694, 2026-07-13): suppliers `[]`, no create-req, Plain
  contractor comment 7041, **no** error-log row, no flip
- ✅ **s6a** `user` (exec 126699): error row `{400, Site Manager…not found}` on 4059 + admin
  comment 7042 via sandbox 398783
- ✅ **s6b** `addr`: error row names "Coastal Ninety Nine" (NumberToSpelled proven) on 4058
- ✅ **s6c** `acct`: error row `Selected Account (CWR-099-999-612200-###-Other Operating)…` —
  capex-blank fallback proven on 4059
- ✅ **s7** `createreq` (exec ~126710): error row carries mock 500 body verbatim on 4060, no flip
- ✅ **s8** `failMode=attachq` (2026-07-14, on 4060 after PDF upload): create-req succeeded, attach
  500 → error row 20 = **Attach Quote's own** "Mock requisition-attachment failure" (OQ-017 proof),
  4060 NOT flipped (8054, meta1 null)
- ✅ **idem** (exec 126687, ran FIRST on 4052 as-found with meta1 set): early-exit at "No Existing
  Requisition?", zero Coupa traffic
- ◐ **R1/R2**: ✅ **user variant** (exec 126714): 4056 PATCHed to user 398783 via
  `assignmentType/assignment`, re-fired s5 → Get Assigned User → Contractor Comment (User) 7049.
  ✅ **R2 admin-comment** covered by s6a/b/c. ☐ **team variant** still blocked on OQ-040.
  Error-log rows 16–19 left in table for inspection; delete before Step 3 error tests or filter id.

### A5. Step 3 suite (`NH1giNups8iICMZe`) — webhook-fired

**SUITE COMPLETE 2026-07-14.** Staged: 4 Coupa URLs → mock (DEPLOYMENT §4 revert rows); activated
for the fires, deactivated after; failMode reset `""`. Fixtures: 4053 (owner added "Upload Invoice
Here" instruction + PDF in UI — initial leading-quote typo `"Upload Invoice Here` proved the
matcher is exact-equality); 4055 (meta2=555001 PATCHed on via API). Learned: tasks with ZERO
instructions (Step 2 seeder WOs like 4097) halt at Get Instructions (0 items) — faithful to Make's
empty-bundle behavior, but pick instr-bearing fixtures.

- ✅ **S3-1** invoice happy (rows 79–81): PO fetched **by id** `{"id":"555001"}` (OQ-030 proven),
  poAttachment POST w/ real invoice link, "@Jordan Buyer" comment, 0 error rows
- ✅ **S3-2** no invoice (via the typo'd first fire on 4053): PO by id + comment posted, **no
  attach**, 0 error rows
- ✅ **S3-3** `failMode=poattach` (rows 82–83 + error row 22): attach 500 → error-log +1 "Mock
  PO-attachment failure", comment **NOT** posted
- ✅ **S3-4** `failMode=pocomment` (error row 21, on 4055): comment 500 → error-log +1

### A6. EHS Create WO suite (`isLUx7cUjkmKggD2`) — owner Execute per run

**Pre-test fixes — APPLIED 2026-07-20** (see build spec §12 / DEPLOYMENT §5 permanent block):
`due` → epoch seconds; `metadata.meta1` → top-level `String(meta1)`; `@EHS;` → `@EHSWO;`;
instruction-update URL → `/v2/tasks/instructions/{id}` (support-confirmed); image write split out
of the verbiage PATCH into a new `Attach Instruction Image` node (`PUT .../image`, multipart field
`image` — route proven live on sandbox instr 13200); `EHS: Fetch Attachment` → `responseFormat:
file`. OQ-042 resolved — not a blocker (nodes write verbiage, which IS updatable; only the
answer/`response` field is API-immutable).

Staging — APPLIED 2026-07-20: EHS URLs → mock-EHS host (5 nodes) + credential `ZEf4C1rpYSbBgLbX`
attached; Limble sandbox cred already in place; A1–H fixtures live inline in the mock's Build
node; mock attachment route serves real binary PNG w/ `Content-Disposition` filename (verified by
curl). Sandbox locations/regions/teams/template seeded 2026-07-20 (owner locations + API-seeded
rest; teardown ledger `sandbox-seed-record-a6.md`).

**SUITE PASSED 2026-07-21, execution 126934** (first attempt 126921 crashed: n28 body used
`$json.questionList.Verification` — wrong item context, `$json` = Limble instruction object →
`undefined` body; fixed to `$('Extract Last Question').item...` mirroring n27; orphan task 4191
deleted):

- ✅ **Single Execute covers A1+A2, B, C, D, E, F, G, H** → exactly **5** tasks created
  (4192–4196 = A1/B/C/D/E); G dropped at acceptable-answer gate, F dropped at region allowlist
  (BE-99), H + A2 never reached the form split (QuestionsSelector filter / dedupe)
- ✅ Per-task assertions: name `EHS Facility Inspection Checklist Deficiencies - <FormNumber>`,
  meta1=RowUID (top-level string), correct location + team (602733–602737), `@EHSWO;` tag
  (OQ-038 fix), due=now+7d epoch, instruction PATCH verbatim
  `"Deficiencies from Inspection:  <Verification>"` (double space) on instrs 14936–14940
- ✅ OQ-037 dedupe-typo proof: A1 won over A2 (task 4192 = `FIC-1001`, no FIC-1002 task)
- ✅ Image (B) vs non-image (C) vs no-attachment (D) branches — B (4193): `Attach Instruction
  Image` PUT fired, `instructionFiles[]` gained `178460441194564-deficiency-photo.png`;
  C/D: verbiage-only PATCH, PUT not reached; OQ-035
  last-only respected (B used B-Q3, ignored B-Q1)

### A7. EHS Update Inspection suite (`8JvtesynrYtZbw7U`) — webhook-fired; run last, reuses A6 outputs or seeded parents

Staging — PARTIAL 2026-07-21: EHS URLs (n11 fetch + n13 update) → mock-EHS host (revert at
cutover); mock's `fetch EHS-INSP-UPD-1` + `update` routes verified by curl (`{Entity:{...}}`
shape matches n12); Limble/EHS credentials already attached. Fixture skeletons seeded (real IDs
replace plan's 9001/9101/9102/9002/9003): **4198**=U1 parent (`@EHSWO;`+meta1), **4199/4200**=
children, **4201**=U3 non-EHS, **4202**=U4 parent. **BLOCKED on owner UI steps** — completion
notes, dateCompleted, and child-WO instruction links are NOT API-writable (probed 2026-07-21);
see owner checklist in `sandbox-seed-record-a6.md`. Run risk: API-created instructions carry no
`meta` key — `Has Child WO?` reads `$json.meta.associatedTask` and may error on meta-less
instructions; U1/U4 will reveal.

- ☐ **U1** parent completed w/ 2 children → capture row `inspectionID=EHS-INSP-UPD-1`,
  `udfCompletionNotes` = exact §4.3 concat string (parent + both child notes, Denver-tz timestamp)
- ☐ **U2** non-completion payload → drops at `Is Completed?`, zero calls
- ☐ **U3** completed non-EHS WO 9002 → drops at `@EHSWO;`/meta1 gate
- ☐ *(optional)* **U4** zero-children parent 9003 → Aggregate empty-input behavior
- ☐ OQ-036 negative: dead comments-fetch/lastComment nodes confirmed absent

### A8. Wrap-up gates (before declaring Phase A done)

- ☐ Reset all failMode rows to `""`; verify capture tables archived/cleared as desired
- ☐ Sandbox teardown per each plan's §6–7 (dud tasks 4080–4082, consumed fixtures) — or defer to
  cutover teardown in `DEPLOYMENT.md` §3; pick one, record it
- ☐ Doc debt: Step 2 build-spec §72/§203 `metadata.metaN` → top-level + `String()`
- ☐ Decisions that block cutover, chase in parallel with the grind: OQ-011/OQ-014 (timezone →
  final crons), OQ-019 (who is 317887), OQ-035/OQ-037 (flag dispositions), OQ-018 (500-user cap),
  OQ-013 (export self-error), Token-Regen failure-email recipient
- ◐ **Coupa test instance exists** — `coastalwasteinc-test.coupahost.com` (found 2026-07-13 in the
  standing token-table row; tracked as **OQ-039**). Converts most Phase-C risk into Phase A **if**
  owner authorizes testing against it + supplies current test client creds. EHS sandbox still
  unknown — ask Coastal. Owner decision pending.

---

## PHASE B — Cutover mechanics (not tests, but every Phase C observation depends on them)

Full authoritative list = `DEPLOYMENT.md`. Test-relevant reverts, per workflow as it ships:

- ☐ Mock hosts → real hosts (Coupa ×2 in Step 2, ×6 in Step 1, Step 3's; EHS hosts in both EHS
  workflows; Token Regen token URL)
- ☐ Limble sandbox cred → Coastal prod cred (every Limble node)
- ☐ "Get Admin User" 398783 → real admin 317887 (Step 1 + Step 2)
- ☐ Mock token row purged; real client_id/secret in the isolated credential (OQ-005)
- ☐ EHS API key **rotated** and installed as n8n credential
- ☐ Email recipients restored (ethan@ on Export; Token-Regen recipient per decision)
- ☐ Limble webhooks 775/776/777 repointed to n8n URLs, **old Fuse subscriptions disabled**
  (OQ-020 — double-fire window)
- ☐ Final crons set per resolved timezone

---

## PHASE C — Go-live validation (can ONLY be observed live, post-swap)

Nothing here is testable pre-cutover: mocks can't prove real Coupa/EHS response shapes, real
credentials, real webhook delivery, or prod-scale data. Activate **one workflow at a time, in
this order** — each step de-risks the next, converting big-bang risk into canary risk.

### C1. Token Regeneration — first (lowest blast radius, proves real Coupa auth)

- ☐ First run: real token written to the token table; scope preserved
- ☐ WATCH: real OAuth endpoint shape vs. mock's guess; retry/alert path never exercised live

### C2. Step 2 — second (read-heavy; proves real Coupa GET shapes BEFORE Step 1 writes anything)

- ☐ First few 5-min polls: `Get Associated Requisition` / `Get PO Created From Req.` parse real
  JSON (the **OQ-028 guessed-shape risk lands here** — top risk of the whole cutover)
- ☐ WATCH: any pre-existing prod WOs in "PO Requested" get processed correctly on first poll
  (backlog surge); error-log table for shape-mismatch rows; no false status flips
- ☐ WATCH: meta1 population on real prod tasks (OQ-024 was sandbox-proven only)

### C3. Error Log Export — third

- ☐ First 15-min cycle with real rows (C2 shakeout will likely provide some): email reaches
  ethan@, only reported rows deleted
- ☐ WATCH: Mountain-time formatting on real timestamps across a DST boundary (OQ-011/OQ-014)

### C4. Step 1 — fourth (first real WRITE to Coupa)

- ☐ Shepherd the **first real task comment manually**: watch users/addresses/accounts/suppliers
  lookups against real Coupa data (segment codes were docx-derived, never API-verified — OQ-009)
- ☐ First real requisition created; quote attachment upload accepted by real Coupa
- ☐ WATCH: webhook fires exactly once (OQ-020 double-fire); real admin 317887 receives error
  comments; supplier names with `&` encode correctly against real Coupa; listUsers >500 silent
  miss (OQ-018) — check prod Coupa user count once, early
- ☐ WATCH: end-to-end Step 1 → Step 2 chain completes on a real PR→PO conversion

### C5. Step 3 — fifth

- ☐ First real WO completion: PO fetched by id from real meta2; invoice file attaches to real PO;
  "@Jordan Buyer" comment lands (verify that user exists/still-relevant in prod Coupa)
- ☐ WATCH: real invoice file-link shape from prod Limble instructions

### C6. EHS Create WO — sixth (EHS has NEVER been called live — every field is OQ-009-grade)

- ☐ First daily 4:00 PM run: real EHS list/fetch response shapes; attachment-fetch **binary**
  expectation (node uses `responseFormat: file` since 2026-07-20 — if the real EHS endpoint
  returns JSON/base64 instead of raw bytes + `Content-Disposition` filename, the node needs a
  decode step); `createATask` field names verified against sandbox 2026-07-09, re-confirm on prod
- ☐ WATCH: rotated API key accepted; inspection volume vs. fixture-scale assumptions;
  real site Titles all resolve through `EHSLimbleLocationMapping` (fixtures covered 6 sites —
  prod may have more); duplicate-run behavior on day 2 (dedupe + OQ-037 disposition)

### C7. EHS Update Inspection — last

- ☐ First real completed EHS WO: `updateAnInspection`/`updateAnInstruction` endpoint+method were
  **guessed** (PATCH) — this is the first proof; write-back accepted by real EHS
- ☐ WATCH: child-task `meta.associatedTask` resolves on real data; completion-note timestamp in
  America/Denver; `@EHSWO;` gate matches what C6 actually stamped

### C8. Steady-state watch window (first 1–2 weeks)

- ☐ Error-log table review daily; every row triaged (shape mismatch vs. transient)
- ☐ Confirm old Fuse scenarios stayed off (no duplicate PRs/comments/WOs — the definitive
  OQ-020 check)
- ☐ Keep Fuse scenarios intact-but-disabled as the rollback lever until the window closes;
  rollback = repoint Limble webhooks back + reactivate Make scenarios
- ☐ First DST transition after go-live: verify the 3 schedules fire at intended local times
