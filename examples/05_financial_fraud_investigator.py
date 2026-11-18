#!/usr/bin/env python3
"""
Example 5: Financial Fraud & Trading Compliance Investigator (Crash Resilience)
===============================================================================
Demonstrates an institutional finance / trading compliance agent executing a
multi-step fraud investigation with custom trade ticket identifiers, protected
market data queries over ZeroMCP, and deterministic ZeroLoop crash recovery.

Key Capabilities Demonstrated:
1. Custom Institutional Entity Rules: Masks proprietary clearing accounts and
   trade identifiers (e.g. TRD-NYC-849102, ACCT-SEC-991203).
2. Protocol-Grade Tool Hosting (ZeroMCP): Fast-path JSON-RPC 2.0 tool execution
   connecting to market surveillance microservices.
3. Mid-Investigation Crash Recovery (ZeroLoop): Simulates an abrupt host crash
   at Step 3 of a 5-step loop, then rehydrates from the SQLite WAL journal,
   resuming execution without duplicate market side-effects.
4. Cryptographic Proof of Lineage: Event hash chain (SHA-256) guarantees that
   audit records submitted to regulators (SEC / FINRA) have not been tampered with.

Usage:
    python3 examples/05_financial_fraud_investigator.py --test
"""

import sys
import os
import json
import time
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional

# Add suite root to path
EXAMPLES_DIR = Path(__file__).resolve().parent
SUITE_ROOT = EXAMPLES_DIR.parent
if str(SUITE_ROOT) not in sys.path:
    sys.path.insert(0, str(SUITE_ROOT))

from ecosystem_loader import zeroleak, zeroloop, agenttrace, zeromcp


class TradingSurveillanceAgent:
    """Surveillance investigator analyzing anomalous trade blocks."""
    def __init__(self, storage_dir: Optional[str] = None):
        self.storage_dir = storage_dir or tempfile.mkdtemp(prefix="surveillance_storage_")
        self.vault = zeroleak.ZeroLeak(mode="enforce")

        # Custom trade entity rules
        self.vault.register_custom_rule(
            zeroleak.CustomEntityRule(
                name="TRADE_ID",
                pattern=r"\bTRD-[A-Z]{3}-[0-9]{6}\b",
                priority=80,
                description="Institutional trade execution ticket ID"
            )
        )
        self.vault.register_custom_rule(
            zeroleak.CustomEntityRule(
                name="CLEARING_ACCT",
                pattern=r"\bACCT-SEC-[0-9]{6}\b",
                priority=75,
                description="Brokerage clearing custody account number"
            )
        )

        self.tracer = agenttrace.AgentTracer(service_name="trading-surveillance")

    def run_investigation(self, dispatch_alert: str, simulate_crash_at_step: Optional[int] = None) -> Dict[str, Any]:
        """Runs the 5-step surveillance investigation with optional crash injection."""
        loop_id = "surveillance_case_9021"

        with self.tracer.span("fraud_investigation_loop", kind=agenttrace.SpanKind.AGENT) as root_span:
            trace_id = root_span.trace_id

            # Step 1: Pre-mask raw trade ticket (strips trade ID, account, API token)
            masked_alert = self.vault.mask(dispatch_alert, trace_id=trace_id)

            loop = zeroloop.DurableLoop(loop_id=loop_id, storage_dir=self.storage_dir)
            loop.start()
            loop.step_start("ingest_alert", inputs={"trace_id": trace_id})
            loop.step_complete(outputs={"masked_alert": masked_alert})

            # Step 2: Query order book depth
            loop.step_start("query_order_book", inputs={"trade": "[TRADE_ID_1]"})
            order_book_res = {"depth": "THIN_LIQUIDITY", "spread": 0.42, "matched_volume": 50000}
            loop.step_complete(outputs={"order_book": order_book_res})

            # Step 3: Crash injection point
            if simulate_crash_at_step == 3:
                # Abruptly close WAL journal simulating power outage or process SIGKILL
                loop.journal.close()
                return {
                    "status": "CRASHED_INJECTED",
                    "crashed_at_step": 3,
                    "loop_id": loop_id,
                    "storage_dir": self.storage_dir
                }

            # Step 3 (Normal): Reconstruct counterparty graph
            loop.step_start("reconstruct_counterparties", inputs={"acct": "[CLEARING_ACCT_1]"})
            counterparties = ["BROKER_DEALER_ALPHA", "OFFSHORE_FEEDER_BETA"]
            loop.step_complete(outputs={"counterparties": counterparties})

            # Step 4: Flag suspicious wash trading pattern
            loop.step_start("evaluate_compliance_violation", inputs={"threshold": 0.95})
            violation_status = "POTENTIAL_WASH_SALE"
            loop.step_complete(outputs={"violation": violation_status})

            # Step 5: Synthesize regulator report and unmask
            loop.step_start("synthesize_regulatory_report", inputs={"action": "generate_filing"})
            mock_llm_report = (
                f"SURVEILLANCE REPORT:\n"
                f"Execution [TRADE_ID_1] via clearing custody [CLEARING_ACCT_1] exhibited circular wash routing. "
                f"Contact authorized compliance lead at [EMAIL_1] immediately."
            )
            restituted_report = self.vault.unmask(mock_llm_report, trace_id=trace_id)
            loop.step_complete(outputs={"report_len": len(restituted_report)})
            receipt = loop.complete(final_output=restituted_report)
            loop.close()

            return {
                "status": "COMPLETED",
                "trace_id": trace_id,
                "sanitized_alert": masked_alert,
                "regulatory_report": restituted_report,
                "total_steps": receipt.total_steps,
                "chain_verified": receipt.chain_verified
            }

    def resume_after_crash(self, loop_id: str, trace_id: str) -> Dict[str, Any]:
        """Rehydrates loop from SQLite WAL and completes investigation."""
        # Load durable loop from journal
        loop = zeroloop.DurableLoop.load(loop_id=loop_id, storage_dir=self.storage_dir)
        resumed_from = loop.step_idx

        # Resume Step 3
        loop.step_start("reconstruct_counterparties", inputs={"acct": "[CLEARING_ACCT_1]"})
        loop.step_complete(outputs={"counterparties": ["BROKER_DEALER_ALPHA", "OFFSHORE_FEEDER_BETA"]})

        # Resume Step 4
        loop.step_start("evaluate_compliance_violation", inputs={"threshold": 0.95})
        loop.step_complete(outputs={"violation": "POTENTIAL_WASH_SALE"})

        # Resume Step 5
        loop.step_start("synthesize_regulatory_report", inputs={"action": "generate_filing"})
        mock_llm_report = (
            f"SURVEILLANCE REPORT (POST-RECOVERY):\n"
            f"Execution [TRADE_ID_1] via clearing custody [CLEARING_ACCT_1] confirmed wash violation. "
            f"Contact compliance lead at [EMAIL_1]."
        )
        restituted_report = self.vault.unmask(mock_llm_report, trace_id=trace_id)
        loop.step_complete(outputs={"report_len": len(restituted_report)})
        receipt = loop.complete(final_output=restituted_report)
        loop.close()

        return {
            "status": "RECOVERED_AND_COMPLETED",
            "resumed_from_step": resumed_from,
            "total_steps": receipt.total_steps,
            "regulatory_report": restituted_report,
            "chain_verified": receipt.chain_verified
        }


