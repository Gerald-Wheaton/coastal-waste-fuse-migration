# DEPLOYMENT — Coastal Waste, Fuse → n8n cutover

Personal checklist. Modeled on `../deer-valley/DEPLOYMENT.md` (see also
`DEPLOYMENT-REFERENCE-DOC.md` in this repo, which is that file copied over as a reference).
Coastal is bigger — 7 scenarios across 2 integrations (Limble⇄Coupa, Limble⇄EHS Insight) — so
this doc has one section per workflow instead of one flat list.

**Do not use this doc to build workflows.** It's the pre-publish gate: everything here is stuff
that must be true right before you flip a workflow live, not part of the build spec itself. Build
specs live in `docs/build-specs/`.

Status as of 2026-07-27: build complete; **Phase A testing complete** (A8 wrap-up aside). All 7 target
workflows exist and are **deployed inactive** (5 confirmed inactive via live read 2026-07-23 —
Token Regen, Step 3, Error Log Export, EHS-Create, EHS-Update; Step 1/Step 2 not re-listed this
pass, last known inactive after suite-end deactivation). The live test scoreboard is
`docs/test-plan/test-sequence.md`; this doc is only the pre-publish cutover gate.

**2026-08-01 — OQ-048 PORT EXECUTED.** The go-live target is now
`https://coastal.n8n.fm360consulting.com` (owner ruling 2026-07-30). All 7 workflows exist
there, inactive, **already in cutover config** (real Coupa/EHS hosts, prod templateID 842,
restored recipients, placeholder credentials) — which ABSORBS this doc's per-workflow [M]
staging-revert boxes for the coastal copies: the FM360 copies deliberately KEEP their test
config as the regression rig, so do NOT run the URL/cred/recipient reverts against FM360.
New coastal IDs (workflows, data tables, placeholder credentials, webhook URLs) + transform
receipts: **`docs/oq-048-port-ledger.md`** (authoritative until folded in here).

**CUTOVER EXECUTED 2026-08-01 ~18:07 UTC — all 7 coastal workflows ACTIVE, all 3 Limble hooks
repointed, all 7 Fuse scenarios disabled-not-deleted.** Every pre-activation gate listed here
is therefore closed: 4 credentials populated (all 4 now proven by live calls — see the
2026-08-03 review note in section 7), real Coupa PROD scope set, OQ-019 confirmed-by-use,
OQ-020 repoints done at cutover, section 7 Eastern re-run PASSED (exec 127523). What remains
is **Phase C shepherd watch**, not gating work — and the unproven paths listed in section 7's
2026-08-03 note.

Phase A suite status: **A1 Step 2 ✅** (incl. S2-2 team-comment — PASS 2026-07-24, exec 127081,
OQ-040 resolved) · **A2 Token Regen ✅** · **A3 Error Log Export ✅** · **A4 Step 1 ✅** (team
contractor-comment variant unblocked by OQ-040, not separately re-run — optional) · **A5
Step 3 ✅** · **A6 EHS Create WO ✅** (exec 126934, 2026-07-21) · **A7 EHS Update ✅ PASSED
2026-07-25** (U1–U4 + regression, execs 127253–127262 — see `test-sequence.md` A7) ·
**A8 wrap-up ☐**. **2026-07-27:** the OQ-038 tag
reversal (`@EHS;` both sides) was re-verified by execution — A7 U1/U4 re-ran green on re-seeded
fixtures (execs 127376/127384), A6 re-ran via owner click (exec 127388, tasks 4234–4238 all
`@EHS;`), and the **Create→Update closed loop was proven for the first time** (exec 127410:
Create's own task 4237 drove Update's gate to a successful mock write-back). The OQ-037 dedupe
fix (parallel session, 2026-07-26) also verified live — the A-scenario winner is now FIC-1002.
All Phase
A runs against mock Coupa + mock EHS + live Limble sandbox (loc 98472) — **no workflow has been
tested against the real Coupa/EHS APIs yet** (that is Phase C, post-cutover). Test rigs live:
Mock Coupa (`F05TiUurpc2kqxe0`), Mock EHS (`EBIzCJ0XJaJ5jUpp`), Limble seeder (`qyMChP0DKfI04r4a`).

---

## 0. Cross-cutting items (apply to more than one workflow)

### Cutover readiness triage (added 2026-07-27)

Every unchecked box below is tagged by **who can act on it**:

- **[M]** mechanical — ours, via MCP/API, no external input needed: node URL reverts off the mock
  hosts, Limble credential swaps to prod, email-recipient restores, mock-row/table cleanup,
  seeder-branch removal, sandbox fixture teardown. One focused pass, no blockers.
