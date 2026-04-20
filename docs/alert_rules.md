# Alert Rules Reference

> Defines all firing conditions, severity, owners, and SLO links for the VFCare observability lab.
> For step-by-step diagnosis and mitigation, see [runbook.md](runbook.md).

---

## Summary Table

| # | Alert Name | Severity | Condition | Window | Owner | SLO |
|---|---|:---:|---|:---:|---|---|
| 1 | `high_latency_p95` | P2 | `latency_p95_ms > 3000` | 5m | team-oncall | Latency P95 < 3000ms / 28d |
| 2 | `high_error_rate` | P1 | `error_rate_pct > 5` | 3m | team-oncall | Error Rate < 2% / 28d |
| 3 | `cost_budget_spike` | P2 | `hourly_cost_usd > 2× baseline` | 15m | finops-owner | Daily cost < $2.50 / 1d |
| 4 | `quality_degradation` | P3 | `quality_score_avg < 0.6` | 15m | ml-oncall | Quality ≥ 0.75 / 28d |
| 5 | `pii_leak_detected` | P1 | `pii_leak_count > 0` | 1m | security-oncall | Zero PII in logs |

---

## 1. high_latency_p95

| Field | Value |
|---|---|
| **Severity** | P2 |
| **Condition** | `latency_p95_ms > 3000 for 5m` |
| **PromQL** | `histogram_quantile(0.95, sum(rate(lab_request_latency_ms_bucket[5m])) by (le)) > 3000` |
| **Notification** | `slack-oncall`, `email-oncall` |
| **Escalation** | No ack in 15m → page team lead |
| **Runbook** | [runbook.md#1-high-latency-p95](runbook.md#1-high-latency-p95) |
| **Config ref** | `config/alert_rules.yaml` → `high_latency_p95` |

---

## 2. high_error_rate

| Field | Value |
|---|---|
| **Severity** | P1 (Critical) |
| **Condition** | `error_rate_pct > 5 for 3m` |
| **PromQL** | `(100 * sum(rate(lab_requests_total{status="error"}[3m])) / clamp_min(sum(rate(lab_requests_total[3m])), 0.0001)) > 5` |
| **Notification** | `slack-oncall`, `pagerduty` |
| **Escalation** | No ack in 5m → page engineering manager |
| **Runbook** | [runbook.md#2-high-error-rate](runbook.md#2-high-error-rate) |
| **Config ref** | `config/alert_rules.yaml` → `high_error_rate` |

---

## 3. cost_budget_spike

| Field | Value |
|---|---|
| **Severity** | P2 |
| **Condition** | `hourly_cost_usd > 2× baseline for 15m` |
| **PromQL** | `sum(increase(lab_cost_usd_total[1h])) > 2.5` |
| **Notification** | `slack-finops`, `email-finops` |
| **Escalation** | Hourly burn > 5× baseline → page team lead |
| **Runbook** | [runbook.md#3-cost-budget-spike](runbook.md#3-cost-budget-spike) |
| **Config ref** | `config/alert_rules.yaml` → `cost_budget_spike` |

---

## 4. quality_degradation

| Field | Value |
|---|---|
| **Severity** | P3 |
| **Condition** | `quality_score_avg < 0.6 for 15m` |
| **Notification** | `slack-ml-team` |
| **Escalation** | Persists > 1h → page ML lead |
| **Runbook** | [runbook.md#4-quality-degradation](runbook.md#4-quality-degradation) |
| **Config ref** | `config/alert_rules.yaml` → `quality_degradation` |

---

## 5. pii_leak_detected

| Field | Value |
|---|---|
| **Severity** | P1 (Critical) |
| **Condition** | `pii_leak_count > 0 for 1m` |
| **Notification** | `slack-security`, `pagerduty` |
| **Escalation** | Immediate. Compliance team auto-notified |
| **Runbook** | [runbook.md#5-pii-leak-detected](runbook.md#5-pii-leak-detected) |
| **Config ref** | `config/alert_rules.yaml` → `pii_leak_detected` |

---

## Escalation Policy

| Severity | Ack Time | Escalation |
|:---:|:---:|---|
| **P1** | 5 min | → Engineering Manager if no ack |
| **P2** | 15 min | → Team Lead if no ack |
| **P3** | 1 hour | → Team Lead if persists > 2h |