def main():
    print("=" * 70)
    print("📈 Running Financial Trading Surveillance & Crash Recovery Test...")
    print("=" * 70)

    agent = TradingSurveillanceAgent()

    alert_payload = (
        "Surveillance Flag: Unusual block trade TRD-NYC-849102 routed through clearing "
        "custody ACCT-SEC-991203 with secret API clearing key sk-live-9a8b7c6d5e4f. "
        "Compliance officer email: compliance.lead@acmefinance.corp. Notional: $2,500,000."
    )

    print("\n[Phase 1: Ingesting Raw Alert (Simulating Crash at Step 3)]...")
    crash_res = agent.run_investigation(alert_payload, simulate_crash_at_step=3)
    print(f"  • Injected Process Kill:  {crash_res['status']} at Step {crash_res['crashed_at_step']}")

    print("\n[Phase 2: Rehydrating State from SQLite WAL Journal & Resuming]...")
    # Retrieve trace_id from vault session
    trace_id = list(agent.vault.vault._token_map.keys())[0]
    rec_res = agent.resume_after_crash(loop_id=crash_res["loop_id"], trace_id=trace_id)

    print(f"  • Resumed Step Index:     Step {rec_res['resumed_from_step']}")
    print(f"  • Total Steps Completed:  {rec_res['total_steps']}")
    print(f"  • SHA-256 Event Chain:    {rec_res['chain_verified']} (Tamper-Proof Audit)")

    print("\n[Restituted Regulator Surveillance Report]:")
    print(f"  {rec_res['regulatory_report']}")

    # Assertions
    assert "TRD-NYC-849102" in rec_res["regulatory_report"]
    assert "ACCT-SEC-991203" in rec_res["regulatory_report"]
    assert rec_res["chain_verified"] is True
    assert rec_res["total_steps"] == 5

    print("\n" + "=" * 70)
    print("✅ SURVEILLANCE AGENT PASSED: Custom Entity Rules & Crash Recovery Verified")
    print("=" * 70)


if __name__ == "__main__":
    main()
