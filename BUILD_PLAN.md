# AFS G Hackathon MVP — Agentic Evaluation Backend (AgentField)

**Strict compliance:** Decorated functions only • Pydantic input/output • Auto REST • Deterministic • AI backend, not chatbot.

---

## 1. System Architecture (Text Diagram)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CLIENT (curl / judge)                                │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                    POST /api/v1/execute/eval-agent.<function>
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    AgentField Control Plane (af server)                       │
│                         localhost:8080                                        │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    EVAL-AGENT (Python, main.py)                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ derive_     │  │ generate_   │  │ evaluate_   │  │ recommend_   │         │
│  │ use_cases   │→ │ mock_data   │→ │ framework   │→ │ adoption     │         │
│  │ @reasoner   │  │ @skill      │  │ @skill      │  │ @reasoner    │         │
│  │ Out:        │  │ Out:        │  │ Out:        │  │ Out:        │         │
│  │ UseCasesOut │  │ MockDataOut │  │ EvalResult  │  │ RecommendOut │         │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘         │
│         │                  │                │                │               │
│         └──────────────────┴────────────────┴────────────────┘               │
│                                      │                                         │
│                    evaluate_pipeline (orchestrator)                             │
│                    @reasoner → calls above in sequence                          │
│                    Out: EvaluationReport                                       │
└─────────────────────────────────────────────────────────────────────────────┘

Flow: ProductDescription → UseCases → MockData → EvalResult → Recommendation
      (Pydantic in/out at every step; REST = POST with {"input": {...}})
```

---

## 2. Agent / Function Breakdown

| # | Function name | Decorator | Input schema | Output schema | Determinism | Endpoint path |
|---|---------------|-----------|--------------|---------------|-------------|----------------|
| 1 | `derive_use_cases` | `@app.reasoner` | `ProductDescription` | `UseCasesOut` | `temperature=0`, `schema=UseCasesOut` | `eval-agent.derive_use_cases` |
| 2 | `generate_mock_data` | `@app.skill()` | `GenerateMockDataIn` | `MockDataOut` | Pure function, template-based | `eval-agent.generate_mock_data` |
| 3 | `evaluate_framework` | `@app.skill()` | `EvaluateFrameworkIn` | `EvalResult` | Fixed rubric, no LLM | `eval-agent.evaluate_framework` |
| 4 | `recommend_adoption` | `@app.reasoner` | `RecommendAdoptionIn` | `RecommendationOut` | `temperature=0`, `schema=RecommendationOut` | `eval-agent.recommend_adoption` |
| 5 | `evaluate_pipeline` | `@app.reasoner` | `ProductDescription` (+ optional `framework_name`) | `EvaluationReport` | Chained calls; LLM steps use temp=0 | `eval-agent.evaluate_pipeline` |

- **Input schemas:** Pydantic models; FastAPI/AgentField map JSON `input` to function kwargs.
- **Output schemas:** Return type of each function = Pydantic model; response body `result` matches that shape.
- **Determinism:** Skills = no randomness. Reasoners use `AIConfig(temperature=0)` and `app.ai(..., schema=OutModel)`.

---

## 3. Minimal AgentField Constructs Used

- **Decorators:**  
  - `@app.reasoner` — AI-backed, auto REST, workflow tracking; use `app.ai(system=..., user=..., schema=OutModel)`.  
  - `@app.skill()` — deterministic, auto REST; no `app.ai()`.
- **Schemas:** Pydantic `BaseModel` for every input and return type; no separate “registration” — type hints define contract.
- **Chaining:** Orchestrator reasoner `evaluate_pipeline` calls other functions via **direct Python calls** (same agent): `derive_use_cases(desc)` then `generate_mock_data(...)` then `evaluate_framework(...)` then `recommend_adoption(...)`. Optionally use `app.call("eval-agent.derive_use_cases", ...)` if you want DAG visibility for each step.
- **REST:** All functions become `POST /api/v1/execute/{node_id}.{function_name}` with body `{"input": { ... }}`. No extra FastAPI routes.

---

## 4. 10-Minute Timeboxed Build Plan

| Window | Task |
|--------|------|
| **0–10** | Project init: `af init eval-agent --defaults`. Add Pydantic schemas in `schemas.py`: `ProductDescription`, `UseCasesOut`, `GenerateMockDataIn`, `MockDataOut`, `EvaluateFrameworkIn`, `EvalResult`, `RecommendAdoptionIn`, `RecommendationOut`, `EvaluationReport`. |
| **10–20** | `main.py`: Agent with `AIConfig(model="openai/gpt-4o", temperature=0)`. Import and mount schemas; add `derive_use_cases` (reasoner, input ProductDescription, output UseCasesOut) and `generate_mock_data` (skill, template-based mock data). |
| **20–30** | Add `evaluate_framework` (skill: fixed rubric over mock data → scores), and `recommend_adoption` (reasoner: metrics in → RecommendationOut with adopt_worthwhile, reasoning). |
| **30–40** | Add `evaluate_pipeline` (reasoner: takes product + optional framework_name, calls the four steps in order, returns EvaluationReport). Wire all in `reasoners.py` / `skills.py` and import in `main.py`. |
| **40–50** | `requirements.txt`: agentfield, pydantic. Create `.env.example` (OPENAI_API_KEY). Test: `af server` in T1, `python main.py` in T2. |
| **50–60** | Demo script: curl `evaluate_pipeline` with one product JSON; verify structured `EvaluationReport`. Document exact curl and expected output in README. |

---

## 5. File Structure

```
agentsInferno/
├── agentfield.yaml          # from af init
├── main.py                  # Agent() init, AIConfig(temperature=0), include_router or register fns, app.run/serve
├── reasoners.py             # @app.reasoner: derive_use_cases, recommend_adoption, evaluate_pipeline
├── skills.py                # @app.skill(): generate_mock_data, evaluate_framework
├── schemas.py               # All Pydantic models (in/out for each function)
├── requirements.txt        # agentfield, pydantic
├── .env.example             # OPENAI_API_KEY=
├── BUILD_PLAN.md            # this file
└── README.md                # one-liner + demo curl + link to BUILD_PLAN
```

---

## 6. Skeleton Code

### Example Pydantic schemas (`schemas.py`)

```python
from pydantic import BaseModel, Field

