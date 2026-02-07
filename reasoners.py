"""AI reasoners: analyse product, search agents, test with mock data, build notification report. All use temperature=0 + schema."""

import registry
from schemas import (
    AgentTestResult,
    AgenticOpportunitiesOut,
    AgentsFoundOut,
    EvalResult,
    NotificationReport,
    ProductDescription,
    RecommendationOut,
    RecommendAdoptionIn,
    ReportInsights,
    UseCaseItem,
    UseCasesOut,
)


def register(app):
    """Register reasoner handlers on the given Agent. Call from main.py after creating app."""

    def _is_envelope(d: dict) -> bool:
        """True if this looks like an execution envelope, not the actual result."""
        return isinstance(d, dict) and ("execution_id" in d or "run_id" in d or ("status" in d and "result" in d))

    def _unwrap(raw: dict, max_depth: int = 5) -> dict:
        """Recursively extract the actual result from app.call() until we get payload (no envelope)."""
        if not isinstance(raw, dict) or max_depth <= 0:
            return raw if isinstance(raw, dict) else {}
        if not _is_envelope(raw):
            return raw
        for key in ("result", "output", "data", "body"):
            if key in raw and isinstance(raw[key], dict):
                return _unwrap(raw[key], max_depth - 1)
        return raw

    # --- Step 2: Model analyses product to search for ways to include agentic AI ---
    @app.reasoner
    async def analyse_agentic_opportunities(product: ProductDescription) -> AgenticOpportunitiesOut:
        """Analyse product and identify concrete ways to include agentic AI (use cases, workflows)."""
        return await app.ai(
            system=(
                "You analyse a product and identify 3–4 concrete ways to include agentic AI. "
                "For each: id (short slug), title, description, suggested_agent_type (e.g. task automation, support triage, research). "
                "Also provide a short summary of where agentic AI fits. Output only the structured data."
            ),
            user=f"Product: {product.name} ({product.domain}). {product.one_liner}",
            schema=AgenticOpportunitiesOut,
        )

    # --- Step 3a: Search simulated registry (document of new agents) — demo path ---
    @app.reasoner
    async def search_agents_from_registry(
        product: ProductDescription,
        opportunities: AgenticOpportunitiesOut | None = None,
    ) -> AgentsFoundOut:
        """Search the agent registry (agent_registry.json) for agents matching the product and opportunities."""
        if isinstance(product, dict):
            product = ProductDescription(**product)
        opp_list = (opportunities.get("opportunities") if isinstance(opportunities, dict) else getattr(opportunities, "opportunities", None)) or []
        registry_agents = registry.search_registry(
            product_name=product.name,
            product_domain=product.domain,
            one_liner=product.one_liner,
            opportunities=opp_list,
            max_agents=4,
        )
        if not registry_agents:
            registry_agents = registry.load_registry()[:3]
        agents = [
            {"name": a.get("name", "Unknown"), "reason_relevant": (a.get("description", "") or "From registry.")[:120], "category": a.get("category", "file-search")}
            for a in registry_agents
        ]
        return AgentsFoundOut(agents=agents, search_context="Searched agent_registry.json (simulated repository of new agents).")

    # --- Step 3b: Legacy LLM search ---
    @app.reasoner
    async def search_agents_for_product(
        product: ProductDescription,
        opportunities: AgenticOpportunitiesOut | None = None,
    ) -> AgentsFoundOut:
        """Legacy: LLM suggests agents. Pipeline uses registry search for demo."""
        if isinstance(product, dict):
            product = ProductDescription(**product)
        context = f"Product: {product.name} ({product.domain}). {product.one_liner}"
        opp_list = (opportunities.get("opportunities") if isinstance(opportunities, dict) else getattr(opportunities, "opportunities", None)) or []
        if opp_list:
            context += "\nOpportunities: " + ", ".join(
                (o.get("title") or o.get("name", "")) if isinstance(o, dict) else getattr(o, "title", "")
                for o in opp_list
            )
        return await app.ai(
            system=(
                "You search for the best or newly released AI agent frameworks relevant to the product. "
                "Consider well-known frameworks (e.g. LangChain, CrewAI, AutoGen, AgentField, LlamaIndex) and any newer ones. "
                "For each agent: name, reason_relevant (why it fits this product), category (orchestration, RAG, multi-agent, etc.). "
                "Return 3–4 agents. Also set search_context to a one-line note on what you considered."
            ),
            user=context,
            schema=AgentsFoundOut,
        )

    # --- Legacy: single use-case derivation (kept for backward compat) ---
    @app.reasoner
    async def derive_use_cases(product: ProductDescription) -> UseCasesOut:
        """Derive agent-relevant use cases. Use analyse_agentic_opportunities for the new flow."""
        return await app.ai(
            system=(
                "You derive exactly 3 agent-relevant use cases for a product. "
                "Each use case must have id (short slug), name, and description. Output only the structured list."
            ),
            user=f"Product: {product.name} ({product.domain}). {product.one_liner}",
            schema=UseCasesOut,
        )

    def _ensure_eval_result(d: dict) -> EvalResult:
        """Normalize so we have an EvalResult; unwrap if eval_result came as envelope from app.call."""
        if isinstance(d, EvalResult):
            return d
        if isinstance(d, dict) and _is_envelope(d):
            d = _unwrap(d)
        # Build from dict; allow missing notes with default
        return EvalResult(
            framework_name=d.get("framework_name", "unknown"),
            score_completeness=float(d.get("score_completeness", 0)),
            score_determinism=float(d.get("score_determinism", 0)),
            score_fit=float(d.get("score_fit", 0)),
            overall_score=float(d.get("overall_score", 0)),
            notes=d.get("notes", ""),
        )

    @app.reasoner
    async def recommend_adoption(inp: RecommendAdoptionIn) -> RecommendationOut:
        """Recommend whether framework adoption is worthwhile from evaluation metrics."""
        # Unwrap if inp or inp.eval_result came as envelope (e.g. from cross-agent call)
        if isinstance(inp, dict):
            inp = RecommendAdoptionIn(
                framework_name=inp.get("framework_name", "unknown"),
                eval_result=_ensure_eval_result(inp.get("eval_result") or {}),
            )
        else:
            er = getattr(inp, "eval_result", None)
            if er is not None and isinstance(er, dict) and (_is_envelope(er) or "framework_name" not in er):
                inp = RecommendAdoptionIn(framework_name=inp.framework_name, eval_result=_ensure_eval_result(er))
        return await app.ai(
            system=(
                "You are an adoption advisor. Given framework name and evaluation scores, "
                "output adopt_worthwhile (bool), confidence (0-1), and reasoning (short). "
                "Be consistent: high overall_score and good fit -> adopt_worthwhile true."
            ),
            user=f"Framework: {inp.framework_name}. Eval: {inp.eval_result.model_dump()}",
            schema=RecommendationOut,
        )

    # --- Step 5: Model delivers custom performance insights and adoption guidance as a notification ---
    @app.reasoner
    async def build_notification_report(
        product_name: str,
        opportunities_summary: str,
        agents_tested: list[dict],
    ) -> ReportInsights:
        """Generate overall_insights and notification_message from test results. Pipeline assembles full NotificationReport."""
        return await app.ai(
            system=(
                "You write the final part of a notification for the user. You are given their product name, "
                "a summary of where agentic AI fits, and a list of agents tested with eval results and adopt_recommended + reasoning. "
                "Output only: overall_insights (custom performance insights comparing the agents, 2–4 sentences), "
                "notification_message (very short 2–3 sentence summary symbolising the notification: what they asked for and main takeaway)."
            ),
            user=(
                f"Product: {product_name}. Opportunities: {opportunities_summary}. Agents tested: {agents_tested}"
            ),
            schema=ReportInsights,
        )

    # --- Hackathon demo: same flow but skip LLM analyse (use fixed opportunities). Fast, works without API key. ---
    @app.reasoner
    async def evaluate_pipeline_demo(product: ProductDescription) -> NotificationReport:
        """Demo pipeline: fixed opportunities → search registry → simulate → rule-based verdict. No LLM required."""
        if isinstance(product, dict):
            product = ProductDescription(**product)
        opps = {
            "opportunities": [
                {"id": "o1", "title": "Document gap analysis", "description": "Identify gaps in compliance and ESG docs.", "suggested_agent_type": "file-search"},
                {"id": "o2", "title": "File search for policy & evidence", "description": "Search across policies and evidence for reporting.", "suggested_agent_type": "file-search"},
            ],
            "summary": "Agentic AI fits document search, gap analysis, and compliance evidence retrieval.",
        }
        opportunities_summary = opps["summary"]
        registry_agents = registry.search_registry(
            product_name=product.name,
            product_domain=product.domain,
            one_liner=product.one_liner,
            opportunities=opps["opportunities"],
            max_agents=4,
        )
        if not registry_agents:
            registry_agents = registry.load_registry()[:3]
        use_case_name = opps["opportunities"][0]["title"]
        agents_tested = []
        for agent in registry_agents:
            agent_name = agent.get("name", "Unknown")
            eval_result = registry.simulate_run(agent, use_case_name)
            eval_result_dict = eval_result.model_dump()
            adopt = eval_result.overall_score >= 0.75
            agents_tested.append({
                "agent_name": agent_name,
                "eval_result": eval_result_dict,
                "adopt_recommended": adopt,
                "reasoning": f"Simulated overall score {eval_result.overall_score:.2f}; recommend adopt for score ≥ 0.75.",
            })
        overall_insights = f"From registry: {', '.join(a['name'] for a in registry_agents)}. Best fit for '{use_case_name}' based on simulated completeness, determinism, and fit."
        notification_message = f"Demo report for {product.name}: {sum(1 for a in agents_tested if a['adopt_recommended'])} of {len(agents_tested)} agents recommended for adoption (score ≥ 0.75)."
        return NotificationReport(
            product_name=product.name,
            opportunities_summary=opportunities_summary,
            agents_tested=[AgentTestResult(**a) for a in agents_tested],
            overall_insights=overall_insights,
            notification_message=notification_message,
        )

    # --- Full pipeline: 1) product → 2) analyse → 3) search agents → 4) test each with mock data → 5) notification report ---
    @app.reasoner
    async def evaluate_pipeline(product: ProductDescription) -> NotificationReport:
        """Run full flow: analyse product for agentic opportunities, search agents, test each with mock data, deliver notification report."""
        if isinstance(product, dict):
            product = ProductDescription(**product)
        node = "eval-agent"

        # --- INPUT ---
        print("\n" + "=" * 60 + "\n[INPUT] Product\n" + "=" * 60)
        print(f"  name: {product.name}\n  domain: {product.domain}\n  one_liner: {product.one_liner}\n")

        # Step 2: Analyse product for ways to include agentic AI (fallback for demo if LLM unavailable)
        fallback_opps = {
            "opportunities": [
                {"id": "o1", "title": "Document gap analysis", "description": "Identify gaps in compliance and ESG docs.", "suggested_agent_type": "file-search"},
                {"id": "o2", "title": "File search for policy & evidence", "description": "Search across policies and evidence for reporting.", "suggested_agent_type": "file-search"},
            ],
            "summary": "Agentic AI fits document search, gap analysis, and compliance evidence retrieval.",
        }
        try:
            opps = _unwrap(await app.call(
                f"{node}.analyse_agentic_opportunities",
                product=product.model_dump(),
            ))
        except Exception:
            opps = fallback_opps
        if not opps.get("opportunities"):
            opps = fallback_opps
        opportunities_summary = opps.get("summary", "Agentic AI opportunities identified.")
        print("\n" + "=" * 60 + "\n[STEP 2] Agentic opportunities for your product\n" + "=" * 60)
        print(f"  summary: {opportunities_summary}")
        for o in opps.get("opportunities") or []:
            title = o.get("title") or o.get("name", "")
            desc = (o.get("description") or "")[:80]
            agent_type = o.get("suggested_agent_type", "")
            print(f"  - {title} ({agent_type}): {desc}...")
        print()

        # Step 3: Search simulated agent registry (repository of new agents)
        registry_agents = registry.search_registry(
            product_name=product.name,
            product_domain=product.domain,
            one_liner=product.one_liner,
            opportunities=opps.get("opportunities") or [],
            max_agents=4,
        )
        if not registry_agents:
            registry_agents = registry.load_registry()[:3]
        print("\n" + "=" * 60 + "\n[STEP 3] Agents from registry (search result)\n" + "=" * 60)
        print("  source: agent_registry.json (simulated repository)")
        for a in registry_agents:
            print(f"  - {a.get('name')} ({a.get('category')}) [{a.get('released')}]: {a.get('description', '')[:60]}...")
        print()

        # Use first opportunity as the use case for simulation
        first_opp = opps["opportunities"][0]
        use_case_id = first_opp.get("id", "o1")
        use_case_name = first_opp.get("title", first_opp.get("name", "Default"))

        # Step 4: Simulate run for each agent from registry → AI verdict
        agents_tested = []
        for agent in registry_agents:
            agent_name = agent.get("name", "Unknown")
            eval_result = registry.simulate_run(agent, use_case_name)
            eval_result_dict = eval_result.model_dump()
            try:
                recommendation = _unwrap(await app.call(
                    f"{node}.recommend_adoption",
                    inp={"framework_name": agent_name, "eval_result": eval_result_dict},
                ))
            except Exception:
                recommendation = {
                    "adopt_worthwhile": eval_result.overall_score >= 0.75,
                    "reasoning": f"Simulated overall score {eval_result.overall_score}; adopt if score ≥ 0.75.",
                }
            agents_tested.append({
                "agent_name": agent_name,
                "eval_result": eval_result_dict,
                "adopt_recommended": recommendation.get("adopt_worthwhile", False),
                "reasoning": recommendation.get("reasoning", ""),
            })
            # --- PRINT per-agent: registry metrics, simulated scores, verdict ---
            m = agent.get("metrics") or {}
            print("\n" + "-" * 60 + f"\n[STEP 4] Agent: {agent_name}\n" + "-" * 60)
            print("  registry metrics:", {k: v for k, v in m.items()})
            print("  best_for:", agent.get("best_for", []))
            e = eval_result_dict
            print(f"  simulated scores: completeness={e.get('score_completeness')}, determinism={e.get('score_determinism')}, fit={e.get('score_fit')}, overall={e.get('overall_score')}")
            print(f"  AI verdict: adopt_recommended={recommendation.get('adopt_worthwhile')}; reasoning: {recommendation.get('reasoning', '')}")

        # Step 5: Build notification report (performance insights + why adopt or not)
        try:
            insights_raw = await app.call(
                f"{node}.build_notification_report",
                product_name=product.name,
                opportunities_summary=opportunities_summary,
                agents_tested=agents_tested,
            )
            insights = _unwrap(insights_raw) if isinstance(insights_raw, dict) else {}
        except Exception:
            insights = {}
        if not isinstance(insights, dict):
            insights = {}
        overall_insights = insights.get("overall_insights") or "Performance insights across tested agents."
        notification_message = insights.get("notification_message") or f"Report for {product.name}: see agents_tested and overall_insights."
        print("\n" + "=" * 60 + "\n[STEP 5] Notification report\n" + "=" * 60)
        print(f"  overall_insights: {overall_insights}")
        print(f"  notification_message: {notification_message}\n" + "=" * 60 + "\n")

        # Ensure each agent's eval_result is EvalResult-shaped (already normalized above; _safe_agent_result as fallback)
        def _safe_agent_result(a: dict) -> dict:
            er = a.get("eval_result") or {}
            if isinstance(er, dict) and _is_envelope(er):
                er = _ensure_eval_result(er).model_dump()
            elif isinstance(er, dict) and ("framework_name" not in er or "overall_score" not in er):
                er = _ensure_eval_result(er).model_dump()
            return {**a, "eval_result": er}

        return NotificationReport(
            product_name=product.name,
            opportunities_summary=opportunities_summary,
            agents_tested=[AgentTestResult(**_safe_agent_result(a)) for a in agents_tested],
            overall_insights=overall_insights,
            notification_message=notification_message,
        )
