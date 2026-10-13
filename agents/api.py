"""
FastAPI REST API Server for Federated Feature Selection Agent.
"""
import hmac
import os
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from .base import AuditLogger, PHIGuard, SecurityException
from .models import SystemTaskPayload, ConsensusDossier
from .supervisor import SystemSupervisor

supervisor = SystemSupervisor(model_provider="mock")

app = FastAPI(
    title="Federated Feature Selection Agent API",
    description="Enterprise Distributed Component Platform (Privacy-Preserving Federated Healthcare & FHE)",
    version="3.0.0-ENTERPRISE",
)


class ChatRequest(BaseModel):
    query: str


@app.get("/health")
def health():
    return {"status": "HEALTHY", "service": "federated-feature-selection-agent", "domain": "Privacy-Preserving Federated Healthcare & FHE", "standard": "HIPAA Safe Harbor §164.514 / Google SecAgg Standards", "version": "3.0.0-ENTERPRISE"}


@app.get("/metrics")
def metrics():
    return {
        "dossiers_processed_total": len(supervisor.dossier_registry),
        "audit_blocks_total": len(AuditLogger.get_trail()),
        "system_status": "NOMINAL_OPTIMAL"
    }


@app.post("/api/audit")
def api_audit(payload: SystemTaskPayload):
    try:
        dossier = supervisor.process_task(payload)
    except SecurityException:
        raise HTTPException(status_code=422, detail="Sensitive identifiers are not accepted") from None
    return dossier.to_dict()


@app.post("/api/chat")
def api_chat(req: ChatRequest):
    try:
        ans = supervisor.query_supervisory_chat(req.query)
        return {"response": ans}
    except SecurityException:
        raise HTTPException(status_code=422, detail="Sensitive identifiers are not accepted") from None


@app.get("/api/audit/logs")
def api_audit_logs(x_api_key: Optional[str] = Header(default=None)):
    """Log metadata requires an explicitly configured access token."""
    configured_token = os.getenv("AUDIT_API_TOKEN")
    if not configured_token or not x_api_key or not hmac.compare_digest(configured_token, x_api_key):
        raise HTTPException(status_code=403, detail="Audit log access disabled or unauthorized")
    return {"audit_trail": AuditLogger.get_trail(), "verified": AuditLogger.verify_integrity()}
