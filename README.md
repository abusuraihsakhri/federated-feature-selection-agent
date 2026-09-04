# Federated Feature Selection Agent

> **Domain:** Privacy-Preserving Healthcare & Federated Computing
> **Reference Guidelines & Standards:** `HIPAA Safe Harbor §164.514 & Differential Privacy RDP`

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## 📖 What It Does

**Federated Feature Selection Agent** is an analytical and computational platform implementing decentralized mutual information & Lasso multi-omics biomarker ranking across distributed worker agents. Task payloads are evaluated by specialized workers that check metric thresholds, safety boundaries, and protocol conformance, then aggregated into a cryptographically signed consensus dossier.

---

## ⚙️ Architecture

The project contains two coordinated subsystems:

| Package | Role |
|:--------|:-----|
| `agents/` | Core platform — Pydantic models, supervisor orchestrator, specialized workers, PHI guard, HMAC-SHA256 audit trail, FastAPI REST server |
| `fed_feature_selector/` | Frontier engine — dataclass models, domain engine, sub-agent coordinator, alternate CLI/serve entry points |
| `enrichment.py` | Eight domain-specific enrichment engines (secure aggregation, DP budget monitoring, Byzantine resilience, cross-silo selection, privacy-utility visualization, feature compression, HIPAA/GDPR audit, Renyi DP composition) |
| `simulator.py` | High-throughput stress-testing simulator with adversarial PHI injection |
| `web/index.html` | Browser-based operations console |

### Key Modules

- **`agents/supervisor.py`** — `SystemSupervisor` orchestrates worker evaluations and builds consensus dossiers
- **`agents/workers.py`** — `InvariantQCWorker`, `SafetyEscalationWorker`, `ProtocolConformanceWorker`
- **`agents/base.py`** — `PHIGuard` (PHI outbound interceptor), `AuditTrail` / `AuditLogger` (HMAC-SHA256 tamper-evident logs)
- **`agents/models.py`** — Pydantic v2 schemas with input validation
- **`agents/api.py`** — FastAPI REST endpoints
- **`cli.py`** — Primary CLI entry point (`audit`, `chat`, `batch`, `verify-audit`, `serve`)

---

## 💻 Quickstart

### Prerequisites
- Python 3.10, 3.11, or 3.12
- No required runtime dependencies (FastAPI/uvicorn/pydantic/pytest optional for server & tests)

### Install
```bash
pip install fastapi uvicorn pydantic pytest
```

### 1. Guided Interactive Audit
```bash
python cli.py audit
python cli.py audit --task-id TASK-01 --target KEY-01 --primary 28.5 --secondary 14.2 --critical --status DISCORDANT
```

### 2. Supervisory Chat
```bash
python cli.py chat "What standard is applied?"
```

### 3. Batch CSV Processing
```bash
python cli.py batch -i sample.csv -o results.csv
```

### 4. Verify Audit Trail Integrity
```bash
python cli.py verify-audit
```

### 5. Launch REST Server
```bash
python cli.py serve --host 127.0.0.1 --port 8000
```

### Input Data Schema

| Field | Type | Description | Requirement |
|:------|:-----|:------------|:------------|
| `task_id` | string (max 128 chars) | Unique task / case identifier | Required |
| `target_identifier` | string (max 128 chars) | Entity, patient key, or target | Required |
| `primary_metric` | float | Primary domain measurement or score | Required |
| `secondary_metric` | float | Secondary kinetic or confidence score | Optional (default 0.0) |
| `is_critical_flag` | bool | Emergency escalation trigger | Optional (default false) |
| `status_descriptor` | string (max 128 chars) | Status code or phenotype descriptor | Optional (default "NOMINAL") |

---

## 🛡️ Security Architecture

* **Zero-PHI Outbound Interceptor:** Active regex inspection blocking SSNs, MRNs, phone numbers, email addresses, DOBs, and patient identifiers. Raises `SecurityException` on detection.
* **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation. `verify_integrity()` checks **both** chain linkage **and** the HMAC signature of each entry (detects tampering with signatures, chain links, or payload hashes).
* **Input Validation:** All string fields are length-capped (128 chars), whitespace-stripped, and reject embedded control characters.
* **Batch Path Safety:** The `batch` command resolves paths to absolute form and rejects any input or output path that escapes the working directory.
* **No Hardcoded Secrets:** The audit key is read from the `AUDIT_SECRET_KEY` environment variable. If unset, a random ephemeral key is generated per session (with a logged warning) — no static default is embedded in source.

### Environment Variables

| Variable | Purpose | Required |
|:---------|:--------|:---------|
| `AUDIT_SECRET_KEY` | HMAC signing key for the audit trail | Recommended (random key generated if absent) |
| `MODEL_PROVIDER` | LLM provider selection (`mock`, `ollama`, `claude`, `openai`) | No (default `mock`) |

---

## 🧪 Testing & Verification

Run the full automated test suite:

```bash
pytest -v
```

This runs 24 tests covering:
- PHI guard enforcement and email-regex correctness
- Audit-trail HMAC signature verification and tamper detection
- Payload input validation (length limits, control-character rejection, whitespace stripping)
- Batch CLI path-traversal guards and error handling
- Worker evaluations, supervisor consensus, and CLI commands
- Enrichment engine thresholds and suite execution

Execute high-throughput batch simulation benchmarks:

```bash
python simulator.py 1000
```

---

## 🐳 Container Deployment

```bash
docker build -t federated-feature-selection-agent .
docker run -p 8000:8000 -e AUDIT_SECRET_KEY=<your-secret> federated-feature-selection-agent
```

Or with Docker Compose:

```bash
AUDIT_SECRET_KEY=<your-secret> docker compose up
```

> **Important:** Always set `AUDIT_SECRET_KEY` in production. Without it the container generates a random ephemeral key, meaning audit signatures will not survive a restart.

---

## 📄 License

MIT License — see [LICENSE](LICENSE).
