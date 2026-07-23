#!/usr/bin/env bash
# Generic Limble-webhook trigger helper for the 3 webhook-triggered n8n workflows.
# DESIGN ARTIFACT — generalises tools/sandbox-seed/fire.sh (which hardcoded Step 1's
# comment event + URL). See docs/test-plan/limble-sandbox-fixtures.md §7.
#
# The Limble webhook gateways consume ONLY {status, taskID}. Event -> status mapping:
#   comment   -> "ADDED COMMENT TO TASK"   (Step 1: Create Requisition; new task comment)
#   complete  -> "COMPLETE"                (Step 3: WO Completed  AND  EHS-Update Inspection)
# Step 2, EHS-Create, Token Regen and Error Log Export are SCHEDULE-triggered — not fired
# here; execute/activate those in n8n instead (they self-discover their work).
#
# Usage:
#   ./fire.sh <event> <taskID> <webhook-url>
#   ./fire.sh comment  4052 https://.../webhook-test/<step1-path>
#   ./fire.sh complete 4052 https://.../webhook-test/<step3-path>       # Step 3
#   ./fire.sh complete 9001 https://.../webhook-test/<ehs-update-path>  # EHS-Update
#   ./fire.sh raw:"SOME STATUS" 4052 <url>    # escape hatch: send an arbitrary status string
#
# WEBHOOK URL: pass it explicitly. Step 1's PRODUCTION path is the only one documented
# (below, as a convenience default for `comment`). No sandbox webhook is registered
# (OQ-020/OQ-028), so for INACTIVE workflows use the n8n editor's "Listen for test event"
# button and pass the resulting webhook-TEST URL. Step 3 and EHS-Update have no documented
# sandbox URLs yet — you MUST supply one.
set -euo pipefail

STEP1_PROD_URL="https://fm360.n8n.fm360consulting.com/webhook/coastal-coupa-create-requisition-step1"

EVENT="${1:?usage: fire.sh <event: comment|complete|raw:\"STATUS\"> <taskID> <webhook-url>}"
TASK_ID="${2:?missing <taskID>}"
URL="${3:-}"

case "$EVENT" in
  comment)  STATUS="ADDED COMMENT TO TASK"; URL="${URL:-$STEP1_PROD_URL}" ;;
  complete) STATUS="COMPLETE" ;;
  raw:*)    STATUS="${EVENT#raw:}" ;;
  *) echo "unknown event '$EVENT' (use: comment | complete | raw:\"STATUS\")" >&2; exit 2 ;;
esac

if [[ -z "$URL" ]]; then
  echo "no webhook URL: '$EVENT' has no default — pass the n8n webhook (or webhook-test) URL as arg 3" >&2
  exit 2
fi

echo "POST $URL  <-  {status:\"$STATUS\", taskID:$TASK_ID}"
curl -sS -X POST "$URL" \
  -H "Content-Type: application/json" \
  -d "{\"status\":\"${STATUS}\",\"taskID\":${TASK_ID}}"
echo
