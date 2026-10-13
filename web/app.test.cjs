"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const { evaluateTask } = require("./app.js");

const nominal = {
  task_id: "TASK-1", target_identifier: "SYN-01", primary_metric: 12,
  secondary_metric: 4, status_descriptor: "NOMINAL", is_critical_flag: false,
};
test("nominal task produces no alerts and no audit signature", () => {
  const result = evaluateTask(nominal);
  assert.equal(result.overall_urgency, "ROUTINE");
  assert.equal(result.total_alerts, 0);
  assert.equal(result.audit_signature, null);
});
test("threshold comparisons are strict", () => {
  const exact = evaluateTask({...nominal,primary_metric:25,secondary_metric:12});
  assert.equal(exact.total_alerts, 0);
  const exceeded = evaluateTask({...nominal,primary_metric:25.01,secondary_metric:12.01});
  assert.equal(exceeded.total_alerts,2);
  assert.equal(exceeded.overall_urgency,"ELEVATED_RISK");
});
test("critical flag has priority even with other alerts", () => {
  const result = evaluateTask({...nominal,is_critical_flag:true,primary_metric:30,status_descriptor:"DISCORDANT"});
  assert.equal(result.total_alerts,3);
  assert.equal(result.critical_alerts_count,1);
  assert.equal(result.overall_urgency,"CRITICAL_STAT_PANIC");
  assert.equal(result.integrity_status,"RECALIBRATION_REQUIRED");
});
test("status keyword check is case-insensitive", () => {
  assert.equal(evaluateTask({...nominal,status_descriptor:"possible anomaly"}).total_alerts,1);
});
test("non-finite and empty input rejected", () => {
  for (const bad of [NaN, Infinity, -Infinity]) {
    assert.throws(() => evaluateTask({...nominal,primary_metric:bad}),/finite/);
    assert.throws(() => evaluateTask({...nominal,secondary_metric:bad}),/finite/);
  }
  assert.throws(() => evaluateTask({...nominal,task_id:""}),/task_id/);
  assert.throws(() => evaluateTask({...nominal,task_id:"x".repeat(129)}),/task_id/);
  assert.throws(() => evaluateTask({...nominal,is_critical_flag:"true"}),/boolean/);
});
