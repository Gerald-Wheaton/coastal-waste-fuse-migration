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
- ✅ **S2-2 team-assigned — PASS 2026-07-24 (exec 127081, OQ-040 resolved):** real maintenance team
  **605550** created at loc 98472 via the seeder's new `coastal-seed-team` branch (`POST /v2/teams`),
  fixture WO **4213** (PO Requested 8055, meta1=424242, `@CoupaWO;`) seeded assigned to it. Step 2
  run: `Get Team` returned team 605550 (`automaticallyCreated:0`, real — was `[]` for role-team
  107065), `Post Team Comment` posted **commentID 7107** on 4213. Team-comment path proven end to
  end. (Same mechanism unblocks the Step 1 R1 team variant — team 605550 available if run.)
- ✅ **S2-err-oq019 — PASS 2026-07-26 (exec 127334):** re-test of the error path after the OQ-019
  fix inserted `Get Escalation Admin ID` ahead of `Get Admin User`. `failMode=getreq`, poll picked
  up the only 8055 WO (**4228**) → `Err: Requisition Fetch Failed` → error-log row **24**
  (`AxiosError` / "Mock get-requisition failure") → **`Get Escalation Admin ID` returned
  `value="398783"`** from Data Table `L0npQPPEXQI9JRzX` → `Get Admin User` resolved userID 398783
  → **admin comment 7141** on 4228. Status not flipped (4228 still 8055), fixture reusable.
  `failMode` reset to `""` after.

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
- ✅ **R1/R2 — COMPLETE 2026-07-26**: ✅ **user variant** (exec 126714): 4056 PATCHed to user
  398783 via `assignmentType/assignment`, re-fired s5 → Get Assigned User → Contractor Comment
  (User) 7049. ✅ **R2 admin-comment** covered by s6a/b/c. ✅ **team variant PASS (exec 127325,
  2026-07-26)**: 4056 re-PATCHed to real team **605550** (`assignmentType:team` → userID 0,
  teamID 605550), fresh trigger comment **7137** posted so it wins the strict-`>` latest-comment
  tiebreak, s5 re-fired → `Team Assigned?` true → `Get Assigned Team` (605550) →
  **Post Contractor Comment (Team) commentID 7138**, mention rendered
  `@Coastal TEST Maint Team (S2-2 DELETE)`. 29 nodes ran; no error-log row, no status flip
  (4056 still 8054), meta1 null — s5 asymmetry preserved.
  Error-log rows 16–19 left in table for inspection; delete before Step 3 error tests or filter id.
  **Regression found by this run (fixed same day):** first fire (exec **127324**) died at
  `Get Limble Users` — `last can't be used on undefined value`. The OQ-018 pagination fix
  applied 2026-07-26 used `{{ $response.body.last().userID }}`, and n8n evaluates that
  expression on the **first** request when there is no `$response` body, so *every* Step 1 run
  was failing ahead of all Coupa traffic. Corrected to
  `={{ $response?.body?.last()?.userID ?? 0 }}` (`cursor=0` probe-verified equivalent to
  omitting the param; `cursor=` empty → HTTP 400). Re-fire = exec 127325 PASS, 54 users in one
  page. Multi-page branch still unproven at runtime. See OQ-018 addendum + build-spec 9.1.
  **Fixture state now:** 4056 is team-assigned (605550), not user-assigned — re-PATCH if a
  future run needs the user variant.
