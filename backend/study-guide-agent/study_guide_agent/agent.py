"""Compatibility entrypoint expected by the ADK FastAPI loader."""

import importlib
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

agent_module = importlib.import_module("app.agent")
app = agent_module.app
root_agent = agent_module.root_agent

__all__ = ["app", "root_agent"]
