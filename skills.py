"""Deterministic skills: generate_mock_data, evaluate_framework. No LLM; pure/template-based."""

from schemas import (
    EvalResult,
    EvaluateFrameworkIn,
    GenerateMockDataIn,
    MockDataOut,
)


def register(app):
    """Register skill handlers on the given Agent. Call from main.py after creating app."""

    @app.skill()
    def generate_mock_data(inp: GenerateMockDataIn) -> MockDataOut:
        """Produce deterministic mock data for a use case. Same input -> same output."""
        payload = {
            "use_case": inp.use_case_name,
            "use_case_id": inp.use_case_id,
            "mock_input": "deterministic_sample",
            "scenario": "default",
            "sample_ticket": {"subject": "Support request", "body": "Need help with integration"},
        }
        return MockDataOut(use_case_id=inp.use_case_id, payload=payload)

    @app.skill()
    def evaluate_framework(inp: EvaluateFrameworkIn) -> EvalResult:
        """Fixed rubric over mock data. No LLM; deterministic scores."""
        # Deterministic: hash-like scores from framework name + use case name
        base = hash((inp.framework_name, inp.use_case_name)) % 1000 / 1000.0
        s1 = round(0.7 + (base * 0.25), 2)
        s2 = round(0.75 + ((1 - base) * 0.2), 2)
        s3 = round(0.65 + (base * 0.3), 2)
        s1, s2, s3 = min(1.0, s1), min(1.0, s2), min(1.0, s3)
        overall = round((s1 + s2 + s3) / 3, 2)
        return EvalResult(
            framework_name=inp.framework_name,
            score_completeness=s1,
            score_determinism=s2,
            score_fit=s3,
            overall_score=overall,
            notes="Deterministic rubric applied to mock payload.",
        )