- ✅ **s6c-oq019 — PASS 2026-07-26 (exec 127330):** re-test of the error path after the OQ-019 fix
  inserted `Get Escalation Admin ID` ahead of `Get Admin User`. Owner posted a fresh trigger
  comment on **4059** (`Status was changed from Open to PO Create` — needed, the prior latest
  comment was A4's admin comment and would have bounced the n08 gate) and activated the workflow;
  fired `{status:"ADDED COMMENT TO TASK", taskID:4059}` at `failMode=acct`. `Err: Account Missing`
  → error-log row **23**, message byte-identical to A4's row 18 → **`Get Escalation Admin ID`
  returned `value="398783"`** from Data Table `L0npQPPEXQI9JRzX` → `Get Admin User` resolved userID
  398783 → **admin comment 7140** on 4059. Workflow deactivated after; `failMode` reset to `""`.
  4059 unchanged (8054, meta1 null) — still reusable.

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
`due` → epoch seconds; `metadata.meta1` → top-level `String(meta1)`; ~~`@EHS;` → `@EHSWO;`~~
**(tag change REVERTED 2026-07-27 — back to `@EHS;`, OQ-038 reversal)**;
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

**RE-RUN REQUIRED — OQ-037 full fix applied 2026-07-26** (node `n07` "Filter To Latest Completed",
`jsCode` + `notes` rewritten; workflow still INACTIVE; build spec section 13). The dedupe semantics
changed, so execution 126934's dedupe assertion no longer describes the code under test. **Nothing
has been run against the fixed node — no pass may be claimed for it.**

- ☐ **A6 re-run (owner Execute)** — the 2026-07-21 block below stands as the historical record of
  the *pre-fix* code, not as current coverage. On re-run:
  - **A1/A2 expectation INVERTS:** the single Coastal 10 task must be **`FIC-1002`** (A2 — newer
    `UpdatedDtm`, submitted), `meta1 = EHS-INSP-A2`. `FIC-1001` winning would now be a failure.
  - **New case I (draft-only site, `BE-60`)** — must produce **zero** tasks; assert `EHS-INSP-I`
    is absent from `Filter To Latest Completed`'s output items (so the drop is attributable to
    the draft guard, not to a missing location/team downstream).
  - **New case J (`BE-30`, draft with a later `UpdatedDtm` than E, listed before E)** — E must
    still win; no task named `FIC-3001`. This is what distinguishes "drop drafts before dedupe"
    from "drop drafts after picking the max".
  - Net task count stays **5**, but the A-site winner changes (A2/B/C/D/E).
  - **Fixture prerequisite — SATISFIED 2026-07-27.** I and J are now in all three places:
    `ehs-auditinspection-list.json` (11 rows; **J sits immediately before E — that order is the
    test**), `ehs-inspection-fetch.json` (`EHS-INSP-I`, `EHS-INSP-J`), and the mock's inline
    `Build` node (`LIST` + `INSP`). Two new webhook/SET pairs were added to mock EHS
    `EBIzCJ0XJaJ5jUpp` (now 53 nodes) so `fetch/EHS-INSP-I` and `fetch/EHS-INSP-J` resolve;
    **all three endpoints probed live by curl — HTTP 200, and `RecurringTaskCompleteDtm: ""`
    survives the wire un-stripped** (the one shape risk in these cases). No republish was needed.
    No Limble re-seeding (I never reaches Limble; J reuses E's location/region/team). No
    regeneration of the existing fixtures — they already spell `UpdatedDtm`, which matches live EHS.
  - **Predicted outcome (dry-run of `n07`'s deployed `jsCode` over the 11-row set, 2026-07-27, not
    an execution):** survivors `A2, B, C, D, E, F, G`; `A1/H/I/J` absent; F drops at the region
    allowlist and G at the acceptable-answer gate → **5 tasks: FIC-1002, FIC-1200, FIC-2300,
    FIC-2400, FIC-3000**. The same dry-run confirms case J discriminates: a
    guard-*after*-dedupe implementation yields **4** tasks (E lost, no `FIC-3000`), and no guard
    at all leaves J and I in the survivor set. Treat this as the expected-value sheet for the
    re-run, not as coverage.
  - Everything else in the suite (B/C/D/E/F/G/H, image vs non-image, OQ-035, OQ-038 tag, OQ-043
    guards) is unaffected by the change but re-runs in the same single Execute.

**SUITE PASSED 2026-07-21, execution 126934 — pre-OQ-037-fix code; superseded by the re-run above**
(first attempt 126921 crashed: n28 body used
`$json.questionList.Verification` — wrong item context, `$json` = Limble instruction object →
`undefined` body; fixed to `$('Extract Last Question').item...` mirroring n27; orphan task 4191
deleted):

- ✅ **Single Execute covers A1+A2, B, C, D, E, F, G, H** → exactly **5** tasks created
  (4192–4196 = A1/B/C/D/E); G dropped at acceptable-answer gate, F dropped at region allowlist
  (BE-99), H + A2 never reached the form split (QuestionsSelector filter / dedupe)
- ✅ Per-task assertions: name `EHS Facility Inspection Checklist Deficiencies - <FormNumber>`,
  meta1=RowUID (top-level string), correct location + team (602733–602737), `@EHSWO;` tag
  **[STALE 2026-07-27: node now stamps `@EHS;` — this assertion must be re-pointed and A6's
  description check re-run; everything else in A6 is unaffected]**
  (OQ-038 fix), due=now+7d epoch, instruction PATCH verbatim
  `"Deficiencies from Inspection:  <Verification>"` (double space) on instrs 14936–14940
- ~~✅ OQ-037 dedupe-typo proof: A1 won over A2 (task 4192 = `FIC-1001`, no FIC-1002 task)~~
  **→ ASSERTION INVALID as of 2026-07-26.** It verified the *pre-fix* first-seen behavior, which
  the OQ-037 full fix removed. Superseded by the inverted A1/A2 expectation in the re-run block
  above; this line is retained only as the record of what the old code did.
- ✅ Image (B) vs non-image (C) vs no-attachment (D) branches — B (4193): `Attach Instruction
  Image` PUT fired, `instructionFiles[]` gained `178460441194564-deficiency-photo.png`;
  C/D: verbiage-only PATCH, PUT not reached; OQ-035
  summary-question rule respected (B used B-Q3, correctly ignored B-Q1) — confirmed by-design
  2026-07-26, OQ-035 closed

### A7. EHS Update Inspection suite (`8JvtesynrYtZbw7U`) — webhook-fired; run last, reuses A6 outputs or seeded parents

Staging — READY 2026-07-25: EHS URLs (n11 fetch + n13 update) → mock-EHS host (revert at
cutover); mock's `fetch EHS-INSP-UPD-1` + `update` routes verified by curl (`{Entity:{...}}`
shape matches n12); Limble/EHS credentials attached. **Fixtures rebuilt** (old 4198-plan
skeletons scrapped — full story + mechanism in `sandbox-seed-record-a6.md`): **U1 parent =
4218** (`@EHSWO;`+meta1, completed, exact note) with children **4220 + 4222**, spawned via
**type-14 "Work Order" instructions** — the only mechanism that stamps `meta.associatedTask`
(confirmed against prod template 842; one type-14 instr per child, UI "Start another WO");
**4201**=U3 non-EHS (as-is); U4 optional, needs a fresh zero-children parent. **Three port
fixes approved + applied 2026-07-25** (permanent — no cutover revert): n05 `?limit=100`
(page-size-2 clip dropped children 2+), n06 `meta?.associatedTask` (plain `.meta.` threw on
the meta-less text instruction), n07 host-prepend (`meta.associatedTask` is a relative path
`/v2/tasks/?tasks=NNNN`, not a full URL — OQ-009 assumption resolved). Residual: dangling
type-14 instr **15056** on 4218 → deleted task 4221; delete it before U1, or accept as an
adversarial deleted-child case (watch for `undefined` in notes).

