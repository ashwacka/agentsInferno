# ESG product: input, outputs at each step, and summary

## Your product (input)

```json
{
  "input": {
    "product": {
      "name": "ESG Gap Compliance",
      "domain": "ESG / Sustainability reporting",
      "one_liner": "AI gap analysis compliance platform for ESG reporting, relying on file search AI agents and tools"
    }
  }
}
```

---

## What the system does (step-by-step)

**Step 1 — INPUT (your product)**  
- **name:** ESG Gap Compliance  
- **domain:** ESG / Sustainability reporting  
- **one_liner:** AI gap analysis compliance platform for ESG reporting, relying on file search AI agents and tools  

**Step 2 — Agentic opportunities**  
- LLM analyses where agentic AI fits your product.  
- **Output:** `opportunities` (e.g. “document gap analysis”, “file search over ESG docs”, “compliance checklist automation”) + `summary`.  
- *With OPENAI_API_KEY set you get real suggestions; otherwise a default summary is used.*

**Step 3 — Agents considered**  
- LLM suggests which agents/frameworks are relevant (e.g. LlamaIndex for file search, LangChain, RAG tools).  
- **Output:** `agents` (name, reason_relevant, category) + `search_context`.  
- *This does not include “released when” today; you could extend the prompt/schema to ask for recency.*

**Step 4 — Per-agent: test data + metrics + adopt?**  
- For each agent: generate mock data → run deterministic evaluation → LLM recommends adopt or not.  
- **Output per agent:**  
  - **mock_data:** test payload (e.g. sample ESG doc, scenario).  
  - **metrics:** `score_completeness`, `score_determinism`, `score_fit`, `overall_score`, `notes`.  
  - **adopt_recommended** (bool) + **reasoning** (short).  
- *Noticeable feedback: completeness (does it cover the use case), determinism (reproducibility), fit (how well it matches your file-search / compliance use case).*

**Step 5 — Notification report**  
- **Output:** `overall_insights` (comparison across agents) + `notification_message` (short takeaway).

---

## Final API output (shape)

```json
{
  "execution_id": "...",
  "status": "succeeded",
  "result": {
    "product_name": "ESG Gap Compliance",
    "opportunities_summary": "...",
    "agents_tested": [
      {
        "agent_name": "...",
        "eval_result": {
          "framework_name": "...",
          "score_completeness": 0.0,
          "score_determinism": 0.0,
          "score_fit": 0.0,
          "overall_score": 0.0,
          "notes": "..."
        },
        "adopt_recommended": true,
        "reasoning": "..."
      }
    ],
    "overall_insights": "...",
    "notification_message": "..."
  },
  "duration_ms": 3000
}
```

---

## Your question answered (3–4 lines)

**Which latest agent, released when, is more optimal for which part of my product, performance on test data, noticeable metrics, and should I use it?**

The pipeline identifies which agents (e.g. LlamaIndex for file search, LangChain for orchestration) fit which part of your ESG platform, runs each against mock compliance/file-search data, and reports **completeness** (coverage), **determinism** (reproducibility), and **fit** (match to your use case) plus an overall score and short notes. It does **not** currently return “released when” — you’d extend the “search agents” step to ask the model for recency or plug in a separate source. You should use the agent that scores highest on **fit** for your file-search-heavy gap analysis and that gets **adopt_recommended: true** with reasoning that matches your needs (e.g. “strong for document RAG and structured outputs”). Run with a valid `OPENAI_API_KEY` in `agentsInferno/.env` so opportunities, agent list, and adoption reasoning are real; otherwise you only get fallback/default text and mock scores.
