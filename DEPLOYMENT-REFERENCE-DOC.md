# DEPLOYMENT — Deer Valley Meter Sync, Fuse → n8n cutover

Personal checklist. Workflow `Deer Valley - Meter Sync` = `kdMutRMC0eZ48mjY` (INACTIVE, on
sandbox Limble cred). Schedule already set: `0 2,8,14,20` America/Denver.

**Token:** n8n shares Fuse's FuelCloud token (rotating, single holder). Current valid one is
in the n8n table. Don't parallel-run; don't run n8n again pre-cutover or Fuse loses the token.

## Cutover
1. **Turn off** the live Fuse "Deer Valley - Meter Syncing" scenario.
2. **Swap Limble cred** sandbox → prod on these 4 nodes: `Get Limble Assets`, `Get Meter
   Field`, `Get Fuel Cloud ID Field`, `Update Odometer (Limble)`.
3. **Set email recipients** (currently all gerald@ test):
   - `Send Out of Range Email` → tkendrick@, bbennett@, fleetmaintenance@ (all
     @deervalley.com). No mmay@, no ethan@.
   - `Send Update Failure Alert` → _____ (FM360 internal)
   - Auth Refresh token-failure email (sub-wf `abiqzIOngPgAJBz0`) → _____ (FM360 internal)
4. **Manual run** ("Test workflow"), eyeball `Compare Odometer` (updateArray small,
   recordArray ~empty) + that PATCHes succeed.
5. **Activate** the schedule on `kdMutRMC0eZ48mjY`. Leave Auth Refresh inactive.

## Rollback
Deactivate n8n, copy the current token from the n8n table back into Fuse's first HTTP node,
re-enable Fuse. (Keep Fuse disabled-not-deleted until n8n runs clean for a few cycles.)
