# ZeroStack: 5-Minute Quickstart & Integration Manual

Welcome to **ZeroStack**. This guide will take you from zero to a production-ready, leak-proof, durable autonomous agent pipeline in under five minutes.

---

## ⏱️ 5-Minute "Clone & Run" Walkthrough

### 1. Requirements
* **Python 3.9+**
* **Zero 3rd-Party Dependencies** (`pip install` is never required; uses 100% Python standard library).

### 2. Verify Your Environment in 5 Seconds
```bash
# Clone the repository with all submodules
git clone --recurse-submodules https://github.com/creativeuncommons/ZeroStack.git
cd ZeroStack

# Run the automated conformance sentinel (audits imports, runs 25 tests, fault injection, & microbenchmarks)
./scripts/zerostack-check --audit
```
If you see `🎉 ALL ZEROSTACK CONVERGENCE GATES PASSED (100% PRODUCTION READY)`, your machine is completely configured.

---

## 🔌 The Minimal Integration: "Connect 3 Pipes" (< 15 Lines)

If you already have an existing agent or LLM loop and simply want **instant PII/secret protection** and **sub-millisecond tool pruning**, you only need to connect three minimal pipes:

### Pipe Architecture Overview
```
┌────────────────┐      Pipe 1: mask()      ┌─────────────────────────┐
│ Raw User Prompt├─────────────────────────►│ Clean Surrogate Prompt  │
└────────────────┘                          └────────────┬────────────┘
                                                         │
                                                         ▼
                                            ┌─────────────────────────┐
                                            │ LLM (OpenAI / Claude /  │
                                            │ Ollama / Local Models)  │
                                            └────────────┬────────────┘
                                                         │
┌────────────────┐     Pipe 2: unmask()     ┌────────────▼────────────┐
│ Authentic Text │◄─────────────────────────┤ LLM Output with Tokens  │
└────────────────┘                          └─────────────────────────┘
```

### The 15-Line Drop-in Snippet
```python
from ecosystem_loader import zeroleak, hypergate

# 1. Initialize engines (zero disk overhead, pure RAM)
vault = zeroleak.ZeroLeak()
pruner = hypergate.ToolPruner()  # Registers your tool catalog

# Pipe 1: Mask raw prompt before sending to any cloud LLM
raw_prompt = "Process invoice for user alice@acme.com, SSN 123-45-6789, API key sk-live-99a8b7c6d5e4."
trace_id = "sess_001"
clean_prompt = vault.mask(raw_prompt, trace_id=trace_id)
# clean_prompt -> "Process invoice for user [EMAIL_1], SSN [SSN_1], API key [API_KEY_1]."

# Pipe 2: Prune 500+ tool schemas down to the top-5 in 0.13 ms
active_tools = pruner.prune(clean_prompt, top_k=5)

# (Invoke your LLM of choice here using clean_prompt and active_tools)
mock_llm_response = "Verified client [EMAIL_1] with SSN [SSN_1]. Balance is $5,000."

# Pipe 3: Restitute tokens back to authentic data for display or internal execution
final_output = vault.unmask(mock_llm_response, trace_id=trace_id)
# final_output -> "Verified client alice@acme.com with SSN 123-45-6789. Balance is $5,000."
```

---

## 🧩 Harness Adapters: Connecting to Common Agent Frameworks

### 1. LangChain / LangGraph Adapter

Connect ZeroLeak and ZeroLoop directly via standard LangChain Callbacks and Tool wrappers:

```python
from langchain.callbacks.base import BaseCallbackHandler
from langchain.tools import tool
from ecosystem_loader import zeroleak, zeroloop

class ZeroLeakCallbackHandler(BaseCallbackHandler):
    """Intercepts prompts and outputs across LangChain chains."""
    def __init__(self, trace_id: str):
        self.vault = zeroleak.ZeroLeak()
        self.trace_id = trace_id

    def on_llm_start(self, serialized, prompts, **kwargs):
        # Mask every prompt crossing the network boundary
        for i, prompt in enumerate(prompts):
            prompts[i] = self.vault.mask(prompt, trace_id=self.trace_id)

    def on_llm_end(self, response, **kwargs):
        # Unmask completions for client presentation
        for generations in response.generations:
            for gen in generations:
                gen.text = self.vault.unmask(gen.text, trace_id=self.trace_id)

# Protecting LangChain Tools against surrogate parameter injection:
# @vault.protect_tool unmasks surrogate parameters for internal execution,
# then defangs and re-masks outputs before sending back to LLM context:
@tool
@vault.protect_tool
def execute_bank_transfer(client_email: str, amount: float, _trace_id: str = "sess_001") -> str:
    """Internal tool receives authentic email (e.g. alice@acme.com), not [EMAIL_1]."""
    return f"Transferred ${amount} to {client_email}"
```

