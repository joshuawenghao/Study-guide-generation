"""Compatibility helpers for the current ADK 2.0 beta environment."""

from __future__ import annotations

import sys
import types
from importlib.metadata import PackageNotFoundError, version


class _FeatureNameProxy:
    def __getattr__(self, name: str) -> str:
        return name


def ensure_google_adk_beta_compat() -> None:
    """Install a narrow shim for the broken 2.0.0b1 `google.adk.features` import surface.

    The published `google-adk==2.0.0b1` wheel used by this repository exposes
    `google.adk.workflow` but omits the `google.adk.features` module that other ADK
    internals import at import time. Until a fixed beta or stable release is available,
    this shim supplies the specific symbols those imports expect.
    """

    if "google.adk.features" in sys.modules:
        return

    try:
        adk_version = version("google-adk")
    except PackageNotFoundError:
        return

    if adk_version != "2.0.0b1":
        return

    features = types.ModuleType("google.adk.features")
    features.FeatureName = _FeatureNameProxy()
    features.is_feature_enabled = lambda *args, **kwargs: False
    features.override_feature_enabled = lambda *args, **kwargs: None
    features.experimental = lambda *args, **kwargs: lambda value: value
    sys.modules["google.adk.features"] = features
