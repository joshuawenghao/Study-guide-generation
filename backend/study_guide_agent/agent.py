# backend/study_guide_agent/agent.py
#
# ADK entry point. Defines root_agent which ADK discovers when you run:
#   adk web        (from backend/ directory)
#   adk run study_guide_agent
#
# Currently a minimal placeholder agent so ADK can load the package.
# The full dynamic workflow will be implemented in Phase 7 (Task 7.1).

from google.adk.agents import Agent

root_agent = Agent(
    model="gemini-2.0-flash",
    name="study_guide_generator",
    description="Generates structured K-12 study guides from teacher-provided lesson inputs.",
    instruction=(
        "You are a study guide generation assistant. "
        "You help teachers create structured, curriculum-aligned study guides. "
        "This agent will be replaced with a full dynamic workflow in a later task."
    ),
)