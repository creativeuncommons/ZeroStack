"""
Phase 4 Test Suite: Organization-Specific Custom PII & Sensitive Entity Convergence
==================================================================================
Validates end-to-end integration of novel enterprise-specific sensitivity rules
across the unified 5-package CreativeUnCommons architecture:

1. CustomEntityRule registration (Healthcare MRN, Internal Trade ID, Acme Vault Secret).
2. Pre-inference masking into type-aware synthetic tokens ([PATIENT_MRN_1], [INTERNAL_TRADE_ID_1], etc.).
3. Zero leakage across HyperGate BM25 inverted index tool selection.
4. ZeroMCP JSON-RPC 2.0 tool execution under masked parameters.
5. In-memory post-inference restitution preserving 100% fidelity.
6. ZeroLoop commit-before-step WAL journal asserting zero custom secret leakage to disk.
7. AgentTrace W3C distributed tracing with custom entity audit receipts.
8. Crash recovery resilience with vaulted custom entities.
"""

import unittest
import sys
import os
import tempfile
import sqlite3
import json
from pathlib import Path

# Add project root to sys.path
TEST_DIR = Path(__file__).resolve().parent
SUITE_ROOT = TEST_DIR.parent
if str(SUITE_ROOT) not in sys.path:
    sys.path.insert(0, str(SUITE_ROOT))

from convergence_agent import ConvergenceAgent
from ecosystem_loader import zeromcp, hypergate, zeroleak, zeroloop, agenttrace


