# Evidence chuẩn Member D (baseline + 3 incidents)

## 1. Baseline (evidence_baseline.json)
- Chạy: `scripts/load_test.py --repeat 20 --timeout 10 --summary-json evidence_baseline.json --base-url http://127.0.0.1:8000`
- Không incident, hệ thống ở trạng thái bình thường.
- File: evidence_baseline.json

## 2. Incident 1: cost_spike (evidence_incident1.json)
- Inject: `scripts/inject_incident.py --scenario cost_spike --base-url http://127.0.0.1:8000`
- Chạy: `scripts/load_test.py --repeat 20 --timeout 10 --summary-json evidence_incident1.json --base-url http://127.0.0.1:8000`
- File: evidence_incident1.json

## 3. Incident 2: rag_slow (evidence_incident2.json)
- Inject: `scripts/inject_incident.py --scenario rag_slow --base-url http://127.0.0.1:8000`
- Chạy: `scripts/load_test.py --repeat 20 --timeout 10 --summary-json evidence_incident2.json --base-url http://127.0.0.1:8000`
- File: evidence_incident2.json

## 4. Incident 3: tool_fail (evidence_incident3.json)
- Inject: `scripts/inject_incident.py --scenario tool_fail --base-url http://127.0.0.1:8000`
- Chạy: `scripts/load_test.py --repeat 20 --timeout 10 --summary-json evidence_incident3.json --base-url http://127.0.0.1:8000`
- File: evidence_incident3.json

## 5. Reset incidents
- Tắt toàn bộ incidents: `scripts/inject_incident.py --scenario all --disable --base-url http://127.0.0.1:8000`

## 6. File evidence
- evidence_baseline.json
- evidence_incident1.json
- evidence_incident2.json
- evidence_incident3.json

Tất cả file JSON này đã được sinh ra trong workspace, sẵn sàng nộp hoặc kiểm tra.