> ⚠️ **A7 RESULTS INVALIDATED 2026-07-27 — gate literal changed under them (OQ-038 reversal).**
> `WO is an EHS WO?` (n04) now tests `description contains "@EHS;"`, not `"@EHSWO;"`. The A7
> parent fixtures still carry the **old** literal — verified read-only 2026-07-27:
> **4218** = `"EHS deficiency parent fixture @EHSWO;"`, **4202** = `"EHS parent fixture zero
> children @EHSWO;"`. `"@EHSWO;"` does **not** contain `"@EHS;"` (after `@EHS` it continues
> `WO;`), so **U1 and U4 would now drop at the gate** — the passes below no longer demonstrate
> what they claim. Everything they proved *downstream* of the gate (limit fix, optional-chain,
> host-prepend, note formatting, zero-children rewire) is unaffected in logic but unverified
> against the current config.
> - **U2 stays valid** (exec 127253) — drops at `Is Completed?`, never reaches the gate.
> - **U3 stays valid** (exec 127254) — negative fixture **4201** has description
>   `"ordinary WO, no EHS tag"` and `meta1: null`, so it drops under either literal.
> **Fixtures RE-SEEDED 2026-07-27 — done.** Both descriptions PATCHed via
> `PATCH /v2/tasks/{id}` (HTTP 200 each), preflighted on `locationID == 98472` + expected name
> before writing, and read back:
> - **4218** → `"EHS deficiency parent fixture @EHS;"`, `customTags` `['@EHSWO']` → **`['@EHS']`**
> - **4202** → `"EHS parent fixture zero children @EHS;"`, `customTags` → **`['@EHS']`**
>
> Limble re-parsed `customTags` from the description automatically — no separate tag write needed.
> Note for anyone scripting against this API: Limble's WAF returns **403 / Cloudflare 1010** for
> the default Python-urllib User-Agent; set an explicit UA (already documented at
> `tools/sandbox-seed/seed.py:74`).
>
> **RE-RUN 2026-07-27 (owner-authorized activation; workflow activated, fired, deactivated again).**
> Pre-flight before activating: confirmed n11/n13 still point at the **mock-EHS** host and n03 uses
> the **sandbox** Limble credential, so no live EHS write and no prod Limble touch. Mock EHS
> (`EBIzCJ0XJaJ5jUpp`) confirmed active first.
>
> - ✅ **U1 RE-VALIDATED — exec 127376.** Gate matched `@EHS;` (1 item, true branch) → full chain →
>   `EHS: Update Inspection` returned `{Success: true, Message: "Inspection updated (MOCK)"}`.
>   Write-back string exact, both child notes concatenated with the verbatim leading space.
>   **Bonus: this also closes n10's "formatting re-verify pending post-flip" note** — the
>   timestamp now renders `(Completed 07/25/2026 02:17 PM)`, which is correct
>   **America/New_York** for epoch 1785003479 (the old `12:17 PM` was the pre-OQ-014 Denver
>   rendering; Denver=12:17, New_York=14:17, UTC=18:17 — verified by calculation). The 2026-07-25
>   U1 line below still quotes the stale Denver string.
> - ⚠️ **U4 first attempt fired against the WRONG fixture (my error) — exec 127379, discard.** I
>   fired **4202**, the *stale, scrapped* U4 skeleton (`dateCompleted: 0`, **zero instructions**).
>   The fixture that produced the 2026-07-25 U4 pass is **4223**. The 4202 PATCH was wasted effort
>   on a dead fixture — but the mis-fire paid for itself, see the NEW GAP note below.
> - ✅ **U4 RE-VALIDATED — exec 127384, on the correct fixture 4223.** 4223's description PATCHed
>   to `"EHS parent fixture zero children @EHS;"` (owner ran the curl; HTTP 200, read back
>   `customTags: ['@EHS']`, `locationID: 98472` guard-checked). Chain: gate matched `@EHS;` →
>   `Collect Child Links` emitted **1 item** `{childLinks: []}` (the always-1-item rewire holding
>   under the new gate) → `Any Child Links?` took the **false** branch with 1 item →
>   `Build Child Completion Notes` → `childWOCompNotes: ""` → write-back
>   `"(Completed 07/25/2026 05:37 PM)\n…\nU4 zero-children parent completed.\n"` →
>   `EHS: Update Inspection` returned `{Success: true}`. Zero-children path writes back, which is
>   the whole point of the 2026-07-25 rewire — **confirmed still working after the gate flip**.
>   Timestamp cross-checks as America/New_York for 4223's `dateCompleted` 1785015466 (3h20m after
>   4218's, matching U1's 02:17 PM).
>
> **NEW GAP FOUND by the mis-fire (exec 127379) — worth keeping.** The 4202 run passed the
> `@EHS;` gate, then **stopped dead at `Get Instructions` with 0 items out**: `Collect Child
> Links` never executed, so the whole write-back tail was skipped and the execution still
> reported **"success"** with no EHS write. This is the **OQ-045 zero-input-skip class, unfixed in
> this workflow** — and it is one level *earlier* than the U4 case the 2026-07-25 rewire fixed
> (that one was "≥1 instruction but zero child-linked"; this is "zero instructions at all").
> `alwaysOutputData` was applied to `Get Instructions` on **Step 1 + Step 3** under OQ-045 but
> **not** here. Reachability in prod: template 842 always creates 3 instructions, so this needs
> someone to have deleted them all — low, same profile as OQ-045's accepted residual. Decide
> document-vs-fix; not fixed unilaterally.
>
> **A6 SIDE RE-VERIFIED + CLOSED-LOOP PROVEN 2026-07-27 — OQ-038 fully settled.**
> Owner Execute-clicked `isLUx7cUjkmKggD2` (**exec 127388**, manual, workflow left inactive).
> Pre-checked first: all 5 EHS nodes on the mock host, all Limble nodes on the
> `Gerald Limble Sandbox` credential.
>
> - ✅ **A6 description assertion CLOSED.** 5 tasks created — **4234** (FIC-1002), **4235**
>   (FIC-1200), **4236** (FIC-2300), **4237** (FIC-2400), **4238** (FIC-3000) — *all five* with
>   `description … @EHS;` and `customTags: ["@EHS"]`. Read from Limble, not from config.
>   F/G/H correctly produced nothing (no FIC-9900, no FIC-4000, no VEH-5000).
> - ⚠️ **A1/A2 EXPECTATION NOW INVERTED — `ehs-test-plan.md` is stale here.** This run's
>   A-scenario winner was **FIC-1002 / `meta1: EHS-INSP-A2`**, where every prior run produced
>   FIC-1001 (A1). **Not a regression:** a parallel session applied the **OQ-037 fix on
>   2026-07-26** (`Filter To Latest Completed` now spells `UpdatedDtm` on both sides *and* hoists
>   the `RecurringTaskCompleteDtm` draft check out of the formerly-dead branch — their node notes
>   cite 86/86 live prod records carrying `UpdatedDtm`). Latest-completed-wins is now the correct
>   behavior, so **A2 beating A1 is the pass condition going forward.** The test plan's "must
>   contain FIC-1001, not FIC-1002" needs flipping.
> - ✅ **CLOSED LOOP Create→Update PROVEN — exec 127410.** The gap the test plan had deferred
>   ("until a real Create→Update closed-loop test") is now closed. **4237**, created by EHS Create
>   with its own `@EHS;` stamp, was completed and fired at Update: gate matched on Create's
>   genuine output → `meta1: EHS-INSP-D` routed to the matching mock inspection → write-back
>   `{Success: true}`, timestamp `(Completed 07/27/2026 02:23 PM)` (America/New_York for epoch
>   1785176616). **The two literals are now verified to match in practice, not by assumption** —
>   which was the whole substance of OQ-038.
>   - Caveat: 4237's `completionNotes` is `""`, so the write-back's parent-notes section is empty.
>     `completionNotes` and `dateCompleted` are **not API-writable** (`is not allowed` on PATCH);
>     only a UI completion populates them. Note *concatenation* was already proven by U1/U4, so
>     this does not weaken the result.
>   - **Limble completion contract learned here:** `PATCH /v2/tasks` **rejects built-in statuses
>     on `statusID`** (both `2` and `0` → 400 `` `statusID` contains an invalid value ``), though
>     custom statuses like 8054 are accepted. Completion goes through
>     `{"status":1,"assignmentType":"team","assignment":<teamID>}`, which sets `statusID:2` and
>     `dateCompleted` as side effects. A task cannot be PATCHed back to Open afterward. This
>     corrects `limble-sandbox-fixtures.md`'s "complete (API + UI)" phrasing.
>
> **Net state:** OQ-038's flip to `@EHS;` is execution-verified on **both** workflows and
> end-to-end. Both left **inactive**. Remaining follow-ups: flip the A1/A2 expectation in
> `ehs-test-plan.md`, and the zero-instruction gap decision below.