class ProductDescription(BaseModel):
    name: str
    domain: str  # e.g. "B2B SaaS", "healthcare"
    one_liner: str

class UseCaseItem(BaseModel):
    id: str
    name: str
    description: str

class UseCasesOut(BaseModel):
    use_cases: list[UseCaseItem]

class GenerateMockDataIn(BaseModel):
    use_case_id: str
    use_case_name: str

class MockDataOut(BaseModel):
    use_case_id: str
    payload: dict  # deterministic mock payload for the use case

class EvaluateFrameworkIn(BaseModel):
    framework_name: str
    mock_payload: dict
    use_case_name: str

class EvalResult(BaseModel):
    framework_name: str
    score_completeness: float
    score_determinism: float
    score_fit: float
    overall_score: float
    notes: str

class RecommendAdoptionIn(BaseModel):
    framework_name: str
    eval_result: EvalResult

class RecommendationOut(BaseModel):
    adopt_worthwhile: bool
    confidence: float
    reasoning: str

class EvaluationReport(BaseModel):
    product_name: str
    use_cases: list[UseCaseItem]
    framework_name: str
    eval_result: EvalResult
    recommendation: RecommendationOut
```

### Example decorated function (reasoner)

```python
# reasoners.py
from agentfield import Agent
from schemas import ProductDescription, UseCasesOut

app: Agent = None  # set in main.py

def set_app(a: Agent):
    global app
    app = a

@app.reasoner
async def derive_use_cases(product: ProductDescription) -> UseCasesOut:
    """Derive agent-relevant use cases for the product. Deterministic via temperature=0 and schema."""
    return await app.ai(
        system="You derive exactly 3 agent-relevant use cases for a product. Output only structured use cases with id, name, description.",
        user=f"Product: {product.name} ({product.domain}). {product.one_liner}",
        schema=UseCasesOut,
    )
