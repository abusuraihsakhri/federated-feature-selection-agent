"""Regression coverage for validation, access control and CSV path traversal."""
import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from agents.api import api_audit, api_audit_logs
from agents.base import SecurityException
from agents.models import SystemTaskPayload
from agents.supervisor import SystemSupervisor
from cli import main as main_cli
from fed_feature_selector.cli import main as frontier_cli
from fed_feature_selector.engine import FrontierDomainEngine


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), float("-inf")])
def test_nonfinite_metrics_rejected(bad):
    for field in ("primary_metric", "secondary_metric"):
        values = {"task_id": "TASK", "target_identifier": "KEY", "primary_metric": 1.0}
        values[field] = bad
        with pytest.raises(ValidationError):
            SystemTaskPayload(**values)
    with pytest.raises(ValueError):
        FrontierDomainEngine.evaluate_primary_parameter(bad)
    with pytest.raises(ValueError):
        FrontierDomainEngine.evaluate_secondary_kinetics(bad, False)


def test_nested_metadata_phi_rejected_without_leak():
    payload = SystemTaskPayload(task_id="TASK", target_identifier="KEY", primary_metric=1,
                                attributes={"nested": {"contact": "person@example.com"}})
    with pytest.raises(SecurityException):
        SystemSupervisor().process_task(payload)
    with pytest.raises(HTTPException) as exc:
        api_audit(payload)
    assert exc.value.status_code == 422
    assert "example.com" not in str(exc.value.detail)


def test_control_characters_rejected():
    with pytest.raises(ValidationError):
        SystemTaskPayload(task_id="line\nfeed", target_identifier="KEY", primary_metric=1)


def test_audit_logs_disabled_without_token(monkeypatch):
    monkeypatch.delenv("AUDIT_API_TOKEN", raising=False)
    with pytest.raises(HTTPException) as exc:
        api_audit_logs(x_api_key=None)
    assert exc.value.status_code == 403


def test_audit_logs_require_correct_token(monkeypatch):
    monkeypatch.setenv("AUDIT_API_TOKEN", "nontrivial-test-token")
    with pytest.raises(HTTPException) as exc:
        api_audit_logs(x_api_key="wrong")
    assert exc.value.status_code == 403
    assert api_audit_logs(x_api_key="nontrivial-test-token")["verified"] is True


@pytest.mark.parametrize("entry", [main_cli, frontier_cli])
def test_batch_rejects_symlink_escape(entry, tmp_path, monkeypatch):
    working = tmp_path / "working"
    working.mkdir()
    outside = tmp_path / "sensitive.csv"
    outside.write_text("task_id,target_identifier,primary_metric\nT,K,1\n")
    (working / "link.csv").symlink_to(outside)
    monkeypatch.chdir(working)
    with pytest.raises(SystemExit):
        entry(["batch", "-i", "link.csv", "-o", "out.csv"])


@pytest.mark.parametrize("entry", [main_cli, frontier_cli])
def test_batch_rejects_sibling_prefix_escape(entry, tmp_path, monkeypatch):
    working = tmp_path / "work"
    sibling = tmp_path / "working"
    working.mkdir()
    sibling.mkdir()
    (sibling / "data.csv").write_text("task_id,target_identifier,primary_metric\nT,K,1\n")
    monkeypatch.chdir(working)
    with pytest.raises(SystemExit):
        entry(["batch", "-i", "../working/data.csv", "-o", "out.csv"])


def test_batch_skips_unsafe_data_without_echoing_identifiers(tmp_path, monkeypatch, capsys):
    (tmp_path / "in.csv").write_text(
        "task_id,target_identifier,primary_metric\n"
        "GOOD,KEY,2\n"
        "SENSITIVE,person@example.com,3\n"
    )
    monkeypatch.chdir(tmp_path)
    assert main_cli(["batch", "-i", "in.csv", "-o", "out.csv"]) == 0
    out = (tmp_path / "out.csv").read_text()
    assert "GOOD" in out
    assert "person@example.com" not in out
    assert "person@example.com" not in capsys.readouterr().err