### 2. CrewAI Interceptor

Wrap your CrewAI task runners to ensure tasks execute with complete privacy and crash durability:

```python
from crewai import Agent, Task, Crew
from ecosystem_loader import zeroleak, zeroloop

vault = zeroleak.ZeroLeak()

def privacy_wrapped_task(raw_description: str, session_id: str, agent: Agent) -> str:
    # 1. Pre-mask sensitive customer records
    sanitized_description = vault.mask(raw_description, trace_id=session_id)
    
    # 2. Run standard CrewAI Task
    task = Task(description=sanitized_description, expected_output="Audit summary", agent=agent)
    crew = Crew(agents=[agent], tasks=[task])
    raw_crew_result = crew.kickoff()
    
    # 3. Post-restitute cited records
    return vault.unmask(str(raw_crew_result), trace_id=session_id)
```

### 3. Native Custom Loop with ZeroLoop Crash Resilience

For autonomous agents running multi-step tool graphs, wrap the turn loop in `ZeroLoop`:

```python
import os
from ecosystem_loader import zeroloop, zeroleak

loop_id = "agent_investigation_01"
storage_dir = "./state"
db_path = os.path.join(storage_dir, f"{loop_id}.db")

# Start or resume after crash
if os.path.exists(db_path):
    loop = zeroloop.DurableLoop.load(loop_id=loop_id, storage_dir=storage_dir)
else:
    loop = zeroloop.DurableLoop(loop_id=loop_id, storage_dir=storage_dir)
    loop.start()

vault = zeroleak.ZeroLeak()

for step_idx in range(loop.step_idx, 5):
    # Step commit-before-execution
    loop.step_start(step_name=f"step_{step_idx}", inputs={"task": "inspect_balance"})
    
    # Tool execution with idempotency caching & input unpacking
    result = loop.execute_tool(
        tool_name="query_account",
        tool_fn=lambda token: {"balance": 1500, "client": token},
        inputs={"token": "[EMAIL_1]"}
    )
    
    loop.step_complete(outputs={"result": result})

receipt = loop.complete(final_output="Investigation successful")
loop.close()
```

---

## 🏛️ Maximal Enterprise Architecture (All 5 Packages Synchronized)

In an enterprise deployment, all five packages operate in lockstep, guaranteeing zero PII leakage, high throughput, durable state recovery, and complete W3C telemetry:

```
                              ┌────────────────────────────────────────┐
                              │       Inbound User Interaction         │
                              └───────────────────┬────────────────────┘
                                                  │ (Raw prompt with PII)
                                                  ▼
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│ 1. AgentTrace: Spawns root trace & injects canonical W3C traceparent (00-{trace_id}-{span_id}-01)│
└─────────────────────────────────────────────────┬────────────────────────────────────────────────┘
                                                  │
                                                  ▼
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│ 2. ZeroLoop: Instantiates DurableLoop; commits genesis event to SQLite WAL journal               │
└─────────────────────────────────────────────────┬────────────────────────────────────────────────┘
                                                  │
                                                  ▼
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│ 3. ZeroLeak: Tokenizes PII/Secrets into [SURROGATE_ID] in volatile RAM vault (0 disk leakage)    │
└─────────────────────────────────────────────────┬────────────────────────────────────────────────┘
                                                  │ (Sanitized prompt only)
                                                  ▼
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│ 4. HyperGate: BM25 Inverted Index prunes 1,000 tool schemas down to top-5 tools in 0.13 ms      │
└─────────────────────────────────────────────────┬────────────────────────────────────────────────┘
                                                  │ (Top-5 tools + sanitized prompt)
                                                  ▼
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│ 5. Model Inference: LLM processes prompt and issues tool call using synthetic parameters         │
└─────────────────────────────────────────────────┬────────────────────────────────────────────────┘
                                                  │
                                                  ▼
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│ 6. ZeroMCP: Dispatches JSON-RPC 2.0 tool execution; ZeroLeak restores parameters in-process      │
└─────────────────────────────────────────────────┬────────────────────────────────────────────────┘
                                                  │
                                                  ▼
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│ 7. ZeroLoop: Commits tool output; verifies SHA-256 hash chain and idempotency deduplication      │
└─────────────────────────────────────────────────┬────────────────────────────────────────────────┘
                                                  │
                                                  ▼
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│ 8. ZeroLeak: Restitutes citations in final synthesis; AgentTrace closes span and flushes receipt│
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🏢 Customizing for Your Organization

### 1. Adding Bespoke PII & Sensitive Entity Rules

Enterprises often possess proprietary identifiers that generic PII detectors ignore (e.g. Medical Record Numbers, Internal Clearing IDs, Custom API Keys).

#### Option A: Declarative JSON Rule Pack (Zero Code)
Create `enterprise_rules.json`:
```json
{
  "rules": [
    {
      "name": "PATIENT_MRN",
      "pattern": "\\bMRN-[0-9]{4}-[0-9]{4}\\b",
      "priority": 70,
      "description": "Hospital medical record number"
    },
    {
      "name": "INTERNAL_TRADE_ID",
      "pattern": "\\bTRD-[A-Z]{3}-[0-9]{6}\\b",
      "priority": 75,
      "description": "Internal institutional trade identifier"
    }
  ]
}
```
Set the environment variable:
```bash
export ZEROLEAK_CUSTOM_RULES_PATH="/etc/zeroleak/enterprise_rules.json"
```
Every `ZeroLeak()` engine instantiated in your infrastructure will automatically ingest, validate, and schedule these rules.

#### Option B: Programmatic Rules with Custom Algorithmic Validators
```python
from ecosystem_loader import zeroleak

