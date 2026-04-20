# Evidence Collection Sheet

## Required screenshots
- Langfuse trace list with >= 10 traces
- One full trace waterfall
- JSON logs showing correlation_id
- Log line with PII redaction
- Dashboard with 6 panels
- Alert rules with runbook link

## Optional screenshots
- Incident before/after fix
- Cost comparison before/after optimization
- Auto-instrumentation proof

## Member D Execution Artifacts
- Baseline outputs:
	- `data/member_d/baseline_c1.txt`
	- `data/member_d/baseline_c5.txt`
	- `data/member_d/baseline_c10.txt`
- Incident outputs:
	- `data/member_d/incident_rag_slow_c5.txt`
	- `data/member_d/incident_rag_slow_c10.txt`
	- `data/member_d/incident_tool_fail_c5.txt`
	- `data/member_d/incident_tool_fail_c10.txt`
	- `data/member_d/incident_cost_spike_c5.txt`
	- `data/member_d/incident_cost_spike_c10.txt`
- Metrics snapshots:
	- `data/member_d/baseline_metrics.json`
	- `data/member_d/incident_rag_slow_metrics.json`
	- `data/member_d/incident_tool_fail_metrics.json`
	- `data/member_d/incident_cost_spike_metrics.json`
- Consolidated summary:
	- `data/member_d/member_d_summary.json`

Notes:
- App was run in mock mode (`VFCARE_MOCK=1`) to complete test flow without external API key.
- Incident flags were verified disabled at handoff (`rag_slow=false`, `tool_fail=false`, `cost_spike=false`).