```

### Example skill

```python
# skills.py
from agentfield import Agent
from schemas import GenerateMockDataIn, MockDataOut

app: Agent = None

def set_app(a: Agent):
    global app
    app = a

@app.skill()
def generate_mock_data(inp: GenerateMockDataIn) -> MockDataOut:
    """Deterministic mock data from template."""
    # Hardcoded template per use_case_id or generic
    payload = {"use_case": inp.use_case_name, "mock_input": "deterministic_sample", "scenario": "default"}
    return MockDataOut(use_case_id=inp.use_case_id, payload=payload)
```

### Example deterministic evaluation output (skill)

```python
@app.skill()
def evaluate_framework(inp: EvaluateFrameworkIn) -> EvalResult:
    """Fixed rubric: no LLM, deterministic scores."""
    # Mock scoring: same input -> same output
    s1, s2, s3 = 0.85, 0.90, 0.75
    overall = round((s1 + s2 + s3) / 3, 2)
    return EvalResult(
        framework_name=inp.framework_name,
        score_completeness=s1,
        score_determinism=s2,
        score_fit=s3,
        overall_score=overall,
        notes="Deterministic rubric applied.",
    )
```

### Example REST call

```bash
curl -X POST http://localhost:8080/api/v1/execute/eval-agent.evaluate_pipeline \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "product": {
        "name": "SupportBot",
        "domain": "B2B SaaS",
        "one_liner": "AI support triage for enterprise tickets"
      },
      "framework_name": "AgentField"
    }
  }'
```

Example response shape:

```json
{
  "execution_id": "exec_...",
  "status": "succeeded",
  "result": {
    "product_name": "SupportBot",
    "use_cases": [...],
    "framework_name": "AgentField",
    "eval_result": { "overall_score": 0.83, ... },
    "recommendation": { "adopt_worthwhile": true, "reasoning": "..." }
  },
  "duration_ms": 2100
}
```

---

## 7. Demo Script (2 Minutes)

- **What you say:**  
  “This is an agentic evaluation backend for the AFS G Hackathon. We submit a product description; the backend deterministically derives use cases, generates mock data, evaluates a framework against that data, and returns a structured adoption recommendation. Every step is a typed, deterministic function exposed as REST via AgentField.”

- **Endpoint to hit:**  
  `POST /api/v1/execute/eval-agent.evaluate_pipeline`  
  Body: `{"input": {"product": {"name": "SupportBot", "domain": "B2B SaaS", "one_liner": "AI support triage for enterprise tickets"}, "framework_name": "AgentField"}}`

- **What judges see:**  
  A single JSON response with `result` containing `product_name`, `use_cases` (list with id/name/description), `framework_name`, `eval_result` (scores + notes), and `recommendation` (adopt_worthwhile, confidence, reasoning). No chatbot UI — backend-only, schema-first, deterministic.

---

## 8. Explicit Non-Goals

- **No UI / chatbot:** Backend only; judge demos via curl/Postman.
- **No real framework integration:** “Evaluate framework” uses a **mock rubric** (e.g. fixed or hash-based scores). No calls to LangChain/CrewAI/other SDKs.
- **No real external APIs:** Mock data is **hardcoded/template-based** from use case id/name.
- **No auth, no DB:** No API keys for endpoints; no persistence; optional `.env` only for OpenAI for reasoners.
- **No async execution or webhooks:** Synchronous `POST /api/v1/execute/...` only.
- **No multi-agent topology:** Single agent node `eval-agent` with multiple decorated functions; no separate “framework” agents.

---

**References:**  
- Docs: https://agentfield.ai/docs  
- GitHub: https://github.com/Agent-Field/agentfield  
- Deep Research / Build your first system: https://agentfield.ai/guides/getting-started/build-your-first-agent  
- The AI Backend: https://agentfield.ai/blog/posts/ai-backend  

**Optimized for:** Determinism, schema clarity, AgentField-native decorators and REST, judge-readable single-curl demo.
