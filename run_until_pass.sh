#!/usr/bin/env bash
# Call evaluate_pipeline until status is "succeeded". Requires: af server + python main.py running.

set -e
MAX_ATTEMPTS="${MAX_ATTEMPTS:-10}"
URL="http://localhost:8080/api/v1/execute/eval-agent.evaluate_pipeline"
BODY='{"input":{"product":{"name":"SupportBot","domain":"B2B SaaS","one_liner":"AI support triage for enterprise tickets"}}}'

for i in $(seq 1 "$MAX_ATTEMPTS"); do
  echo "Attempt $i/$MAX_ATTEMPTS..."
  RESP=$(curl -s -X POST "$URL" -H "Content-Type: application/json" -d "$BODY")
  STATUS=$(echo "$RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('status',''))" 2>/dev/null || echo "")
  if [ "$STATUS" = "succeeded" ]; then
    echo "SUCCESS"
    echo "$RESP" | python3 -m json.tool
    exit 0
  fi
  echo "Status: $STATUS"
  echo "$RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print('Error:', d.get('error_message','')[:200])" 2>/dev/null || echo "$RESP" | head -c 300
  echo ""
  [ "$i" -lt "$MAX_ATTEMPTS" ] && sleep 2
done
echo "Failed after $MAX_ATTEMPTS attempts"
exit 1