- **[EXT]** externally blocked — needs Coastal/Ethan, cannot be done from here:
  1. **OQ-020** — Limble webhook admin for the 3 webhook repoints (Step 1, Step 3, EHS Update).
     **Currently has NO owner**: Ethan reported 2026-07-27 he no longer has user access to
     Coastal's Limble. This is the critical path — it gates 3 of 7 workflows.
  2. **EHS key rotation** — see the corrected credential row below: the old exposed key still
     worked against live EHS on 2026-07-27, so rotation is unverified at best.
  3. **OQ-019** — one Coastal confirmation that `317887` (Brandon Ray Freckleton) is still the
     right escalation contact for the error-path @-mention.
- **[C]** Phase-C by design — first-live verification against real Coupa/EHS. OQ-039/OQ-028
  resolved that there is **no pre-cutover live pass**; these boxes close during the cutover
  watch (`test-sequence.md` Phase C), not before. Their mock-suite equivalents are already ✅.
- **[GO]** the activation act itself — owner-gated, deliberately last, in the dependency order
  given at the bottom of this file.

**[M] pass attempted 2026-07-27 — partial.** Completed: both Data Table cleanups (stale TEST
row deleted, mock token row replaced with a blank-token row, error-log mock rows 16–22
deleted with 23/24 kept as the §7 re-run fixture) — those boxes are now [x] with evidence.
**Blocked by the local Claude Code permission classifier, NOT by any external dependency:**
every n8n *workflow* write (all Limble credential swaps, all mock-URL reverts, both email
recipient restores, the templateID revert, the seeder-branch removal) and the sandbox
teardown script (`teardown.py`, staged in the session scratchpad — guarded, ledger-driven).
These remain [M] and re-runnable the moment a session has write permission; nothing about
the workflows themselves changed. One net-new [EXT] surfaced: the Coupa request-scope value
(see §1).


### Credentials to create/swap on the n8n instance

| Credential | Used by | Sandbox → Prod swap needed |
| --- | --- | --- |
| **Limble** (HTTP Header/Bearer auth against Limble API) | Step 1, Step 2, Step 3, EHS-Create, EHS-Update | **✅ Loaded into n8n credential store 2026-07-03 (OQ-015 resolved); `.env` scrubbed.** Build/test runs on the sandbox credential (`MX0lwgfyFiGUBh5W`); before go-live, repoint every Limble-calling node's credential to Coastal's prod credential (`qn6u8jEK085DoHT8`) — tracked per-workflow below. |
| **Coastal Coupa OAuth Client Credentials** (`httpCustomAuth`, per OQ-005) | Token Regeneration, Step 1, Step 2, Step 3 | **✅✅ PROD creds loaded on COASTAL 2026-08-01 — and the 2026-07-03 capture below turned out to be TEST-environment creds** (owner discovered this while populating: the real values came from Fuse's Token Regeneration workflow, not the datastore row as first captured; Ethan's "grab current values at capture time" advice was load-bearing). Coastal credential `kH7NaehFRB3s2RLt` now holds the actual PROD client_id/secret; the coastal token-table row also carries the real PROD `scope` (~150 entries, space-joined) plus a live prod-minted starter token whose embedded scope claim matches — verified 2026-08-01. The FM360 copy below retains the TEST creds, which is consistent with its test-rig role. Historical: **Loaded into n8n credential store 2026-07-03 (OQ-015 resolved)** — client_id/secret sourced from Make datastore `324` (client `coastal_waste (PROD)`). The `oauth_token`/`access_token` is ephemeral, minted daily by Token Regeneration. Target host `coastalwasteinc.coupahost.com`. Never write the real values into this repo — n8n credential store only. **Retrieval path confirmed by Ethan 2026-07-27:** the Fuse datastore is "CLIENTS - API Acct Information and Key" (= datastore `324`), row `coastal_waste (PROD)`, fields `client_id` / `client_secret` / `scope`; Fuse refreshes the token daily at midnight (matches the ported daily 12:00AM cron). Ethan advises grabbing the **current** values when ready to capture — re-verify client_id/secret against that row at cutover (ours were captured 2026-07-03), and pull `scope` from the same row (see the [EXT] scope box in section 1). |
| **EHS Insight API key** (`X-ApiKey` header) | EHS-Create, EHS-Update | **ROTATION REMOVED FROM ENGAGEMENT SCOPE — owner ruling 2026-08-01:** deployment ships on the existing key; rotation + old-key revocation is **transferred to the client team** (owner is documenting the handoff note). Standing facts for that team: the key sits in plaintext in 2 git-tracked blueprint exports (9 occurrences) and was verified working against live EHS on 2026-07-27; when rotated, update n8n credential `ZLLpBIVYKWS99BwK` on `coastal.n8n.fm360consulting.com` (both EHS workflows read it — no node edits needed). Historical status: **⚠️ ROTATION UNVERIFIED — row corrected 2026-07-27 (was wrongly ✅).** A key was loaded into credential `ZEf4C1rpYSbBgLbX` on 2026-07-03, but the OLD exposed key (`apikey-160448cf-...`, 9 plaintext occurrences in the blueprint exports) **still returned HTTP 200 against live EHS on 2026-07-26/27** — the authorized OQ-038 verification reads used it. So either rotation never happened or the old key was never revoked; the credential's stored value cannot be read back via MCP to tell which. **Treat as NOT rotated until Coastal confirms the old key is dead** — it grants working access to their production safety system from two git-tracked files. (The `__EHS_INSIGHT_CREDENTIAL_ID__` placeholder was resolved 2026-07-20 — credential attached to all EHS nodes, see sections 5/6.) |
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
| Coastal - Integration Config | nothing (new — OQ-019 sanctioned fix) | Step 1 (read), Step 2 (read) |

