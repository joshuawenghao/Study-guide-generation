"""Loader package for scaffold-native conversational eval flows."""

import importlib
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

agent = importlib.import_module("eval_app.agent")
app = agent.app

__all__ = ["agent", "app"]
