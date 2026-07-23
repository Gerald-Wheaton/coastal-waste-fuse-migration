| Workflow | Schedule / Trigger | n8n Build Status |
| --- | --- | --- |
| Coastal - Coupa Token Regeneration (PROD) | Daily @ 12:00AM (MST) | Ready to Test |
| Coastal - Create Requisition in Coupa (Step 1) (PROD) | Limble Webhook (Task Endpoint) - Event: New Task Comment | Ready to Test |
| Coastal - Check For New PRs Ordered & Update Limble WO (Step 2) (PROD) | Every 5 minutes | Ready to Test |
| Coastal - WO Completed; Update Coupa PO (Step 3) (PROD) | Limble Webhook (Task Endpoint) - Event: Task Completed | Ready to Test |
| Coastal - Create WO From EHS Inspection (PROD) | Daily @ 4:00PM (MST) | Ready to Test |
| Coastal - Update EHS Inspection From Limble WO (PROD) | Limble Webhook (Task Endpoint) - Event: Task Completed | Ready to Test |
| Coastal - Coupa Integration Error Log Export | Every 15 minutes | Ready to Test |

Status values: **In Progress** (design/build not yet started or underway) · **Ready to Test**
(built in n8n, awaiting real credentials/values or a live test run) · **Completed** (tested
and confirmed working).
