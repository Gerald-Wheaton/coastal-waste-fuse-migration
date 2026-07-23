# Fuse (Make.com) → n8n: recurring translation patterns

Cross-engagement patterns confirmed by ≥2 independent instances. Sources:

- **deer-valley** — "Deer Valley Meter Sync" (FuelCloud↔Limble). Deployed twice to real n8n
  instances, validated 0 errors, tested against live prod Limble data. Inactive pending final
  cutover, but structurally shipped. See `deer-valley/n8n-workflows/MIGRATION-NOTES.md`,
  `DEBUG-REFERENCE.md`.
- **drink-pak** — "Step 1" (New Limble PO→SAP) and "Step 2" (PO Closure & Check). Built in a
  real n8n instance via MCP, validated 0 errors, tested against sandbox/mock data only —
  never activated (gated on unresolved SAP IP whitelisting). Weaker bar than deer-valley
  (no live-data test), but a real, validated n8n node graph, not just a design doc. See
  `drink-pak/docs/build-specs/step-1/step1-build-notes.md`,
  `drink-pak/docs/build-specs/step-2/step2-build-spec.md`.
- Drink-pak's other three workflows (Vendor Sync, Error Report, Error Report–Taxes) never
  left the design-doc stage — excluded as evidence entirely.

---

## 1. Bundle→item model (Repeater / Aggregator / Feeder)

**Pattern:** don't hunt for 1:1 loop nodes. n8n's item array already carries the
multiplicity Make needed a repeater+roundtrip-variable+aggregator triad for. Replace the
whole triad with a **Code node that emits one n8n item per unit of work**, let the
downstream node run natively once per item, then a **second Code node that flattens
`$input.all()` back into one array** where Make would have used an aggregator.

- `BasicRepeater` (page count via a custom paging function) → Code node emitting `{page: i}`
  items (deer-valley: `Vehicles - Build Pages`, ports `DeerValleyAPICallAmount` verbatim;
  drink-pak: documented in `01-module-translation.md` as "compute pages then loop", Vendor
  Sync's `DrinkPakAPIPaging` — design-stage only, not yet built).
- `BasicAggregator` → Code node using `$input.all()` to flatten pages back into one list
  (deer-valley: `Vehicles/Transactions - CompileList`, ports `DeerValleyCompileList`
  verbatim).
- `BasicFeeder` (splits an array into per-record iteration) → Code node `.map()`-ing an
  array into `{json: x}` items (deer-valley: `Split Updates` / `Split Records`; drink-pak
  Step 2: native **Loop Over Items** over `po_tracking` rows — Step 2 kept a literal
  per-item loop where deer-valley used a flatten/split Code node, so the concrete node choice
  varies, but the underlying move — collapse Make's repeat/aggregate machinery into plain
  item-array operations — is the same in both).
- Step 1 (drink-pak) explicitly chose Code nodes over Split Out/Aggregate for its per-line
  loop specifically "to avoid n8n's array-wrapping ambiguity" — not a literal node-shape
  match to the Make modules, same reasoning as deer-valley's approach.

**Gotcha (seen in both):** an HTTP response that's a single JSON array gets auto-split by
n8n into N items, which can silently multiply a downstream call that Make would have fired
once per bundle.
- deer-valley: `Collapse A/B/C` Code nodes re-collapse Limble's array response to 1 item
  before the next HTTP call.
- drink-pak: Make's 1-indexed multi-return values (`result[1]/[2]/[3]`) had to be
  rewritten to n8n's 0-indexed `[0]/[1]` at every consumption site (finding "CC1" in
  `02-iml-functions.md`) — a different symptom of the same root cause: Make's bundle
  semantics don't map 1:1 onto n8n's item/array semantics, so every read site needs a
  manual audit, not a mechanical find-replace.

---

## 2. Custom/private Make app → HTTP Request

**Pattern:** a private Make app (`fuse-<client>-app:universalModule` or similar) has no n8n
equivalent — every operation becomes a plain **HTTP Request node** hitting the vendor API
directly, one node per Make operation, with the app's stored connection replaced by an
explicit n8n credential.

- deer-valley: `fuse-limble-app:universalModule` → `n8n-nodes-base.httpRequest` nodes
  (`Update Odometer (Limble)`, etc.), auth via **HTTP Header Auth credential**
  (`Deer Valley Limble`, `Authorization: Bearer <key>`), replacing the Make connection
  object 1:1 per operation.
- drink-pak: `fuse-limble-app:universalModule` operations (`listPO`, `listPOItems`,
  `createVendor`, etc.) → HTTP Request nodes against `api.limblecmms.com` directly, auth via
  Basic auth + a static `Authkey` header, one reusable Limble credential
  (`Gerald Limble Sandbox` in testing, swapped for a live key at go-live).