Record the table IDs here once created — later build specs and the workflows themselves need
to agree on the same ID:

- Coastal Coupa OAuth Token: `QAj62weJaWmRBJ76` (Token Regen writes; Step 1/2/3 read)
- Coastal Coupa Error Log: `6GbR5Rxezl7hqk9i` (Step 1 + Step 3 write; Error Log Export drains)
- Coastal - Integration Config: `L0npQPPEXQI9JRzX` (read-only from workflows; edited by hand)
  — key/value/notes. Current rows:

  | key | value | meaning |
  | --- | --- | --- |
  | `escalation_admin_user_id` | `398783` (test) → **`317887` at cutover** | Limble userID @-mentioned by the Step 1 + Step 2 error-path admin comment (OQ-019) |

### Workflow IDs (OQ-007 — resolved)

All 7 target n8n workflow IDs assigned (owner-provisioned shells). Write only to the named ID.
Write authorization is still granted one scenario at a time per OQ-003.

**2026-08-01: activation targets are now the COASTAL IDs** (OQ-048 port). FM360 IDs stay as
the test/regression rig — never activate those at cutover.

| Workflow | FM360 ID (test rig) | Coastal ID (GO-LIVE) | Active? |
| --- | --- | --- | --- |
| Coupa Token Regeneration | `oCAl4h0SZenEtbNs` | `1phqgrpFuSZOFqxS` | ☐ |
| Create Requisition in Coupa (Step 1) | `WJSs6apAdVH5yKkq` | `4fFRbDT7bluYEPc7` | ☐ |
| Check For New PRs Ordered & Update Limble WO (Step 2) | `WYJyHdQGcdeD8wEr` | `vwo0YcZewnyodSzL` | ☐ |
| WO Completed; Update Coupa PO (Step 3) | `NH1giNups8iICMZe` | `2T9TghNyHbp6LWhH` | ☐ |
| Create WO From EHS Inspection | `isLUx7cUjkmKggD2` | `6mAzjD1LG6AcDV5p` | ☐ |
| Update EHS Inspection From Limble WO | `8JvtesynrYtZbw7U` | `uhmXW1jlImUdXQVw` | ☐ |
| Coupa Integration Error Log Export | `hR5YnDixecDz9HzJ` | `0twTCK5xGFsB9k79` | ☐ |

### Email recipients (OQ-010 — dev override, restore before go-live)

Every email-sending node currently routes to `gerald@fm360consulting.com` only, via the
**Integrations Ionos** credential. Before go-live, restore real recipients:

| Node / Workflow | Real recipient(s) | Status |
| --- | --- | --- |
| "Token Refresh Failed" — Coupa Token Regeneration | `integrations@fm360consulting.com` (owner decision 2026-07-25; also the from-address — self-addressed on purpose) | ☑ **done on COASTAL** (carried from the OQ-048 port; OQ-013 alert recipient restored 2026-08-01). FM360 copy keeps gerald@ permanently as the test rig — no restore there |
| Coupa Integration Error Log Export report | `ethan@fm360consulting.com` (confirmed — matches source Make blueprint) | ☑ **done on COASTAL, live-verified 2026-08-03** (exec 1294: SMTP 250, envelope from `integrations@` → to `ethan@`, `rejected: []`). FM360 copy keeps gerald@ permanently — no restore there |

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

**2026-08-01 (OQ-048 port): the three coastal production URLs are now known** — register
THESE, not fm360 ones:

- Step 1 (New Task Comment): `https://coastal.n8n.fm360consulting.com/webhook/coastal-coupa-create-requisition-step1`
- Step 3 (Task Completed): `https://coastal.n8n.fm360consulting.com/webhook/coastal-coupa-wo-completed-step3`
- EHS Update (Task Completed): `https://coastal.n8n.fm360consulting.com/webhook/coastal-ehs-update-inspection`

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

- [x] Coastal Coupa OAuth Client Credentials populated with real client_id/secret — **stale
      box, already true:** loaded 2026-07-03 (OQ-015; section 0 credential table)
