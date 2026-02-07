"""Pydantic schemas for all agent inputs and outputs. Every decorated function uses these for REST contract."""

from pydantic import BaseModel, Field


class ProductDescription(BaseModel):
    """Structured description of the user's product."""

    name: str
    domain: str = Field(description="e.g. B2B SaaS, healthcare")
    one_liner: str


class UseCaseItem(BaseModel):
    """Single agent-relevant use case."""

    id: str
    name: str
    description: str


class UseCasesOut(BaseModel):
    """Output of derive_use_cases."""

    use_cases: list[UseCaseItem]


class GenerateMockDataIn(BaseModel):
    """Input for generate_mock_data skill."""

    use_case_id: str
    use_case_name: str


class MockDataOut(BaseModel):
    """Deterministic mock payload for a use case."""

    use_case_id: str
    payload: dict


class EvaluateFrameworkIn(BaseModel):
    """Input for evaluate_framework skill."""

    framework_name: str
    mock_payload: dict
    use_case_name: str


class EvalResult(BaseModel):
    """Structured evaluation metrics for a framework."""

    framework_name: str
    score_completeness: float = Field(ge=0, le=1)
    score_determinism: float = Field(ge=0, le=1)
    score_fit: float = Field(ge=0, le=1)
    overall_score: float = Field(ge=0, le=1)
    notes: str


class RecommendAdoptionIn(BaseModel):
    """Input for recommend_adoption reasoner."""

    framework_name: str
    eval_result: EvalResult


class RecommendationOut(BaseModel):
    """Whether adoption is worthwhile and why."""

    adopt_worthwhile: bool
    confidence: float = Field(ge=0, le=1)
    reasoning: str


class EvaluationReport(BaseModel):
    """Legacy single-agent report. New flow uses NotificationReport."""

    product_name: str
    use_cases: list[UseCaseItem]
    framework_name: str
    eval_result: EvalResult
    recommendation: RecommendationOut


# --- New flow: analyse → search agents → test with mock data → notification report ---


class AgenticOpportunity(BaseModel):
    """One way to include agentic AI in the product."""

    id: str
    title: str
    description: str
    suggested_agent_type: str = Field(description="e.g. task automation, support triage, research")


class AgenticOpportunitiesOut(BaseModel):
    """Output of analyse_agentic_opportunities."""

    opportunities: list[AgenticOpportunity]
    summary: str = Field(description="Short summary of where agentic AI fits")


class AgentFound(BaseModel):
    """One agent/framework relevant to the product."""

    name: str
    reason_relevant: str
    category: str = Field(description="e.g. orchestration, RAG, multi-agent")


class AgentsFoundOut(BaseModel):
    """Output of search_agents_for_product."""

    agents: list[AgentFound]
    search_context: str = Field(description="What was searched or considered")


class AgentTestResult(BaseModel):
    """Per-agent test result for the notification report."""

    agent_name: str
    eval_result: EvalResult
    adopt_recommended: bool
    reasoning: str


class ReportInsights(BaseModel):
    """LLM-generated part of the notification: insights and short message."""

    overall_insights: str = Field(description="Custom performance insights across the agents tested")
    notification_message: str = Field(description="Short 2–3 sentence summary for the user (the notification)")


class NotificationReport(BaseModel):
    """Final notification to user: performance insights and adoption guidance."""

    product_name: str
    opportunities_summary: str
    agents_tested: list[AgentTestResult]
    overall_insights: str = Field(description="Custom performance insights across agents")
    notification_message: str = Field(description="Short summary meant to symbolise the notification to the user")
