# Build Spec — Coastal - Coupa Token Regeneration (PROD)

Status: **built in n8n** (2026-07-01), workflow ID `oCAl4h0SZenEtbNs` ("Coupa - Token
Refresh"), inactive. Built after explicit owner go-ahead, scoped to this workflow only —
the other 6 Coastal scenarios have workflow shells provisioned but remain design-only
until each gets its own explicit go-ahead (see OQ-003 addendum, OQ-007).

Source blueprint: `docs/OG-workflows/Coastal - Coupa Token Regeneration (PROD).json`
(3 modules, 0 `onerror` chains, no custom functions — the simplest of the 7 scenarios).

---

## 1. Purpose

Refresh Coupa's OAuth2 access token daily and make it available to the three other
Coupa-side workflows (Create Requisition / Check For New PRs Ordered / WO Completed), none
of which are in scope for this spec.

## 2. Trigger

| | Source (Make) | n8n target |
| --- | --- | --- |
| Type | Scheduled, daily @ 12:00 AM MST | **Schedule Trigger** node, Cron mode, `0 0 * * *` |
| Timezone | Literal "MST" per `docs/workflow-list.md` — not independently verifiable from the blueprint export (schedules live in Make's scenario settings, not the JSON) | **`America/Denver`** (DST-aware) — confirmed, OQ-011 resolved |

## 3. Source flow (Make, as-is)

1. `datastore:SearchRecord` (id 2, "Grab the Coastal Coupa Auth Record") — reads datastore
   324, filtered `client = "coastal_waste (PROD)"`. Returns `client_id`, `client_secret`,
   `scope`, `grant_type`, plus `client`/`apiConnection` (carried through, unused downstream).
2. `http:ActionSendData` (id 4) — `POST https://coastalwasteinc.coupahost.com/oauth2/token`,
   `Content-Type: application/x-www-form-urlencoded`, body: `client_id`, `grant_type` (literal
   `client_credentials`), `scope`, `client_secret`. `handleErrors: true`.
3. `datastore:AddRecord` (id 3, "Update Auth Record w/ New OAuth2 Token") — overwrites the
   same datastore-324 record, same key, with all original fields plus `oauth_token` set from
   step 2's `access_token` response field.

No `onerror` chain anywhere in this scenario — a token-refresh failure is currently silent
in production. (Confirmed via `docs/workflow-overview.md` and a direct read of the export.)

## 4. Design decisions locked in for this spec

These are the calls made while scaffolding this workflow — see `open-questions.md` for the
full record (OQ-005 addendum, OQ-010, OQ-011).

1. **Faithful port, not a switch to n8n-native OAuth2 credential management.** n8n's
   `httpRequest` node supports a built-in "OAuth2 API" credential with a Client Credentials
   grant that would auto-refresh per call, making a scheduled refresh workflow unnecessary.
   Rejected for now — bigger behavior change than OQ-005 sanctioned, and it presumes a design
   for workflows #2-4 that haven't been scoped yet. This workflow keeps doing the manual
   token POST and writing the result somewhere for others to read.
2. **`datastore:SearchRecord` (module 2) is dropped entirely.** Under OQ-005, client_id and
   client_secret already move into an n8n credential — once that's true, there's nothing left
   for a lookup step to fetch (grant_type was already a hardcoded literal in the source; scope
   is handled per decision 3 below). Net: this workflow goes from 3 modules to 2 real steps
   (call token endpoint → store result) plus a failure branch.
3. **`scope` is read from the Data Table**, not hardcoded. Revised after §4.2 shipped:
   `grant_type` stays a literal (required by the OAuth2 client_credentials grant itself — not
   vestigial, unlike the datastore's unused copy of it in the source). `scope` is a real,
   client-specific input to the token request, just not secret, so it gets its own column on
   "Coastal - Coupa OAuth Token" (added via the n8n UI — the public API can't alter an
   existing table's schema, rename only) and a **Get row** lookup step ahead of the HTTP
   node. This reintroduces a lookup step the earlier design dropped, scoped narrowly to just
   `scope` — client_id/client_secret still come from the credential, not this table.
4. **client_id/client_secret live in an n8n credential of type `httpCustomAuth`** ("Custom
   Auth" under the HTTP Request node's Generic Credential options), not a predefined OAuth2
   credential — because we're manually building the token request ourselves, not delegating
   the OAuth flow to n8n. This credential type holds a JSON blob that n8n merges into the
   outgoing request (body/headers/qs) at send time, so the secret values never need to appear
   in the node's visible configuration or in an expression.
5. **The refreshed token is written to a new, dedicated n8n Data Table**, not the shared
   error-log-style table and not a re-creation of the full 7-field datastore-324 record.
   Schema trimmed to what's actually read downstream (per the project's established
   convention — see `docs/module-translation-reference.md` §6). Workflows #2-4 will read from
   this table instead of datastore 324 when their specs are written — not built here, but the
   dependency is now anchored to a concrete name (§6 below).
6. **Error handling added** (a sanctioned fix under OQ-001 — this workflow currently fails
   silently in Make). Does **not** reuse the shared Coupa error-log Data Table that Step 1/
   Step 3 will write to, because that table's schema requires `limbleWONum`, and this workflow
   has no Limble WO context at all — faking that field was rejected. Instead: a direct email
   alert on failure.
7. **Email delivery uses the "Integrations Ionos" credential** (per OQ-010, which applies
   across all 7 workflows). **Recipient during build/pre-launch: `gerald@fm360consulting.com`
   only** — swap to the real production recipient when the owner confirms go-live (OQ-010).

## 5. Target n8n node graph

```
[Schedule Trigger]
        |
        v
[Data Table: Get row (scope lookup)]
        |
        v
[HTTP Request: Refresh Coupa OAuth Token] ---(error output)---> [Send Email: Token Refresh Failed]
        |
   (success output)
        v
[Data Table: Upsert "Coastal - Coupa OAuth Token" row]
```

### 5.1 Schedule Trigger

- Cron: `0 0 * * *`
- Timezone: `America/Denver` (flagged — OQ-011)

### 5.2a Data Table — "Get Coastal Coupa Auth Config"

- Node: `n8n-nodes-base.dataTable`, resource `row`, operation `get`
- Filter: `client = "coastal_waste"`
- Purpose: fetch `scope` (non-secret, but not hardcoded — see §4.3) ahead of the token call.
  `client_id`/`client_secret` are **not** read here — they stay in the `httpCustomAuth`
  credential (§5.2b). Reintroduces a narrow version of the lookup step §4.2 originally
  dropped, scoped only to `scope`.

### 5.2b HTTP Request — "Refresh Coupa OAuth Token"

- Method: `POST`
- URL: `https://coastalwasteinc.coupahost.com/oauth2/token`
- Body type: Form-Urlencoded
  - `grant_type` = `client_credentials` (literal — required by the OAuth2 client_credentials
    grant itself, not the same as the source datastore's unused copy of this field)
  - `scope` = `={{ $json.scope }}` (from the Get-row lookup, §5.2a)
- Headers: `Content-Type: application/x-www-form-urlencoded`
- Authentication: Generic Credential Type → **Custom Auth**
  - Credential name: **"Coastal Coupa OAuth Client Credentials"** (n8n credential ID
    `7ZQlnJJWRJsZw1C3`, created with placeholder JSON — real client_id/client_secret still
    need to be entered directly in the n8n UI; never passed through this chat or written into
    this repo per CLAUDE.md's Secrets constraint):
    ```json
    { "body": { "client_id": "REPLACE_ME_IN_N8N_UI", "client_secret": "REPLACE_ME_IN_N8N_UI" } }
    ```
    **Action needed:** owner (or whoever holds the real Coupa client_id/secret) opens this
    credential in the n8n UI and replaces the placeholder values before this workflow can
    actually succeed on a real run.
  - **Merge behavior — confirmed against a live example in this instance**, not just docs:
    `httpCustomAuth`'s JSON is a partial request-config object (`headers`/`qs`/`body` keys)
    that n8n deep-merges into the outgoing request at send time. Checked "GeoTab - Inland
    Steel" (same credential type, used by the "Odometers - Geotab to Limble" workflow's "Get
    Credentials" node) — that node has no body/query params configured at all, meaning the
    entire request payload comes from the credential's JSON blob. Same pattern applies here.
- On Error: **Continue (using error output)** — routes failures to the email branch instead of
  halting/retrying indefinitely.
- **Retry On Fail: enabled, 3 attempts** — closest n8n equivalent to the Make scenario's
  `maxErrors: 3`. Falls through to the failure-email branch only after all 3 attempts fail.

### 5.3 Data Table — Upsert "Coastal - Coupa OAuth Token"

Data Table created, name: **"Coastal - Coupa OAuth Token"** (n8n Data Table ID
`QAj62weJaWmRBJ76`). Single row, keyed by a fixed label (mirrors the source's
single-record-per-client pattern; there's only ever one Coastal Coupa token).

| Column | Type | Source | Written by this workflow? |
| --- | --- | --- | --- |
| `client` | string | literal `"coastal_waste"` — the match key | yes (upsert match key) |
| `oauth_token` | string | `{{ $json.access_token }}` from the HTTP Request response | yes |
| `refreshed_at` | date | current execution timestamp | yes |
| `scope` | string | added via n8n UI (API can't alter existing table schema) — seeded manually with the real Coupa scope value | **no** — read by §5.2a, deliberately left out of the Upsert's column mapping so it's never overwritten |

Operation: **Upsert row**, filter `client = "coastal_waste"`. `apiConnection`, `client_id`,
`grant_type`, `client_secret` all live in the credential or as literals — not in this table.

### 5.4 Send Email — "Alert: Coupa Token Refresh Failed"

- Node: `n8n-nodes-base.emailSend`, credential: **Integrations Ionos** (id `vPXcXvRpktLu49Vr`)
- From: `integrations@fm360consulting.com` (matches the pattern used by the analogous
  "Deer Valley - Auth Refresh" workflow's failure-alert node in this same instance)
- To: `gerald@fm360consulting.com` (dev/pre-launch only — OQ-010)
- Subject: `Coastal Coupa Token Regeneration failed`
- Body: plain-text, includes `{{ $json.error }}` from the HTTP node's error output.

## 6. Cross-workflow dependency this creates

Workflows #2 (Create Requisition), #3 (Check For New PRs Ordered), #4 (WO Completed) currently
read the Coupa token from datastore 324. Their specs (not written yet) should read from the
**"Coastal - Coupa OAuth Token"** Data Table (`QAj62weJaWmRBJ76`, §5.3) instead.

## 7. What's actually built vs. still open

**Built (2026-07-01):**
- Workflow `oCAl4h0SZenEtbNs` ("Coupa - Token Refresh") — 5 nodes (Schedule Trigger → Get
  row → HTTP Request → Upsert row / Send Email on error), validated 0 errors, inactive.
- Credential `7ZQlnJJWRJsZw1C3` ("Coastal Coupa OAuth Client Credentials", type
  `httpCustomAuth`) — placeholder values only.
- Data Table `QAj62weJaWmRBJ76` ("Coastal - Coupa OAuth Token") — 4 columns (`client`,
  `oauth_token`, `refreshed_at`, `scope`); `scope` column added via the n8n UI directly
  (public API doesn't support altering an existing table's schema).

**Still open:**
- **Real Coupa client_id/client_secret** — must be entered into the credential via the n8n UI
  directly (§5.2b). The workflow cannot succeed on a real run until this happens.
- **Real scope value** — owner is seeding the `scope` column's row value directly (pulled
  from Make's datastore 324, which isn't exported to this repo). Not secret, but not yet
  confirmed done.
- **Activation** — the workflow is built but left inactive; turning it on (so the schedule
  actually fires) is a separate decision, not yet asked.
- **`httpCustomAuth` merge behavior** (§5.2b) — confirmed against a live example in this
  instance ("GeoTab - Inland Steel"), not literally test-run for this credential yet — worth
  one real execution once the real secrets are in place.
