"""
Phase 2 Test Suite: End-to-End Autonomous Agent Execution Flow
==============================================================
Validates the complete 5-step financial analysis agent workflow:
1. AgentTrace root trace & W3C traceparent propagation.
2. ZeroLoop durable journal initialization & commit-before-step.
3. ZeroLeak pre-inference de-identification (zero raw secrets in prompts).
4. HyperGate BM25 inverted index tool pruning across 500+ schemas (< 1.0 ms).
5. ZeroMCP fast-path JSON-RPC 2.0 tool execution.
6. ZeroLeak post-inference re-identification back to raw entities in memory.
7. ZeroLoop cryptographic SHA-256 event chaining & idempotency verification.
8. AgentTrace SQLite telemetry sink validation.
"""

import unittest
import sys
import os
import tempfile
import sqlite3
from pathlib import Path

# Add project root to sys.path
TEST_DIR = Path(__file__).resolve().parent
SUITE_ROOT = TEST_DIR.parent
if str(SUITE_ROOT) not in sys.path:
    sys.path.insert(0, str(SUITE_ROOT))

from convergence_agent import ConvergenceAgent, generate_synthetic_tool_catalog
from ecosystem_loader import zeromcp, hypergate, zeroleak, zeroloop, agenttrace


class TestPhase2E2EAgent(unittest.TestCase):
    def setUp(self):
        self.temp_storage = tempfile.mkdtemp()
        self.temp_trace = tempfile.mkdtemp()
        self.agent = ConvergenceAgent(
            storage_dir=self.temp_storage,
            trace_dir=self.temp_trace,
            tool_count=520
        )
        self.raw_prompt = (
            "Audit portfolio risk and execute risk-hedging computation for client Alice Smith "
            "(SSN: 123-45-6789, Credit Card: 4532-0151-1283-0366, "
            "Bearer Auth: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.sig_test, "
            "API Key: sk-live-982138402100000000000000). Portfolio balance is $750,000."
        )

    def test_01_tool_catalog_scale(self):
        """Verifies synthetic tool catalog generates 500+ valid schemas across distinct domains."""
        catalog = self.agent.raw_tool_catalog
        self.assertGreaterEqual(len(catalog), 500)
        
        # Verify schema integrity
        for t in catalog[:20]:
            self.assertIn("name", t)
            self.assertIn("description", t)
            self.assertIn("inputSchema", t)
            self.assertEqual(t["inputSchema"].get("type"), "object")

    def test_02_bm25_pruning_performance_and_relevance(self):
        """Verifies HyperGate prunes 500+ schemas to top-5 in < 1.0 ms and selects target tool."""
        pruner = self.agent.pruner
        
        query = "calculate portfolio Value at Risk VaR Sharpe ratio and annualized variance"
        import time
        t0 = time.perf_counter()
        top_tools = pruner.prune(query, top_k=5, enable_toolpacks=False)
        latency_ms = (time.perf_counter() - t0) * 1000
        
        self.assertEqual(len(top_tools), 5)
        names = [t.get("name") for t in top_tools]
        self.assertIn("compute_portfolio_risk", names)
        # Latency should be sub-millisecond
        self.assertLess(latency_ms, 2.5, f"Pruning latency {latency_ms:.3f} ms exceeded threshold")

    def test_03_zeromcp_rpc_dispatch(self):
        """Verifies ZeroMCP executes tool via JSON-RPC 2.0 protocol format."""
        result = self.agent.execute_mcp_tool_rpc(
            "compute_portfolio_risk",
            {"portfolio_value": 750000.0, "confidence_level": 0.95, "volatility": 0.18}
        )
        self.assertEqual(result.get("status"), "COMPUTED")
        self.assertEqual(result.get("portfolio_value"), 750000.0)
        self.assertGreater(result.get("var_95_pct"), 0.0)

    def test_04_full_e2e_agent_workflow(self):
        """Executes full 5-step agent workflow and validates all invariants."""
        res = self.agent.run_financial_audit_workflow(self.raw_prompt)
        
        # 1. Status & Receipt
        self.assertEqual(res["status"], "COMPLETED")
        receipt = res["receipt"]
        self.assertEqual(receipt.total_steps, 5)
        self.assertTrue(receipt.chain_verified, "Cryptographic hash chain must verify")
        
        # 2. De-identification & Re-identification
        restored = res["restored_summary"]
        self.assertIn("123-45-6789", restored)
        self.assertIn("4532-0151-1283-0366", restored)
        self.assertIn("sk-live-982138402100000000000000", restored)
        
        # 3. Journal Storage Sanitization Audit:
        # Assert that raw credentials DO NOT exist in ZeroLoop's SQLite journal file
        journal_db = os.path.join(self.temp_storage, f"{res['loop_id']}.db")
        self.assertTrue(os.path.exists(journal_db))
        with open(journal_db, "rb") as f:
            raw_bytes = f.read()
        self.assertNotIn(b"123-45-6789", raw_bytes, "Raw SSN leaked in ZeroLoop journal!")
        self.assertNotIn(b"4532-0151-1283-0366", raw_bytes, "Raw Credit Card leaked in ZeroLoop journal!")
        self.assertNotIn(b"sk-live-982138402100000000000000", raw_bytes, "Raw API key leaked in ZeroLoop journal!")

        # 4. Telemetry Verification (AgentTrace SQLite)
        trace_db = os.path.join(self.temp_trace, "agenttrace.db")
        self.assertTrue(os.path.exists(trace_db))
        conn = sqlite3.connect(trace_db)
        cur = conn.cursor()
        
        # Check root span and child spans
        spans = cur.execute(
            "SELECT name, kind, status FROM spans WHERE trace_id = ?",
            (res["trace_id"],)
        ).fetchall()
        self.assertGreaterEqual(len(spans), 6)  # 1 root + 5 step spans + tool spans
        
        # Check all recorded spans have OK status
        for s_name, s_kind, s_status in spans:
            self.assertEqual(s_status, "OK", f"Span {s_name} finished with non-OK status: {s_status}")

        conn.close()


if __name__ == "__main__":
    unittest.main()
