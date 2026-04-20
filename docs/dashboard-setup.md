# Dashboard Setup (Grafana + Prometheus)

## 1. Start app
```bash
uvicorn app.main:app --reload
```

## 2. Start observability stack
```bash
docker compose up -d
```

Endpoints:
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (admin/admin)
- App metrics scrape target: `http://host.docker.internal:8000/metrics/prometheus`

## 3. Generate load data
```bash
python scripts/load_test.py --reset-logs --concurrency 5
```

## 4. Validate logs (API records only)
```bash
python scripts/validate_logs.py --service api
```

## 5. Dashboard rubric checks
- Open `Lab13 Overview` in Grafana
- Time range `Last 1 hour`
- Auto-refresh `15s`
- Verify all 6 required panels show non-empty data:
  1. Latency P50/P95/P99
  2. Traffic (QPS/request count)
  3. Error rate + breakdown
  4. Cost over time
  5. Tokens in/out
  6. Quality proxy
- Capture one full-screen screenshot for evidence.

## 6. Incident drill
```bash
python scripts/inject_incident.py --scenario rag_slow
python scripts/load_test.py --concurrency 5
python scripts/inject_incident.py --scenario rag_slow --disable
```

Repeat for:
- `tool_fail`
- `cost_spike`
