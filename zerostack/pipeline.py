"""
ZeroStack High-Performance Production Pipeline
=============================================
Unified enterprise orchestration coordinating:
1. ZeroLeak: Sub-millisecond pre-inference PII/secret masking and vault mapping.
2. HyperGate: BM25 semantic tool pruning (reducing token context costs by 40-70%).
3. ZeroMCP: Zero-overhead Model Context Protocol JSON-RPC 2.0 tool execution.
4. ZeroLoop: Commit-before-step durable SQLite WAL state machine with crash rehydration.
5. AgentTrace: Distributed W3C traceparent logging and OTLP telemetry sinks.

Zero external dependencies: 100% Python standard library.
"""

import os
import sys
import time
import json
import uuid
from typing import Dict, Any, List, Optional, Callable, Tuple
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent
REPO_ROOT = PACKAGE_DIR.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ecosystem_loader import zeromcp, hypergate, zeroleak, zeroloop, agenttrace
from zerostack.config import EnterpriseConfig

MAX_INPUT_CHARS = 2_000_000

def take_bounded_slice(text: str, max_chars: int = MAX_INPUT_CHARS) -> str:
    """Defensive stream ingestion bounds: takes a safe slice to prevent memory exhaustion."""
    if len(text) > max_chars:
        return text[:max_chars]
    return text


