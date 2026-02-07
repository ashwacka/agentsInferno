# agentsInferno

**AFS G Hackathon MVP:** Agentic evaluation backend (AgentField). User inputs their product → model analyses where to include agentic AI → **search runs over a simulated repository of new agents** (`agent_registry.json`) → **simulated run** per agent from registry metrics → **AI verdict** (adopt or not + reasoning). No real agent APIs; demo-ready.

**Flow:** 1) Product input → 2) Analyse product for agentic opportunities → 3) **Search registry** (features, metrics, best_for) → 4) **Simulate run** from metrics → 5) **AI verdict** + notification report.

**Full 1-hour build plan:** [BUILD_PLAN.md](./BUILD_PLAN.md) · **Inputs/outputs:** [INPUTS_AND_OUTPUTS.md](./INPUTS_AND_OUTPUTS.md)

## Run

1. **Install:**  
   `pip install -r requirements.txt`  
   Install [AgentField CLI](https://agentfield.ai/docs/installation): `curl -fsSL https://agentfield.ai/get | sh` (then reload shell).
2. **Env:** Copy `.env.example` to `.env` and set `OPENAI_API_KEY`.
3. **Terminal 1:** `af server` (control plane at http://localhost:8080).
4. **Terminal 2:** `python main.py` (agent at http://localhost:8001).
5. **Terminal 3 (or 2 after Ctrl+C):** `./run_demo.sh` — or use the curl under Demo below.

## Demo

```bash
./run_demo.sh
# or
curl -X POST http://localhost:8080/api/v1/execute/eval-agent.evaluate_pipeline \
  -H "Content-Type: application/json" \
  -d '{"input":{"product":{"name":"SupportBot","domain":"B2B SaaS","one_liner":"AI support triage for enterprise tickets"}}}'
```

**Result:** A `NotificationReport`: `product_name`, `opportunities_summary`, `agents_tested` (per-agent **simulated** scores + adopt/reasoning), `overall_insights`, `notification_message`.

**Simulated agent registry:** `agent_registry.json` holds a list of agents with `name`, `features`, `metrics` (latency_p95_ms, accuracy_retrieval, cost_per_1k_queries_usd, file_formats, etc.), and `best_for`. The pipeline **searches** this document and **simulates** a run from metrics to produce scores; the LLM gives the final **AI verdict** (adopt or not).

**Other endpoints:** `analyse_agentic_opportunities`, `search_agents_from_registry`, `search_agents_for_product`, `build_notification_report`, `derive_use_cases`, `generate_mock_data`, `evaluate_framework`, `recommend_adoption` — same base URL and `{"input": {...}}` body.

## API key (one for all LLM steps)

You do **not** need a separate API key per LLM or per step. A single **`OPENAI_API_KEY`** in `agentsInferno/.env` is used for every reasoner (analyse opportunities, search agents, recommend adoption, build notification). All of them use the same model (`openai/gpt-4o` by default). Set it once:

```bash
# In agentsInferno/.env
OPENAI_API_KEY=sk-your-openai-key
```

Without it, LLM steps fail with `AuthenticationError` and the pipeline falls back to default/empty text and zeros for metrics.