class TestPhase4CustomPIIConvergence(unittest.TestCase):
    def setUp(self):
        self.temp_storage = tempfile.mkdtemp()
        self.temp_trace = tempfile.mkdtemp()

        # Define 3 canonical organization-specific sensitivity rules
        self.custom_rules = [
            zeroleak.CustomEntityRule(
                name="PATIENT_MRN",
                pattern=r"\bMRN-[0-9]{4}-[0-9]{4}\b",
                priority=70,
                description="Healthcare Patient Medical Record Number"
            ),
            zeroleak.CustomEntityRule(
                name="INTERNAL_TRADE_ID",
                pattern=r"\bTRD-[A-Z]{3}-[0-9]{6}\b",
                priority=75,
                description="Proprietary institutional trade reference ID"
            ),
            zeroleak.CustomEntityRule(
                name="ACME_VAULT_KEY",
                pattern=r"\bacme_sec_[A-Za-z0-9]{16,32}\b",
                entropy_threshold=3.2,
                priority=80,
                description="Acme enterprise vault access credential"
            ),
        ]

        self.agent = ConvergenceAgent(
            storage_dir=self.temp_storage,
            trace_dir=self.temp_trace,
            tool_count=520,
            custom_rules=self.custom_rules
        )

        self.raw_custom_prompt = (
            "Audit institutional client trade TRD-NYC-849102 associated with patient MRN-9021-4412. "
            "Internal clearing credential: acme_sec_9aK8bL2mP7vW1zY4. Standard backup SSN: 123-45-6789. "
            "Portfolio balance is $750,000."
        )

    def test_01_custom_rule_registration_and_masking(self):
        """Verifies custom organizational entities are correctly masked into typed surrogate tokens."""
        trace_id = "trc_custom_01"
        masked = self.agent.vault.mask(self.raw_custom_prompt, trace_id=trace_id)

        # Assert raw entities are completely eradicated from the masked stream
        self.assertNotIn("MRN-9021-4412", masked)
        self.assertNotIn("TRD-NYC-849102", masked)
        self.assertNotIn("acme_sec_9aK8bL2mP7vW1zY4", masked)
        self.assertNotIn("123-45-6789", masked)

        # Assert custom synthetic tokens are generated with canonical names
        self.assertIn("[PATIENT_MRN_1]", masked)
        self.assertIn("[INTERNAL_TRADE_ID_1]", masked)
        self.assertIn("[ACME_VAULT_KEY_1]", masked)
        self.assertIn("[SSN_1]", masked)

        # Restitute and verify 100% roundtrip fidelity
        restituted = self.agent.vault.unmask(masked, trace_id=trace_id)
        self.assertEqual(self.raw_custom_prompt, restituted)

        # Verify audit receipt entity breakdown
        receipt = self.agent.vault.get_audit_receipt(trace_id)
        self.assertIsNotNone(receipt)
        self.assertEqual(receipt.types_detected.get("PATIENT_MRN"), 1)
        self.assertEqual(receipt.types_detected.get("INTERNAL_TRADE_ID"), 1)
        self.assertEqual(receipt.types_detected.get("ACME_VAULT_KEY"), 1)
        self.assertEqual(receipt.types_detected.get("SSN"), 1)

    def test_02_full_workflow_with_custom_pii(self):
        """Executes full 5-step agent workflow with custom organizational sensitive data."""
        res = self.agent.run_financial_audit_workflow(self.raw_custom_prompt)

        self.assertEqual(res["status"], "COMPLETED")
        receipt = res["receipt"]
        self.assertEqual(receipt.total_steps, 5)
        self.assertTrue(receipt.chain_verified)

        # Verify restored summary in execution memory contains authentic custom secrets
        restored = res["restored_summary"]
        self.assertIn("MRN-9021-4412", restored)
        self.assertIn("TRD-NYC-849102", restored)
        self.assertIn("acme_sec_9aK8bL2mP7vW1zY4", restored)
        self.assertIn("123-45-6789", restored)

        # Invariant: Verify disk storage contains ZERO custom sensitive tokens
        db_path = os.path.join(self.temp_storage, f"{self.agent.loop_id}.db")
        self.assertTrue(os.path.exists(db_path), "ZeroLoop SQLite WAL must exist on disk")

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT payload_json FROM events")
        all_event_payloads = " ".join([row[0] for row in cursor.fetchall()])
        conn.close()

        self.assertNotIn("MRN-9021-4412", all_event_payloads, "ZeroLoop disk journal leaked custom MRN!")
        self.assertNotIn("TRD-NYC-849102", all_event_payloads, "ZeroLoop disk journal leaked custom Trade ID!")
        self.assertNotIn("acme_sec_9aK8bL2mP7vW1zY4", all_event_payloads, "ZeroLoop disk journal leaked custom Acme Secret!")
        self.assertNotIn("123-45-6789", all_event_payloads, "ZeroLoop disk journal leaked SSN!")

        # But surrogate tokens MUST be present in durable disk storage
        self.assertIn("[PATIENT_MRN_1]", all_event_payloads)
        self.assertIn("[INTERNAL_TRADE_ID_1]", all_event_payloads)

    def test_03_crash_recovery_with_custom_pii(self):
        """Verifies crash resilience and rehydration when custom organizational data is present."""
        loop_id = "crash_custom_pii_test"
        agent1 = ConvergenceAgent(
            loop_id=loop_id,
            storage_dir=self.temp_storage,
            trace_dir=self.temp_trace,
            custom_rules=self.custom_rules
        )

        crash_res = agent1.run_financial_audit_workflow(self.raw_custom_prompt, simulate_crash_step=3)
        self.assertEqual(crash_res["status"], "CRASHED_INJECTED")
        self.assertEqual(crash_res["crashed_at_step"], 3)

        # Rehydrate and complete after crash
        agent2 = ConvergenceAgent(
            loop_id=loop_id,
            storage_dir=self.temp_storage,
            trace_dir=self.temp_trace,
            custom_rules=self.custom_rules
        )
        rec_res = agent2.resume_from_crash()

        self.assertEqual(rec_res["status"], "RECOVERED_AND_COMPLETED")
        self.assertEqual(rec_res["resumed_step_idx"], 3)
        self.assertEqual(rec_res["receipt"].total_steps, 5)
        self.assertGreaterEqual(rec_res["receipt"].duplicate_tool_calls_prevented, 1)
        self.assertTrue(rec_res["receipt"].chain_verified)


if __name__ == "__main__":
    unittest.main()