class ZeroStackSession:
    """Manages state, masking, and tracing for an individual execution session."""

    def __init__(self, pipeline: "ZeroStackPipeline", session_id: str):
        self.pipeline = pipeline
        self.session_id = session_id
        self.root_span = None
        self.trace_id = None
        self.root_span_id = None
        self.w3c_traceparent = None
        self.loop = None
        self.step_idx = 0

    def __enter__(self):
        # 1. Start root telemetry span
        self.span_ctx = self.pipeline.tracer.span(
            f"{self.pipeline.config.app_name}.turn",
            kind=agenttrace.SpanKind.AGENT
        )
        self.root_span = self.span_ctx.__enter__()
        self.trace_id = self.root_span.trace_id
        self.root_span_id = self.root_span.span_id
        self.w3c_traceparent = agenttrace.format_traceparent(self.trace_id, self.root_span_id)
        self.root_span.set_attribute("session_id", self.session_id)
        self.root_span.set_attribute("w3c.traceparent", self.w3c_traceparent)

        # 2. Initialize durable loop if enabled
        if self.pipeline.config.enable_wal_journal:
            self.loop = zeroloop.DurableLoop(
                loop_id=self.session_id,
                task_name=self.pipeline.config.app_name,
                storage_dir=self.pipeline.config.storage_dir
            )
            self.loop.journal.set_meta("traceparent", self.w3c_traceparent)
            self.loop.journal.set_meta("trace_id", self.trace_id)
            self.loop.start()

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if self.loop and self.loop.state != zeroloop.LoopState.COMPLETED:
                if exc_type is None:
                    self.loop.complete(final_output="Session turn finished cleanly")
                else:
                    self.loop.journal.close()
        finally:
            if self.span_ctx:
                if exc_type:
                    self.root_span.set_attribute("error", True)
                    self.root_span.set_attribute("error.message", str(exc_val))
                self.span_ctx.__exit__(exc_type, exc_val, exc_tb)

    def mask(self, text: str) -> str:
        """De-identifies sensitive entities into type-aware surrogate tokens."""
        return self.pipeline.vault.mask(text, trace_id=self.trace_id)

    def unmask(self, text: str) -> str:
        """Restitutes surrogate tokens back to their raw values in-memory."""
        return self.pipeline.vault.unmask(text, trace_id=self.trace_id)

    def prune_tools(
        self,
        query: str,
        tools: List[Dict[str, Any]],
        top_k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Filters a large tool catalog to the top-K semantically relevant tools via BM25."""
        if not self.pipeline.config.enable_bm25_pruning or not tools:
            return tools

        k = top_k or self.pipeline.config.default_top_k_tools
        pruner = hypergate.ToolPruner(tools)
        return pruner.prune(query, top_k=k, enable_toolpacks=self.pipeline.config.enable_toolpacks)

    def execute_mcp_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Executes a tool call via fast-path ZeroMCP JSON-RPC."""
        self.step_idx += 1
        with self.pipeline.tracer.span(
            f"tool.{tool_name}",
            kind=agenttrace.SpanKind.TOOL,
            trace_id=self.trace_id,
            parent_span_id=self.root_span_id
        ) as tspan:
            tspan.set_attribute("tool.name", tool_name)
            
            # Commit before step in durable loop
            step_meta = None
            if self.loop:
                step_meta = self.loop.step_start(
                    step_name=f"step_{self.step_idx}_{tool_name}",
                    tool_name=tool_name,
                    inputs=arguments
                )
                if step_meta.get("cached"):
                    return step_meta["cached_output"]

            # Dispatch via ZeroMCP
            rpc_req = {
                "jsonrpc": "2.0",
                "id": self.step_idx,
                "method": "tools/call",
                "params": {"name": tool_name, "arguments": arguments}
            }
            resp = zeromcp.handle_single_request(rpc_req)
            if "error" in resp:
                raise RuntimeError(f"ZeroMCP tool execution error for '{tool_name}': {resp['error']}")

            res_content = resp.get("result", {})
            
            # Commit result to durable journal
            if self.loop and step_meta:
                self.loop.step_complete(outputs=res_content)

            return res_content


class ZeroStackPipeline:
    """Enterprise-grade coordinator for the ZeroStack software suite."""

    def __init__(self, config: Optional[EnterpriseConfig] = None):
        self.config = config or EnterpriseConfig()

        # Initialize AgentTrace
        self.tracer = agenttrace.AgentTracer(
            service_name=self.config.app_name,
            storage_dir=self.config.trace_dir
        )

        # Persistent ZeroLeak instance preserving in-memory vault across turn lifecycle
        self._vault = None
        self._init_vault()

    def _init_vault(self):
        if self.config.custom_rules:
            self._vault = zeroleak.ZeroLeak(custom_rules=self.config.custom_rules)
        else:
            self._vault = zeroleak.ZeroLeak()

    @property
    def vault(self):
        if self._vault is None:
            self._init_vault()
        return self._vault

    @classmethod
    def create_enterprise(
        cls,
        app_name: str = "EnterpriseAgent",
        custom_rules: Optional[List[zeroleak.CustomEntityRule]] = None,
        storage_dir: Optional[str] = None,
        trace_dir: Optional[str] = None
    ) -> "ZeroStackPipeline":
        """Factory constructor for zero-boilerplate enterprise initialization."""
        cfg = EnterpriseConfig(
            app_name=app_name,
            storage_dir=storage_dir,
            trace_dir=trace_dir,
            custom_rules=custom_rules or []
        )
        return cls(cfg)

    def add_custom_rule(
        self,
        name: str,
        pattern: str,
        priority: int = 50,
        entropy_threshold: Optional[float] = None,
        description: str = ""
    ) -> "ZeroStackPipeline":
        """Registers a custom organization-specific sensitivity rule and updates the vault."""
        self.config.add_custom_rule(
            name=name,
            pattern=pattern,
            priority=priority,
            entropy_threshold=entropy_threshold,
            description=description
        )
        self._init_vault()
        return self

    def session(self, session_id: Optional[str] = None) -> ZeroStackSession:
        """Creates an execution context for an individual multi-turn agent interaction."""
        sid = session_id or f"session_{uuid.uuid4().hex[:12]}"
        return ZeroStackSession(self, sid)

    def execute_turn(
        self,
        session_id: str,
        user_prompt: str,
        available_tools: Optional[List[Dict[str, Any]]] = None,
        inference_fn: Optional[Callable[[str, List[Dict[str, Any]]], str]] = None
    ) -> Dict[str, Any]:
        """
        Executes a complete turnkey agent turn with pre-inference masking,
        BM25 tool pruning, durable execution commit, inference, and post-inference re-identification.
        """
        t0 = time.perf_counter()
        safe_input = take_bounded_slice(user_prompt)
        with self.session(session_id) as sess:
            # 1. Pre-inference masking
            masked_prompt = sess.mask(safe_input)

            # 2. BM25 tool pruning
            pruned_tools = sess.prune_tools(masked_prompt, available_tools or [])

            # 3. Model Inference (if callable provided)
            raw_model_response = ""
            if inference_fn:
                raw_model_response = inference_fn(masked_prompt, pruned_tools)
            else:
                raw_model_response = f"Simulated response acknowledging: {masked_prompt}"

            # 4. Post-inference re-identification
            clean_output = sess.unmask(raw_model_response)

            duration_ms = (time.perf_counter() - t0) * 1000.0

            return {
                "session_id": session_id,
                "trace_id": sess.trace_id,
                "w3c_traceparent": sess.w3c_traceparent,
                "masked_prompt": masked_prompt,
                "tools_presented": len(pruned_tools),
                "model_response": clean_output,
                "latency_ms": round(duration_ms, 3)
            }
