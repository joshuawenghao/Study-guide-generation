"""Compatibility entrypoint expected by the ADK FastAPI loader."""

from app.agent import app, root_agent

__all__ = ["app", "root_agent"]