- **No shared base-URL abstraction in either engagement** — each node hardcodes its full
  URL rather than centralizing a base-URL variable. Consistent across both; not something
  either team introduced as an improvement.
- **Rotating/session-style auth doesn't fit n8n's static credential model** — both
  engagements worked around it, differently: deer-valley pulls FuelCloud's OAuth token via a
  raw header expression sourced from a Data Table row (`{{ $('Get Token').first().json.oauth_token }}`,
  no credential object at all); drink-pak's SAP B1 login uses a session-cookie step
  (`SAP Login` → `Set-Cookie: B1SESSION`) combined with a static header, also not modeled as
  an n8n credential. Take from this: if the source system's auth is a rotating token or
  session cookie rather than a static key, plan for an explicit "fetch/refresh token" node
  feeding a raw header expression — don't force it into n8n's credential UI.

---

## 3. Router/Switch semantics

**Pattern:** Make's `BasicRouter` filter conditions don't need a literal Switch node port —
in both engagements the routing decision was pulled **upstream into the Code node that
produces the branch data**, and the "route" itself became a plain **array-emptiness check**
(map over `[]` → zero items → nothing fires downstream) rather than an explicit filter
condition on a Switch node.

- deer-valley: `BasicRouter` (module 55, 3 filtered routes) → multiple parallel connections
  straight out of `Compare Odometer`, which returns `{updateArray, recordArray}`; empty
  arrays naturally produce zero items with no explicit "no route matched" branch needed.
- drink-pak Step 2: router `#191`'s two routes (a filtered delete route, an unconditional
  update/closeout route) ported as two parallel branches off an IF/Switch rather than a
  literal router replica.

**Gotcha, confirmed in both — audit "always-run" and "no-filter" routes before porting
them as-is, they often hide unintended behavior:**
- deer-valley: the source's third route (search→aggregate→email→clear-datastore) ran
  *unconditionally* every cycle, emailing an empty report when there was nothing to report.
  The n8n port deliberately changed this to gate on `recordArray.length === 0` — a
  documented, sanctioned deviation, not an oversight.
- drink-pak Step 1: two source routers (`#102`, `#138`) had no filter on their "continue"
  branch at all, so both the error path and the continue path fired unconditionally — flagged
  as inconsistent with stated client intent and required explicit owner sign-off before
  changing to "abort-before-create" semantics (`open-questions.md` C6), rather than being
  silently ported as-is.

Net: when a Make router branch has no filter condition, treat it as a flag for review, not
as "nothing to translate" — in both engagements it turned out to encode a real bug or an
unintended always-run behavior.

---

## 4. Error handling (`onerror[]`)

**Pattern:** both engagements replaced the Make error datastore with an **n8n Data Table**
as the log sink, but split error handling into two tiers: per-node inline handling for
expected/recoverable failures (mirroring Make's per-module `onerror`), plus one
workflow-level catch-all for everything else.

- deer-valley: no n8n Error Trigger workflow used — purely Code-node-driven, per-branch
  logging (`Build Update Error Records` → `Log Update Error`/`Log Out of Range` Data Table
  writes) plus `retryOnFail`/3 tries on every HTTP node (no Fuse-side equivalent).
- drink-pak: uses n8n's native **Error Trigger** workflow pattern (`Error Trigger → Send Alert`)
  as the catch-all tier, *plus* per-node error branches via `continueErrorOutput` feeding
  named logging nodes (e.g. `Insert error_log (Life #140)`) for expected failures — i.e. the
  two-tier split is the same shape, but drink-pak additionally adopted n8n's built-in
  Error Trigger mechanism where deer-valley didn't.
- Both replaced the Make error datastore with a **Data Table**, not static data or an
  external DB (deer-valley: `Deer Valley - Meter Sync Error Log`; drink-pak: `error_log` /
  `error_log_taxes`).
- Both dropped or never re-implemented the source's "clear all error records" step —
  deer-valley explicitly retains history instead of clearing every cycle; drink-pak's
  equivalent digest/clear workflow (Error Report) was never built.
- **Gotcha, drink-pak only (single instance, flag for future engagements):** n8n's
  Error Trigger workflow runs in an isolated execution context — a node inside it cannot
  read `$('CFG')` or any node from the failed run. Confirmed via a real test execution.
  Workaround: hardcode alert-recipient values on the error-workflow node rather than
  binding to shared config/env. Worth checking for on every future engagement that uses
  Error Trigger, since it will trip whoever wires it next.

---

## 5. Custom IML/JS function → Code node

**Pattern:** port each custom Make function as a **named, near-verbatim inner function**
inside its own Code node, with a thin driver on top that translates Make's implicit bundle
context into n8n's explicit `$json`/`$input`/`$('Node').item` access. Both engagements
treated this as an audit-then-port process, not a blind copy:

- deer-valley: every function from `functions.js` kept as a named block inside its Code
  node (e.g. `DeerValleyAPICallAmount` verbatim inside `Vehicles - Build Pages`).
- drink-pak: functions collected in `functions.js`, then evaluated one-by-one in a written
  audit doc (`02-iml-functions.md`) *before* any porting — same "verbatim unless flagged"
  discipline, made explicit as a repo convention rather than done ad hoc.

**Recurring gotcha class — bundle-vs-item path rewrites are required at every read site,
not optional cleanup:**
- deer-valley: none flagged as unresolved, but the `Collapse` nodes (pattern 1) exist for
  the same underlying reason.
- drink-pak: explicit finding class "CC6" — Make paths like `.data.Error`/`.resultArr`
  rewritten to n8n's `x.json.Error` shape at every consumption site; a 1-indexed→0-indexed
  fix (CC1) fell in the same bucket; an implicit-global var (`desc = ...` with no `let`)
  that Make's IML sandbox tolerated but n8n's stricter Code node execution does not, was a
  mandatory fix applied without needing sign-off (unlike other deviations).

**Convention confirmed in both: don't "fix" the function's logic while porting it, even
when you spot a bug** — treat behavior changes as a separate, sanctioned decision requiring
owner sign-off, distinct from the mechanical port.
- deer-valley: `DeerValleyCompareOdometer`'s comparison logic was changed (string vs.
  numeric compare), but called out explicitly in both the Code node comment and the
  migration notes as a deliberate spec change, not a silent fix.
