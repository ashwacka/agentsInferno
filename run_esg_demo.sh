#!/usr/bin/env bash
# ESG product: AI gap analysis compliance platform for ESG reporting (file-search agents/tools).
# Run with: af server (T1), python3 main.py (T2), then ./run_esg_demo.sh
# Prints at each step appear in the agent terminal (T2).

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
echo "Calling evaluate_pipeline for ESG product..."
echo "INPUT (from esg_input.json):"
cat "$SCRIPT_DIR/esg_input.json"
echo ""
curl -s -X POST http://localhost:8080/api/v1/execute/eval-agent.evaluate_pipeline \
  -H "Content-Type: application/json" \
  -d @"$SCRIPT_DIR/esg_input.json" \
  | python3 -m json.tool
echo ""
