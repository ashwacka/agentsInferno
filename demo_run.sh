#!/usr/bin/env bash
# Hackathon demo: one use case, clear output. Run with af server + python3 main.py already running.

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# Demo endpoint: no LLM needed, uses registry + simulated scores (fast for hackathon)
API="http://localhost:8080/api/v1/execute/eval-agent.evaluate_pipeline_demo"

echo "=============================================="
echo "  AGENTS INFERNO — Hackathon Demo"
echo "=============================================="
echo ""
echo "Use case: ESG Gap Compliance — AI gap analysis platform for ESG reporting (file-search agents)."
echo ""

# Use case payload
PAYLOAD='{"input":{"product":{"name":"ESG Gap Compliance","domain":"ESG / Sustainability reporting","one_liner":"AI gap analysis compliance platform for ESG reporting, relying on file search AI agents and tools"}}}'

echo "Calling pipeline (search registry → simulate run → verdict)..."
echo ""

RESP=$(curl -s --max-time 30 -X POST "$API" -H "Content-Type: application/json" -d "$PAYLOAD") || true

if echo "$RESP" | python3 -c "import sys,json; json.load(sys.stdin)" 2>/dev/null; then
  echo "$RESP" | python3 -m json.tool
  echo ""
  echo "=============================================="
  echo "  Demo summary"
  echo "=============================================="
  echo "$RESP" | python3 -c "
import sys, json
d = json.load(sys.stdin)
r = d.get('result') or {}
print('Product:', r.get('product_name', '—'))
print('Opportunities:', r.get('opportunities_summary', '—')[:80] + '...')
print('Agents tested:', [a.get('agent_name') for a in r.get('agents_tested', [])])
for a in r.get('agents_tested', [])[:4]:
    e = a.get('eval_result', {})
    print('  -', a.get('agent_name'), '| overall:', e.get('overall_score'), '| adopt:', a.get('adopt_recommended'))
print('Notification:', (r.get('notification_message') or '—')[:120] + '...')
" 2>/dev/null || echo "$RESP" | head -20
else
  echo "Response (raw):"
  echo "$RESP"
fi
echo ""
