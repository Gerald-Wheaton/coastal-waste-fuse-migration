# Handoff 4471 — OQ-048 port EXECUTED (7/7 on coastal); Step 1 stray-create incident; resume list

Written 2026-08-01 (session of 2026-07-31). Prior context: handoff-3157 (ruling + verdict),
handoff-6482 (the old blocked [M] pass — now ABSORBED by this port, do not re-run against FM360).

## Goal

Execute the OQ-048 port: all 7 workflows + placeholder credentials + data tables onto
`https://coastal.n8n.fm360consulting.com`, in cutover config, per the owner rulings captured
in-session (cutover-config-direct; failMode table does not port; verification = validate +
inspection, no execution pre-cutover).

## Current Progress — PORT COMPLETE

- **7/7 workflows on coastal, inactive, cutover config.** All IDs, per-workflow transform
  receipts, webhook URLs, and the placeholder-credential/table IDs: **`docs/oq-048-port-ledger.md`**
  (authoritative). Also synced: DEPLOYMENT.md (banner, ID table with coastal column, webhook
  URLs), OQ-048 addendum in open-questions.md, project CLAUDE.md tooling section, memory file.
- 3 data tables created + seeded (token row: blank oauth_token + Phase-A stub scope; config
  row: 317887 pending OQ-019; error-log empty). 4 placeholder credentials created (same types
  as real — httpHeaderAuth x2, httpCustomAuth, smtp), names marked `[PLACEHOLDER - populate value]`.
- Error Log Export's OQ-013 self-error alert recipient was restored to
  integrations@fm360consulting.com on the coastal copy (was gerald@ dev override; OQ-013
  resolution documents the intended value — no owner ask needed).
- Port ran as 4 sequential background agents + 1 redo agent; every transform grep-gated
  (fm360.n8n / mock hosts / old cred+table IDs / gerald@ all zero-hit before create).

## Step 1 stray-create incident (READ THIS before any future n8n CREATE)

Batch D's create of Step 1 landed on **DrinkPak** — the shared MCP binding flipped mid-batch
(parallel session active that night). The agent's ID-addressed read-backs (get/validate on the
new ID) all "passed" because they succeed on whatever instance holds the workflow —
**instance-blind**. Caught only by a physical `n8n_list_workflows` on coastal (6, not 7).
Stray `EabuMg2NUvyXGUmo` deleted from DrinkPak (owner-approved; first delete attempt was
blocked by the auto-mode permission classifier — owner approval cleared it). Redo created
**`4fFRbDT7bluYEPc7`** with immediate physical LIST verification (7/7, nodeCount 50).
Global lesson recorded in ~/.claude/CLAUDE.md: **a CREATE is verified only by a LIST on the
intended instance.**

## What Worked

- Interview-first ratification (AskUserQuestion) of the 3 port sub-decisions before building.
- Sequential background agents with per-batch transform specs, expected-count assertions, and
  grep gates; scratchpad JSON artifacts for audit (`wf1-3`, `step2/3-*`, `ehs-create-*`,
  `create-payload.json` — session scratchpad, gone next session).
- Chunked structure+filtered fetch for the 50-node Step 1 (full fetch would truncate).
- Physical-presence LIST as the create success criterion (the incident-catcher).

## What Didn't Work

- Two agent runs died to transient "Connection closed mid-response" API errors — resume via
  SendMessage worked; parse the JSONL transcript for recovered state when the final report is
  lost.
- ID-addressed read-backs as create verification (see incident).
- `n8n_delete_workflow` blocked by auto-mode classifier (same class as handoff-6482's blocks);
  owner per-call approval cleared it.
- `settings.binaryMode: "separate"` (present on all FM360 sources) is rejected by the n8n
  public API create schema — dropped on all 7 coastal copies (instance default applies).
  Watch item at C6: confirm binary handling on EHS Create's attachment fetch.

## Next Steps (session task list mirror)

1. **Owner populates on coastal:** 4 placeholder credentials (Limble prod header, ROTATED EHS
   key, Coupa client_id/secret custom-auth JSON — verify the JSON shape against the FM360
   credential when populating, placeholder shape was a guess — Ionos SMTP); real Coupa PROD
   `scope` on token-table row `u818Gq3vZSTXdgeh` (currently Phase-A stub; capture path in
   DEPLOYMENT section 0/1).
2. **[EXT] chase (unchanged, now coastal-targeted):** OQ-020 webhook admin (UNOWNED — critical
   path; the 3 URLs are in the ledger + DEPLOYMENT webhook section); EHS key rotation + old-key
   revocation (old key still worked 2026-07-27); OQ-019 confirm 317887 (coastal config row
   pre-set, edit if Coastal names someone else).
3. **Section 7 Eastern re-run** — owner Execute on FM360 `hR5YnDixecDz9HzJ`; error-log rows
   23/24 are the staged fixture (do NOT clean); THEN restore ethan@ on the FM360 copy if
   desired (coastal copy already ships ethan@ + integrations@ alert).
4. **Sandbox teardown** (`python3 tools/sandbox-seed/teardown.py`, Bash-permission-gated) +
   seeder `coastal-seed-team` branch removal (3 nodes, n8n write on FM360).
5. **Owner decision:** EHS Update zero-instruction gap (document vs alwaysOutputData fix —
   test-sequence.md A7 "NEW GAP" note; if fixed, apply to coastal copy `uhmXW1jlImUdXQVw`).
6. **Cutover execution** (owner-gated): disable Fuse scenario per workflow, register the 3
   coastal webhooks + disable Fuse subscriptions, activate coastal IDs one at a time.
   **Order discrepancy to resolve first:** DEPLOYMENT.md sequence vs test-sequence.md Phase C
   order (C1 Token → C2 Step 2 → C3 Error Log → C4 Step 1 → C5 Step 3 → C6/C7 EHS) — Phase C
   order recommended (Step 2 read-heavy, proves real Coupa GET shapes before Step 1 writes).
7. **Phase C shepherd watch** per test-sequence.md C1–C8 (incl. OQ-047 #2 capture, OQ-037
   first live behavior, OQ-018 prod user count, binaryMode watch at C6).
8. Doc debt (small): flip A1/A2 expectation in ehs-test-plan.md (FIC-1002 now the pass);
   Step 2 build-spec sections 72/203 metadata note; cosmetic FM360-ID references inside 3
   coastal node notes (ledger lists them). Commit the repo changes (uncommitted:
   CLAUDE.md, DEPLOYMENT.md, open-questions.md, docs/oq-048-port-ledger.md, this handoff).

## Standing constraints (unchanged)

- Never activate a workflow without asking the owner. Verify n8n instance by URL before any
  MCP call; verify CREATEs by LIST on the intended instance. Serialize all n8n writes in one
  agent. ~100 MCP calls/day. Mock rigs only for Coupa/EHS; Limble writes sandbox-only
  (loc 98472). No real credential values in repo files, ever.
