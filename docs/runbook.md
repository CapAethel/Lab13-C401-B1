# Incident Runbook

> **How to use**: When an alert fires, jump to the matching section below.  
> Follow steps **in order**. Alert firing conditions are defined in [alert_rules.md](alert_rules.md).

---

## 1. High Latency P95

**Alert**: `high_latency_p95` | Severity: P2 | SLO: < 3000ms / 28d

### Symptoms
- Requests taking > 3 s at the 95th percentile for 5+ minutes
- Users report slow or "hung" chat responses

### Diagnosis Steps
1. Check current P95 in Grafana → **Latency P50/P95/P99** panel.
2. Identify which `feature` is slow: filter logs by `event=response_sent`, sort by `latency_ms` desc.
3. Check Langfuse traces for the slow `correlation_id` — look for an unusually long retrieval or tool span.
4. Run: `grep '"latency_ms"' data/logs.jsonl | python -c "import sys,json; rows=[json.loads(l) for l in sys.stdin]; print(sorted([r.get('latency_ms',0) for r in rows], reverse=True)[:5])"`
5. Review `VFCARE_MOCK` — if `0`, real LLM calls may be hitting rate limits.

### Mitigation
- **Short-term**: Enable `VFCARE_MOCK=1` to reduce latency until the root cause is resolved.
- **RAG slow**: Increase vector store timeout or switch to a cached response path.
- **LLM slow**: Reduce `max_tokens`, enable streaming, or switch to a faster model tier.
- **Tool slow**: Check external API health (`/health` endpoint of downstream services).

### Recovery Checklist
- [ ] P95 drops below 3000ms for ≥ 5 minutes
- [ ] No new `high_latency_p95` alerts firing
- [ ] Post-incident note added to `data/incidents.json` (key: `rag_slow` if applicable)

---

## 2. High Error Rate

**Alert**: `high_error_rate` | Severity: P1 | SLO: < 2% / 28d

### Symptoms
- HTTP 5xx responses to `/chat` endpoint
- `event=response_sent` log entries with `status=error`

### Diagnosis Steps
1. Check Grafana → **Error rate** panel for spike timing and error type.
2. Find erroring requests: `grep '"status": "error"' data/logs.jsonl | head -20`
3. Extract `correlation_id` from the first failing log; search Langfuse for matching trace.
4. Check `app/main.py` exception handler — `detail` field in the error response contains the raw exception.
5. Review recent deployments or config changes that coincide with the spike.

### Mitigation
- **Tool failures**: Inject `tool_fail` incident scenario to reproduce locally: `python scripts/inject_incident.py --scenario tool_fail`
- **LLM errors**: Check API key validity (`OPENAI_API_KEY` env var); switch to mock mode.
- **Schema errors**: Run `python scripts/validate_logs.py` — if it reports schema mismatches, check `app/schemas.py`.

### Recovery Checklist
- [ ] Error rate below 2% for ≥ 3 minutes
- [ ] Root cause documented in `docs/blueprint-template.md` Section 4
- [ ] Incident disabled: `curl -X POST http://127.0.0.1:8000/incidents/tool_fail/disable`

---

## 3. Cost Budget Spike

**Alert**: `cost_budget_spike` | Severity: P2 | Budget: < $2.50/day

### Symptoms
- Hourly cost exceeds 2× rolling baseline for 15+ minutes
- `cost_usd` values in logs trending sharply upward

### Diagnosis Steps
1. Compute recent cost: `grep '"cost_usd"' data/logs.jsonl | python -c "import sys,json; print(sum(json.loads(l).get('cost_usd',0) for l in sys.stdin))"`
2. Identify expensive features: group `cost_usd` by `feature` in logs.
3. Check `tokens_in` and `tokens_out` — large input context (RAG chunks) drives cost up.
4. Inject `cost_spike` scenario: `python scripts/inject_incident.py --scenario cost_spike`
5. Compare token counts vs. baseline in Grafana → **Tokens in/out** panel.

### Mitigation
- Reduce `max_tokens` in agent config.
- Enable response caching for repeated queries (high-confidence RAG hits).
- Add a per-session token budget guard in `app/agent.py`.
- Switch non-critical features to a cheaper model tier.

### Recovery Checklist
- [ ] Hourly cost below 2× baseline for ≥ 15 minutes
- [ ] Token limits reviewed and enforced in config
- [ ] FinOps team notified if daily budget exceeded

---

## 4. Quality Degradation

**Alert**: `quality_degradation` | Severity: P3 | SLO: quality ≥ 0.75 / 28d

### Symptoms
- `quality_score` in `response_sent` logs consistently below 0.6
- Users reporting unhelpful or inaccurate answers

### Diagnosis Steps
1. Filter low-quality responses: `grep '"quality_score"' data/logs.jsonl | python -c "import sys,json; [print(l.strip()) for l in sys.stdin if json.loads(l).get('quality_score',1)<0.6]"`
2. Check which `feature` has the lowest scores.
3. Compare agent answers against `data/expected_answers.jsonl` using `chat.py` or `scripts/validate_logs.py`.
4. Review RAG retrieval: low-quality answers often correlate with poor retrieval context.
5. Check if system prompt in `app/system_prompt.txt` was recently modified.

### Mitigation
- Refresh the RAG knowledge base with updated VinFast documentation.
- Review and update `data/expected_answers.jsonl` ground-truth entries.
- Revert recent changes to `app/system_prompt.txt` if quality dropped after an edit.
- Increase retrieval `top_k` to surface more relevant context.

### Recovery Checklist
- [ ] Quality score average above 0.75 for ≥ 15 minutes
- [ ] Affected feature identified and knowledge base updated
- [ ] Expected answers validated: `python chat.py --validate`

---

## 5. PII Leak Detected

**Alert**: `pii_leak_detected` | Severity: P1 | Policy: Zero PII in logs

### Symptoms
- Raw phone numbers, emails, or credit card numbers appear unredacted in `data/logs.jsonl`
- PII scrubber (`app/pii.py`) not replacing sensitive tokens with `[REDACTED_*]`

### Diagnosis Steps
1. Scan logs immediately: `python -c "import re, pathlib; txt = pathlib.Path('data/logs.jsonl').read_text(); hits = re.findall(r'0[0-9]{9}|[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}|[0-9]{13,16}', txt); print(hits)"`
2. Identify the `correlation_id` of the leaking request from the matching log line.
3. Reproduce: call `/chat` with the same PII-containing query; check raw log output.
4. Inspect `app/pii.py` — verify all regex patterns cover the leaked format.
5. Check `app/logging_config.py` — confirm `scrub_pii` processor is applied before the JSON sink.

### Mitigation
- **Immediate**: Rotate any credentials visible in logs. Notify compliance/security team.
- Fix the missing pattern in `app/pii.py` and redeploy.
- Delete or overwrite the affected log file after extracting the `correlation_id` for audit.
- Run: `python scripts/validate_logs.py` to confirm no remaining leaks.

### Recovery Checklist
- [ ] No raw PII found in `data/logs.jsonl` after re-scan
- [ ] `pii_leak_detected` alert no longer firing
- [ ] Security incident logged; compliance team notified
- [ ] `app/pii.py` patterns updated and unit tests in `tests/test_pii.py` passing: `pytest tests/test_pii.py -v`
