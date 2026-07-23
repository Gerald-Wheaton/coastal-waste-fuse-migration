#!/usr/bin/env bash
# Fire the Step 1 webhook the way Limble would (OQ-028 test rig).
# Blueprint gateway consumes only {status, taskID}.
#
# Usage: ./fire.sh <taskID> [webhook-url]
#
# Default URL is Step 1's PRODUCTION webhook path - requires the workflow to be
# ACTIVE in n8n. For a one-off run with the workflow inactive, use the editor's
# "Listen for test event" and pass the webhook-test URL as the 2nd arg.
set -euo pipefail

TASK_ID="${1:?usage: fire.sh <taskID> [webhook-url]}"
URL="${2:-https://fm360.n8n.fm360consulting.com/webhook/coastal-coupa-create-requisition-step1}"

curl -sS -X POST "$URL" \
  -H "Content-Type: application/json" \
  -d "{\"status\":\"ADDED COMMENT TO TASK\",\"taskID\":${TASK_ID}}"
echo
