# agentsInferno

**AFS G Hackathon MVP:** Agentic evaluation backend (AgentField). User inputs their product → model analyses where to include agentic AI → model searches for best/new agents → tests each agent with mock data → delivers a custom notification report (performance insights + adopt or not per agent). All logic as decorated functions with Pydantic in/out and auto REST.

**Flow:** 1) Product input → 2) Analyse product for agentic opportunities → 3) Search for relevant AI agents → 4) Test each agent against mock data → 5) Notification report (insights + why adopt or not).

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

**Result:** A `NotificationReport`: `product_name`, `opportunities_summary`, `agents_tested` (per-agent eval + adopt/reasoning), `overall_insights`, `notification_message`.

**Other endpoints:** `analyse_agentic_opportunities`, `search_agents_for_product`, `build_notification_report`, `derive_use_cases`, `generate_mock_data`, `evaluate_framework`, `recommend_adoption` — same base URL and `{"input": {...}}` body.