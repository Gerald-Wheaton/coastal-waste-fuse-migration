# OQ-048 Port Ledger — coastal.n8n.fm360consulting.com

Working ledger for the OQ-048 port (started 2026-07-31). Canonical record lands in
`open-questions.md` OQ-048 + `DEPLOYMENT.md` when the port completes; this file is the
in-flight source of truth for new IDs.

Owner rulings 2026-07-31 (in-session, ratified via interview):
- Port shape: coastal copies created **directly in cutover config** (real hosts, placeholder
  prod-type credentials, restored recipients, prod templateID 842).
- failMode config table (`YkCIlyx7lUUNs7vG`) does **NOT** port — FM360 mock-rig only.
- Port verification standard: `n8n_validate_workflow` + node inspection. **No execution on
  coastal pre-cutover** (OQ-039 — first execution is Phase C by design).

## Data Tables (created 2026-07-31)

| Table | FM360 ID (test) | Coastal ID (cutover) | Seed state |
| --- | --- | --- | --- |
| Coastal - Coupa OAuth Token | `QAj62weJaWmRBJ76` | `u818Gq3vZSTXdgeh` | row id 1: `client=coastal_waste`. **Seed state superseded — LIVE as of 2026-08-01 (see "Owner population" below):** real PROD `scope` (~150 `core.*` entries) and a live daily-minted `oauth_token`. Re-verified 2026-08-03 (Step 2 exec 1291 read the row; `refreshed_at`/`updatedAt` = 04:00:30Z that morning). Original seed was blank `oauth_token` + Phase-A stub scope |
| Coastal - Coupa Integration Error Log | `6GbR5Rxezl7hqk9i` | `On8bmdryDYfoBjMG` | empty |
| Coastal - Integration Config | `L0npQPPEXQI9JRzX` | `dhGuWwRx1a8uIvp3` | row id 1: `escalation_admin_user_id=317887` — **OQ-019 confirmed-by-use 2026-08-01** (owner: "continue to reference this ID"); no longer pending |

Schemas copied column-for-column from FM360 (verified via listTables 2026-07-31):
token = client/oauth_token/refreshed_at(date)/scope; error-log =
limbleWONum/errorCode/errorMsg/timestamp(date); config = key/value/notes.

## Credentials (created 2026-07-31 as placeholders — **ALL 4 POPULATED 2026-08-01**)

Names below are the as-created placeholder names; the owner dropped the `[PLACEHOLDER …]`
suffix on population and the credential **IDs did not change**. All 4 are now proven by live
calls (2026-08-03 review): Limble PROD header via real task fetches, EHS key via real EHS
GETs, Coupa httpCustomAuth via the daily token mint, Ionos SMTP via Error Log Export exec 1294.
The "Owner action" column is historical. See "Owner population — COMPLETE 2026-08-01" below.

| Credential | Type | Coastal ID | Replaces (FM360) | Owner action |
| --- | --- | --- | --- | --- |
| Coastal Waste Limble PROD | httpHeaderAuth | `V3fUTHSMtAkRUHlT` | `MX0lwgfyFiGUBh5W` (sandbox) / `qn6u8jEK085DoHT8` (prod, FM360-only) | paste prod Limble `Authorization` header value |
| Coastal Waste - EHS API Key | httpHeaderAuth | `ZLLpBIVYKWS99BwK` | `ZEf4C1rpYSbBgLbX` | paste **rotated** EHS key (header `X-ApiKey`); old key must be revoked first |
| Coastal Coupa OAuth Client Credentials | httpCustomAuth | `kH7NaehFRB3s2RLt` | FM360 Coupa cred | populate custom-auth JSON with PROD client_id/client_secret (capture path: Fuse datastore 324, row `coastal_waste (PROD)` — Ethan confirmed 2026-07-27). Placeholder JSON shape is a guess: `{"body":{"client_id":...,"client_secret":...}}` — **verify against the FM360 credential's real JSON shape when populating; the Token Regen mint request depends on it** |
| Integrations Ionos | smtp | `XbGIxN8MFDM3DJoS` | FM360 Ionos cred | populate real Ionos SMTP user/password/host/port |

## Workflows (port COMPLETE — 7/7 created, all ACTIVE since cutover 2026-08-01)