- [x] Coastal Coupa OAuth Token Data Table ID confirmed correct — `QAj62weJaWmRBJ76`,
      exercised at A2 T1 (token row written, exec 126675) and read by every Step 1/2/3 suite run
- [ ] **[M]** "Token Refresh Failed" email recipient restored to `integrations@fm360consulting.com`
      (decided 2026-07-25; node currently gerald@ dev-only per OQ-010 — swap at cutover)
- [x] Schedule timezone resolved (OQ-014, 2026-07-25) — cron daily @ 12:00AM **America/New_York**,
      `settings.timezone` flipped + verified by read-back
- [ ] **[C]** First-live token mint against real `coastalwasteinc.coupahost.com` — confirm
      token written to Data Table (mock equivalent ✅ A2 T1; this is the Phase-C1 canary)
- [ ] **[GO]** Activate — ID long assigned (OQ-007); activation is the cutover act itself

**Test-only staging applied 2026-07-13 — MUST be reverted before cutover:**
- [ ] **[M]** **Token URL:** `Refresh Coupa OAuth Token` repointed to mock
      `https://fm360.n8n.fm360consulting.com/webhook/mock-coupa/oauth2/token` — revert to
      `https://coastalwasteinc.coupahost.com/oauth2/token`.
- [x] Mock token value (`MOCK-TOKEN-COUPA-REFRESHED`) purged from Coupa OAuth Token table
      `QAj62weJaWmRBJ76` — **done 2026-07-27 ([M] pass):** mock row deleted, replaced by a
      fresh `coastal_waste` row (id 4) with **blank `oauth_token`** and the scope column
      preserved, so Token Regen's `Get Coastal Coupa Auth Config` scope read keeps working
      pre-mint. Covers the shared §2/§3/§4 mock-row boxes too (one table, one action).
- [x] Stale `Coastal_Waste (TEST)` row (id 1, expired test-instance JWT) deleted from the same
      table — **done 2026-07-27 ([M] pass).** Its request-scope string (the only evidence of
      the scope shape Fuse used) was preserved to `docs/coupa-oauth-scope-reference.md`
      before deletion; the expired JWT was not preserved. (OQ-039 resolved 2026-07-25: no
      test-instance pass; Coupa shapes examined at go-live under the C4 first-shepherd
      watch — OQ-028 is the tracking item.)
- [x] **[EXT — RESOLVED 2026-08-01]** **Real PROD `scope` set on the COASTAL token row**
      (`u818Gq3vZSTXdgeh`, ~150 space-joined `core.*` entries); re-verified live 2026-08-03 via
      Step 2 exec 1291, and the daily-minted JWT's embedded `scope` claim matches the stored
      column. The **FM360** row deliberately keeps the Phase-A stub as the test rig. Original
      item, retained for context: `scope` on the `coastal_waste` row was the
      Phase-A mock stub (`core.requisition.read core.purchase_order.read`). Before the C1
      first live mint, set the real PROD request scope — authoritative value lives in Make
      datastore `324` (client `coastal_waste (PROD)`, Ethan/owner can read it); the shape
      reference is `docs/coupa-oauth-scope-reference.md`. (Flagged during the 2026-07-27
      [M] pass — this was never a checklist item before because the mock never validated
      scope.) **Ethan confirmed the retrieval path 2026-07-27:** go to the Fuse
      "CLIENTS - API Acct Information and Key" datastore, row `coastal_waste (PROD)`, and
      grab the current `client_id`, `client_secret`, and `scope` values when ready to
      capture credentials. Same pull should re-verify client_id/secret (captured 2026-07-03)
      alongside scope. He also confirmed tokens refresh daily at midnight — matches this
      workflow's daily 12:00AM Eastern cron.

## 2. Create Requisition in Coupa (Step 1)

- [ ] **[M]** Limble credential swapped sandbox → Coastal prod (`MX0lwgfyFiGUBh5W` →
      `qn6u8jEK085DoHT8`)
- [x] Coupa credential confirmed reading from Coastal Coupa OAuth Token table — **stale box:**
      the token-table read (`QAj62weJaWmRBJ76`) was exercised end-to-end throughout A1/A4/A5
- [x] Coastal Coupa Error Log table ID confirmed correct — `6GbR5Rxezl7hqk9i`, written by the
      A4 error scenarios (rows 16–24) and drained by A3
- [ ] **[EXT — OQ-020, currently NO owner]** Limble webhook subscription (New Task Comment)
      repointed to this workflow's n8n URL
- [ ] **[C]** First-live run against a real Limble task comment (realistic-comment mock suite
      ✅ A4; real Coupa lookups/segment codes are the Phase-C4 shepherd watch)
- [ ] **[GO]** Activate — ID long assigned (OQ-007); activation is the cutover act itself

