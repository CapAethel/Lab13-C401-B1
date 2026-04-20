# Demo Checklist (Pass-safe)

## Before demo
- [ ] `python -m pytest -q` passes
- [ ] `python scripts/validate_logs.py --service api` score >= 80
- [ ] `docker compose up -d` healthy (Prometheus + Grafana)
- [ ] Grafana dashboard `Lab13 Overview` has all 6 panels with real data
- [ ] Langfuse has >= 10 traces

## Required screenshots
- [ ] Trace list with >= 10 traces
- [ ] One trace waterfall
- [ ] JSON log line containing `correlation_id`
- [ ] JSON log line showing PII redaction
- [ ] Dashboard (all 6 panels visible)
- [ ] Alert rules + runbook link

## Incident storyline
- [ ] Inject incident (`rag_slow` or `tool_fail` or `cost_spike`)
- [ ] Show metric anomaly in dashboard
- [ ] Open related trace and identify slow/failing span
- [ ] Pivot to logs via `correlation_id`
- [ ] State root cause + fix action + preventive measure

## Report completion
- [ ] Fill `docs/blueprint-template.md` group metadata
- [ ] Fill final score fields (`VALIDATE_LOGS_FINAL_SCORE`, `TOTAL_TRACES_COUNT`, `PII_LEAKS_FOUND`)
- [ ] Fill SLO current values
- [ ] Fill individual contribution evidence links (commit/PR)