| Workflow | FM360 ID | Coastal ID | Validated | Webhook path |
| --- | --- | --- | --- | --- |
| Coupa Token Regeneration ("Coupa - Token Refresh") | `oCAl4h0SZenEtbNs` | `1phqgrpFuSZOFqxS` | ✅ 2026-07-31, 0 err/0 warn | (schedule) |
| Create Requisition in Coupa (Step 1) | `WJSs6apAdVH5yKkq` | `4fFRbDT7bluYEPc7` | ✅ 2026-08-01 — exactly the 5 known `Err: *` naming-heuristic false positives, 0 other errors (50 nodes / 45 connection keys, physical-presence verified in coastal list) | `coastal-coupa-create-requisition-step1` (POST) |
| Check For New PRs Ordered (Step 2) | `WYJyHdQGcdeD8wEr` | `vwo0YcZewnyodSzL` | ✅ 2026-07-31 — 4 validator errors, ALL the known `Err: *` naming-heuristic false-positive class (error-handler Set nodes; graph byte-identical to the A1-suite-passing FM360 copy) | (schedule, 5-min) |
| WO Completed; Update Coupa PO (Step 3) | `NH1giNups8iICMZe` | `2T9TghNyHbp6LWhH` | ✅ 2026-07-31, 0 err/0 warn | `coastal-coupa-wo-completed-step3` (POST) |
| Create WO From EHS Inspection | `isLUx7cUjkmKggD2` | `6mAzjD1LG6AcDV5p` | ✅ 2026-07-31, 0 err/0 warn (34 nodes — DEPLOYMENT's "30 nodes" note is stale; OQ-043 guards + n25a grew it) | (schedule, daily 16:00 America/New_York) |
| Update EHS Inspection From Limble WO | `8JvtesynrYtZbw7U` | `uhmXW1jlImUdXQVw` | ✅ 2026-07-31, 0 err/0 warn | `coastal-ehs-update-inspection` (POST) |
| Coupa Integration Error Log Export ("Coupa - Integration Error Log Export") | `hR5YnDixecDz9HzJ` | `0twTCK5xGFsB9k79` | ✅ 2026-07-31, 0 err/0 warn | (schedule) |

Port notes (2026-07-31):
- Transform verified by grep on the created payloads: zero hits for `fm360.n8n`, `mock-coupa`,
  `mock-ehs`, old credential IDs, old table IDs, `YkCIlyx7lUUNs7vG` on both created workflows.
- Error Log Export's coastal copy initially retained ONE `gerald@fm360consulting.com` in the
  **"Alert: Error Log Export Failed"** node (OQ-013 self-error path — distinct from the report
  recipient, restored to ethan@). OQ-013's resolution documents the intended go-live recipient:
  **integrations@fm360consulting.com** (gerald@ was the OQ-010 dev override). **Patched on the
  coastal copy 2026-07-31** (patchNodeField, read back, re-validated clean); coastal copy now
  zero-hit for gerald@. FM360 original untouched (still gerald@, correct until go-live).
- FM360 source credential IDs observed: Coupa httpCustomAuth `7ZQlnJJWRJsZw1C3`, Ionos smtp
  `vPXcXvRpktLu49Vr` (mapped by ANY-of-type rule). All Limble nodes on FM360 carry the sandbox
  cred `MX0lwgfyFiGUBh5W`; prod cred `qn6u8jEK085DoHT8` appeared nowhere.
- All FM360 sources carry `settings.binaryMode: "separate"`, which the n8n public API create
  schema rejects — dropped on the coastal creates (instance default applies). Watch item:
  confirm this doesn't change binary handling for EHS Create's attachment fetch (C6).
- Batch A transformed payloads archived in session scratchpad `wf{1,2,3}-*.json`; batch B
  artifacts `step{2,3}-{raw,coastal}.json` + `transform.py` same place.
- Batch B deviations (documented, non-functional): old table IDs inside node `notes` text were
  repointed to the coastal IDs (3 notes total) so the zero-hit grep gate holds; Step 3's
  `Get Coupa Token` note still references FM360 Token Refresh ID `oCAl4h0SZenEtbNs` — coastal
  equivalent is `1phqgrpFuSZOFqxS`, cosmetic only.
- Step 2 transform detail: 10 Limble cred nodes swapped; token table ×1, error-log ×2,
  Integration Config ×1 repointed. Step 3: 2 Limble nodes (n03/n05), token ×1, error-log ×1.
- EHS Create transform detail: 5 mock-ehs hosts reverted, templateID `"4189"`→`"842"` inside
  `Create Deficiency Task` jsonBody, 8 Limble cred nodes + 5 EHS cred nodes swapped,
  `alwaysOutputData` intact on the OQ-043 guard pair; post-create full read confirmed timezone
  America/New_York + cron `0 16 * * *`. Cosmetic residue: `Create Deficiency Task` note still
  cites FM360 EHS-Update ID `8JvtesynrYtZbw7U` (coastal counterpart `uhmXW1jlImUdXQVw`).

Coastal webhook base: `https://coastal.n8n.fm360consulting.com/webhook/<path>` — the 3 webhook
paths feed OQ-020's Limble repoints:

- Step 1 (New Task Comment): `https://coastal.n8n.fm360consulting.com/webhook/coastal-coupa-create-requisition-step1`
- Step 3 (Task Completed): `https://coastal.n8n.fm360consulting.com/webhook/coastal-coupa-wo-completed-step3`
- EHS Update (Task Completed): `https://coastal.n8n.fm360consulting.com/webhook/coastal-ehs-update-inspection`

(All POST. Production webhook URLs go live only on activation — register in Limble at cutover.)

**OQ-020 API capability — PROVEN 2026-08-01.** Coastal prod Limble webhooks are manageable via
the public API with the credential already in hand (.env ENCODED_AUTH — which reaches the
Coastal PROD account, not a separate sandbox; label was misleading, see handoff/lessons):
- Live hooks: **1742 / 1743 / 1744** (the docs' "775/776/777" were Make-internal IDs), all
  `type: "task"`, enabled, endpoints on `hook.fuse.limblecmms.com`.
- Contract: `GET /v2/webhooks` (list); `POST /v2/webhooks {endpoint, type}` → 201 `{webhookID}`;
  `PATCH /v2/webhooks/{id}` requires the FULL body (`endpoint` AND `type` — partial patch 400s);
  `DELETE /v2/webhooks/{id}` → 200. No event-subtype field exists — every `task` hook receives
  the full task-event stream; receiving workflows filter (matches the ported gates).
- Probe was create+delete of a temporary hook (2851) on PROD — ~2s lifetime, dead-path endpoint,
  zero leftovers verified. Unintentional prod write (credential label trusted); logged as an
  OQ-003 breach in the session record, lesson captured.
- **Cutover repoint is therefore self-service:** at activation, PATCH each of 1742/1743/1744
  full-body to the three coastal URLs above (mapping across the 3 is functionally arbitrary —
  identical streams — but keep 1:1 for the rollback revert), with owner authorization at that
  moment. No Limble UI admin required. Rollback = PATCH endpoints back to the Fuse URLs.

## Port completion summary (2026-07-31)

**All 7 workflows ported, all inactive, all in cutover config.**

**Step 1 stray-create incident (2026-08-01):** the first Step 1 create (`EabuMg2NUvyXGUmo`)
landed on the **DrinkPak** instance — the shared MCP binding flipped mid-batch (a parallel
session was active); the batch agent's ID-addressed read-backs succeeded cross-instance and
were therefore instance-blind. Caught by a physical `n8n_list_workflows` on coastal (6, not 7).
Stray deleted from DrinkPak (owner-approved), payload re-created on coastal as
**`4fFRbDT7bluYEPc7`** with physical-presence verification (coastal list showed 7/7,
nodeCount 50). Rule going forward: a CREATE is verified only by a LIST on the intended
instance — never by ID-addressed reads. Verification standard per the
2026-07-31 owner ruling: `n8n_validate_workflow` + structure/node inspection + grep gates on
every transformed payload (no execution on coastal pre-cutover — Phase C by design, OQ-039).
Zero writes to FM360 throughout; instance binding verified by URL before every call batch.

Step 1 port details: 6/6 mock-coupa hosts reverted; 16/16 Limble cred nodes (ID list matches
the 2026-07-27 audit exactly); token table ×1, error-log ×1 (single writer n39 funnels all 5
error paths), Integration Config ×1 (+1 notes-only edit); OQ-018 guarded pagination expression
byte-exact on n10; alwaysOutputData intact on n13. Step 1's six Coupa HTTP nodes carry NO
credentials block (Bearer via expression from `Get Coupa Token`) — the httpCustomAuth
placeholder is used by Token Refresh only.

Cosmetic residue (notes-only, harmless, fix at leisure): Step 3 + Step 1 notes cite FM360
Token-Refresh ID `oCAl4h0SZenEtbNs` (coastal: `1phqgrpFuSZOFqxS`); EHS Create note cites FM360
EHS-Update ID `8JvtesynrYtZbw7U` (coastal: `uhmXW1jlImUdXQVw`).

**Owner population — COMPLETE 2026-08-01:** all 4 credentials populated + renamed (PLACEHOLDER
suffix dropped, IDs unchanged); Coupa creds are the ACTUAL PROD pair from Fuse's Token
Regeneration workflow (the 2026-07-03 capture was TEST-environment creds — discovered during
population); token-table row now carries the real PROD scope (~150 entries) + a live
prod-minted starter token whose embedded scope claim matches (verified); EHS credential holds
the EXISTING key per client ruling 2026-08-01 (rotation deferred post-deployment, C8 window);
config row 317887 confirmed-by-use (owner: "continue to reference this ID", abstracted in the
Integration Config table for one-row changes).

**Remaining before activation:** OQ-020 webhook repoints (API-capable, execute at cutover);
Fuse scenario disables; activation order decision; sandbox teardown (any time).

## Cutover log (2026-08-01) — rollback reference

Limble hook rollback endpoints (PATCH full-body `{endpoint, type}` to revert):

| Hook | Fuse endpoint (rollback target) | Repointed to (coastal) | When |
| --- | --- | --- | --- |
| 1742 | `https://hook.fuse.limblecmms.com/4uptpuxz8ybbh7e82cmytp2pm8r7jvqd` | `.../webhook/coastal-coupa-create-requisition-step1` | ✅ 2026-08-01 ~17:5x UTC |
| 1743 | `https://hook.fuse.limblecmms.com/mo66o8115g95ij3w5ufav64tb1l0egqg` | `.../webhook/coastal-coupa-wo-completed-step3` | ✅ 2026-08-01 R5 (Step 3 ACTIVE first) |
| 1744 | `https://hook.fuse.limblecmms.com/i77o5ff8ojnpw8lzpk5966exqy9428fw` | `.../webhook/coastal-ehs-update-inspection` | ✅ 2026-08-01 R7 (EHS Update ACTIVE first) |

**CUTOVER COMPLETE 2026-08-01 ~18:07 UTC.** Final board verified by list: 7/7 workflows ACTIVE
on coastal; all 3 Limble hooks verified pointing at coastal (enabled=1); all 7 Fuse scenarios
disabled-not-deleted (rollback lever intact). R6 EHS Create ACTIVE (first live run = today's
4:00 PM Eastern cron); R7 EHS Update ACTIVE + hook 1744 repointed. Phase C watch (C1 ✅ mint
exec 425 · C2 first poll ✅ exec 426) now running — C4/C5 await first real events, C6 today
16:00 ET, C7 awaits first completed EHS WO.

Activation log: R1 Token Refresh ACTIVE + C1 live mint PASS (exec 425, real
`{access_token, token_type, expires_in}` shape); R2 Step 2 ACTIVE, first poll PASS (exec 426:
prod-Limble status lookup resolved, 0-WO backlog, clean exit; Coupa GET-shape proof deferred
to first real PR); R3 Error Log Export ACTIVE; R4 Step 1 ACTIVE + hook 1742 repointed.

Post-cutover day-1 (2026-08-01 evening):
- **C6 first live EHS run PASS** (exec 461, 20:00:00, 12.3s): real EHS shapes parse clean
  (`{ResultCode, List[]}` / `{ResultCode, Entity{...}}`), `UpdatedDtm` + `RecurringTaskCompleteDtm`
  present on real data (OQ-037 field spellings confirmed live), 18 in-window inspections
  fetched, 0 deficient survivors → 0 WOs (consistent with ~1/month prod baseline). Task-create/
  attachment/mapping branches await a deficiency day. OQ-037 draft-drop + OQ-047 window watch
  continue on subsequent daily runs.
- **Zero-instruction fix (A7 gap, owner-approved 2026-08-01) applied to BOTH copies:**
  `alwaysOutputData: true` on `Get Instructions` — FM360 `8JvtesynrYtZbw7U` + coastal
  `uhmXW1jlImUdXQVw` (live published version read back and verified, activeVersionId
  b7bb51a7). **Execution-verified by proxy only:** identical fix class proven on Step 1
  (exec 127289) + Step 3 (exec 127286) under OQ-045; downstream `Collect Child Links`
  optional-chaining tolerance verified by code read; direct execution impossible — sandbox
  wiped (see below).
- **Sandbox discovered WIPED by other hands** (2026-08-01): Limble location 98472 AND A6
  locations 98872–98878 return `[]` — all ledgered fixtures gone. Teardown task is done
  externally; the planned FM360-staged execution test for the zero-instruction fix became
  impossible (rebuilding fixtures in the Coastal account is unclean post-cutover: live hooks
  would fire production workflows at fake data). Residual teardown item: `coastal-seed-team`
  branch (3 nodes) still in FM360 seeder `qyMChP0DKfI04r4a` — **CLEARED 2026-08-01: branch
  removed (14→11 nodes) and the whole seeder DEACTIVATED** (write-capable test rig with no
  remaining target). Teardown fully closed. Mock Coupa/EHS rigs left active on FM360 as the
  standing regression environment.
- **EHS key rotation removed from engagement scope** (owner ruling 2026-08-01): client team
  carries rotation post-handoff; facts + procedure recorded in DEPLOYMENT section 0 EHS row.

## Post-cutover review — 2026-08-03 (day 3 live)

Reviewed all coastal execution history. **Every execution since cutover is `status: success`,
with zero errors** — but most of that green comes from correct early gate exits, not from work
performed. Node-level verification, not status-level:

**Proven live**

- **Token Refresh** (`1phqgrpFuSZOFqxS`) — fired 08-02 and 08-03 at 04:00:30Z (= midnight ET).
  Exec 982 ran 4/4 nodes **including the store node** `Update Coastal Coupa OAuth Token`, on a
  real `{access_token, token_type, expires_in}` response; the 5th node (failure alert) correctly
  did not run. This is the Deer-Valley silent-failure check (a token refresh whose HTTP node
  error-branches to an alert still reports `success`) — it passes.
- **Token row** carries a live JWT + real PROD scope; `refreshed_at`/`updatedAt` advance daily.
  Note: JWT `exp` = `iat + 86400`, i.e. the token expires exactly when the next daily refresh
  runs. Faithful to Fuse's daily-midnight design, but the margin is ~zero — **one missed refresh
  run is an outage.** Watch item, not a defect.
- **Limble PROD reads** — Step 2's `Get 'PO Requested' Status ID` resolves to `statusID 5782`
  with `name: "PO Requested"` (the name in the response self-validates the ID, ruling out a
  wrong-status silent zero); Step 1/Step 3 `Get Task` return full real task objects.
- **Limble webhook delivery** — all 3 coastal endpoints receiving real events; body shape
  `{taskID, status, category, user}`.
- **EHS GETs** — real envelopes `{ResultCode, List[]}` and `{ResultCode, Entity{…}}` parse clean.
- **EHS Create cron** — 3/3 daily runs on time (execs 461 / 853 / 1293 at 20:00:00Z). Durations
  12.3 s / 33.0 s / 3.6 s = inspection-volume variance, **not** a trend. All three ended at
  `Any Deficient Forms?` false → 0 WOs, consistent with the ~1/month deficiency baseline.
- **Error Log Export + Ionos SMTP, on the COASTAL copy** — see DEPLOYMENT section 7
  (2026-08-03 note). Previously proven only on the FM360 copy at A3 E1.

**Still unproven live — the real Phase C risk**

- **Every Coupa call except `/oauth/token` is still unexercised by the workflows themselves.**
  Step 2 exits at `Get 'PO Requested' WOs` → 0 items (Coupa never contacted); Step 1 exits at
  `Is CoupaWO in PO Create?`; Step 3 exits at `WO is Coupa Related?`. No requisition created, no
  PR/PO read, no invoice pushed in 3 days.
- **HOWEVER — Step 2's Coupa response ENVELOPES are now verified (2026-08-03, out-of-band
  read-only probe, owner-run).** This was the PC-Maintenance-PB5 / CWI-FIX-06 risk; it is closed
  for Step 2:
  - `GET /api/requisitions/{id}` + `Accept: application/json` → **HTTP 200, bare JSON object**
    (37 keys), with `.id` and `.status` present (`'draft'` on the sample). So
    `Get Associated Requisition` → `Is Requisition Ordered?` (`$json.status == "ordered"`)
    resolves correctly — **no wrapper, no silent-`undefined` drop.**
  - `GET /api/purchase_orders?requisition-header[id]={id}` → **HTTP 200, bare JSON array**, as
    the node note assumes (n8n splits to items). The literal-bracket query key is accepted (no
    400). Sample returned `[]` because the test requisition was `draft`.
  - **Coupa field names are kebab-case** (`buyer-note`, `created-at`, `line-count`,
    `estimated-tax-amount`). Step 2's only multi-word read already uses bracket notation —
    `$("Get PO Created From Req.").item.json["po-number"]` — so it is correct. Any future Coupa
    field read must use bracket notation, not dot.
  - Probe method note: the JWT was integrity-gated locally (iat/exp/client_id checked against
    the stored row) before any request, so a `401` could not be mistaken for an envelope result.
    Four in-session attempts were denied by the Bash permission classifier; the owner ran it.
  - **Residual CLOSED same day:** `GET /api/purchase_orders?limit=1` returned a real PO —
    `po-number` present and non-null, `id` present (sample `10370`), 39 keys all kebab-case.
    **Step 2's Coupa contract is fully verified: both envelopes + both field names.** Noted for
    future changes: one PO is ~64 KB, and `requisition-header` is a nested object on the PO.
  - **Watch item (not a defect, 1:1 posture):** an empty `[]` from the PO lookup becomes 0 items
    in n8n and prunes the rest of the chain silently — no WO update, no error row. Fuse read
    `body[1]` and would have errored. Benign in that a later 5-min poll retries, but it means an
    `ordered` requisition with no visible PO produces zero signal.
- **The empty backlog is genuine, not a query artifact:** an independent Limble prod query for
  `statusIDs=5782` also returns `[]`, agreeing with the workflow's own HTTP node. Three days is
  too few to characterize the expected event rate — do not read the silence as either healthy
  or broken without Coastal's baseline.
- **EHS WO-creation half** of `6mAzjD1LG6AcDV5p` (create / attachment / location-mapping,
  ~26 of 34 nodes) — awaits a deficiency day.
- **EHS Update write path** (`uhmXW1jlImUdXQVw`) — webhook runs are 14–30 ms gate-outs; no
  `@EHS;`-tagged completion has arrived. The OQ-045 zero-instruction `alwaysOutputData` fix
  remains execution-verified by proxy only.

### Alerting added 2026-08-03 (OQ-049) — 8th workflow on coastal

The day-3 review surfaced that **unhandled** failures reached nobody: EHS Update and EHS Create have
no error handling at all, Step 3 routes only 3 of its nodes to the error log, Token Refresh's
**store** node has no error branch, and no workflow had `settings.errorWorkflow` set. With the owner
away from 2026-08-05 there is no shepherd, so this was sanctioned as a fix (OQ-049).

- **`Coastal - Unhandled Error Alert` — `E4eyrICfuZLTFyyr`** (ACTIVE, 2 nodes): `errorTrigger` →
  `emailSend` to `integrations@` via `XbGIxN8MFDM3DJoS`.
- `settings.errorWorkflow = E4eyrICfuZLTFyyr` on **all 7** production workflows.
- **Proven by execution, not config** — exec **1325**: Error Trigger received real context, email
  returned SMTP 250. The first attempt with the handler left **inactive produced ZERO executions**
  (no published version to invoke, fails silently) — see OQ-049 for the full finding.
- Coastal now holds **8 workflows**. Note for future audits: a count of 7 is now WRONG.
