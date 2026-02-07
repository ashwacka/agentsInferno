# Inputs and Expected Outputs

All endpoints: `POST http://localhost:8080/api/v1/execute/eval-agent.<function_name>`  
Request body: `{"input": { ... }}`  
Response: `{ "execution_id": "...", "status": "succeeded"|"failed", "result": { ... }, "duration_ms": N }`

---

## 1. `derive_use_cases` (reasoner, uses LLM)

**Input**
```json
{
  "input": {
    "product": {
      "name": "string",
      "domain": "string",
      "one_liner": "string"
    }
  }
}
```

**Expected output** (`result`)
```json
{
  "use_cases": [
    {
      "id": "string",
      "name": "string",
      "description": "string"
    }
  ]
}
```
Exactly 3 use cases (per prompt). All fields strings.

---

## 2. `generate_mock_data` (skill, deterministic)

**Input**
```json
{
  "input": {
    "use_case_id": "string",
    "use_case_name": "string"
  }
}
```

**Expected output** (`result`)
```json
{
  "use_case_id": "string",
  "payload": {
    "use_case": "string",
    "use_case_id": "string",
    "mock_input": "deterministic_sample",
    "scenario": "default",
    "sample_ticket": { "subject": "...", "body": "..." }
  }
}
```
Same input → same output every time.

---

## 3. `evaluate_framework` (skill, deterministic)

**Input**
```json
{
  "input": {
    "framework_name": "string",
    "mock_payload": {},
    "use_case_name": "string"
  }
}
```

**Expected output** (`result`)
```json
{
  "framework_name": "string",
  "score_completeness": 0.0,
  "score_determinism": 0.0,
  "score_fit": 0.0,
  "overall_score": 0.0,
  "notes": "string"
}
```
All scores between 0 and 1. Same input → same scores.

---

## 4. `recommend_adoption` (reasoner, uses LLM)

**Input**
```json
{
  "input": {
    "framework_name": "string",
    "eval_result": {
      "framework_name": "string",
      "score_completeness": 0.0,
      "score_determinism": 0.0,
      "score_fit": 0.0,
      "overall_score": 0.0,
      "notes": "string"
    }
  }
}
```

**Expected output** (`result`)
```json
{
  "adopt_worthwhile": true,
  "confidence": 0.0,
  "reasoning": "string"
}
```
`confidence` between 0 and 1.

---

## 5. `analyse_agentic_opportunities` (reasoner)

**Input:** `product`: `{ name, domain, one_liner }`

**Expected output** (`result`)
```json
{
  "opportunities": [
    { "id": "string", "title": "string", "description": "string", "suggested_agent_type": "string" }
  ],
  "summary": "string"
}
```

---

## 6. `search_agents_for_product` (reasoner)

**Input**
```json
{
  "input": {
    "product": { "name": "string", "domain": "string", "one_liner": "string" },
    "opportunities": { "opportunities": [...], "summary": "string" }
  }
}
```
`opportunities` is optional (output from step 5).

**Expected output** (`result`)
```json
{
  "agents": [
    { "name": "string", "reason_relevant": "string", "category": "string" }
  ],
  "search_context": "string"
}
```

---

## 7. `build_notification_report` (reasoner)

**Input:** `product_name`, `opportunities_summary`, `agents_tested` (list of `{ agent_name, eval_result, adopt_recommended, reasoning }`)

**Expected output** (`result`): `ReportInsights` — `{ "overall_insights": "string", "notification_message": "string" }`

---

## 8. `evaluate_pipeline` (reasoner, full flow)

**Input**
```json
{
  "input": {
    "product": {
      "name": "string",
      "domain": "string",
      "one_liner": "string"
    }
  }
}
```

**Expected output** (`result`) — `NotificationReport`
```json
{
  "product_name": "string",
  "opportunities_summary": "string",
  "agents_tested": [
    {
      "agent_name": "string",
      "eval_result": {
        "framework_name": "string",
        "score_completeness": 0.0,
        "score_determinism": 0.0,
        "score_fit": 0.0,
        "overall_score": 0.0,
        "notes": "string"
      },
      "adopt_recommended": true,
      "reasoning": "string"
    }
  ],
  "overall_insights": "string",
  "notification_message": "string"
}
```
Flow: 1) User product → 2) analyse_agentic_opportunities → 3) search_agents_for_product → 4) for each agent: generate_mock_data, evaluate_framework, recommend_adoption → 5) build_notification_report. Delivers a small report symbolising a notification to the user.
