"""
Phase 3 Test Suite: Simulated Fault Injection & Crash Recovery Verification
===========================================================================
Audits:
1. Simulates abrupt process crash / abortion mid-execution at Step 3 of 5.
2. Rehydrates state via `DurableLoop.load()`.
3. Verifies:
   - Resumed step index matches exactly (Step 3).
   - Prior tool side-effects are not duplicated (Idempotency gate intercepts and replays cached result).
   - Trace ID and span parentage remain continuous and unbroken across recovery.
   - Final loop receipt achieves 100% cryptographic SHA-256 chain verification.
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

from convergence_agent import ConvergenceAgent
from ecosystem_loader import zeroloop, agenttrace


class TestPhase3FaultInjection(unittest.TestCase):
    def setUp(self):
        self.temp_storage = tempfile.mkdtemp()
        self.temp_trace = tempfile.mkdtemp()
        self.loop_id = "test_fault_recovery_session"
        self.raw_prompt = (
            "Audit client Alice Smith SSN 123-45-6789 card 4532-0151-1283-0366 "
            "bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.sig_test "
            "api sk-live-982138402100000000000000 for portfolio risk and hedge calculations."
        )

    def test_01_crash_and_resumption_invariants(self):
        """Injects crash at Step 3, rehydrates state, and verifies recovery invariants."""
        # --- PHASE 1: EXECUTE UNTIL STEP 3 AND CRASH ---
        agent1 = ConvergenceAgent(
            loop_id=self.loop_id,
            storage_dir=self.temp_storage,
            trace_dir=self.temp_trace,
            tool_count=520
        )
        crash_result = agent1.run_financial_audit_workflow(self.raw_prompt, simulate_crash_step=3)
        
        self.assertEqual(crash_result["status"], "CRASHED_INJECTED")
        self.assertEqual(crash_result["crashed_at_step"], 3)
        orig_trace_id = crash_result["trace_id"]
        orig_root_span_id = crash_result["root_span_id"]

        # --- PHASE 2: REHYDRATE STATE IN SEPARATE INSTANCE ---
        agent2 = ConvergenceAgent(
            loop_id=self.loop_id,
            storage_dir=self.temp_storage,
            trace_dir=self.temp_trace,
            tool_count=520
        )
        recovery_result = agent2.resume_from_crash()

        self.assertEqual(recovery_result["status"], "RECOVERED_AND_COMPLETED")
        self.assertEqual(recovery_result["resumed_step_idx"], 3, "Resumed step index must match crashed step exactly")
        
        receipt = recovery_result["receipt"]
        self.assertEqual(receipt.total_steps, 5, "Total steps should complete all 5 planned steps")
        self.assertGreaterEqual(receipt.crash_recoveries, 1, "Crash recovery tally must be >= 1")
        self.assertGreaterEqual(receipt.duplicate_tool_calls_prevented, 1, "Idempotency gate must prevent duplicate tool execution")
        self.assertTrue(receipt.chain_verified, "Cryptographic hash chain must be 100% verified after recovery")

        # --- PHASE 3: DISTRIBUTED TRACE LINEAGE AUDIT ---
        trace_db = os.path.join(self.temp_trace, "agenttrace.db")
        self.assertTrue(os.path.exists(trace_db))
        conn = sqlite3.connect(trace_db)
        cur = conn.cursor()

        # Audit spans table
        spans = cur.execute(
            "SELECT name, trace_id, parent_span_id, status FROM spans ORDER BY start_time_ns ASC"
        ).fetchall()
        
        trace_ids = {s[1] for s in spans}
        self.assertEqual(len(trace_ids), 1, "All spans across crash and recovery must share the exact same trace ID")
        self.assertIn(orig_trace_id, trace_ids)

        # Ensure root span exists and recovery span is attached to it
        recovery_spans = [s for s in spans if "recovery" in s[0]]
        self.assertGreaterEqual(len(recovery_spans), 1)
        self.assertEqual(recovery_spans[0][2], orig_root_span_id, "Recovery span parent must be the original root span")

        conn.close()

    def test_02_idempotency_key_consistency(self):
        """Verifies deterministic idempotency key computation across re-executions."""
        inputs = {"portfolio_value": 750000.0, "shock_pct": 15.0}
        k1 = zeroloop.compute_idempotency_key(3, "simulate_monte_carlo_drawdown", inputs)
        k2 = zeroloop.compute_idempotency_key(3, "simulate_monte_carlo_drawdown", inputs)
        self.assertEqual(k1, k2)

        # Mutating inputs yields distinct key
        k3 = zeroloop.compute_idempotency_key(3, "simulate_monte_carlo_drawdown", {"portfolio_value": 750000.0, "shock_pct": 20.0})
        self.assertNotEqual(k1, k3)


if __name__ == "__main__":
    unittest.main()
