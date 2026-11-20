"""
ZeroStack: Zero-Dependency Enterprise Agent Infrastructure
==========================================================
Unified high-performance agent infrastructure coordinating:
- ZeroLeak: Sub-millisecond PII de-identification & ephemeral token vaults
- HyperGate: BM25 semantic tool pruning & circuit-breaker rate limiting
- ZeroMCP: Low-latency Model Context Protocol JSON-RPC 2.0 tool execution
- ZeroLoop: Durable SQLite WAL state machines with crash rehydration
- AgentTrace: Zero-overhead W3C distributed tracing & OTLP telemetry sinks

100% Python Standard Library. Zero 3rd-Party Dependencies. Air-Gapped Ready.
"""

from zerostack.config import EnterpriseConfig
from zerostack.pipeline import ZeroStackPipeline, ZeroStackSession
from zerostack.middleware import wrap_openai, wrap_anthropic, wrap_llm
from zerostack.doctor import run_doctor_audit
from ecosystem_loader import zeroleak

# Re-export CustomEntityRule for zero-friction sensitivity definitions
CustomEntityRule = zeroleak.CustomEntityRule

__version__ = "1.0.0"
__all__ = [
    "EnterpriseConfig",
    "ZeroStackPipeline",
    "ZeroStackSession",
    "CustomEntityRule",
    "wrap_openai",
    "wrap_anthropic",
    "wrap_llm",
    "run_doctor_audit",
    "__version__",
]
