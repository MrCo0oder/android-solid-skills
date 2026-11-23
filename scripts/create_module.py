#!/usr/bin/env python3
"""Repository entry point for the generator bundled with the solid skill."""

import importlib.util
from pathlib import Path
import sys

_IMPLEMENTATION = (
    Path(__file__).resolve().parents[1]
    / "skills" / "solid" / "scripts" / "create_module.py"
)
_spec = importlib.util.spec_from_file_location("solid_create_module", _IMPLEMENTATION)
if _spec is None or _spec.loader is None:
    raise ImportError(f"Cannot load module generator: {_IMPLEMENTATION}")
_generator = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_generator)


def __getattr__(name):
    """Keep the original importable helpers available to callers and tests."""
    return getattr(_generator, name)


if __name__ == "__main__":
    sys.exit(_generator.main())
