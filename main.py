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

register_skills(app)
register_reasoners(app)

if __name__ == "__main__":
    # dev=False avoids Uvicorn reload (which requires app as import string and was shutting the server down)
    app.serve(port=8001, dev=False)