def luhn_or_checksum_validator(val: str) -> bool:
    # Custom business logic (e.g. check digits summing to multiple of 10)
    digits = [int(c) for c in val if c.isdigit()]
    return len(digits) > 0 and sum(digits) % 10 == 0

engine = zeroleak.ZeroLeak()
engine.register_custom_rule(
    zeroleak.CustomEntityRule(
        name="CUSTOM_CLIENT_TOKEN",
        pattern=r"\bcli_[A-Za-z0-9]{16}\b",
        validator=luhn_or_checksum_validator,
        entropy_threshold=3.0,  # Rejects predictable dummy tokens
        priority=80
    )
)

# Ingest prompt containing the custom token (digits 9+8+2+1=20 satisfy validator):
# clean_prompt = engine.mask("Client ID: cli_9aK8bLmPqvW1zY2a", trace_id="sess_001")
# -> "Client ID: [CUSTOM_CLIENT_TOKEN_1]"
```

---

## 🛡️ Edge Cases & Production Troubleshooting

| Issue / Symptom | Root Cause | Recommended Fix |
| :--- | :--- | :--- |
| **`[TOKEN_1]` appears in user output** | Mismatched `trace_id` passed to `unmask()` | Ensure the exact `trace_id` generated during `mask()` is forwarded across the pipeline. Cross-tenant lookups deliberately fail closed to prevent data leaks. |
| **Domain not masked (`user@example.com`)** | Domain is in default allowlist | `example.com`, `localhost`, and `test.com` are allowlisted by default. Override via `export ZEROLEAK_ALLOWLIST="mydomain.com"` or pass `allowlist=set()` to the constructor. |
| **Table ingestion slower than expected** | Regex back-tracking or nested spans | ZeroLeak uses $O(M \log M)$ bisect interval insertion. Ensure custom regexes avoid catastrophic backtracking (e.g. `(a+)+`). |
| **Loop resumes from prior step after crash** | Expected crash-recovery behavior | `ZeroLoop` automatically rehydrates state from the SQLite WAL journal. Inspect `receipt.duplicate_tool_calls_prevented` to verify idempotency protection. |
| **Tool schema window exceeded** | Too many schemas sent to LLM | Use `hypergate.ToolPruner(schemas).prune(prompt, top_k=5)` to keep tool context below 1,000 tokens while searching 500+ schemas. |

---

## 📜 Conformance & Auditing Checklist

Before deploying your agentic harness to staging or production, run the automated verification suite:

- [ ] Run `./scripts/zerostack-check --audit` to confirm zero dependency conflicts and SLA adherence.
- [ ] Run `python3 -m unittest discover -s tests -p "test_*.py"` to verify all 5 phases pass.
- [ ] Verify `zero_disk_leakage = true` in the generated audit receipt.
- [ ] Ensure SQLite WAL journal directory has appropriate POSIX permissions (`chmod 700 ./state`).
