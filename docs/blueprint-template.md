# Day 13 Observability Lab Report

> **Instruction**: Fill in all sections below. This report is designed to be parsed by an automated grading assistant. Ensure all tags (e.g., `[GROUP_NAME]`) are preserved.

## 1. Team Metadata
- [GROUP_NAME]: B1-C401
- [REPO_URL]: https://github.com/CapAethel/Lab13-C401-B1.git
- [MEMBERS]:
  - Member A: Chu Thị Ngọc Huyền | Role: Logging & PII
  - Member B: Chu Bá Tuấn Anh | Role: Tracing & Enrichment
  - Member C: Nguyễn Mai Phương | Role: SLO & Alerts
  - Member D: Hứa Quang Linh | Role: load test + incident injection
  - Member E: Nguyễn Thị Tuyết | Role: Demo & Report
  - Member F: Nguyễn Văn Lĩnh | Role: Blueprint & Demo Lead

---

## 2. Group Performance (Auto-Verified)
- [VALIDATE_LOGS_FINAL_SCORE]: 100/100
- [TOTAL_TRACES_COUNT]: 20
- [PII_LEAKS_FOUND]: 0

---

## 3. Technical Evidence (Group)

### 3.1 Logging & Tracing
- [EVIDENCE_CORRELATION_ID_SCREENSHOT]: [evidence/correlation_id_flow.png]
- [EVIDENCE_PII_REDACTION_SCREENSHOT]: [evidence/pii_redaction_logs.png]
- [EVIDENCE_TRACE_WATERFALL_SCREENSHOT]: [evidence/trace_waterfall_req-a88c09f1.png]
- [TRACE_WATERFALL_EXPLANATION]: In trace `req-a88c09f1` (session `s01`), the main chat span shows end-to-end latency around 150ms and aligns with logs from `request_received` to `response_sent` using the same `correlation_id`. The most interesting child span is retrieval/tool context preparation before generation: it completes quickly and confirms that latency is dominated by model response time, not by pre-processing. This matches stable latency seen across sessions (`s01`-`s10`) and supports the conclusion that there is no tail-latency regression in this run.

### 3.2 Dashboard & SLOs
- [DASHBOARD_6_PANELS_SCREENSHOT]: [evidence/dashboard_6_panels.png]
- [SLO_TABLE]:
| SLI | Target | Window | Current Value |
|---|---:|---|---:|
| Latency P95 | < 3000ms | 28d | 241ms |
| Error Rate | < 2% | 28d | no data |
| Cost Budget | < $2.5/day | 1d | no data |
- [DASHBOARD_PANEL_NOTES]:
  - Latency P50/P95/P99 (ms) with SLO line
  - Traffic (requests/min)
  - Error rate (%), with error-type breakdown
  - Cost over time (USD/hour or USD/day)
  - Tokens in/out (tokens/min)
  - Quality proxy (accepted recommendation rate %)

### 3.3 Alerts & Runbook
- [ALERT_RULES_SCREENSHOT]: [evidence/alert_rules_runbook.png]
- [ALERT_RULES_REFERENCE]: [docs/alert_rules.md](docs/alert_rules.md) — firing conditions, severity, PromQL, owners, escalation policy for all 5 alerts
- [SAMPLE_RUNBOOK_LINK]: [docs/runbook.md#1-high-latency-p95](docs/runbook.md) — step-by-step diagnosis and mitigation for all 5 scenarios

---

## 4. Incident Response (Group)
- [SCENARIO_NAME]: (e.g., rag_slow)
- [SYMPTOMS_OBSERVED]:
- [ROOT_CAUSE_PROVED_BY]: (List specific Trace ID or Log Line)
- [FIX_ACTION]:
- [PREVENTIVE_MEASURE]:

---

## 5. Individual Contributions & Evidence

### [MEMBER_A_NAME]
- [TASKS_COMPLETED]:
- [EVIDENCE_LINK]: (Link to specific commit or PR)

### [MEMBER_B_NAME]
- [TASKS_COMPLETED]:
- [EVIDENCE_LINK]:

### [MEMBER_C_NAME]
- [TASKS_COMPLETED]:
- [EVIDENCE_LINK]:

### [MEMBER_D_HỨA_QUANG_LINH]
- [TASKS_COMPLETED]:
  - Thiết kế, nâng cấp và vận hành toàn bộ quy trình load test, bao gồm baseline và 3 kịch bản incident (cost_spike, rag_slow, tool_fail).
  - Viết/tối ưu script `scripts/load_test.py` và `scripts/inject_incident.py` với các tuỳ chọn CLI mới, xuất evidence JSON, kiểm soát lỗi robust.
  - Thực hiện chạy thực tế, thu thập và lưu trữ bộ evidence chuẩn (baseline + 3 incidents) cho grading.
  - Đảm bảo quy trình evidence tự động, có thể kiểm tra lại nhiều lần, reset trạng thái hệ thống sau khi test.
- [EVIDENCE_LINK]:
  - [evidence_MemberD.md](../../evidence_MemberD.md) — hướng dẫn và tổng hợp evidence
  - [evidence_baseline.json](../../evidence_baseline.json)
  - [evidence_incident1.json](../../evidence_incident1.json)
  - [evidence_incident2.json](../../evidence_incident2.json)
  - [evidence_incident3.json](../../evidence_incident3.json)
  - [scripts/load_test.py](../../scripts/load_test.py)
  - [scripts/inject_incident.py](../../scripts/inject_incident.py)

---

## 6. Bonus Items (Optional)
- [BONUS_COST_OPTIMIZATION]: (Description + Evidence)
- [BONUS_AUDIT_LOGS]: (Description + Evidence)
- [BONUS_CUSTOM_METRIC]: (Description + Evidence)
