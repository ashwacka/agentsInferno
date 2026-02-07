#!/usr/bin/env bash
# Run the full pipeline once. Requires: control plane (af server) and agent (python main.py) already running.

set -e
echo "Calling evaluate_pipeline (product → analyse → search agents → test with mock data → notification report)..."
curl -s -X POST http://localhost:8080/api/v1/execute/eval-agent.evaluate_pipeline \
  -H "Content-Type: application/json" \
  -d '{"input":{"product":{"name":"SupportBot","domain":"B2B SaaS","one_liner":"AI support triage for enterprise tickets"}}}' \
  | python3 -m json.tool
echo ""
