# ZeroStack: Zero-Dependency Autonomous Agent Runtime & Inference Gateway

[![ZeroStack CI](https://github.com/creativeuncommons/ZeroStack/actions/workflows/ci.yml/badge.svg)](https://github.com/creativeuncommons/ZeroStack/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)
[![Dependencies](https://img.shields.io/badge/dependencies-0%20(Pure%20Stdlib)-brightgreen)](scripts/zerostack-check)
[![Overhead Budget](https://img.shields.io/badge/turn%20latency-<5.0ms-brightgreen)](benchmarks/BENCHMARK_REPORT.md)

**ZeroStack** is an ultra-fast, zero-dependency reference runtime, inference gateway, and autonomous agent stack built exclusively on the **Python standard library**. It unifies five specialized, production-hardened micro-libraries into a cohesive, sub-millisecond execution engine:

1. **ZeroMCP** (`packages/ZeroMCP`): Zero-dependency Model Context Protocol server/client, JSON-RPC 2.0 dispatch, and tool hosting (< 15 µs).
2. **HyperGate** (`packages/HyperGate`): Dynamic BM25 tool pruning across 500+ schemas in < 0.2 ms and semantic caching.
3. **ZeroLeak** (`packages/ZeroLeak`): Reversible in-memory PII/secret de-identification vault (< 60 µs, 1,000-row table in 22 ms, zero disk leakage).
4. **ZeroLoop** (`packages/ZeroLoop`): Event-sourced durable execution state machine with commit-before-step SQLite WAL journaling & crash recovery.
5. **AgentTrace** (`packages/AgentTrace`): W3C distributed tracing, trajectory telemetry, and parent-child span propagation.

> **Looking for quick integration?** See [QUICKSTART.md](QUICKSTART.md) for the **5-Minute Clone & Run guide** and [ENTERPRISE_PLAYBOOK.md](ENTERPRISE_PLAYBOOK.md) for the **Enterprise Architecture, Market Moat Matrix vs. Presidio/LiteLLM/Langfuse, and Turnkey 3-Line Drop-in Adapters**.

---

## 🚀 Turnkey Day 1 Enterprise Quickstart

ZeroStack requires **zero external dependencies** and installs immediately in any Python 3.10+ environment:

```bash
# 1. Install or clone
pip install git+https://github.com/creativeuncommons/ZeroStack.git

# 2. Run 10-point enterprise pre-flight health audit (< 100 ms)
python3 -m zerostack.doctor
```

### 3-Line Turnkey Drop-In Middleware

```python
from openai import OpenAI
from zerostack import wrap_openai

# Wrap any existing OpenAI client in 1 line
client = wrap_openai(OpenAI())

# Outbound prompts are automatically sanitized of PII, tools are pruned via BM25, 
# distributed W3C traces are captured, and responses are transparently unmasked!
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Check ledger for Alice (SSN: 123-45-6789)."}],
    tools=enterprise_tools
)
```

---

## 🏛️ Core Architectural Invariants

- **Zero 3rd-Party Dependencies**: The entire stack, test suites, and examples rely strictly on the Python standard library (`sqlite3`, `json`, `hashlib`, `urllib`, `dataclasses`, `time`, `pathlib`, `uuid`, `ast`, `re`, `bisect`). Zero `pip install` required.
- **Orchestration Overhead Budget**: The cumulative pipeline turn overhead across all 5 systems (`Trace Start` + `Loop Journal` + `Vault Mask` + `BM25 Prune` + `MCP Dispatch` + `Vault Restore` + `Loop Commit` + `Trace Span Close`) executes in **< 5.0 ms** combined latency (measured: **0.655 ms** p50, **1.743 ms** p95).
- **Zero Data Leakage & Fourfold Spillover Defense**: Sensitive credentials, PII, and customer secrets never cross into model prompts or tool discovery indices unmasked. Ephemeral in-memory surrogates (`[SSN_1]`, `[CREDIT_CARD_1]`, `[BEARER_TOKEN_1]`) are reconciled strictly in volatile RAM. Persistent journals and SQLite WAL files contain zero raw sensitive data.
- **High-Density Structured Context Scaling**: Ingests massive tabular contexts (1,000+ rows / 3,000+ entities) in **22.3 ms** via $O(M \log M)$ bisect interval insertion. Post-inference citation unmasking is decoupled from table size, executing in **0.195 ms** (< 1.0 ms SLA).
- **Deterministic Crash Recovery**: Injected hard process kills mid-loop resume from the exact committed step without re-executing non-idempotent tool side-effects or dropping distributed trace lineage.
- **Automated Upstream Submodule Drift Sentinel**: ZeroStack links directly to the five upstream `creativeuncommons` repositories via Git submodules. An automated daily CI drift sentinel updates submodules, executes regression suites across all 5 phases, and prevents broken or drifting community commits from polluting ZeroStack.

---

## 📁 Repository Layout

```
ZeroStack/
├── README.md                              # Comprehensive architectural manual
├── QUICKSTART.md                          # 5-minute integration guide & harness adapters
├── LICENSE                                # Apache 2.0 License
├── .gitmodules                            # Git submodules for all 5 core packages
├── packages/                              # Upstream Git submodules (creativeuncommons)
│   ├── ZeroMCP/                           # Fast-path MCP JSON-RPC protocol server/client
│   ├── HyperGate/                         # Semantic caching & BM25 tool pruning
│   ├── ZeroLeak/                          # PII/Secret vault & prompt injection firewall
│   ├── ZeroLoop/                          # Durable SQLite WAL state machine
│   └── AgentTrace/                        # W3C distributed tracing & telemetry
├── zerostack_loader.py                    # Unified standalone package discovery & loader
├── convergence_agent.py                   # Reference multi-turn autonomous agent
├── examples/                              # Ready-to-run enterprise production architectures
│   ├── README.md                          # Enterprise adoption guide & architecture map
│   ├── 01_central_inference_proxy.py      # Reverse proxy gateway with privacy & tool pruning
│   ├── 02_healthcare_hipaa_agent.py       # Clinical EHR agent with custom MRN/NPI rules
│   ├── 03_customer_support_crm.py         # CRM bot with 200+ tools & refund idempotency
│   ├── 04_rag_document_sanitizer.py       # 500+ row table sanitizer & 0.1 ms citation unmask
│   └── 05_financial_fraud_investigator.py # Trading compliance loop with WAL crash recovery
├── tests/
│   ├── test_phase1_imports.py             # Phase 1: Clean imports & zero 3rd-party deps
│   ├── test_phase2_e2e_agent.py           # Phase 2: Full 5-step financial analysis agent flow
│   ├── test_phase3_fault_injection.py     # Phase 3: Step-3 crash injection & recovery
│   ├── test_phase3_drift_detection.py     # Phase 3: Cross-package API & schema drift audit
│   ├── test_phase4_custom_pii.py          # Phase 4: Custom organizational sensitivity rules
│   └── test_phase5_table_density.py       # Phase 5: High-density tables & spillover defense
├── benchmarks/
│   ├── benchmark_ecosystem.py             # 1,000-iteration microbenchmark runner
│   └── BENCHMARK_REPORT.md                # Unified Markdown benchmark report
└── scripts/
    ├── zerostack-check                    # Comprehensive CI conformance & release sentinel
    └── submodule-sync                     # Automated upstream sync & drift verification
```

---

## 🚀 Quickstart: 5 Minutes to Production

### 1. Clone with Submodules
```bash
git clone --recurse-submodules https://github.com/creativeuncommons/ZeroStack.git
cd ZeroStack
```

### 2. Run Complete Conformance Sentinel (5-second gatekeeper)
Execute the automated gatekeeper to audit zero dependencies, test suites, fault injection, API drift, and latency SLAs:
```bash
./scripts/zerostack-check --audit
```

### 3. Run Test Suites Directly
```bash
python3 -m unittest discover -s tests -p "test_*.py" -v
```

### 4. Run Benchmark Suite (1,000 iterations)
```bash
python3 benchmarks/benchmark_ecosystem.py --iterations 1000
```

---

## 🏢 Enterprise Reference Architectures (`examples/`)

ZeroStack includes five production architectures ready to be deployed as central infrastructure:

| Architecture | Domain | Key Capabilities Demonstrated | Run Command |
| :--- | :--- | :--- | :--- |
| **`01_central_inference_proxy.py`** | **Central LLM Proxy** | Sub-4.0 ms reverse proxy gateway with W3C tracing, PII scrubbing, tool pruning, and audit state logging. | `python3 examples/01_central_inference_proxy.py --test` |
| **`02_healthcare_hipaa_agent.py`** | **Healthcare / Clinical** | HIPAA Safe Harbor de-identification, custom Patient MRN & Physician NPI rules, protected EHR queries. | `python3 examples/02_healthcare_hipaa_agent.py` |
| **`03_customer_support_crm.py`** | **Customer Support / CRM** | Pruning 200+ CRM tools down to top-3 in 0.08 ms; ZeroLoop idempotency preventing duplicate refunds. | `python3 examples/03_customer_support_crm.py` |
| **`04_rag_document_sanitizer.py`** | **Enterprise RAG** | Masking 500-row tables (1,500 entities) in 17 ms; embedding-safe chunks with 0.1 ms citation unmasking. | `python3 examples/04_rag_document_sanitizer.py` |
| **`05_financial_fraud_investigator.py`**| **Trading Compliance** | Institutional Trade IDs, mid-loop hard SIGKILL fault injection, and deterministic WAL recovery. | `python3 examples/05_financial_fraud_investigator.py` |

---

## 📊 Measured Performance Benchmark (1,000 Iterations)

| Component | Metric | Target SLA | Measured p50 | Measured p95 | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **AgentTrace** | Span lifecycle & commit | < 500 μs | **128.5 μs** | **298.2 μs** | 🟢 **PASS** |
| **ZeroLeak (Built-in)** | Small payload mask + vault | < 250 μs | **60.7 μs** | **74.6 μs** | 🟢 **PASS** |
| **ZeroLeak (Custom Rules)** | Custom entity rule resolution | < 250 μs | **54.1 μs** | **66.4 μs** | 🟢 **PASS** |
| **ZeroLeak (Table Dump 60KB)** | 1,000 rows / 3,000 entities | < 50 ms | **22.3 ms** | **25.1 ms** | 🟢 **PASS** |
| **ZeroLeak (Citation Unmask)** | 50 cited entities from 3,000 vault | < 1.0 ms | **0.195 ms** | **0.230 ms** | 🟢 **PASS** |
| **HyperGate (100 tools)** | BM25 Inverted Index Prune | < 0.200 ms | **0.033 ms** | **0.037 ms** | 🟢 **PASS** |
| **HyperGate (500 tools)** | BM25 Inverted Index Prune | < 1.000 ms | **0.138 ms** | **0.167 ms** | 🟢 **PASS** |
| **HyperGate (1,000 tools)** | BM25 Inverted Index Prune | < 2.000 ms | **0.278 ms** | **0.380 ms** | 🟢 **PASS** |
| **ZeroMCP** | Fast-path JSON-RPC 2.0 | < 100 μs | **13.0 μs** | **14.5 μs** | 🟢 **PASS** |
| **ZeroLoop** | WAL Step + Tool + Commit | < 1.000 ms | **0.231 ms** | **0.416 ms** | 🟢 **PASS** |
| **Composite Pipeline Turn** | Cumulative Turn Overhead | **< 5.000 ms** | **0.655 ms** | **1.743 ms** | 🟢 **PASS** |

---

## 🛡️ License

Apache License 2.0. See [LICENSE](LICENSE) for details.
