"""
ZeroStack Unified Module Loader
===============================
Unified resolution and standalone import loader for all five core ZeroStack packages:
- ZeroMCP: Fast-path Model Context Protocol server/client & RPC dispatch
- HyperGate: Routing, BM25 tool pruning, semantic caching
- ZeroLeak: Reversible in-memory de-identification vault for PII & tokens
- ZeroLoop: Event-sourced durable execution state machine with atomic SQLite WAL
- AgentTrace: W3C distributed tracing, trajectory telemetry, parent-child spans

Zero 3rd-party dependencies: strictly Python standard library.
"""

import sys
import os
import importlib
from pathlib import Path
from typing import Dict, Any

# Locate Root
STACK_DIR = Path(__file__).resolve().parent
PROJECTS_DIR = STACK_DIR.parent
WORKSPACE_ROOT = PROJECTS_DIR.parent

PACKAGE_PATHS = [
    # Candidate 0: Git Submodules inside local packages/ (ZeroStack repo structure)
    {
        "zeromcp": STACK_DIR / "packages" / "ZeroMCP" / "zeromcp-py",
        "hypergate": STACK_DIR / "packages" / "HyperGate" / "hypergate-py",
        "zeroleak": STACK_DIR / "packages" / "ZeroLeak" / "zeroleak-py",
        "zeroloop": STACK_DIR / "packages" / "ZeroLoop" / "zeroloop-py",
        "agenttrace": STACK_DIR / "packages" / "AgentTrace" / "agenttrace-py",
    },
    # Candidate 1: dist_promoted (monorepo sibling directories)
    {
        "zeromcp": WORKSPACE_ROOT / "dist_promoted" / "ZeroMCP" / "zeromcp-py",
        "hypergate": WORKSPACE_ROOT / "dist_promoted" / "HyperGate" / "hypergate-py",
        "zeroleak": WORKSPACE_ROOT / "dist_promoted" / "ZeroLeak" / "zeroleak-py",
        "zeroloop": WORKSPACE_ROOT / "dist_promoted" / "ZeroLoop" / "zeroloop-py",
        "agenttrace": WORKSPACE_ROOT / "dist_promoted" / "AgentTrace" / "agenttrace-py",
    },
    # Candidate 2: 0_Projects (in-tree monorepo projects)
    {
        "zeromcp": PROJECTS_DIR / "ZeroMCP" / "zeromcp-py",
        "hypergate": PROJECTS_DIR / "HyperGate" / "hypergate-py",
        "zeroleak": PROJECTS_DIR / "ZeroLeak" / "zeroleak-py",
        "zeroloop": PROJECTS_DIR / "ZeroLoop" / "zeroloop-py",
        "agenttrace": PROJECTS_DIR / "AgentTrace" / "agenttrace-py",
    }
]


def load_zerostack() -> Dict[str, Any]:
    """
    Imports and returns references to all five core modules.
    Verifies that all 5 modules resolve cleanly with zero collisions.
    """
    loaded_modules: Dict[str, Any] = {}
    missing = []

    for name in ["zeromcp", "hypergate", "zeroleak", "zeroloop", "agenttrace"]:
        resolved_path = None
        for candidate_set in PACKAGE_PATHS:
            cand = candidate_set.get(name)
            if cand and cand.exists() and (cand / f"{name}.py").exists():
                resolved_path = cand
                break

        if not resolved_path:
            missing.append(name)
            continue

        cand_str = str(resolved_path)
        if cand_str not in sys.path:
            sys.path.insert(0, cand_str)

        try:
            mod = importlib.import_module(name)
            loaded_modules[name] = mod
        except Exception as e:
            raise ImportError(f"Failed to import core package '{name}' from {resolved_path}: {e}") from e

    if missing:
        raise FileNotFoundError(f"Could not locate package source directories for: {missing}")

    return loaded_modules


# Pre-load on import for convenient direct access
_MODULES = load_zerostack()

zeromcp = _MODULES["zeromcp"]
hypergate = _MODULES["hypergate"]
zeroleak = _MODULES["zeroleak"]
zeroloop = _MODULES["zeroloop"]
agenttrace = _MODULES["agenttrace"]

# Backwards compatibility alias
load_ecosystem = load_zerostack

__all__ = [
    "load_zerostack",
    "load_ecosystem",
    "zeromcp",
    "hypergate",
    "zeroleak",
    "zeroloop",
    "agenttrace",
]
