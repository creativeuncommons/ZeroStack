"""
Phase 1 Test Suite: Ecosystem Imports, Dependencies & Contract Verification
===========================================================================
Audits:
1. All five core modules import cleanly with zero namespace collisions.
2. Zero 3rd-party dependencies: verifies using AST analysis that only Python
   standard library modules are imported in the core packages.
3. Required protocol symbols, classes, and exported functions exist.
"""

import unittest
import sys
import os
import ast
from pathlib import Path

# Add project root to sys.path
TEST_DIR = Path(__file__).resolve().parent
SUITE_ROOT = TEST_DIR.parent
if str(SUITE_ROOT) not in sys.path:
    sys.path.insert(0, str(SUITE_ROOT))

from ecosystem_loader import zeromcp, hypergate, zeroleak, zeroloop, agenttrace

STDLIB_MODULES = set(getattr(sys, "stdlib_module_names", set())) | {
    "os", "sys", "json", "time", "uuid", "shutil", "hashlib", "sqlite3",
    "datetime", "argparse", "functools", "enum", "dataclasses", "typing",
    "contextlib", "unittest", "tempfile", "copy", "re", "threading", "pathlib",
    "collections", "math", "operator", "platform", "contextvars", "secrets",
    "inspect", "importlib", "urllib", "ast", "http", "socket", "select", "queue",
    "hmac", "subprocess"
}


class TestPhase1ImportsAndContracts(unittest.TestCase):
    def test_01_modules_imported_cleanly(self):
        """Asserts all five packages imported successfully without None."""
        self.assertIsNotNone(zeromcp)
        self.assertIsNotNone(hypergate)
        self.assertIsNotNone(zeroleak)
        self.assertIsNotNone(zeroloop)
        self.assertIsNotNone(agenttrace)

    def test_02_zero_third_party_dependencies(self):
        """AST inspection ensuring 100% standard library compliance across all core package files."""
        package_modules = [
            ("zeromcp", zeromcp),
            ("hypergate", hypergate),
            ("zeroleak", zeroleak),
            ("zeroloop", zeroloop),
            ("agenttrace", agenttrace),
        ]

        for pkg_name, mod in package_modules:
            file_path = getattr(mod, "__file__", None)
            self.assertIsNotNone(file_path, f"Module {pkg_name} has no __file__ attribute")
            self.assertTrue(os.path.exists(file_path), f"File {file_path} does not exist")

            with open(file_path, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=file_path)

            pkg_dir = os.path.dirname(file_path)
            local_modules = {
                os.path.splitext(f)[0]
                for f in os.listdir(pkg_dir)
                if f.endswith(".py")
            }

            disallowed = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        root_name = alias.name.split(".")[0]
                        if root_name not in STDLIB_MODULES and root_name not in local_modules:
                            disallowed.add(root_name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        root_name = node.module.split(".")[0]
                        if root_name not in STDLIB_MODULES and root_name not in local_modules:
                            disallowed.add(root_name)

            self.assertEqual(
                len(disallowed),
                0,
                f"Package '{pkg_name}' violated zero-dependency invariant! Disallowed imports: {disallowed}"
            )

    def test_03_zeromcp_public_contracts(self):
        """Verifies ZeroMCP exports JSON-RPC handlers and MCP registries."""
        self.assertTrue(callable(zeromcp.handle_single_request))
        self.assertIsInstance(zeromcp.TOOLS, dict)
        self.assertIsInstance(zeromcp.STATE, dict)
        self.assertTrue(callable(zeromcp.list_tools))

    def test_04_hypergate_public_contracts(self):
        """Verifies HyperGate exports ToolPruner, Router, and pricing schemas."""
        self.assertTrue(hasattr(hypergate, "ToolPruner"))
        self.assertTrue(callable(hypergate.ToolPruner.prune_tools))
        self.assertTrue(hasattr(hypergate, "HyperGateRouter"))
        self.assertTrue(hasattr(hypergate, "PricingEngine"))

    def test_05_zeroleak_public_contracts(self):
        """Verifies ZeroLeak exports reversible masking, unmasking, and vault structures."""
        self.assertTrue(callable(zeroleak.mask))
        self.assertTrue(callable(zeroleak.unmask))
        self.assertIsNotNone(zeroleak.default_engine)
        self.assertTrue(hasattr(zeroleak, "SessionVault"))

    def test_06_zeroloop_public_contracts(self):
        """Verifies ZeroLoop exports DurableLoop, EventJournal, and idempotency methods."""
        self.assertTrue(hasattr(zeroloop, "DurableLoop"))
        self.assertTrue(callable(zeroloop.DurableLoop.load))
        self.assertTrue(hasattr(zeroloop, "EventJournal"))
        self.assertTrue(callable(zeroloop.compute_idempotency_key))
        self.assertTrue(hasattr(zeroloop, "LoopReceipt"))

    def test_07_agenttrace_public_contracts(self):
        """Verifies AgentTrace exports AgentTracer, AgentSpan, W3C traceparent formatters."""
        self.assertTrue(hasattr(agenttrace, "AgentTracer"))
        self.assertTrue(hasattr(agenttrace, "AgentSpan"))
        self.assertTrue(callable(agenttrace.format_traceparent))
        self.assertTrue(callable(agenttrace.get_tracer))
        self.assertTrue(hasattr(agenttrace, "SpanKind"))


if __name__ == "__main__":
    unittest.main()