- ✅ **U1** PASS (exec 127255, 2026-07-25) — **see invalidation note above; re-run required**: Get Instructions returned all 4 instrs (limit fix
  proven), Has Child WO? passed 3 type-14s no-throw (optional-chain proven), write-back exact
  §4.3 string — `(Completed 07/25/2026 12:17 PM)` from parent dateCompleted 1785003479 (epoch-secs
  + Denver tz proven), both child notes concatenated w/ verbatim leading space, mock returned
  `Success:true` for `EHS-INSP-UPD-1`, zero `undefined`
- ✅ **U1 bonus — deleted-child resilience:** dangling type-14 instr 15056 → deleted task 4221 was
  left in place; its fetch returned empty → contributed zero items, no `undefined`. Orphaned
  child-links degrade gracefully
- ✅ **U2** PASS (exec 127253, 14ms): 2 nodes only (Webhook → Is Completed?), zero Limble/EHS calls
- ✅ **U3** PASS (exec 127254): 4 nodes; Get Task fetched 4201, `@EHSWO;`/meta1 gate dropped it, no
  EHS fetch/update
- ✅ **U4** PASS after sanctioned rewire (2026-07-25). First run (exec 127258, parent 4223)
  **confirmed the silent-stop fidelity gap**: `Has Child WO?` kept 0 items → entire write-back
  tail skipped (6/13 nodes), exec "success" but EHS never updated — source Make aggregator emits
  an empty bundle on zero inputs and would have written back. **Owner-approved rewire applied**
  (workflow now 15 nodes): `Has Child WO?` filter replaced by `Collect Child Links` (Code,
  always 1 item w/ link list) → `Any Child Links?` (IF) → true: `Split Child Links` →
  Get Child Task → Aggregate → Build; false: straight to Build (yields `childWOCompNotes:""`);
  Get Child Task now reads `$json.childLinks`. Re-run PASS (exec 127259): false branch, write-back
  reached mock EHS w/ parent-note-only string, no `undefined`. **U1 regression PASS**
  (exec 127262): byte-identical write-back to 127255, dangling-4221 link still harmless
