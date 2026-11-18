"""
Phase 3 Test Suite: API Drift Detection & Cross-Package Contract Auditing
========================================================================
Audits:
1. Validates that function signatures, parameters, and return types match
   expected ecosystem contracts across all five packages.
2. Checks JSON-RPC 2.0 and MCP 2024-11-05 wire protocol conformance.
3. Audits W3C traceparent formatting and parsing bidirectional invariants.
4. Asserts that data models (enums, dataclasses, schemas) remain synchronized
   and uncorrupted by code drift.
"""

import unittest
import sys
import inspect
from pathlib import Path

# Add project root to sys.path
TEST_DIR = Path(__file__).resolve().parent
SUITE_ROOT = TEST_DIR.parent
if str(SUITE_ROOT) not in sys.path:
    sys.path.insert(0, str(SUITE_ROOT))

from ecosystem_loader import zeromcp, hypergate, zeroleak, zeroloop, agenttrace


class TestPhase3DriftDetection(unittest.TestCase):
    # --- 1. ZeroMCP Wire & Protocol Contract Audit ---
    def test_01_zeromcp_signatures_and_protocol(self):
        """Audits ZeroMCP function signatures and wire protocol structures."""
        # 1.1 handle_single_request signature
        sig = inspect.signature(zeromcp.handle_single_request)
        params = list(sig.parameters.keys())
        self.assertEqual(params, ["msg"])

        # 1.2 Protocol version conformance
        zeromcp.STATE["phase"] = "UNINITIALIZED"
        init_req = {
            "jsonrpc": "2.0",
            "id": "drift_check_1",
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "drift-auditor", "version": "1.0"}
            }
        }
        res = zeromcp.handle_single_request(init_req)
        self.assertEqual(res.get("jsonrpc"), "2.0")
        self.assertEqual(res.get("id"), "drift_check_1")
        self.assertIn("result", res)
        self.assertEqual(res["result"].get("protocolVersion"), "2024-11-05")
        self.assertIn("serverInfo", res["result"])

    # --- 2. HyperGate ToolPruner & Router Contract Audit ---
    def test_02_hypergate_tool_pruner_contract(self):
        """Audits HyperGate ToolPruner methods, signatures, and schema flexibility."""
        self.assertTrue(hasattr(hypergate, "ToolPruner"))
        pruner_cls = hypergate.ToolPruner

        # Check constructor parameters
        sig = inspect.signature(pruner_cls.__init__)
        params = list(sig.parameters.keys())
        self.assertIn("tools", params)
        self.assertIn("k1", params)
        self.assertIn("b", params)

        # Check prune method signature
        prune_sig = inspect.signature(pruner_cls.prune)
        p_params = list(prune_sig.parameters.keys())
        self.assertIn("prompt_or_messages", p_params)
        self.assertIn("top_k", p_params)
        self.assertIn("enable_toolpacks", p_params)

        # Test schema ingestion for both OpenAI and MCP formats
        openai_tool = {
            "type": "function",
            "function": {
                "name": "calc_tax",
                "description": "Calculates sales tax",
                "parameters": {"type": "object", "properties": {"amount": {"type": "number"}}}
            }
        }
        mcp_tool = {
            "name": "calc_interest",
            "description": "Calculates compound interest",
            "inputSchema": {"type": "object", "properties": {"principal": {"type": "number"}}}
        }
        pruner = pruner_cls([openai_tool, mcp_tool])
        res = pruner.prune("tax on purchases", top_k=1, enable_toolpacks=False)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0].get("function", {}).get("name"), "calc_tax")

    # --- 3. ZeroLeak De-Identification Contract Audit ---
    def test_03_zeroleak_vault_and_masking_contract(self):
        """Audits ZeroLeak mask/unmask signatures and SessionVault operations."""
        mask_sig = inspect.signature(zeroleak.mask)
        self.assertIn("text", list(mask_sig.parameters.keys()))
        self.assertIn("trace_id", list(mask_sig.parameters.keys()))

        unmask_sig = inspect.signature(zeroleak.unmask)
        self.assertIn("text", list(unmask_sig.parameters.keys()))
        self.assertIn("trace_id", list(unmask_sig.parameters.keys()))

        # Audit object masking methods
        self.assertTrue(hasattr(zeroleak.default_engine, "mask_object"))
        self.assertTrue(hasattr(zeroleak.default_engine, "unmask_object"))

        # Verify SessionVault contract
        vault = zeroleak.default_engine.vault
        self.assertTrue(hasattr(vault, "get_or_create_token"))
        self.assertTrue(hasattr(vault, "resolve_token"))
        self.assertTrue(hasattr(vault, "get_session_entries"))

    # --- 4. ZeroLoop Durable Execution Contract Audit ---
    def test_04_zeroloop_durable_loop_contract(self):
        """Audits ZeroLoop DurableLoop methods, enums, and receipt structure."""
        loop_cls = zeroloop.DurableLoop
        sig = inspect.signature(loop_cls.__init__)
        params = list(sig.parameters.keys())
        self.assertIn("loop_id", params)
        self.assertIn("task_name", params)
        self.assertIn("storage_dir", params)

        # Core lifecycle methods
        for method_name in ["start", "step_start", "execute_tool", "step_complete", "complete", "load"]:
            self.assertTrue(hasattr(loop_cls, method_name), f"DurableLoop missing method '{method_name}'")

        # Check Enums
        self.assertTrue(hasattr(zeroloop, "LoopState"))
        expected_states = {"PENDING", "RUNNING", "PAUSED", "COMPLETED", "FAILED"}
        actual_states = {s.name for s in zeroloop.LoopState}
        self.assertTrue(expected_states.issubset(actual_states))

        self.assertTrue(hasattr(zeroloop, "EventType"))
        expected_events = {"LOOP_INIT", "STATE_TRANSITION", "STEP_START", "TOOL_CALL_START", "TOOL_CALL_RESULT", "STEP_COMPLETE", "LOOP_COMPLETE"}
        actual_events = {e.name for e in zeroloop.EventType}
        self.assertTrue(expected_events.issubset(actual_events))

    # --- 5. AgentTrace Telemetry Contract Audit ---
    def test_05_agenttrace_w3c_and_span_contract(self):
        """Audits AgentTrace W3C traceparent formatting and span methods."""
        tracer_cls = agenttrace.AgentTracer
        self.assertTrue(hasattr(tracer_cls, "span"))
        self.assertTrue(hasattr(tracer_cls, "inject_trace_headers"))

        # W3C traceparent round-trip audit
        test_trace_id = "4bf92f3577b34da6a3ce929d0e0e4736"
        test_span_id = "00f067aa0ba902b7"
        tp = agenttrace.format_traceparent(test_trace_id, test_span_id, sampled=True)
        self.assertEqual(tp, f"00-{test_trace_id}-{test_span_id}-01")

        parsed = agenttrace.parse_traceparent(tp)
        self.assertIsNotNone(parsed)
        version, trace_id, span_id, flags = parsed
        self.assertEqual(version, "00")
        self.assertEqual(trace_id, test_trace_id)
        self.assertEqual(span_id, test_span_id)
        self.assertEqual(flags, "01")

        # SpanKind and SpanStatus enums
        self.assertTrue(hasattr(agenttrace, "SpanKind"))
        self.assertTrue(hasattr(agenttrace, "SpanStatus"))
        self.assertIn("AGENT", {k.name for k in agenttrace.SpanKind})
        self.assertIn("TOOL", {k.name for k in agenttrace.SpanKind})
        self.assertIn("OK", {s.name for s in agenttrace.SpanStatus})
        self.assertIn("ERROR", {s.name for s in agenttrace.SpanStatus})


if __name__ == "__main__":
    unittest.main()