**Test-only staging applied 2026-07-13 — MUST be reverted before cutover:**
- [ ] **[M]** **Coupa URLs:** 6 nodes (`Coupa: Get User`, `Coupa: Get Address`, `Coupa: Get Account`,
      `Coupa: Get Supplier`, `Coupa: Create Requisition`, `Coupa: Attach Quote`) point at mock
      host `https://fm360.n8n.fm360consulting.com/webhook/mock-coupa` — revert host to
      `https://coastalwasteinc.coupahost.com` (paths unchanged).
- [ ] **[M — value gated by EXT OQ-019]** **Admin-comment target:** no longer a node literal
      (OQ-019 fix, 2026-07-26). `Get Admin
      User` reads its userID from the **`Coastal - Integration Config`** Data Table
      (`L0npQPPEXQI9JRzX`) via the `Get Escalation Admin ID` node. One row flip covers Step 1
      **and** Step 2 — see §3 and the shared checklist item in "Data Tables" above. Do not edit
      the node.
- [x] Mock token row cleanup shared with §1/§3 (`client=coastal_waste` in `QAj62weJaWmRBJ76`) —
      **done 2026-07-27, see §1** (one shared action; row replaced with blank-token row id 4).

**Permanent (do NOT revert) — sanctioned fix under OQ-045 (applied + tested 2026-07-25):**
`Get Instructions` (n13) has `alwaysOutputData: true` so a zero-instruction WO still reaches
`Parse Instruction Responses`, which emits source-faithful defaults and lets the error surface
downstream (source Make continued via empty aggregator bundle; unguarded n8n silently stopped).
Zero-instruction exec 127289 + regression exec 127295 both PASS. Keep at go-live.

**Permanent (do NOT revert) — sanctioned fix under OQ-018 (applied 2026-07-26, corrected and
tested same day):** `Get Limble Users` (n10) paginates the user fetch — query `cursor` =
`{{ $response?.body?.last()?.userID ?? 0 }}`, complete when page length < 500. The optional
chaining and the `?? 0` default are **load-bearing**: n8n evaluates the expression on the first
request too, and the un-guarded original (`{{ $response.body.last().userID }}`) threw
`last can't be used on undefined value` on every run (exec 127324) until corrected. `cursor=0`
is probe-verified equivalent to omitting the param; `cursor=` empty is rejected HTTP 400.
Proven by exec 127325 (54 users, single page). **Watch at go-live:** the multi-page branch has
never executed — prod has 79 users against a 500 page size, so page 2 is not reached today.
- [ ] **[M]** Teardown: delete OQ-045 fixture task **4228** (`DELETE /v2/tasks/4228`) with the other
      sandbox fixtures.

## 3. Check For New PRs Ordered & Update Limble WO (Step 2)

- [ ] **[M]** Limble credential swapped sandbox → Coastal prod (all 10 Limble nodes: currently
      sandbox `MX0lwgfyFiGUBh5W`, revert to PROD `qn6u8jEK085DoHT8`)
- [x] Coupa credential confirmed reading from Coastal Coupa OAuth Token table — **stale box:**
      the token-table read (`QAj62weJaWmRBJ76`) was exercised end-to-end throughout A1/A4/A5
- [x] OQ-008 resolved — error-log subgraph built into `WYJyHdQGcdeD8wEr` 2026-07-09 (OQ-029)
- [ ] **[C]** First-live run (mock-suite equivalent ✅ in Phase A; this box = first real-API
      cycle under the Phase-C watch)
- [ ] **[GO]** Activate on the 5-minute schedule — ID long assigned (OQ-007)

**Test-only staging applied 2026-07-09 — MUST be reverted before cutover:**
- [ ] **[M]** **Coupa URLs:** 2 nodes (`Get Associated Requisition`, `Get PO Created From Req.`)
      point at mock host `https://fm360.n8n.fm360consulting.com/webhook/mock-coupa` — revert to
      `https://coastalwasteinc.coupahost.com`.
- [ ] **[M — value gated by EXT OQ-019]** **Admin-comment target — SHARED WITH STEP 1, do this
      once:** set row
      `key=escalation_admin_user_id` in Data Table **`Coastal - Integration Config`**
      (`L0npQPPEXQI9JRzX`) from the test value **`398783`** (sandbox Site Manager) to the real
      escalation contact **`317887`** (Brandon Ray Freckleton) — or to whoever Coastal names
      instead. Both Step 1 and Step 2 read this one row (OQ-019 sanctioned fix, 2026-07-26);
      neither `Get Admin User` node holds a literal any more.
- [x] **Mock token row** purged from Coupa OAuth Token table `QAj62weJaWmRBJ76` —
      **done 2026-07-27, see §1** (one shared action; row replaced with blank-token row id 4).
- [ ] **[M]** Sandbox test fixtures/dud tasks removed from loc 98472 (4080–4083 etc.; S2-2 fixtures added
      2026-07-24: task **4213** `DELETE /v2/tasks/4213` + team **605550** `DELETE /v2/teams/605550`).
