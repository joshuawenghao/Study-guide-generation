# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from app.app_utils.adk_compat import ensure_google_adk_beta_compat

load_dotenv(Path(__file__).resolve().parents[1] / ".env")
ensure_google_adk_beta_compat()

__all__ = ["app"]


def __getattr__(name: str) -> Any:
	if name == "app":
		from .agent import app as adk_app

		return adk_app
	raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
