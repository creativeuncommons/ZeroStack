# CreativeUnCommons Enterprise Adoption Architecture & Production Examples

This directory provides five ready-to-run, end-to-end production architectures demonstrating how enterprises, financial institutions, and healthcare providers can deploy the CreativeUnCommons ecosystem as their **central infrastructure to support LLM inference and agentic workflows**.

---

## 🏛️ Enterprise Infrastructure Archetypes

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        CENTRAL INFERENCE & AGENTIC INFRASTRUCTURE                      │
├────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                        │
│  [Client Apps / LangChain / CrewAI]       [Healthcare EHRs]       [Trading Desks]      │
│                 │                                │                       │             │
│                 ▼                                ▼                       ▼             │
│  ┌──────────────────────────────────────────────────────────────────────────────────┐  │
│  │                     CENTRAL ENTERPRISE GATEWAY & RUNTIME                         │  │
│  │                                                                                  │  │
│  │   1. PRIVACY FIREWALL (ZeroLeak)                                                 │  │
│  │      • Real-time PII de-identification in < 60 µs (RAM only)                     │  │
│  │      • Custom Organizational Sensitivity Rules (MRNs, Trading IDs, Custody Accts)│  │
│  │      • O(M log M) High-Density Table Ingestion (1,000+ rows in 22 ms)            │  │
│  │                                                                                  │  │
│  │   2. TOOL ROUTING & PRUNING (HyperGate)                                          │  │
│  │      • BM25 dynamic pruning across 500+ tools in < 0.2 ms                        │  │
│  │      • Semantic context caching (slashes LLM token costs by 40-70%)              │  │
│  │                                                                                  │  │
│  │   3. DURABLE STATE & IDEMPOTENCY (ZeroLoop)                                      │  │
│  │      • Commit-before-step SQLite WAL journaling (< 0.25 ms)                      │  │
│  │      • Deterministic crash recovery with zero duplicate side-effects (e.g. no    │  │
│  │        double refunds)                                                           │  │
│  │                                                                                  │  │
│  │   4. TOOL PROTOCOL & DISPATCH (ZeroMCP)                                          │  │
│  │      • Fast-path JSON-RPC 2.0 tool execution (< 15 µs dispatch)                  │  │
│  │      • Protected in-process parameter restitution (@vault.protect_tool)          │  │
│  │                                                                                  │  │
│  │   5. DISTRIBUTED TELEMETRY (AgentTrace)                                          │  │
│  │      • W3C traceparent propagation (00-{trace_id}-{span_id}-01)                  │  │
│  │      • Sub-millisecond span lifecycle & audit receipts                           │  │
│  └──────────────────────────────────────────────────────────────────────────────────┘  │
│                 │ (Sanitized prompts only)                                             │
│                 ▼                                                                      │
│  [Cloud LLM APIs (OpenAI / Anthropic / Bedrock) OR Local vLLM / Ollama]                 │
│                                                                                        │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 📁 Reference Examples Directory

| Example Script | Enterprise Domain | Key Capabilities Demonstrated | Run Command |
| :--- | :--- | :--- | :--- |
| **`01_central_inference_proxy.py`** | **Central LLM Proxy** | Standalone reverse proxy gateway (OpenAI/Anthropic compatible) with PII stripping, tool pruning, W3C telemetry, and restitution. | `python3 examples/01_central_inference_proxy.py --test` |
| **`02_healthcare_hipaa_agent.py`** | **Healthcare / Clinical** | HIPAA Safe Harbor de-identification, custom Medical Record Number (`PATIENT_MRN`) & Physician NPI rules, protected EHR queries. | `python3 examples/02_healthcare_hipaa_agent.py --test` |
| **`03_customer_support_crm.py`** | **CRM & Customer Service** | High-volume support desk with 200+ tools, BM25 tool pruning in < 0.1 ms, and ZeroLoop idempotency preventing double-refunds. | `python3 examples/03_customer_support_crm.py --test` |
| **`04_rag_document_sanitizer.py`** | **Enterprise RAG / Vector Stores** | Pre-processing massive 500+ row tabular datasets (1,500 entities) in 17 ms; embedding-safe chunks with 0.1 ms citation unmasking. | `python3 examples/04_rag_document_sanitizer.py --test` |
| **`05_financial_fraud_investigator.py`**| **Trading Compliance** | Multi-step market surveillance loop with proprietary Trade IDs (`TRD-XXX`), mid-loop crash injection, and deterministic WAL recovery. | `python3 examples/05_financial_fraud_investigator.py --test` |

---

## 🚀 How to Run the Examples

All examples rely strictly on the **Python standard library** with zero external pip dependencies. You can run all of them immediately after cloning:

```bash
# Example 1: Test the Central LLM Gateway
python3 examples/01_central_inference_proxy.py --test

# Example 2: Test the Healthcare HIPAA Agent
python3 examples/02_healthcare_hipaa_agent.py

# Example 3: Test Customer Support with 200+ Tools & Idempotency
python3 examples/03_customer_support_crm.py

# Example 4: Test Tabular RAG Ingestion & Instant Citation Restitution
python3 examples/04_rag_document_sanitizer.py

# Example 5: Test Financial Surveillance with Crash Recovery
python3 examples/05_financial_fraud_investigator.py
```

---

## 🏢 Enterprise Adoption Roadmap

### 1. Central Inference Gateway Deployment
Deploy `01_central_inference_proxy.py` inside your Kubernetes cluster or container mesh. Point your team's LangChain, AutoGen, or custom applications to `http://gateway-internal:8080/v1/chat/completions`. All traffic outbound to external model providers will be automatically de-identified, audited, and traced.

### 2. Custom Organizational Entity Rule Packs
Centralize enterprise-specific regex patterns, Shannon entropy thresholds, and check-digit validators in `/etc/zeroleak/enterprise_rules.json`:
```json
{
  "rules": [
    {
      "name": "PATIENT_MRN",
      "pattern": "\\bMRN-[0-9]{4}-[0-9]{4}\\b",
      "priority": 75,
      "description": "Hospital medical record number"
    },
    {
      "name": "INTERNAL_TRADE_ID",
      "pattern": "\\bTRD-[A-Z]{3}-[0-9]{6}\\b",
      "priority": 80,
      "description": "Institutional trade ticket ID"
    }
  ]
}
```
Set `export ZEROLEAK_CUSTOM_RULES_PATH="/etc/zeroleak/enterprise_rules.json"`. Every gateway instance and agent runner automatically ingests these rules without code changes.

### 3. Tool Pruning at Enterprise Scale
When cataloging hundreds of enterprise microservices in your agent ecosystem, load your tool definitions into `hypergate.ToolPruner`. HyperGate scores schemas via an in-memory BM25 inverted index in **< 0.15 ms**, eliminating the token overhead, latency, and model confusion of passing 200+ tools into an LLM context.

### 4. Zero Data Leakage & Durability Guarantee
* **Volatile RAM Vault**: Sensitive entity pairs are never written to disk, swap partitions, or error logs (`zero_disk_leakage = true`).
* **Cryptographic Event Journal**: ZeroLoop journals step states in SQLite WAL before execution. If a node fails or crashes, agents rehydrate and resume without repeating non-idempotent operations.