- ✅ OQ-036 negative: 13-node structure pull 2026-07-25 — no comments-fetch node, no `lastComment`;
  Is Completed? feeds Get Task directly

### A8. Wrap-up gates (before declaring Phase A done)

- ☐ Reset all failMode rows to `""`; verify capture tables archived/cleared as desired
- ☐ Sandbox teardown per each plan's §6–7 (dud tasks 4080–4082, consumed fixtures) — or defer to
  cutover teardown in `DEPLOYMENT.md` §3; pick one, record it
- ☐ Doc debt: Step 2 build-spec §72/§203 `metadata.metaN` → top-level + `String()`
- ☐ Decisions that block cutover, chase in parallel with the grind: OQ-011/OQ-014 (timezone →
  final crons), OQ-019 (who is 317887), OQ-018 (500-user cap), OQ-013 (export self-error),
  Token-Regen failure-email recipient. (**OQ-037 closed 2026-07-26** — field name settled from
  live EHS, owner sanctioned the full fix, applied to `n07`; no longer a decision, it is now the
  A6 re-run above. OQ-035 closed 2026-07-26 — intended behavior per the EHS review docx, no ask
  needed.)
- ☐ **A6 re-run against the OQ-037-fixed `n07`** (see A6) — Phase A is not done until this runs;
  the 2026-07-21 A6 pass covers pre-fix code only
