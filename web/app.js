"use strict";

/* Mirrors the supervisor's documented screening thresholds, not feature selection. */
function evaluateTask(payload) {
  for (const name of ["task_id", "target_identifier", "status_descriptor"]) {
    if (typeof payload[name] !== "string" || !payload[name].trim() ||
        payload[name].length > 128 || /[\\x00-\\x1f\\x7f]/.test(payload[name])) {
      throw new Error(name + " must be a non-empty string of at most 128 characters without control characters");
    }
  }
  const primary = payload.primary_metric;
  const secondary = payload.secondary_metric;
  if (typeof primary !== "number" || !Number.isFinite(primary) ||
      typeof secondary !== "number" || !Number.isFinite(secondary)) {
    throw new Error("Both metrics must be finite numbers");
  }
  if (typeof payload.is_critical_flag !== "boolean") {
    throw new Error("is_critical_flag must be a boolean");
  }
  const alerts = [];
  if (primary > 25.0) {
    alerts.push({
      origin_worker: "InvariantQCWorker",
      urgency: "ELEVATED_RISK",
      summary: "Primary Metric Threshold Exceeded",
      technical_details: "Primary metric exceeds the demonstration threshold of 25",
    });
  }
  if (payload.is_critical_flag || secondary > 12.0) {
    alerts.push({
      origin_worker: "SafetyEscalationWorker",
      urgency: payload.is_critical_flag ? "CRITICAL_STAT_PANIC" : "ELEVATED_RISK",
      summary: "Critical Safety Interlock Triggered",
      technical_details: "Critical flag set or secondary metric exceeds 12",
    });
  }
  const descriptor = payload.status_descriptor.toUpperCase();
  if (["DISCORDANT", "ANOMALY", "MUTANT", "VIOLATION", "FAIL", "REJECT"].some(word => descriptor.includes(word))) {
    alerts.push({
      origin_worker: "ProtocolConformanceWorker",
      urgency: "ELEVATED_RISK",
      summary: "Protocol Conformance Discordance Detected",
      technical_details: "Status descriptor contains a screening alert keyword",
    });
  }
  const critical = alerts.filter(a => a.urgency === "CRITICAL_STAT_PANIC").length;
  const overall = critical ? "CRITICAL_STAT_PANIC" : alerts.length ? "ELEVATED_RISK" : "ROUTINE";
  return {
    mode: "LOCAL_SCREENING_DEMO",
    task_id: payload.task_id.trim(),
    target_identifier: payload.target_identifier.trim(),
    overall_urgency: overall,
    integrity_status: critical ? "RECALIBRATION_REQUIRED" : alerts.length ? "DISCORDANT_ANOMALY" : "VALIDATED_OPTIMAL",
    total_alerts: alerts.length,
    critical_alerts_count: critical,
    alerts,
    audit_signature: null,
    note: "Local screening only. No federated computation, clinical validation, or cryptographic audit performed.",
  };
}

if (typeof document !== "undefined") {
  const form = document.getElementById("auditForm");
  if (form) {
    const output = document.getElementById("outputConsole");
    const status = document.getElementById("resultStatus");
    const download = document.getElementById("downloadReport");
    let report = null;
    let tasks = 0;
    let alertCount = 0;

    form.addEventListener("submit", event => {
      event.preventDefault();
      try {
        const result = evaluateTask({
          task_id: document.getElementById("task_id").value,
          target_identifier: document.getElementById("target_id").value,
          primary_metric: document.getElementById("primary_metric").valueAsNumber,
          secondary_metric: document.getElementById("secondary_metric").valueAsNumber,
          status_descriptor: document.getElementById("status_descriptor").value,
          is_critical_flag: document.getElementById("is_critical").checked,
        });
        report = result;
        tasks += 1;
        alertCount += result.total_alerts;
        document.getElementById("taskCount").textContent = String(tasks);
        document.getElementById("alertCount").textContent = String(alertCount);
        status.textContent = "Screening completed: " + result.overall_urgency;
        output.textContent = JSON.stringify(result, null, 2);
        download.disabled = false;
      } catch (error) {
        report = null;
        status.textContent = "Validation error. No task processed.";
        output.textContent = error.message;
        download.disabled = true;
      }
    });

    document.getElementById("clearReport").addEventListener("click", () => {
      report = null;
      status.textContent = "No task evaluated yet.";
      output.textContent = "Submit a synthetic task to view the local result.";
      download.disabled = true;
    });

    download.addEventListener("click", () => {
      if (!report) return;
      const blob = new Blob([JSON.stringify(report, null, 2) + "\n"], {type: "application/json"});
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = "screening-result.json";
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
    });
  }
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = {evaluateTask};
}
