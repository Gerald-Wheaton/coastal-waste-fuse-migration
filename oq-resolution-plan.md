# OQ Resolution Plan — how to close every remaining open question

Compiled 2026-07-17 from `open-questions.md` (13 open) + `DEPLOYMENT.md` (open gates that are
questions, not just tasks). Grouped by who can answer. Emails drafted at bottom.

## Priority order

1. **OQ-042** — blocker (EHS Create WO). Send the staged Limble support ticket; Ethan checks Fuse PROD history in parallel.
2. **OQ-039 + OQ-041** — biggest cutover-risk killers (real-Coupa shape + token collision). One Ethan authorization unlocks both.
3. **OQ-014 + OQ-019 + EHS key rotation** — cheap client confirmations; one email.
4. **Decision batch (OQ-013/018/035/037/040 + alert recipient + OQ-020 mechanics)** — one Ethan email.
5. Self-serve verification + doc housekeeping.

## Question list + routing

| ID | Workflow(s) | Question | Ask | How it closes |
|---|---|---|---|---|
| **OQ-042** (BLOCKER) | EHS Create WO (`isLUx7cUjkmKggD2`) | Real Limble instruction-response write endpoint (`PATCH /v2/instructions/{id}` 404s; no public write route exists — GET-shape proven) | **Limble support** (Gmail draft staged 2026-07-17 — send after Ethan review) + **Ethan** (check Fuse PROD run history: did `updateAnInstruction` ever succeed? settles exists-vs-no-op fork) | Support reply gives route → fix node → re-test A6; or confirmed always-no-op → drop node |
| **OQ-039** | Token Regen, Step 2 (Coupa GETs) | Authorize live read-only testing against `coastalwasteinc-test.coupahost.com`? Need current test client_id/secret | **Ethan** (authorization + creds); optionally Coastal confirms instance is non-prod-safe | Approval → load creds → re-run A2 + Step 2 read paths live |
| **OQ-041** | Token Regen (cutover sequencing) | Coupa `client_credentials`: concurrent tokens or rotate-and-invalidate? n8n + Fuse share one client at parallel-run | **Coupa docs** (Compass, via NotebookLM/web) → **empirical test** on OQ-039 instance (mint 2 tokens, check first still valid) → Coupa support only if both inconclusive | Answer sets cutover sequencing: concurrent = parallel-safe; rotate = disable Fuse Coupa scenarios before activating Token Regen |
| **OQ-014** | Token Regen, EHS Create (schedules); Error Log Export (timestamp display) | Eastern vs Mountain — recon: all ~49 Limble locations are America/New_York; "MST" in workflow-list looks like the error | **Coastal** (via Ethan) | Confirmation → likely flip 3 workflows to America/New_York (Token Regen built Denver — 1-line change); update OQ-011/012 entries |
| **OQ-019** | Step 1 + Step 2 error paths | Is Brandon Ray Freckleton (317887, active Super User) still the right escalation @-mention for go-live? | **Coastal** (via Ethan) | Yes → done; No → swap ID in both workflows (also revert test-phase 398783 retarget per DEPLOYMENT sections 2/3) |
| **OQ-020** | Step 1, Step 3, EHS Update (webhooks 1742/1743/1744) | Who has Limble webhook admin; atomic swap vs overlap window acceptable? | **Ethan** (+ Coastal Limble admin) | Mechanics recorded in DEPLOYMENT cutover section |
| **OQ-013** | Error Log Export | Own failures silent (faithful) vs add failure-alert email? | **Ethan** decision | Decision logged; if fix, small build change |
| **OQ-018** | Step 1 | listUsers 500-cap: faithful single page (79 users today) vs paginate? | **Ethan** decision | Decision logged; likely faithful |
| **OQ-035** | EHS Create WO | `last(Questions)` inspects only last question — intended or fix (iterate all deficient)? | **Ethan** (may need Coastal intent) | Decision logged; fix = node change |
| **OQ-037** | EHS Create WO | `CoastalEHSFormFilter` UpdateDtm/UpdatedDtm typo — dedupe keeps first-seen, not latest. Port bug or fix? | **Ethan** decision | Decision logged; fix = 1-char Code-node change |
| **OQ-040** | Step 2 | Team-comment path (S2-2) unprovable — sandbox team 107065 is View Only role-team | **Ethan**: create real maintenance team at loc 98472, or accept Phase-C deferral | Team created → run S2-2; or deferral recorded |
| **OQ-028** | Step 1 (+ all mocked workflows) | Teardown checklist verified at cutover; residuals R1–R3 (assigned-task comments, admin comment, Error Log Export end-to-end); R4 folds into OQ-039 | **Self** (cutover checklist) + OQ-039 outcome | Closes at cutover verification |
| **OQ-009** | All | Authoritative API refs for Limble/Coupa/EHS Insight? | **Ethan** (any Postman/Swagger?) + **NotebookLM** (Limble docs loaded — already used for OQ-042) + public Coupa Compass + EHS Insight dev docs | Pointer received, or closed as "reverse-engineered + live-verified" |