- ✅ **Coupa test instance** — `coastalwasteinc-test.coupahost.com` (found 2026-07-13 in the
  standing token-table row; **OQ-039 resolved 2026-07-25**): owner decision is **no
  test-instance pass**. Real Coupa/EHS response shapes get examined at go-live under the C4
  first-shepherd watch, Fuse disabled-not-deleted as rollback. The stale `Coastal_Waste (TEST)`
  token row (id 1, expired JWT) is deleted at cutover table cleanup — `DEPLOYMENT.md` section 1.
- ✅ **OQ-028 closed 2026-07-26** — the mock-rig tracking entry retired: item 1 (guessed shapes)
  folded into the C4 watch above, item 2 (teardown) superseded by `DEPLOYMENT.md` sections 1-7
  and Phase B below, residual R1-R4 all closed (R1-team PASS exec 127325, see A4).

---

## PHASE B — Cutover mechanics (not tests, but every Phase C observation depends on them)

Full authoritative list = `DEPLOYMENT.md`. Test-relevant reverts, per workflow as it ships:

- ☐ Mock hosts → real hosts (Coupa ×2 in Step 2, ×6 in Step 1, Step 3's; EHS hosts in both EHS
  workflows; Token Regen token URL)
- ☐ Limble sandbox cred → Coastal prod cred (every Limble node)
- ☐ Escalation admin: flip **one** row — `escalation_admin_user_id` in Data Table
  `Coastal - Integration Config` (`L0npQPPEXQI9JRzX`) from `398783` → `317887` (covers Step 1
  **and** Step 2; the `Get Admin User` nodes no longer hold a literal — OQ-019 fix 2026-07-26)
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
  prod may have more); duplicate-run behavior on day 2