- [ ] **[M]** Remove the `coastal-seed-team` branch (3 nodes) added to seeder `qyMChP0DKfI04r4a` 2026-07-24
      (or drop it with the whole seeder at cutover teardown).

**Permanent (do NOT revert) — sanctioned fixes under OQ-024:** the write node
`Set 'PO Approved' Status and Save PO ID` now writes **top-level `meta2`** (not `metadata.meta2`)
and wraps it as **`String(...)`** (Limble rejects the `metadata` object and rejects a numeric
`meta2`). These are correctness fixes, not test scaffolding — keep them at go-live.

## 4. WO Completed; Update Coupa PO (Step 3)

- [ ] **[M]** Limble credential swapped sandbox → Coastal prod (`MX0lwgfyFiGUBh5W` →
      `qn6u8jEK085DoHT8`)
- [x] Coupa credential confirmed reading from Coastal Coupa OAuth Token table — **stale box:**
      the token-table read (`QAj62weJaWmRBJ76`) was exercised end-to-end throughout A1/A4/A5
- [x] Coastal Coupa Error Log table ID confirmed correct (same table as Step 1,
      `6GbR5Rxezl7hqk9i`) — written by A5's error scenarios
- [ ] **[EXT — OQ-020, currently NO owner]** Limble webhook subscription (Task Completed)
      repointed to this workflow's n8n URL
- [ ] **[C]** First-live run (mock-suite equivalent ✅ in Phase A; this box = first real-API
      cycle under the Phase-C watch)
- [ ] **[GO]** Activate — ID long assigned (OQ-007); activation is the cutover act itself

**Test-only staging applied 2026-07-13 — MUST be reverted before cutover:**
- [ ] **[M]** **Coupa URLs:** 4 nodes (`Coupa: Get PO`, `Coupa: Attach Invoice`, `Coupa: Post Comment
      (Invoice)`, `Coupa: Post Comment (No Invoice)`) point at mock host
      `https://fm360.n8n.fm360consulting.com/webhook/mock-coupa` — revert host to
      `https://coastalwasteinc.coupahost.com` (paths unchanged).
- [x] Mock token row cleanup shared with §1/§2/§3 (`client=coastal_waste` in `QAj62weJaWmRBJ76`) —
      **done 2026-07-27, see §1** (one shared action; row replaced with blank-token row id 4).

**Permanent (do NOT revert) — sanctioned fix under OQ-045 (applied + tested 2026-07-25):**
`Get Instructions` (n05) has `alwaysOutputData: true` so a zero-instruction WO still reaches
`Extract Invoice Response`, which emits the empty-invoice default and posts the no-invoice
"@Jordan Buyer" comment — matching source Make (unguarded n8n silently stopped). Zero-instruction
exec 127286 + regression exec 127296 both PASS. Keep at go-live.
- [ ] **[M]** Teardown: delete OQ-045 fixture task **4229** (`DELETE /v2/tasks/4229`) with the other
      sandbox fixtures.

## 5. Create WO From EHS Inspection

Built 2026-07-08, deployed inactive to `isLUx7cUjkmKggD2` (**30 nodes** after the 2026-07-20
fixes below, re-validated clean — 0 errors/warnings). See
`docs/build-specs/ehs-create-wo-build-spec.md` (section 12 for the as-deployed corrections).

**Test status: A6 suite PASSED 2026-07-21** (exec 126934) — 5 deficiency tasks created at correct
locations/teams, `meta1`=RowUID (top-level string), epoch `due`, verbiage PATCH on
all 5, image PUT on the image scenario; negative scenarios all held. **Tag assertion re-verified
2026-07-27** (OQ-038 reversal): re-run exec 127388 — tasks 4234–4238 all stamped `@EHS;`, and the
A-scenario winner is now **FIC-1002** (OQ-037 fix; the old FIC-1001 expectation is retired).
Detail in test-sequence.md A6.

**Permanent (do NOT revert) — fixes applied to the live workflow 2026-07-20:**
- `Create Deficiency Task`: `due` → epoch seconds (`Math.round(...toSeconds())`; API 400s on
  ISO), `metadata.meta1` → top-level `meta1: String(...)` (OQ-024 sanctioned fix).
  ~~description tag `@EHS;` → `@EHSWO;`~~ — **REVERTED 2026-07-27**: the tag is back to `@EHS;`
  and EHS Update's gate was changed to `@EHS;` instead (OQ-038 reversal, Ethan's call — 10 prod
  EHS WOs already carry `@EHS;`, 5 of them still open). Do NOT re-apply `@EHSWO;` to this node
  without changing `8JvtesynrYtZbw7U` n04 in the same breath.
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
- [ ] **[EXT]** EHS Insight API key rotated **and the old key revoked** — see the corrected
      section 0 row: the old exposed key still worked against live EHS 2026-07-27
