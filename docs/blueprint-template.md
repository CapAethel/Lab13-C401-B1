# Day 13 Observability Lab Report

> **Instruction**: Fill in all sections below. This report is designed to be parsed by an automated grading assistant. Ensure all tags (e.g., `[GROUP_NAME]`) are preserved.

## 1. Team Metadata
- [GROUP_NAME]: 
- [REPO_URL]: 
- [MEMBERS]:
  - Member A: Chu Thị Ngọc Huyền | Role: Logging & PII
  - Member B: Chu Bá Tuấn Anh | Role: Tracing & Enrichment
  - Member C: Nguyễn Mai Phương | Role: SLO & Alerts
  - Member D: Hứa Quang Linh | Role: Load Test & Dashboard
  - Member E: Nguyễn Thị Tuyết | Role: Demo & Report
  - Member F: Nguyễn Văn Lĩnh | Role: Blueprint & Demo Lead

---

## 2. Group Performance (Auto-Verified)
- [VALIDATE_LOGS_FINAL_SCORE]: /100
- [TOTAL_TRACES_COUNT]: 
- [PII_LEAKS_FOUND]: 

---

## 3. Technical Evidence (Group)

### 3.1 Logging & Tracing
- [EVIDENCE_CORRELATION_ID_SCREENSHOT]: [Path to image]
- [EVIDENCE_PII_REDACTION_SCREENSHOT]: [Path to image]
- [EVIDENCE_TRACE_WATERFALL_SCREENSHOT]: [Path to image]
- [TRACE_WATERFALL_EXPLANATION]: (Briefly explain one interesting span in your trace)

### 3.2 Dashboard & SLOs
- [DASHBOARD_6_PANELS_SCREENSHOT]: [evidence/dashboard_6_panels.png]
- [SLO_TABLE]:
| SLI | Target | Window | Current Value |
|---|---:|---|---:|
| Latency P95 | < 3000ms | 28d | |
| Error Rate | < 2% | 28d | |
| Cost Budget | < $2.5/day | 1d | |
- [DASHBOARD_PANEL_NOTES]:
  - Latency P50/P95/P99 (ms) with SLO line
  - Traffic (requests/min)
  - Error rate (%), with error-type breakdown
  - Cost over time (USD/hour or USD/day)
  - Tokens in/out (tokens/min)
  - Quality proxy (accepted recommendation rate %)

### 3.3 Alerts & Runbook
- [ALERT_RULES_SCREENSHOT]: [Path to image]
- [SAMPLE_RUNBOOK_LINK]: [docs/alerts.md#L...]

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

### [MEMBER_D_NAME]
- [TASKS_COMPLETED]: 
- [EVIDENCE_LINK]: 

### Nguyễn Thị Tuyết
- [TASKS_COMPLETED]:
  - Xây dựng và duy trì dashboard observability 6 panels với đơn vị đo và ngưỡng cảnh báo rõ ràng.
  - Chuẩn bị bộ bằng chứng dashboard (ảnh chụp + ghi chú từng panel) phục vụ chấm điểm.
  - Điều phối kịch bản demo theo luồng quan sát (Metrics -> Traces -> Logs) và trình bày phần dashboard.
- [EVIDENCE_LINK]:
  - [PR_DASHBOARD_OR_REPORT_LINK]
  - [COMMIT_LINK_1]
  - [COMMIT_LINK_2]

---

## 6. Bonus Items (Optional)
- [BONUS_COST_OPTIMIZATION]: (Description + Evidence)
- [BONUS_AUDIT_LOGS]: (Description + Evidence)
- [BONUS_CUSTOM_METRIC]: (Description + Evidence)
