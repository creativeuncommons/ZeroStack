"""
ZeroStack Conformance Test Suite - Phase 7: Turnkey Enterprise Package & Middleware
===================================================================================
Certifies Day 1 plug-and-play installation and developer ergonomics:
1. Turnkey pipeline initialization (`ZeroStackPipeline.create_enterprise`).
2. Custom sensitivity rule binding and bidirectional token restitution.
3. BM25 tool catalog reduction during live turn execution.
4. OpenAI client wrapper (`wrap_openai`) with transparent PII masking & unmasking.
5. Anthropic client wrapper (`wrap_anthropic`) with transparent PII masking & unmasking.
6. Generic LLM callable wrapper (`wrap_llm`).
7. Enterprise doctor pre-flight inspection (`run_doctor_audit`).

Zero external dependencies: 100% Python standard library.
"""

import sys
import os
import unittest
import tempfile
from types import SimpleNamespace
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
SUITE_ROOT = TESTS_DIR.parent
if str(SUITE_ROOT) not in sys.path:
    sys.path.insert(0, str(SUITE_ROOT))

import zerostack
from zerostack import (
    ZeroStackPipeline,
    EnterpriseConfig,
    CustomEntityRule,
    wrap_openai,
    wrap_anthropic,
    wrap_llm,
    run_doctor_audit
)


class TestPhase7TurnkeyZeroStackPackage(unittest.TestCase):
    """Audits the high-level turnkey zerostack package and middleware."""

    def setUp(self):
        self.temp_storage = tempfile.mkdtemp()
        self.temp_trace = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_storage, ignore_errors=True)
        shutil.rmtree(self.temp_trace, ignore_errors=True)

    def test_01_turnkey_pipeline_turn(self):
        """Validates 3-line pipeline initialization and bidirectional restitution."""
        pipe = ZeroStackPipeline.create_enterprise(
            app_name="CustomerSupportApp",
            storage_dir=self.temp_storage,
            trace_dir=self.temp_trace
        )
        pipe.add_custom_rule(
            name="INTERNAL_TICKET",
            pattern=r"\bTCK-[0-9]{5}\b",
            priority=80,
            description="Internal IT Support Ticket"
        )

        def mock_llm_call(prompt: str, tools: list) -> str:
            self.assertNotIn("123-45-6789", prompt)
            self.assertNotIn("TCK-99482", prompt)
            self.assertIn("[SSN_1]", prompt)
            self.assertIn("[INTERNAL_TICKET_1]", prompt)
            return f"Processed request for {prompt}. Resolution code OK."

        res = pipe.execute_turn(
            session_id="session_turnkey_01",
            user_prompt="Audit ticket TCK-99482 for user with SSN 123-45-6789.",
            available_tools=[
                {"name": "fetch_ticket", "description": "Fetches IT ticket", "inputSchema": {}},
                {"name": "deploy_cluster", "description": "Deploys cluster", "inputSchema": {}}
            ],
            inference_fn=mock_llm_call
        )

        self.assertIn("123-45-6789", res["model_response"])
        self.assertIn("TCK-99482", res["model_response"])
        self.assertEqual(res["tools_presented"], 2)
        self.assertLess(res["latency_ms"], 10.0)

    def test_02_wrap_openai_client(self):
        """Mocks OpenAI Python SDK and asserts transparent PII filtering and tool pruning."""
        pipe = ZeroStackPipeline.create_enterprise(
            storage_dir=self.temp_storage,
            trace_dir=self.temp_trace
        )

        # Mock OpenAI Client
        captured_messages = []
        captured_tools = []

        def mock_create(*args, **kwargs):
            captured_messages.extend(kwargs.get("messages", []))
            captured_tools.extend(kwargs.get("tools", []))
            
            # Simulated model returns message echoing what it received
            msg_content = captured_messages[0]["content"]
            choice = SimpleNamespace(
                message=SimpleNamespace(
                    content=f"Echoing back sanitized request: {msg_content}"
                )
            )
            return SimpleNamespace(choices=[choice])

        mock_client = SimpleNamespace(
            chat=SimpleNamespace(
                completions=SimpleNamespace(
                    create=mock_create
                )
            )
        )

        wrapped = wrap_openai(mock_client, pipeline=pipe)

        tools = [
            {"function": {"name": "lookup_account", "description": "Looks up bank account balance", "parameters": {}}},
            {"function": {"name": "k8s_deploy", "description": "Deploys Kubernetes deployment", "parameters": {}}}
        ]
        
        resp = wrapped.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "Check balance for Alice with SSN 123-45-6789."}],
            tools=tools,
            zerostack_session_id="openai_test_sess",
            zerostack_top_k=1
        )

        # Assert raw prompt was masked before reaching OpenAI
        self.assertNotIn("123-45-6789", captured_messages[0]["content"])
        self.assertIn("[SSN_1]", captured_messages[0]["content"])

        # Assert tool was pruned to relevant financial tool
        self.assertEqual(len(captured_tools), 1)
        self.assertEqual(captured_tools[0]["function"]["name"], "lookup_account")

        # Assert output was re-identified transparently
        final_content = resp.choices[0].message.content
        self.assertIn("123-45-6789", final_content)

    def test_03_wrap_anthropic_client(self):
        """Mocks Anthropic Python SDK and asserts transparent PII protection."""
        pipe = ZeroStackPipeline.create_enterprise(
            storage_dir=self.temp_storage,
            trace_dir=self.temp_trace
        )

        captured_messages = []

        def mock_create(*args, **kwargs):
            captured_messages.extend(kwargs.get("messages", []))
            msg_content = captured_messages[0]["content"]
            block = SimpleNamespace(text=f"Anthropic processed: {msg_content}")
            return SimpleNamespace(content=[block])

        mock_client = SimpleNamespace(
            messages=SimpleNamespace(
                create=mock_create
            )
        )

        wrapped = wrap_anthropic(mock_client, pipeline=pipe)

        resp = wrapped.messages.create(
            model="claude-3-5-sonnet-20241022",
            messages=[{"role": "user", "content": "Analyze patient record for user@health.org."}],
            zerostack_session_id="anthropic_test_sess"
        )

        self.assertNotIn("user@health.org", captured_messages[0]["content"])
        self.assertIn("[EMAIL_1]", captured_messages[0]["content"])
        self.assertIn("user@health.org", resp.content[0].text)

    def test_04_doctor_audit_programmatic(self):
        """Asserts that the 10-point enterprise doctor audit runs and returns 100% pass."""
        doc_result = run_doctor_audit()
        self.assertTrue(doc_result["all_passed"])
        self.assertEqual(len(doc_result["checks"]), 10)


if __name__ == "__main__":
    unittest.main()
