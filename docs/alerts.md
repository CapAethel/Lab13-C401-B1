# Alert Rules and Runbooks

> **How to use this runbook**: When an alert fires, find the matching section below. Follow the steps **in order**. Each section links back to the alert rule in `config/alert_rules.yaml`.

---

## 1. High latency P95

| Field | Value |
|-------|-------|
| **Severity** | P2 |
| **Trigger** | `latency_p95_ms > 3000 for 5m` |
| **SLO** | Latency P95 < 3000ms @ 99.5% over 28d |
| **Impact** | Tail latency breaches SLO; users experience slow responses |
| **Owner** | team-oncall |

### Diagnosis Steps
1. Open **Langfuse** → filter traces by `latency_ms > 3000` in the last 1h
2. Compare span durations: **RAG retrieval** vs **LLM generation**
3. Check if incident toggle `rag_slow` is enabled: `GET /health` → `incidents.rag_slow`
4. Review `/metrics` → compare `latency_p50` vs `latency_p95` (large gap = tail issue)
5. Check if traffic spike correlates with latency (concurrency bottleneck)

### Mitigation
- If RAG is slow → truncate long queries, use fallback retrieval source
- If LLM is slow → lower `max_tokens`, switch to faster model
- If concurrency → scale horizontally or add request queuing
- **Emergency**: disable `rag_slow` toggle → `POST /incidents/rag_slow/disable`

### Recovery Verification
- [ ] `latency_p95` back below 3000ms on `/metrics`
- [ ] No new slow traces in Langfuse for 10 min
- [ ] Update incident post-mortem

---

## 2. High error rate

| Field | Value |
|-------|-------|
| **Severity** | P1 (Critical) |
| **Trigger** | `error_rate_pct > 5 for 3m` |
| **SLO** | Error Rate < 2% @ 99.0% over 28d |
| **Impact** | Users receive 500 errors; service is partially down |
| **Owner** | team-oncall |

### Diagnosis Steps
1. Check `/metrics` → `error_breakdown` to identify dominant `error_type`
2. Search logs: filter by `event=request_failed` and group by `error_type`
3. Open failed traces in Langfuse → identify which span is failing
4. Common causes:
   - `RuntimeError: Vector store timeout` → `tool_fail` incident is on
   - `ValidationError` → bad input schema
   - `ConnectionError` → upstream dependency down

### Mitigation
- If `tool_fail` incident → `POST /incidents/tool_fail/disable`
- If upstream down → enable circuit breaker / fallback response
- If schema error → rollback latest deployment
- **Emergency**: return cached/fallback answers for all requests

### Recovery Verification
- [ ] Error rate dropped below 2% on `/metrics`
- [ ] No new `request_failed` logs for 5 min
- [ ] Send 5 test requests via load_test.py → all return 200
- [ ] Update incident post-mortem

---

## 3. Cost budget spike

| Field | Value |
|-------|-------|
| **Severity** | P2 |
| **Trigger** | `hourly_cost_usd > 2x_baseline for 15m` |
| **SLO** | Daily cost < $2.50 |
| **Impact** | Token burn rate exceeds budget; potential financial waste |
| **Owner** | finops-owner |

### Diagnosis Steps
1. Check `/metrics` → `avg_cost_usd` and `total_cost_usd`
2. Compare `tokens_in_total` vs `tokens_out_total` (output tokens cost 5x more)
3. Check if `cost_spike` incident toggle is enabled: `GET /health`
4. In Langfuse → filter by tag `cost_spike`, compare `usage_details.output` across traces
5. Check if a specific `feature` or `model` is driving the spike

### Mitigation
- If `cost_spike` incident → `POST /incidents/cost_spike/disable`
- Shorten system prompts to reduce input tokens
- Route low-complexity queries to cheaper model (e.g., haiku)
- Enable prompt caching for repeated context
- **Emergency**: rate-limit requests or temporarily degrade to cached responses

### Recovery Verification
- [ ] `avg_cost_usd` trending back to baseline on `/metrics`
- [ ] `tokens_out_total` growth rate normalized
- [ ] Daily projection < $2.50
- [ ] Update incident post-mortem

---

## 4. Quality degradation

| Field | Value |
|-------|-------|
| **Severity** | P3 |
| **Trigger** | `quality_score_avg < 0.6 for 15m` |
| **SLO** | Quality score ≥ 0.75 @ 95.0% over 28d |
| **Impact** | Responses are less relevant or useful; user satisfaction drops |
| **Owner** | ml-oncall |

### Diagnosis Steps
1. Check `/metrics` → `quality_avg` current value
2. In Langfuse → inspect traces with low quality scores
3. Check if RAG retrieval is returning fallback ("No domain document matched")
4. Compare recent traces: are `doc_count` values lower than usual?
5. Check if an incident toggle is distorting results (e.g., `rag_slow` causing timeouts)

### Mitigation
- If RAG returning fallbacks → review `mock_rag.py` corpus, add missing domain keys
- If answer too short → adjust LLM generation parameters
- If `[REDACTED]` tokens in answers → PII scrubbing is too aggressive, tune regex
- **Long-term**: add human feedback loop (thumbs up/down) for better quality signal

### Recovery Verification
- [ ] `quality_avg` back above 0.75 on `/metrics`
- [ ] Spot-check 5 recent traces in Langfuse for reasonable answers
- [ ] Update quality monitoring dashboard

---

## 5. PII leak detected

| Field | Value |
|-------|-------|
| **Severity** | P1 (Critical) |
| **Trigger** | `pii_leak_count > 0 for 1m` |
| **SLO** | Zero PII in logs (compliance requirement) |
| **Impact** | Privacy/compliance violation; potential regulatory exposure |
| **Owner** | security-oncall |

### Diagnosis Steps
1. Run `python scripts/validate_logs.py` → check "Potential PII leaks detected"
2. Search `data/logs.jsonl` for patterns: `@`, `4111`, phone numbers, CCCD
3. Identify which log event contains the leak (check `payload` fields)
4. Trace back to the code path: is `scrub_event` registered in structlog processors?
5. Check if new log fields were added without going through `scrub_text()`

### Mitigation
- **Immediate**: rotate/purge affected log files
- Verify `scrub_event` is in the structlog processor chain (`logging_config.py`)
- Add missing PII patterns to `pii.py` → `PII_PATTERNS` dict
- Test with `python -m pytest tests/test_pii.py`
- **Emergency**: stop log shipping to external systems until fixed

### Recovery Verification
- [ ] `validate_logs.py` shows 0 PII leaks
- [ ] New test requests produce clean logs
- [ ] `test_pii.py` passes with new patterns
- [ ] Security team acknowledged and log retention handled
- [ ] Update incident post-mortem

---

## General Escalation Policy

| Severity | Response Time | Escalation |
|----------|--------------|------------|
| **P1** | 5 min ack | → Engineering Manager if no ack in 5m |
| **P2** | 15 min ack | → Team Lead if no ack in 15m |
| **P3** | 1 hour ack | → Team Lead if persists > 2h |

## Post-Mortem Template
After resolving any P1/P2 alert:
1. **Timeline**: When did it start? When detected? When resolved?
2. **Root Cause**: What caused the issue?
3. **Impact**: How many users/requests affected?
4. **Fix**: What was done to resolve?
5. **Prevention**: What changes prevent recurrence?
