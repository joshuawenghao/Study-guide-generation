# ruff: noqa: E402

from app.app_utils.adk_compat import ensure_google_adk_beta_compat

ensure_google_adk_beta_compat()

from google.adk.agents import Agent
from google.adk.apps import App

root_agent = Agent(
    model="gemini-2.0-flash",
    name="study_guide_generator",
    description=(
        "Generates structured K-12 study guides from teacher-provided lesson inputs."
    ),
    instruction=(
        "You are a study guide generation assistant for teachers. "
        "Produce structured, curriculum-aligned study guides using the fixed "
        "17-section format defined by the project architecture. "
        "When inputs are incomplete, ask for the missing curriculum details instead "
        "of inventing them."
    ),
)

app = App(root_agent=root_agent, name="study_guide_agent")