- [ ] **[M]** Limble credential swapped sandbox → Coastal prod (`MX0lwgfyFiGUBh5W` →
      `qn6u8jEK085DoHT8`)
- [x] Schedule timezone resolved (OQ-014, 2026-07-25) — cron `0 16 * * *` daily @ 4:00PM
      **America/New_York**, `settings.timezone` flipped
- [x] `createATask` field names verified against live Limble API — `due` epoch seconds +
      top-level `String(metaN)` confirmed via live sandbox contract (2026-07-09/2026-07-20);
      remaining fields exercised at A6
- [x] `updateAnInstruction` endpoint/method verified — real routes are
      `PATCH /v2/tasks/instructions/{id}` (verbiage) + `PUT .../image` (multipart), both
      support-confirmed and deployed 2026-07-20 (image PUT proven live)
- [ ] **[C]** EHS attachment-fetch response shape verified — node now expects a **binary file**
      response (`responseFormat: file`); **mock half done 2026-07-20** (serves raw PNG +
      `Content-Disposition` filename, live-curled); the **real** EHS endpoint's byte shape
      remains a Phase-C6 unknown (if it returns JSON/base64, add a decode step)
- [ ] **[C]** First-live run (mock-suite equivalent ✅ in Phase A; this box = first real-API
      cycle under the Phase-C watch)
- [ ] **[GO]** Activate — ID long assigned (OQ-007); activation is the cutover act itself

**Test-only staging applied 2026-07-20 — MUST be reverted before cutover:**
- [ ] **[M]** **EHS URLs:** all 5 EHS nodes (`EHS: List Inspections`, `EHS: List Question Sets`,
      `EHS: Fetch Inspection Detail`, `EHS: Get Hierarchy`, `EHS: Fetch Attachment`) point at
      mock host `https://fm360.n8n.fm360consulting.com/webhook/mock-ehs` — revert host to
      `https://coastalwasteinc.ehsinsight.com` (paths unchanged).
- [ ] **[M]** **templateID:** `Create Deficiency Task` retargeted `"842"` → sandbox template `"4189"`
      2026-07-20 — **revert to `842`** at cutover.
