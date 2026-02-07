"""Eval-agent entry point. All agent logic is in reasoners.py and skills.py as decorated functions."""

import os

from dotenv import load_dotenv

load_dotenv()

from agentfield import Agent, AIConfig

from reasoners import register as register_reasoners
from skills import register as register_skills

app = Agent(
    node_id="eval-agent",
    agentfield_server=os.getenv("AGENTFIELD_SERVER", "http://localhost:8080"),
    version="1.0.0",
    dev_mode=True,
    ai_config=AIConfig(
        model=os.getenv("OPENAI_MODEL", "openai/gpt-4o"),
        temperature=0,  # deterministic
    ),
)

# Fix 422 "Missing required field: inp": control plane sends {"input": {...}} but the agent
# validates the raw body and expects parameter names (e.g. "inp") at top level. Unwrap "input".
import agentfield.agent as _agent_module
_orig_validate = _agent_module.Agent._validate_handler_input
def _patched_validate(self, data, input_types):
    data = data.get("input", data) if isinstance(data, dict) else data
    return _orig_validate(self, data, input_types)
_agent_module.Agent._validate_handler_input = _patched_validate

register_skills(app)
register_reasoners(app)

if __name__ == "__main__":
    # dev=False avoids Uvicorn reload (which requires app as import string and was shutting the server down)
    app.serve(port=8001, dev=False)