- ☐ **WATCH — OQ-037 fixed dedupe, first exposure to real EHS data** (resolved 2026-07-26, full
  fix applied to `n07`; prod has never run this logic). Two behavior changes to confirm live, both
  restoring documented docx requirements that never worked in Make:
  1. **Draft exclusion (docx line 69):** a site whose only in-window SOP is an un-submitted draft
     now yields **zero** WOs where Fuse would have created one from the draft. Expect a *lower* WO
     count than Fuse on such days — that is correct, not a miss. Distinguish it from the OQ-047 #2
     window loss below (different cause, similar symptom: no WO and nothing logged).
  2. **Latest-submitted-wins (docx line 72):** on a site with several submitted SOPs in the
     window, the WO's `meta1` now carries the **latest** inspection's RowUID, not the first one
     EHS returned. Sanity-check one such WO's `meta1` against EHS.
  Live evidence says this will actually trigger: the `AuditInspection/list` probe saw **86
  inspections across only 31 sites** in 72h. Unquantified caveat carried forward — that span
  covers all 21 question sets, not the "Facility Inspection Checklist" selector in a 24h window,
  so collision frequency on this path is likely but unmeasured. Worth capturing on the first runs:
  how many sites actually hit the multi-inspection path, and how many drafts get dropped per day.
- ☐ **WATCH — OQ-047 #2, `CreatedAfter` vs `DatePerformed` (silent data loss).** The list call
  filters on `CreatedAfter=now-24h`; the EHS review docx specifies `DatePerformed`. An
  inspection drafted one day and submitted the next falls outside the window, never becomes a
  WO, and **nothing logs the miss** — it is invisible from the Limble side, which is why this
  could not be settled pre-cutover. This is the first run where real EHS data can answer it.
  Two things to capture on the first live runs:
  1. Does the real `AuditInspection/list` response support / expose a `DatePerformed` filter or
     field? (Settles whether a fix is even available.)
  2. Compare the count of completed Facility Inspection Checklists in EHS for the day against
     the count the workflow actually pulled. A gap = confirmed misses. **Prior baseline for
     scale:** prod Limble holds only **10** EHS WOs for 2025-10-30 → 2026-07-13 (~1/month)
     across 45 EHS-enabled locations — low enough that a systematic miss is plausible, though
     rare WO-worthy deficiencies explain it equally well.

### C7. EHS Update Inspection — last

- ☐ First real completed EHS WO: `updateAnInspection`/`updateAnInstruction` endpoint+method were
  **guessed** (PATCH) — this is the first proof; write-back accepted by real EHS
- ☐ WATCH: child-task `meta.associatedTask` resolves on real data; completion-note timestamp in
  **America/New_York** (was written here as America/Denver — corrected per the A7 U1 re-run, exec
  127376, which rendered `(Completed 07/25/2026 02:17 PM)`, the correct New_York value for epoch
  1785003479); **`@EHS;`** gate matches what C6 actually stamped (literal changed from `@EHSWO;`
  on 2026-07-27, OQ-038 reversal — and note this gate now also matches the **5 pre-cutover prod
  EHS WOs still open**: 2787, 2877, 3097, 3163, 3237. Those will start flowing through Update as
  they complete, which is the intended effect, not a surprise.)

### C8. Steady-state watch window (first 1–2 weeks)

- ☐ Error-log table review daily; every row triaged (shape mismatch vs. transient)
- ☐ Confirm old Fuse scenarios stayed off (no duplicate PRs/comments/WOs — the definitive
  OQ-020 check)
- ☐ Keep Fuse scenarios intact-but-disabled as the rollback lever until the window closes;
  rollback = repoint Limble webhooks back + reactivate Make scenarios
- ☐ First DST transition after go-live: verify the 3 schedules fire at intended local times
