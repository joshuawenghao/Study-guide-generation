"""Local runtime helpers for WeasyPrint native library loading."""

from __future__ import annotations

import ctypes
import ctypes.util
import sys
from collections.abc import Callable
from contextlib import suppress
from pathlib import Path

_HOMEBREW_OPT_ROOTS: tuple[Path, ...] = (
    Path("/opt/homebrew/opt"),
    Path("/usr/local/opt"),
)

_LIBRARY_RELATIVE_PATHS: dict[str, tuple[str, ...]] = {
    "libgobject-2.0-0": ("glib/lib/libgobject-2.0.0.dylib",),
    "gobject-2.0-0": ("glib/lib/libgobject-2.0.0.dylib",),
    "gobject-2.0": ("glib/lib/libgobject-2.0.0.dylib",),
    "libgobject-2.0.0.dylib": ("glib/lib/libgobject-2.0.0.dylib",),
    "libpango-1.0-0": ("pango/lib/libpango-1.0.0.dylib",),
    "pango-1.0-0": ("pango/lib/libpango-1.0.0.dylib",),
    "pango-1.0": ("pango/lib/libpango-1.0.0.dylib",),
    "libpango-1.0.dylib": ("pango/lib/libpango-1.0.0.dylib",),
    "libharfbuzz-0": ("harfbuzz/lib/libharfbuzz.0.dylib",),
    "harfbuzz": ("harfbuzz/lib/libharfbuzz.0.dylib",),
    "harfbuzz-0.0": ("harfbuzz/lib/libharfbuzz.0.dylib",),
    "libharfbuzz.0.dylib": ("harfbuzz/lib/libharfbuzz.0.dylib",),
    "libharfbuzz-subset-0": ("harfbuzz/lib/libharfbuzz-subset.0.dylib",),
    "harfbuzz-subset": ("harfbuzz/lib/libharfbuzz-subset.0.dylib",),
    "harfbuzz-subset-0.0": ("harfbuzz/lib/libharfbuzz-subset.0.dylib",),
    "libharfbuzz-subset.0.dylib": ("harfbuzz/lib/libharfbuzz-subset.0.dylib",),
    "libfontconfig-1": ("fontconfig/lib/libfontconfig.1.dylib",),
    "fontconfig-1": ("fontconfig/lib/libfontconfig.1.dylib",),
    "fontconfig": ("fontconfig/lib/libfontconfig.1.dylib",),
    "libfontconfig.1.dylib": ("fontconfig/lib/libfontconfig.1.dylib",),
    "libpangoft2-1.0-0": ("pango/lib/libpangoft2-1.0.0.dylib",),
    "pangoft2-1.0-0": ("pango/lib/libpangoft2-1.0.0.dylib",),
    "pangoft2-1.0": ("pango/lib/libpangoft2-1.0.0.dylib",),
    "libpangoft2-1.0.dylib": ("pango/lib/libpangoft2-1.0.0.dylib",),
}

_ORIGINAL_FIND_LIBRARY: Callable[[str], str | None] | None = None
_PATCHED = False


def _resolve_homebrew_aliases() -> dict[str, str]:
    aliases: dict[str, str] = {}

    for library_name, relative_paths in _LIBRARY_RELATIVE_PATHS.items():
        for root in _HOMEBREW_OPT_ROOTS:
            for relative_path in relative_paths:
                candidate = root / relative_path
                if candidate.exists():
                    aliases[library_name] = str(candidate)
                    break
            if library_name in aliases:
                break

    return aliases


def ensure_weasyprint_runtime_compat() -> None:
    """Teach macOS local runs how to resolve Homebrew WeasyPrint libraries."""

    global _ORIGINAL_FIND_LIBRARY, _PATCHED

    if sys.platform != "darwin" or _PATCHED:
        return

    aliases = _resolve_homebrew_aliases()
    if not aliases:
        return

    if _ORIGINAL_FIND_LIBRARY is None:
        _ORIGINAL_FIND_LIBRARY = ctypes.util.find_library

    original_find_library = _ORIGINAL_FIND_LIBRARY

    def _patched_find_library(name: str) -> str | None:
        resolved = original_find_library(name)
        if resolved is not None:
            return resolved
        return aliases.get(name)

    ctypes.util.find_library = _patched_find_library

    for resolved_path in dict.fromkeys(aliases.values()):
        with suppress(OSError):
            ctypes.CDLL(resolved_path, mode=getattr(ctypes, "RTLD_GLOBAL", 0))

    _PATCHED = True
