"""
Focused tests for security hardening and reliability improvements:
  - Email PHI regex correctness
  - Audit-trail HMAC signature verification (tamper detection)
  - Payload input validation (length & control-character rejection)
  - Batch CLI path-traversal guard and error handling
  - Enrichment engine deduplication & threshold escalation
"""
import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import tempfile

from agents.base import PHIGuard, AuditTrail, AuditLogger, SecurityException
from agents.models import SystemTaskPayload, UrgencyLevel
from cli import main


# ---------------------------------------------------------------------------
# PHI guard — email regex correctness
# ---------------------------------------------------------------------------
def test_phi_guard_catches_email():
    """A standard email address must be flagged as PHI."""
    with pytest.raises(SecurityException):
        PHIGuard.assert_no_phi("Contact patient at john.doe@example.com please")


def test_phi_guard_allows_clean_text():
    """Normal operational text must pass the PHI guard."""
    PHIGuard.assert_no_phi("Specimen KEY-001 assay result nominal within bounds")


def test_phi_guard_redacts_email():
    """Redaction must replace the email token, not leak it."""
    redacted = PHIGuard.redact_phi("Reach alice@hospital.org for results")
    assert "alice@hospital.org" not in redacted
    assert "[REDACTED_IDENTIFIER]" in redacted


# ---------------------------------------------------------------------------
# Audit trail — HMAC signature verification
# ---------------------------------------------------------------------------
def test_audit_trail_verifies_signatures():
    """verify_integrity must validate the HMAC, not just chain linkage."""
    trail = AuditTrail(secret_key="test-key")
    entry = trail.log("tester", "test_tier", "EVENT", {"k": "v"})
    assert trail.verify_integrity() is True
    assert entry["current_hash"] != ""


def test_audit_trail_detects_tampered_signature():
    """Flipping a bit in a stored signature must fail verification."""
    trail = AuditTrail(secret_key="test-key")
    trail.log("tester", "test_tier", "EVENT", {"k": "v"})
    # Tamper with the stored signature
    trail.logs[0]["current_hash"] = "deadbeef00000000000000000000000000000000"
    assert trail.verify_integrity() is False


def test_audit_trail_detects_tampered_chain():
    """Rewriting a prev_hash link must fail verification."""
    trail = AuditTrail(secret_key="test-key")
    trail.log("tester", "test_tier", "E1", {"k": "v"})
    trail.log("tester", "test_tier", "E2", {"k": "v"})
    # Break the chain
    trail.logs[1]["prev_hash"] = "broken_link_hash_value_0000000000"
    assert trail.verify_integrity() is False


def test_audit_trail_detects_tampered_payload_hash():
    """Changing the payload_hash after signing must fail signature verification."""
    trail = AuditTrail(secret_key="test-key")
    trail.log("tester", "test_tier", "EVENT", {"k": "v"})
    trail.logs[0]["payload_hash"] = "tampered_payload_hash_0000000000000"
    assert trail.verify_integrity() is False


# ---------------------------------------------------------------------------
# Payload input validation
# ---------------------------------------------------------------------------
def test_payload_rejects_overlong_task_id():
    """task_id exceeding max_length must be rejected."""
    with pytest.raises(Exception):
        SystemTaskPayload(task_id="X" * 256, target_identifier="T", primary_metric=1.0)


def test_payload_rejects_control_characters():
    """Embedded control characters in string fields must be rejected."""
    with pytest.raises(Exception):
        SystemTaskPayload(task_id="bad\x00id", target_identifier="T", primary_metric=1.0)


def test_payload_strips_whitespace():
    """Leading/trailing whitespace should be stripped from string fields."""
    p = SystemTaskPayload(task_id="  OK-01  ", target_identifier="  KEY  ", primary_metric=1.0)
    assert p.task_id == "OK-01"
    assert p.target_identifier == "KEY"


def test_payload_accepts_valid_input():
    """A well-formed payload must construct without error."""
    p = SystemTaskPayload(task_id="TASK-01", target_identifier="KEY-01", primary_metric=12.0, secondary_metric=4.0)
    assert p.task_id == "TASK-01"
    assert p.primary_metric == 12.0


# ---------------------------------------------------------------------------
# Batch CLI — path traversal guard & error handling
# ---------------------------------------------------------------------------
def test_batch_rejects_outside_working_directory(tmp_path, capsys):
    """Batch must refuse to read/write outside the working directory."""
    # Create a file outside tmp_path's parent to simulate traversal
    outside = tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, dir=tempfile.gettempdir())
    outside.write("task_id,target_identifier,primary_metric\nEXT-01,K,10.0\n")
    outside.flush()
    outside.close()
    try:
        with pytest.raises(SystemExit):
            main(["batch", "-i", outside.name, "-o", "out.csv"])
    finally:
        os.unlink(outside.name)


def test_batch_handles_missing_input_file():
    """A missing input file must exit cleanly, not raise an unhandled exception."""
    with pytest.raises(SystemExit):
        main(["batch", "-i", "does_not_exist_xyz.csv", "-o", "out.csv"])


def test_batch_skips_invalid_rows(tmp_path, capsys):
    """Rows with unparseable numeric fields must be skipped, not crash the batch."""
    inp = tmp_path / "in.csv"
    out = tmp_path / "out.csv"
    inp.write_text(
        "task_id,target_identifier,primary_metric,secondary_metric\n"
        "OK-01,KEY-01,10.0,4.0\n"
        "BAD-01,KEY-02,not_a_number,4.0\n"
    )
    # Change cwd so the guard accepts the tmp_path files
    old_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        rc = main(["batch", "-i", str(inp), "-o", str(out)])
    finally:
        os.chdir(old_cwd)
    assert rc == 0
    assert out.exists()
    content = out.read_text()
    assert "OK-01" in content
    # The invalid row is skipped, so only the good row appears
    assert content.count("KEY-01") == 1


# ---------------------------------------------------------------------------
# Enrichment engines — deduplication & thresholds
# ---------------------------------------------------------------------------
def test_enrichment_engine_names_preserved():
    """Each specialised engine must keep its distinct feature_name."""
    from enrichment import (
        SecureAggregationForFeatureRankingsEngine,
        DifferentialPrivacyBudgetExhaustionMonitoringEngine,
        ByzantineresilientFeatureRankingEngine,
    )
    assert SecureAggregationForFeatureRankingsEngine.feature_name == "Secure Aggregation for Feature Rankings"
    assert DifferentialPrivacyBudgetExhaustionMonitoringEngine.feature_name == "Differential Privacy Budget Exhaustion Monitoring"
    assert ByzantineresilientFeatureRankingEngine.feature_name == "Byzantine-Resilient Feature Ranking"


def test_enrichment_engine_thresholds():
    """Engines must escalate status correctly at threshold boundaries."""
    from enrichment import SecureAggregationForFeatureRankingsEngine
    eng = SecureAggregationForFeatureRankingsEngine(threshold=1.0)
    assert eng.evaluate(0.5).status == "OPTIMAL"
    assert eng.evaluate(1.5).status == "WARNING"
    assert eng.evaluate(3.0).status == "CRITICAL_ALERT"