- drink-pak: a loose `==` comparison load-bearing for cross-system id matching was
  deliberately preserved rather than hardened to `===`; several known bugs (stale variable
  carryover, divide-by-zero, inconsistent delimiter parsing) were ported as-is under an
  explicit "1:1 port + sanctioned deviations only" rule.
- Both engagements also hit **unused/dead custom functions** referenced only in the
  function library, not the blueprint (deer-valley: `DeerValleyPushFuelCloud`) — confirm
  via a blueprint search rather than porting speculatively, and flag them in the write-up
  instead of guessing at intent.

---

## 6. Make datastore → n8n persistence

**Pattern:** in both engagements, **every** Make datastore — queue, log, or lookup alike —
was replaced with an **n8n Data Table**. Neither engagement used n8n static/workflow data
or an external DB for any datastore.

- deer-valley: lookup datastore (client API keys) → Data Table with native
  `filters.conditions` replicating the search filter; log datastore (errors) → Data Table.
- drink-pak: queue datastore (`po_tracking`, written by Step 1 / read by Step 2 — genuine
  cross-workflow work queue) → Data Table; two log datastores (`error_log`,
  `error_log_taxes`) → Data Tables.
- Both engagements used the port as an opportunity to **shrink the schema to only the
  columns actually read**, rather than mirroring every Make datastore field
  (deer-valley: trimmed an OAuth-token record from 8 fields to the 3 actually used).
- **Gotcha, confirmed independently in both:** Make's per-record round-trip (search by
  internal record key → update → possibly delete by that key) doesn't map cleanly onto
  n8n Data Tables, which have no equivalent internal record-key concept exposed for
  matching.
  - deer-valley: replaced a datastore record-key update round-trip with an
    upsert-by-column-filter (`client = "Deer Valley (Prod)"` matches a single known row).
  - drink-pak: same gap noted explicitly as an open question (`B7`) — Make deletes by
    internal `key`, n8n Data Tables have no such key, so delete-by-column-value was
    substituted instead.

---

## Seen once, unconfirmed (single-instance — not yet an established convention)

- **Rotation-guard fallback on token write-back** (deer-valley only): `Update Tokens` falls
  back to the previously stored `refresh_token` if the refresh response omits one, instead
  of overwriting blindly. Worth doing again, but only one data point.
- **In-memory report building to avoid a read-after-write race** (deer-valley only):
  `Compose OOR Email` builds its report directly from upstream node output instead of
  reading back from the Data Table it just wrote, removing a timing dependency the source
  had via its datastore round-trip.
- **Per-item try/catch inside a loop, as an alternative to Error Trigger** (drink-pak only,
  proposed not built): designed for a case where the item needs `$('CFG')` access that
  Error Trigger's isolated context can't provide (see pattern 4 gotcha). Documented in
  `step2-c26-poison-pill-design.md` but never implemented — a candidate pattern to validate
  on a future engagement, not yet a confirmed convention.
- **Offline fixture test of a ported function before wiring it live** (drink-pak only):
  ran the Code node's transform against a static fixture file and checked exact expected
  outputs before connecting it into the graph. No equivalent step documented in deer-valley.
- **Test-only mock Data Table standing in for a live external read** (drink-pak only):
  `sap_mock` table explicitly flagged as harness-only, to be dropped before go-live.

