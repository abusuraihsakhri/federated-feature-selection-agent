# Federated Feature Selection Agent

A Python task-screening prototype with a standalone browser demonstration. The current implementations evaluate **fixed numeric thresholds and status keywords**; they do not calculate mutual information, fit Lasso models, coordinate federated sites, apply differential privacy, or implement secure aggregation.

## Browser demonstration

Open `web/index.html` locally in a modern browser. The page works without a Python server or external dependencies. It evaluates synthetic tasks using the same threshold and priority rules as `agents/workers.py`, displays a JSON result, and can export that result.

- Primary metric **> 25**: elevated alert.
- Secondary metric **> 12**: elevated alert; a critical flag raises the urgency to critical.
- Status containing **DISCORDANT, ANOMALY, MUTANT, VIOLATION, FAIL, or REJECT**: elevated alert.
- The final urgency is the highest observed alert tier.

The browser page does **not** generate HMAC signatures, create persistent audit logs, send task data to an API, or process files on a server. Do not enter real patient identifiers or protected health information.

## Python workflows

Two related implementations are included:

| Location | Purpose |
| --- | --- |
| `agents/`, `cli.py` | Pydantic-validated task screening, worker alerts, in-memory HMAC-linked audit trail, and FastAPI service |
| `fed_feature_selector/` | Separate dataclass-based threshold-screening coordinator and command-line interface |
| `enrichment.py` | Generic threshold evaluations under eight feature names; not functional cryptographic or differential-privacy implementations |
| `simulator.py` | Synthetic task load simulation |
| `web/` | Standalone local browser screening demo and Node.js unit tests |

### Installation

Use Python 3.10–3.12 (the versions exercised in CI):

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[server,test]"
```

Run the primary CLI:

```bash
python cli.py audit --task-id TASK-01 --target SYNTHETIC-01 --primary 28.5 --secondary 14.2 --status DISCORDANT
python cli.py chat "What is the current rule set?"
python cli.py batch -i sample.csv -o results.csv
python simulator.py 100
```

The separate installed command `federated-feature-selection-engine` uses `fed_feature_selector.cli`; its status codes and thresholds differ from the primary CLI. Batch input/output paths must remain inside the current working directory, including after resolving symbolic links. Rejected rows are skipped.

### FastAPI service

```bash
export AUDIT_SECRET_KEY="set-a-random-private-signing-key"
export AUDIT_API_TOKEN="set-a-separate-random-api-token"
python cli.py serve --host 127.0.0.1 --port 8000
```

Endpoints: `GET /health`, `GET /metrics`, `POST /api/audit`, `POST /api/chat`, and `GET /api/audit/logs`. Interactive OpenAPI documentation is available at `/docs`. The audit-logs endpoint requires an `X-API-Key` header matching `AUDIT_API_TOKEN`; it is disabled when that variable is unset.

`AUDIT_SECRET_KEY` is used for in-memory HMAC audit entries. Without it, the process generates an ephemeral random key, and signatures cannot be verified across restarts. The audit history is **not persisted**; running `verify-audit` in a new CLI process does not recover a previous process's history. No authentication is configured for task-submission endpoints, so keep the service on localhost or behind trusted access controls; do not expose it directly to the internet.

The model-provider factory currently returns a deterministic mock for **all** provider names. It does not contact external language-model services and its responses are not expert verification.

### Containers

```bash
AUDIT_SECRET_KEY="set-a-private-key" AUDIT_API_TOKEN="set-a-separate-token" docker compose up --build
```

Compose binds the API to `127.0.0.1:8000` on the host. The Docker image excludes local secret files through `.dockerignore`. Explicitly publishing the container beyond localhost requires separate authentication and transport-security controls.

## Verification

```bash
pytest -v
node --check web/app.js
node --test web/app.test.cjs
```

GitHub Actions runs Python tests on 3.10, 3.11 and 3.12 plus browser-logic tests on Node.js. The static site can be hosted on GitHub Pages without a Python runtime. The FastAPI service and HMAC audit trail require Python and cannot run on GitHub Pages.

## Privacy and limitations

The Python guard scans for a limited set of identifiable text patterns, including recursively nested task metadata. **Regex screening is not de-identification**, and neither it nor an HMAC signature constitutes HIPAA/GDPR certification. Python task and audit data are held in process memory; the browser demo keeps results in its current page session and exports only on user action. Do not use these example screening thresholds for clinical decisions or interpret the code as validated federated feature-selection methodology.

## License

MIT — see [LICENSE](LICENSE).