- [ ] **[M]** Sandbox A6 fixtures removed at teardown — full ledger (regions 7944/7946–7950, teams
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
- [ ] **[M]** **EHS URLs:** 2 nodes (`EHS: Fetch Inspection`, `EHS: Update Inspection`) point at mock host
      `https://fm360.n8n.fm360consulting.com/webhook/mock-ehs` — revert host to
      `https://coastalwasteinc.ehsinsight.com` (paths unchanged). Verified applied 2026-07-23.
- [ ] **[M]** **A7 fixture teardown at loc 98472:** parent task **4218** (+ its type-14 child links),
      children **4220**/**4222**, U4 parent **4223**, non-EHS control **4201**, and the scrapped
      old-plan skeletons (4198–4200, 4202 if present). Dangling type-14 instruction **15056**
      (→ deleted task 4221) goes with 4218. Ledger: `docs/test-plan/sandbox-seed-record-a6.md`.

- [x] EHS Insight API key rotated and moved into an n8n credential (same rotated key as #5) —
      verified live 2026-07-25: both EHS nodes (n11 `EHS: Fetch Inspection`, n13
      `EHS: Update Inspection`) carry rotated credential `ZEf4C1rpYSbBgLbX`
      ("Coastal Waste - EHS API Key")
- [ ] **[M]** Limble credential swapped sandbox → Coastal prod (`MX0lwgfyFiGUBh5W` →
      `qn6u8jEK085DoHT8`)
- [ ] **[EXT — OQ-020, currently NO owner]** Limble webhook subscription (Task Completed)
      repointed to this workflow's n8n URL
- [x] Dead comments-fetch (module 63) / lastComment (module 64) confirmed dropped per OQ-036 —
      structure pull 2026-07-25 (A7): no comments-fetch node, no `lastComment` anywhere
- [x] **`@EHS;`** tag literal verified to match what "Create WO From EHS Inspection" (#5)
      actually writes — **execution-verified end-to-end 2026-07-27, not assumed.** Both sides are
      `@EHS;` after the OQ-038 reversal. Proof chain: A6 re-run (exec 127388) created tasks
      4234–4238 all stamped `… @EHS;`; then the **closed-loop test (exec 127410)** completed
      Create's own task **4237** and fired it at this workflow — gate matched, `meta1`
      `EHS-INSP-D` routed correctly, write-back `{Success: true}`. First time Create's real output
      drove Update's gate (previously only hand-seeded fixtures). A7 U1/U4 also re-ran green on
      re-seeded fixtures (execs 127376 / 127384).
- [x] Child-task fetch confirmed at A7 (U1, exec 127255): `meta.associatedTask` is a **relative
      path** (`/v2/tasks/?tasks=NNNN`) — host-prepend fix applied; fetched child notes matched
      `body[0].completionNotes` and landed in the write-back string
- [x] Completion-note timestamp mechanics proven at A7 U1, and the **Eastern rendering is now
      re-executed too (2026-07-27)** — closing the residual noted in section 0. Same epoch
      1785003479 rendered `12:17 PM` under Denver (2026-07-25) and **`02:17 PM` under
      America/New_York** at exec 127376; the closed-loop run (127410) rendered
      `(Completed 07/27/2026 02:23 PM)` for epoch 1785176616. Both cross-checked by calculation
      (Denver 12:17 / New_York 14:17 / UTC 18:17). OQ-014's flip is verified on this workflow.
- [ ] **[C]** First-live run — completed parent WO + at least one completed child WO, confirm
      `UDFLimbleWOCompletionNotes` on the real EHS inspection gets both notes concatenated
      (mock closed-loop ✅ exec 127410; note the parent must be completed **in the Limble UI** —
      the API cannot set `completionNotes`, proven 2026-07-27)
- [ ] **[GO]** Activate — ID long assigned (OQ-007); activation is the cutover act itself

## 7. Coupa Integration Error Log Export

- [x] Coastal Coupa Error Log table ID confirmed correct (same table Step 1/Step 3 write to,
      `6GbR5Rxezl7hqk9i`) — drained by A3 E1 against real rows
- [x] Delete-only-exported-records fix in place (OQ-006) — **proven at A3 E1** (exec 126681):
      delete scoped to reported ids [12,13] only; unreported row 9003 survived
- [x] Email recipient `ethan@fm360consulting.com` — **carried by the COASTAL copy from its
      creation (OQ-048 port)**; the FM360 copy deliberately keeps gerald@ forever as the test
      rig (2026-08-01 disposition — no FM360 restore needed).
- [x] **Eastern re-run PASSED 2026-08-01 — exec 127523 (owner Execute on FM360 copy).**
      Report rendered rows 23/24 with **America/New_York** timestamps (stored UTC
      2026-07-27T01:28Z → rendered `07/26/2026, 09:28 PM`; Denver would be 07:28 PM), email
      accepted at gerald@ (SMTP 250, from integrations@), delete scoped to exactly ids
      [23, 24], table read-back empty. Closes OQ-014's last unverified rendering path.
      (Bonus same day: coastal copy exec 424 = empty-table no-op, proving the repointed
      coastal table read — E2 shape.)
- [x] **COASTAL copy end-to-end PASSED live 2026-08-03 — exec 1294** (`0twTCK5xGFsB9k79`). A
      single synthetic row was inserted into the coastal error-log table `On8bmdryDYfoBjMG`,
      then the scheduled 20:00:45Z run drained it: all 7 nodes executed (599 ms vs the 10–25 ms
      empty-table baseline), `Build Report` rendered the Fuse-shaped line with a correct
      America/New_York timestamp (`08/03/2026, 03:59 PM` for stored 19:59Z),
      `Send Error Report Email` returned **SMTP 250** with envelope from
      `integrations@fm360consulting.com` → to `ethan@fm360consulting.com`, `rejected: []`, real
      `messageId`; delete ran id-addressed on `rowIds: [1]` and the table read back empty. **This
      is what proved the coastal `Integrations Ionos` credential** (`XbGIxN8MFDM3DJoS`) — the last
      of the 4 populated credentials with no live evidence, and one only exercised when something
      else fails.
- [x] OQ-006 scoped delete **re-verified on the coastal table 2026-08-03** as a deterministic
      2-row test (the 599 ms single-row run can't distinguish scoped-delete from delete-all):
      rows `id 2` + `id 3` inserted, a filtered `deleteRows` on `id = 2` removed only that row and
      `id 3` survived. Combined with the node config (`Delete Reported Rows` = `deleteRows` with
      `keyValue: {{ $json.rowIds }}`, one call per split item) this closes the question on the
      coastal copy. Test rows cleaned up; table left empty. Note the coastal reader
      `Get Error Log Rows` is `operation: get, returnAll: true` with **no filter** — not the
      `timestamp exists` filter Fuse used; equivalent for a full drain, and the race fix lives in
      the id-scoped delete, not the read.
- [x] **[GO]** Activated on the 15-minute schedule at cutover 2026-08-01 — running every 15 min
      since (execs verified through 2026-08-03)

---

## Cutover sequence (once all 7 are individually ready)

1. Turn off the corresponding live Fuse/Make scenario for each workflow, one at a time — don't
   run both systems against the same Limble/Coupa/EHS account in parallel.
2. Confirm Limble webhook subscriptions point only at n8n (see §0 above). **[EXT — OQ-020:
   needs Limble webhook admin; unowned as of 2026-07-27, Ethan lost Limble access.]**
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
