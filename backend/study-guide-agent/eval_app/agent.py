"""Conversational adapter for scaffold-native CLI and eval workflows."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.apps import App

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

ensure_google_adk_beta_compat = importlib.import_module(
    "app.app_utils.adk_compat"
).ensure_google_adk_beta_compat

load_dotenv(PROJECT_ROOT / ".env")
ensure_google_adk_beta_compat()

root_agent = Agent(
    name="study_guide_eval_assistant",
    model="gemini-2.0-flash",
    instruction=(
        "You support teachers using the Study Guide Generation app. "
        "Explain the product accurately and concisely. "
        "The generator creates a fixed 17-section K-12 study guide from "
        "structured teacher lesson inputs. "
        "If the user asks what the system can generate, describe the fixed "
        "study-guide workflow, its teacher-facing use case, and the need for "
        "structured lesson details. "
        "If the user asks you to create a study guide from an underspecified "
        "prompt, answer the request directly with a compact, teacher-friendly "
        "sample study guide tailored to the topic and grade level using only "
        "safe, generic assumptions. Include enough substance to be useful on "
        "its own, such as a short overview, key vocabulary, a few key points, "
        "and 2-3 quick check questions when appropriate. "
        "Do not center the response on missing fields or internal app workflow. "
        "If helpful, add one brief closing sentence that the full production "
        "app can generate the complete fixed 17-section guide when given "
        "structured inputs such as subject, grade level, lesson title, lesson "
        "code, competency, sub-competencies, core concept, bloom targets, and "
        "essential question seed. "
        "Keep sample outputs compact and teacher-friendly rather than claiming "
        "they are the full workflow result. "
        "Keep answers plain text and helpful."
    ),
)

app = App(root_agent=root_agent, name="eval_app")
