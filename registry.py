"""
Simulated agent registry: load, search, and simulate a run from metrics.
Used when we can't connect to real agents — search this "repository" and derive performance from metrics.
"""

import json
from pathlib import Path

from schemas import EvalResult

_REGISTRY: list[dict] | None = None


def _registry_path() -> Path:
    return Path(__file__).resolve().parent / "agent_registry.json"


def load_registry() -> list[dict]:
    """Load the simulated agent registry from agent_registry.json."""
    global _REGISTRY
    if _REGISTRY is not None:
        return _REGISTRY
    path = _registry_path()
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    _REGISTRY = data.get("agents") or []
    return _REGISTRY


def search_registry(
    product_name: str,
    product_domain: str,
    one_liner: str,
    opportunities: list[dict] | None = None,
    max_agents: int = 4,
) -> list[dict]:
    """
    Search the registry for agents relevant to the product and opportunities.
    Uses keyword overlap on category, best_for, features, and description.
    Returns list of full agent dicts (with metrics) for simulation.
    """
    agents = load_registry()
    if not agents:
        return []

    # Build query tokens from product and opportunities
    tokens = set()
    for s in (product_name, product_domain, one_liner or ""):
        for w in (s or "").lower().replace(",", " ").replace(".", " ").split():
            if len(w) > 2:
                tokens.add(w)
    if opportunities:
        for o in opportunities:
            for key in ("title", "description", "suggested_agent_type"):
                val = o.get(key) or ""
                for w in val.lower().replace(",", " ").split():
                    if len(w) > 2:
                        tokens.add(w)

    scored: list[tuple[float, dict]] = []
    for agent in agents:
        score = 0.0
        searchable = " ".join(
            [
                agent.get("name", ""),
                agent.get("category", ""),
                agent.get("description", ""),
                " ".join(agent.get("features", [])),
                " ".join(agent.get("best_for", [])),
            ]
        ).lower()
        for t in tokens:
            if t in searchable:
                score += 1.0
        # Prefer agents whose best_for or category explicitly match
        best_for = [b.lower() for b in agent.get("best_for", [])]
        for t in tokens:
            if any(t in b for b in best_for):
                score += 2.0
        if agent.get("category", "").lower() in ("file-search", "rag") and any(
            w in ("file", "search", "document", "esg", "compliance", "gap") for w in tokens
        ):
            score += 1.5
        scored.append((score, agent))

    scored.sort(key=lambda x: -x[0])
    # Return at least top 2 if any score > 0, else top 2 by default for demo
    if not scored or scored[0][0] <= 0:
        return agents[:max_agents]
    return [a for _, a in scored[: max(2, max_agents)]]


def simulate_run(agent: dict, use_case_name: str) -> EvalResult:
    """
    Simulate a run of the product's use case with this agent using its registry metrics.
    Produces completeness, determinism, fit, and overall score from metrics (no real execution).
    """
    name = agent.get("name", "Unknown")
    metrics = agent.get("metrics") or {}
    best_for = [b.lower() for b in agent.get("best_for", [])]
    use_lower = (use_case_name or "").lower()

    # Completeness: from accuracy_retrieval and context size
    acc = float(metrics.get("accuracy_retrieval", 0.85))
    ctx = int(metrics.get("max_context_tokens", 100000))
    score_completeness = round(min(1.0, acc + (ctx / 300000) * 0.05), 2)

    # Determinism: inverse of latency variance; use latency as proxy (lower = more predictable)
    latency = int(metrics.get("latency_p95_ms", 500))
    score_determinism = round(max(0.5, 1.0 - (latency / 2000)), 2)

    # Fit: how well best_for matches the use case
    fit = 0.6
    for b in best_for:
        if any(w in b for w in use_lower.split()) or any(w in use_lower for w in b.split()):
            fit = min(1.0, fit + 0.15)
    score_fit = round(fit, 2)

    overall = round((score_completeness + score_determinism + score_fit) / 3, 2)
    notes = (
        f"Simulated from registry: latency_p95={latency}ms, accuracy_retrieval={acc}, "
        f"best_for={', '.join(best_for[:3])}."
    )
    return EvalResult(
        framework_name=name,
        score_completeness=score_completeness,
        score_determinism=score_determinism,
        score_fit=score_fit,
        overall_score=overall,
        notes=notes,
    )