### From DEPLOYMENT.md only (not OQ-numbered)

| Item | Workflow | Ask | How it closes |
|---|---|---|---|
| "Token Refresh Failed" alert recipient (TBD) | Token Regen | **Ethan** | Recipient set in node + DEPLOYMENT table |
| EHS key rotation before go-live | EHS Create + Update | **Coastal** (via Ethan) — action, not question | New key issued → n8n credential only |
| EHS attachment-fetch response shape (file_data mapping guessed) | EHS Create WO | **EHS Insight API docs** (NotebookLM/web) or first live EHS call | Shape confirmed → node verified |
| Child-task fetch resolves + `body[0].completionNotes` shape; completion-note tz | EHS Update | **Self** — live sandbox test (A-phase); tz rides on OQ-014 | Sandbox run proves it |
| Stale doc rows: section 0 says OQ-011 open (resolved via OQ-014 path), Coupa creds "Needed" (loaded 2026-07-03, OQ-015), Data Table ID blanks (known: token `QAj62weJaWmRBJ76`, error log `6GbR5Rxezl7hqk9i`) | — | **Self** — housekeeping edit | DEPLOYMENT.md updated |

## Drafted emails

### 1. To Ethan (ethan@fm360consulting.com) — decision batch + authorizations

> **Subject: Coastal n8n migration — remaining decisions/questions to close test phase**
>
> Hi Ethan,
>
> Test phase is nearly wrapped. These are the open items that need your call — grouped so you can answer inline. IDs reference open-questions.md.
>
> **Blocker first — OQ-042 (EHS Create WO):** the Limble support ticket about the instruction-response write endpoint is drafted and ready; say the word (or edit) and I'll send it. In parallel, could you check the Fuse PROD run history for "Create WO From EHS Inspection" — has its "Update An Instruction" step ever completed successfully? That tells us whether the endpoint exists privately or the write-back was always a no-op.
>
> **Authorizations:**
> 1. OQ-039 — A Coupa TEST instance exists (coastalwasteinc-test.coupahost.com) and we held working client creds for it on 7/1. Authorize read-only test calls (Token Regen + Step 2's two GETs) against it? If yes, I need the current test client_id/secret loaded into the n8n credential. This converts most of our "mock shapes are guesses" cutover risk into pre-cutover testing, and lets me answer OQ-041 (below) empirically.
> 2. OQ-041 — At cutover, n8n and Fuse will share the same Coupa OAuth client. If Coupa rotates-and-invalidates tokens per client, each system's refresh breaks the other during the parallel-run window. I'll check Coupa's docs, but the clean answer is a two-token test on the TEST instance (needs #1).
> 3. OQ-040 — Step 2's team-comment path can't be proven in the sandbox: the only team there (107065) is a "View Only" role-team the /v2/teams endpoint doesn't return. Either create a real maintenance team at sandbox location 98472, or we defer that one assertion to go-live validation (the user-comment variant already passed).
>
> **Faithful-vs-fix decisions:**
> 4. OQ-013 — Error Log Export has no error handling of its own (a failed SMTP send is silent, as in Make today). Port as-is, or add a failure-alert email like Token Regen has?
> 5. OQ-018 — Step 1 fetches Limble users in one page of 500. Coastal has 79 users today. Keep faithful single-page, or paginate?
> 6. OQ-035 — EHS Create WO only inspects the *last* question of an inspection for a deficient answer/attachment (as shipped). Keep, or iterate all deficient questions?
> 7. OQ-037 — The EHS dedupe function has a field-name typo (UpdateDtm vs UpdatedDtm), so a site with multiple inspections in the window keeps the first seen, not the latest. Port the bug, or fix (one-line)?
>
> **Cutover logistics:**
> 8. OQ-020 — Who has Limble webhook admin access for the swap of the 3 webhooks to n8n URLs, and is a brief both-systems-firing overlap acceptable, or must each swap be atomic?
> 9. Token Regen's "Token Refresh Failed" alert — who should receive it in production? (Currently dev-routed to me.)
>
> I've also drafted three quick confirmations for Coastal (timezone, Brandon as escalation contact, EHS key rotation) — draft below; happy to send directly or have you forward it.
>
> Thanks,
> Gerald

### 2. To Coastal (recipient TBD — route via Ethan)

> **Subject: Limble integration migration — three confirmations needed**
>
> Hi [name],
>
> As we prepare to move the Limble–Coupa and Limble–EHS Insight integrations to the new platform, three quick confirmations:
>
> 1. **Timezone** — All of your Limble locations are configured for Eastern time, but the original integration docs list Mountain for the daily schedules. Should the daily jobs (Coupa token refresh at 12:00 AM, EHS inspection sync at 4:00 PM) and error-report timestamps run on Eastern? *(Affects the token-refresh, EHS-sync, and error-report workflows.)*
> 2. **Escalation contact** — When the Coupa integration hits an error, it tags Brandon Ray Freckleton (bfreckleton@coastalwasteinc.com) in a Limble comment on the work order. Is Brandon still the right contact for go-live, or should this point to someone else? *(Affects the Step 1 and Step 2 Coupa workflows.)*
> 3. **EHS Insight API key** — The current key was embedded in the old integration's export files, so we treat it as exposed. Please issue a new EHS Insight API key before go-live; it will be stored only in the new platform's credential vault, and the old key can then be revoked. *(Affects both EHS workflows.)*
>
> Optional fourth, if applicable to you rather than FM360: confirm that coastalwasteinc-test.coupahost.com holds non-production data and is safe for integration testing.
>
> Thanks,
> Gerald Wheaton
> FM360 Consulting

### 3. Limble support (OQ-042)

Already drafted and staged as a Gmail draft (2026-07-17): to support@limblecmms.com, subject
"API v2: how to update an existing task instruction (text/response/image)? No PATCH route
found". Action = Ethan review, then send. Do not redraft.

### 4. Coupa support (OQ-041) — HOLD, only if docs + empirical test both fail

> **Subject: OAuth client_credentials — are access tokens per client concurrent or single-active?**
>
> Hi,
>
> For instance coastalwasteinc.coupahost.com: when a client obtains a new access token via `POST /oauth2/token` (`grant_type=client_credentials`), does the previously issued token for that same client remain valid until its own expiry, or is it invalidated when the new token is issued? We run two systems sharing one client during a migration window and need to know whether token refreshes collide.
>
> Thanks,
> Gerald Wheaton, FM360 Consulting (on behalf of Coastal Waste & Recycling)

## Self-serve next actions (no one to wait on)

1. NotebookLM: query Coupa docs for client_credentials token semantics (OQ-041) and EHS Insight docs for the attachment-fetch response shape.
2. Sandbox: EHS Update child-task fetch + completionNotes shape test (DEPLOYMENT section 6 items).
3. Housekeeping edits to DEPLOYMENT.md stale rows (OQ-011 status, Coupa-cred row, table-ID blanks).
