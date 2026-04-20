# Quy Trình Làm Việc Từng Member - Bài Lab Day 13 Observability

**Thời lượng**: 4 giờ  
**Mục tiêu**: Xây dựng, trang bị đầy đủ, kiểm tra, và báo cáo một hệ thống observability hoàn chỉnh cho FastAPI agent.

---

## 🔄 Timeline Quy Trình Làm Việc

```
Giai đoạn 1: Chuẩn Bị & Setup (0:00 - 0:30)
  └─ Tất cả: Clone repo, tạo venv, cài requirements, tạo .env, chạy app
  └─ Output: App baseline hoạt động (http://localhost:8000/health trả về ok: true)

Giai đoạn 2: Triển Khai (0:30 - 2:30)
  ├─ Member A (Song song): Logging + scrubbing PII
  ├─ Member B (Song song): Tracing + Langfuse tags
  ├─ Member C (Song song): Cấu hình SLO + Luật cảnh báo
  └─ Output: App được trang bị đầy đủ, traces & logs chảy liên tục

Giai đoạn 3: Kiểm Tra & Thu Thập Bằng Chứng (2:30 - 3:30)
  ├─ Member D: Load test (baseline) + Tiêm sự cố
  ├─ Member E: Xây dựng dashboard 6 panel
  └─ Member F: Thu thập bằng chứng + Chuẩn bị script demo

Giai đoạn 4: Demo & Báo Cáo (3:30 - 4:00)
  └─ Tất cả: Demo live + Trả lời Q&A + Nộp bản báo cáo
```

---

## Member A: Logging + Scrubbing PII

**Thời lượng**: 0:30 - 1:15  
**Trách nhiệm**: Cơ sở hạ tầng logging & vệ sinh dữ liệu  
**Phụ thuộc**: Không có (có thể bắt đầu ngay lập tức)

### Công Việc

1. **Sửa middleware correlation ID** (0:30 - 0:40)
   - Mở [app/middleware.py](../app/middleware.py)
   - TODO: Xóa contextvars ở cuối request
   - TODO: Lấy x-request-id từ headers hoặc tạo UUID mới
   - TODO: Bind correlation_id vào structlog contextvars
   - TODO: Thêm correlation_id vào response headers
   - Kiểm tra: `curl -i http://localhost:8000/health` → sẽ thấy `x-request-id` trong response header

2. **Làm phong phú logs với context** (0:40 - 0:50)
   - Mở [app/main.py](../app/main.py)
   - TODO: Mở rộng logs với context yêu cầu (user_id_hash, session_id, feature, model, env)
   - Sử dụng `bind_contextvars()` để bind từ request body
   - Xác minh: `python scripts/validate_logs.py` hiển thị "Log enrichment: PASSED"

3. **Triển khai scrubbing PII** (0:50 - 1:10)
   - Mở [app/logging_config.py](../app/logging_config.py)
   - TODO: Đăng ký PII scrubbing processor trong structlog pipeline
   - Mở [app/pii.py](../app/pii.py)
   - TODO: Thêm các pattern khác (email, điện thoại, thẻ tín dụng, passport Việt Nam, từ khóa địa chỉ)
   - Kiểm tra: Chạy request có email/điện thoại → logs phải scrub thành `[REDACTED-EMAIL]`

4. **Xác minh tất cả kiểm tra vượt qua** (1:10 - 1:15)
   ```bash
   python scripts/load_test.py --concurrency 3
   python scripts/validate_logs.py
   ```
   - Kỳ vọng: Điểm 100/100 cho logging cơ bản, correlation ID, mở rộng logs, PII

### Kết Quả Giao Hàng

- ✅ Correlation ID chảy qua tất cả requests
- ✅ Logs chứa user_id_hash, session_id, feature, model, env
- ✅ Không có email/điện thoại/số thẻ tín dụng dạng plaintext trong logs
- ✅ validate_logs.py score: ≥80/100
- 📄 Ghi lại các regex pattern cho PII ở [docs/blueprint-template.md](./blueprint-template.md)

---

## Member B: Tracing + Langfuse Tags

**Thời lượng**: 0:40 - 1:20  
**Trách nhiệm**: Distributed tracing & metadata quan sát hệ thống  
**Phụ thuộc**: Member A (logging hoạt động) + Cài đặt tài khoản Langfuse

### Công Việc

1. **Cài đặt tích hợp Langfuse** (0:40 - 0:50)
   - Tạo tài khoản miễn phí tại https://langfuse.com
   - Lấy LANGFUSE_PUBLIC_KEY + LANGFUSE_SECRET_KEY
   - Tạo `.env` với:
     ```
     LANGFUSE_PUBLIC_KEY=<key>
     LANGFUSE_SECRET_KEY=<secret>
     LANGFUSE_HOST=https://cloud.langfuse.com
     ```
   - Mở [app/tracing.py](../app/tracing.py) và xác minh decorator `observe` được sử dụng

2. **Gắn tag agent với metadata** (0:50 - 1:10)
   - Mở [app/agent.py](../app/agent.py) (dòng ~25-40)
   - Xác minh decorator `@observe()` trên method `run()`
   - Xác minh `langfuse_context.update_current_trace()` được gọi với:
     - user_id (đã hash)
     - session_id
     - tags (ví dụ: ["lab", feature, model])
   - Xác minh `langfuse_context.update_current_observation()` bao gồm:
     - metadata: doc_count, query_preview
     - usage_details: input tokens, output tokens

3. **Gửi traces kiểm tra** (1:10 - 1:20)
   ```bash
   # Gửi 15+ requests để tích lũy traces
   python scripts/load_test.py --concurrency 1 --repeat 2
   ```
   - Kiểm tra dashboard Langfuse: phải thấy ≥10 traces với metadata
   - Xác minh trace waterfall hiển thị: rag retrieval → llm generation → full pipeline

### Kết Quả Giao Hàng

- ✅ Traces hiển thị trong Langfuse (tối thiểu 10)
- ✅ Mỗi trace gắn tag user_id_hash, session_id, feature
- ✅ Trace hiển thị doc_count, token usage, latency
- ✅ Ảnh chụp: Danh sách traces Langfuse + một waterfall đầy đủ
- 📄 Ghi chú ở [docs/blueprint-template.md](./blueprint-template.md): Các bước tích hợp Langfuse

---

## Member C: SLO + Cảnh báo

**Thời lượng**: 0:50 - 1:40  
**Trách nhiệm**: Service level objectives và luật cảnh báo  
**Phụ thuộc**: Member A (logging), Member B (trace baseline)

### Công Việc

1. **Xem xét baseline SLO** (0:50 - 1:00)
   - Mở [config/slo.yaml](../config/slo.yaml)
   - SLOs hiện tại (có thể chưa được đặt):
     - latency_p95_ms: ?
     - error_rate_%: ?
     - availability_%: ?
   - Chạy baseline test của Member D để hiểu các metric hiện tại:
     ```bash
     python scripts/load_test.py --concurrency 5 --repeat 1 --summary-json data/baseline.json
     ```
   - Từ output, ghi lại p95 latency và error rate

2. **Đặt SLOs thực tế** (1:00 - 1:15)
   - Cập nhật [config/slo.yaml](../config/slo.yaml):
     ```yaml
     slos:
       latency_p95_ms: 1000  # 95% requests < 1s
       error_rate_%: 2       # Cho phép 2% lỗi
       availability_%: 98    # 98% uptime
     ```
   - Lưu các con số baseline cho báo cáo sự cố của Member D

3. **Cấu hình luật cảnh báo** (1:15 - 1:35)
   - Mở [config/alert_rules.yaml](../config/alert_rules.yaml)
   - Đảm bảo 3+ luật cảnh báo:
     - high_latency_p95 (khi p95 > SLO threshold)
     - high_error_rate (khi error_rate > threshold)
     - (tùy chọn) cost_spike hoặc tool_fail detection
   - Liên kết mỗi luật với runbook ở [docs/alerts.md](./alerts.md)
   - Ví dụ định dạng runbook:
     ```markdown
     ## 1. P95 Latency Cao
     - Điều kiện: p95_latency > 1000ms
     - Phát hiện: Kiểm tra endpoint /metrics
     - Giảm nhẹ: Kiểm tra độ trễ RAG với inject_incident --status
     - Nâng cấp: Liên hệ DevOps nếu có incident RAG_SLOW
     ```

4. **Xác minh thresholds** (1:35 - 1:40)
   ```bash
   # Sau này, Member D sẽ kiểm tra: sau khi tiêm incident rag_slow,
   # alert phải kích hoạt tự động
   python scripts/inject_incident.py --scenario rag_slow
   curl http://localhost:8000/metrics  # p95 phải vượt ngưỡng
   ```

### Kết Quả Giao Hàng

- ✅ SLO baselines được ghi lại (p95, error rate, availability)
- ✅ 3+ luật cảnh báo trong alert_rules.yaml với runbooks
- ✅ Thresholds thực tế (dựa trên baseline của member D)
- ✅ Cảnh báo kích hoạt khi tiêm sự cố
- 📄 Runbooks được điền đầy đủ ở [docs/alerts.md](./alerts.md)

---

## Member D: Load Test + Tiêm Sự Cố

**Thời lượng**: 1:15 - 2:50  
**Trách nhiệm**: Kiểm tra hiệu năng & chaos engineering  
**Phụ thuộc**: Member A/B/C (tất cả các member trước hoàn thành)

### Công Việc

1. **Hiệu năng Baseline** (1:15 - 1:30)
   ```bash
   python scripts/load_test.py --concurrency 1 --repeat 1 --summary-json data/baseline_c1.json
   python scripts/load_test.py --concurrency 5 --repeat 1 --summary-json data/baseline_c5.json
   python scripts/load_test.py --concurrency 10 --repeat 1 --summary-json data/baseline_c10.json
   ```
   - Ghi lại min/avg/p95/p99/max cho mỗi mức concurrency
   - Ghi lại: "Dưới tải bình thường, p95 latency là X ms ở concurrency Y"

2. **Liệt kê & hiểu sự cố** (1:30 - 1:40)
   ```bash
   python scripts/inject_incident.py --list
   ```
   - Output hiển thị 3 kịch bản:
     - `rag_slow`: Spike độ trễ retrieval (thêm 2.5s)
     - `tool_fail`: Lỗi vector store
     - `cost_spike`: Tăng token usage 4x
   - Ghi lại dự đoán tác động cho mỗi kịch bản

3. **Tiêm & đo rag_slow** (1:40 - 2:00)
   ```bash
   python scripts/inject_incident.py --scenario rag_slow
   python scripts/load_test.py --concurrency 5 --repeat 1 --summary-json data/incident_rag_slow_c5.json
   python scripts/load_test.py --concurrency 10 --repeat 1 --summary-json data/incident_rag_slow_c10.json
   curl http://localhost:8000/metrics  # Kiểm tra spike p95
   python scripts/inject_incident.py --scenario rag_slow --disable
   ```
   - Ghi lại: "Với rag_slow, p95 tăng từ X đến Y ms (Z% giảm chất lượng)"

4. **Tiêm & đo tool_fail** (2:00 - 2:20)
   ```bash
   python scripts/inject_incident.py --scenario tool_fail
   python scripts/load_test.py --concurrency 5 --repeat 1 --summary-json data/incident_tool_fail_c5.json
   curl http://localhost:8000/metrics  # Kiểm tra error_breakdown
   python scripts/inject_incident.py --scenario tool_fail --disable
   ```
   - Ghi lại: "Với tool_fail, error_rate đạt Z%, lỗi: [error types]"

5. **Tiêm & đo cost_spike** (2:20 - 2:40)
   ```bash
   python scripts/inject_incident.py --scenario cost_spike
   python scripts/load_test.py --concurrency 5 --repeat 1 --summary-json data/incident_cost_spike_c5.json
   curl http://localhost:8000/metrics  # Kiểm tra avg_cost_usd
   python scripts/inject_incident.py --scenario cost_spike --disable
   ```
   - Ghi lại: "Với cost_spike, chi phí trung bình/request tăng từ $X đến $Y"

6. **Xác minh vi phạm SLO** (2:40 - 2:50)
   - Kiểm tra sự cố nào kích hoạt cảnh báo (luật của Member C)
   - So sánh: baseline_c5.json vs incident_*.json
   - Ghi lại: "rag_slow vi phạm SLO ở concurrency 5+ do p95 vượt quá 1000ms"
   - Xác minh tất cả sự cố bị vô hiệu hóa trước khi bàn giao:
     ```bash
     python scripts/inject_incident.py --status
     python scripts/inject_incident.py --scenario all --disable
     ```

### Kết Quả Giao Hàng

- ✅ 3 bản tóm tắt baseline JSON (c1, c5, c10)
- ✅ 3 bản tóm tắt sự cố JSON (rag_slow, tool_fail, cost_spike)
- ✅ Bảng so sánh: Metrics Trước/Sau cho mỗi sự cố
- ✅ Phân tích nguyên nhân: Tại sao mỗi sự cố gây vi phạm SLO
- 📄 Kết quả được ghi lại ở [docs/grading-evidence.md](./grading-evidence.md)
- 📄 Bản tóm tắt tác động sự cố ở [docs/blueprint-template.md](./blueprint-template.md)

---

## Member E: Dashboard + Bằng Chứng

**Thời lượng**: 2:00 - 3:30  
**Trách nhiệm**: Trực quan hóa metrics & thu thập bằng chứng  
**Phụ thuộc**: Member A/B/C (trang bị đầy đủ) + Member D (kết quả kiểm tra)

### Công Việc

1. **Chuẩn bị spec dashboard 6 panel** (2:00 - 2:20)
   - Mở [docs/dashboard-spec.md](./dashboard-spec.md)
   - Thiết kế 6 panel (có thể dùng bất kỳ công cụ nào: Grafana, Kibana, HTML tùy chỉnh, Google Sheets):
     1. **Request Volume Over Time** (biểu đồ dòng QPS)
     2. **Latency Percentiles** (p50, p95, p99 với SLO line)
     3. **Error Rate Trend** (% lỗi theo thời gian)
     4. **Cost Per Request** (chi phí trung bình + breakdown tổng chi phí)
     5. **Token Usage** (input vs output tokens)
     6. **SLO Status** (pass/fail cho latency, error_rate, availability)

2. **Export metrics từ endpoint /metrics** (2:20 - 2:40)
   - Sau mỗi lần chạy kiểm tra, capture output `/metrics`
   - Phân tích và tải vào công cụ dashboard
   - Tạo snapshots hiển thị:
     - Trạng thái Baseline (tất cả xanh)
     - Trạng thái một sự cố (vi phạm SLO hiển thị)

3. **Thu thập ảnh chụp bằng chứng** (2:40 - 3:20)
   - Chụp ảnh danh sách các mục bắt buộc ở [docs/grading-evidence.md](./grading-evidence.md):
     - ✅ Danh sách traces Langfuse (≥10 traces) từ Member B
     - ✅ Một waterfall trace đầy đủ Langfuse
     - ✅ JSON logs hiển thị correlation_id (từ logs.jsonl)
     - ✅ Dòng log với PII redaction (từ Member A)
     - ✅ Dashboard 6 panel
     - ✅ Luật cảnh báo với runbook links
     - ✅ validate_logs.py score: ≥80/100
     - ✅ Biểu đồ trước/sau sự cố

4. **Tổ chức thư mục bằng chứng** (3:20 - 3:30)
   - Tạo thư mục `docs/evidence/` với tất cả ảnh chụp
   - Đặt tên mỗi ảnh: `01_langfuse_list.png`, `02_langfuse_waterfall.png`, v.v.
   - Tạo tệp index: `docs/evidence/README.md` liệt kê những gì mỗi ảnh chứng minh

### Kết Quả Giao Hàng

- ✅ Dashboard 6 panel (định dạng trực quan hoặc có thể export)
- ✅ Dashboard hiển thị baseline (tất cả xanh)
- ✅ Dashboard hiển thị sự cố (vi phạm SLO hiển thị)
- ✅ 8+ ảnh chụp được đặt tên trong `docs/evidence/`
- ✅ Index bằng chứng có lời giải thích cho mỗi ảnh chụp
- 📄 Phần mô tả ngắn ở [docs/grading-evidence.md](./grading-evidence.md)

---

## Member F: Bản Báo Cáo + Dẫn Dắt Demo

**Thời lượng**: 2:30 - 3:50  
**Trách nhiệm**: Báo cáo cuối cùng, script demo, phối hợp team  
**Phụ thuộc**: Tất cả các member khác (đầu vào liên tục)

### Công Việc

1. **Cài đặt template báo cáo** (2:30 - 2:45)
   - Mở [docs/blueprint-template.md](./blueprint-template.md)
   - Điền phần: **Team Roster**
     ```markdown
     - Member A: [Tên] | Logging & PII
     - Member B: [Tên] | Tracing & Tags
     - Member C: [Tên] | SLO & Alerts
     - Member D: [Tên] | Load Test & Incidents
     - Member E: [Tên] | Dashboard & Evidence
     - Member F: [Tên] | Blueprint & Demo
     ```

2. **Thu thập báo cáo cá nhân** (2:45 - 3:15)
   - Yêu cầu từ mỗi member phần của họ:
     - **Member A**: Regex patterns PII, triển khai correlation ID
     - **Member B**: Langfuse tags, quyết định metadata trace
     - **Member C**: SLO baseline, cơ sở đặt ngưỡng cảnh báo
     - **Member D**: Bản tóm tắt tác động sự cố, phát hiện nguyên nhân gốc
     - **Member E**: Thiết kế dashboard, lựa chọn metric
     - **Member F** (bạn): Demo flow + Bài học team
   - Điền mỗi phần trong báo cáo với 2-3 bullet point cho mỗi member

3. **Soạn script demo** (3:15 - 3:35)
   - Tạo phần: **Demo Flow (5 phút live)**
     ```markdown
     1. Khởi động app + hiển thị baseline /health (30s)
     2. Gửi requests → hiển thị logs chảy vào logs.jsonl (30s)
     3. Hiển thị traces Langfuse với tags và latency (45s)
     4. Tiêm sự cố rag_slow, hiển thị spike metrics (60s)
     5. Giải thích trigger cảnh báo từ dashboard (30s)
     6. Vô hiệu hóa sự cố, hiển thị hồi phục (30s)
     7. Trả lời Q&A (thời gian còn lại)
     ```
   - Script các lệnh chính xác để tránh lỗi demo:
     ```bash
     # Baseline
     curl http://localhost:8000/health
     curl http://localhost:8000/metrics | jq .
     
     # Gửi requests
     python scripts/load_test.py --concurrency 3
     tail -5 data/logs.jsonl
     
     # Tiêm sự cố
     python scripts/inject_incident.py --scenario rag_slow
     sleep 2
     python scripts/load_test.py --concurrency 5
     curl http://localhost:8000/metrics | jq '.latency_p95'
     
     # Reset
     python scripts/inject_incident.py --scenario all --disable
     ```

4. **Chạy thử demo** (3:35 - 3:50)
   - Chạy script demo đầy đủ một lần
   - Tính thời gian mỗi phần để vừa 5-7 phút
   - Xác minh tất cả lệnh hoạt động
   - Chụp ảnh thành công states cho bằng chứng
   - Tạo kế hoạch dự phòng (ví dụ: trace được ghi trước nếu Langfuse chậm)

### Kết Quả Giao Hàng

- ✅ Hoàn thành [docs/blueprint-template.md](./blueprint-template.md) với tất cả phần được điền
- ✅ Team roster với tên members và roles
- ✅ Đóng góp cá nhân được ghi lại (2-3 bullet cho mỗi member)
- ✅ Script demo với các lệnh chính xác
- ✅ Chạy thử hoàn thành, thời gian được xác minh
- ✅ Kế hoạch dự phòng được ghi lại
- 📄 Báo cáo sẵn sàng để nộp

---

## 🎯 Checklist Bàn Giao

### Trước Demo (3:45)

- [ ] Tất cả TODO blocks trong code hoàn thành → `python scripts/validate_logs.py` ≥80/100
- [ ] ≥10 traces hiển thị trong Langfuse
- [ ] Dashboard 6 panel live và hiển thị metrics
- [ ] Luật cảnh báo được ghi lại với runbooks
- [ ] Ảnh chụp bằng chứng được thu thập ở `docs/evidence/`
- [ ] Tất cả sự cố của Member D bị vô hiệu hóa (`--scenario all --disable`)
- [ ] Git commits được push (tất cả members)
- [ ] Báo cáo được điền với đóng góp team

### Trong Demo (3:50 - 4:00)

- [ ] Member F chạy script demo live
- [ ] Hiển thị baseline metrics + logs + traces
- [ ] Tiêm rag_slow, hiển thị vi phạm SLO + cảnh báo
- [ ] Thể hiện nhận thức về tác động sự cố
- [ ] Team sẵn sàng trả lời các câu hỏi debug

### Sau Demo (4:00)

- [ ] Nộp báo cáo cho giảng viên
- [ ] Nộp ảnh chụp bằng chứng
- [ ] Xác minh tất cả commits được ghi nhận cho members đúng
- [ ] Ăn mừng! 🎉

---

## 📌 Các Điểm Bàn Giao Chính Giữa Members

| Từ | Tới | Kết Quả Giao Hàng | Trường Hợp Sử Dụng |
|------|----|----|----------|
| A | B | Logs chảy vào logs.jsonl | Xác minh tracing không làm hỏng logs |
| B | C | ≥10 traces trong Langfuse | Xác minh SLO thresholds so sánh với trace latency baseline |
| C | D | SLO yaml + luật cảnh báo | Member D dùng những thứ này làm tiêu chí pass/fail |
| D | E | Bản tóm tắt sự cố (JSON) | Dashboard hiển thị so sánh trước/sau |
| E | F | Ảnh chụp bằng chứng | Báo cáo tham chiếu bằng chứng hoàn thành |
| F | Tất cả | Script demo + câu hỏi | Team luyện Q&A trước demo live |

---

## 💡 Mẹo Cho Từng Member

### Member A
- Sử dụng `print(structlog_config)` để xác minh thứ tự processor
- Kiểm tra PII với: `python -c "from app.pii import scrub; print(scrub('Email: test@example.com'))"`

### Member B
- Sử dụng view "Generational" Langfuse để thấy request traces nhóm theo feature
- Thêm custom tags cho debug: `tags=["prod", "v1.2", "issue-123"]`

### Member C
- Sử dụng endpoint `/metrics` thường xuyên để calibrate thresholds (không đoán)
- Viết runbooks như bạn debug lúc 3 sáng—hãy cụ thể

### Member D
- Lưu tất cả bản tóm tắt JSON vào thư mục `data/` cho Member E
- Ghi lại lệnh tạo ra mỗi kết quả (để có thể lặp lại)

### Member E
- Phối hợp với Member D: yêu cầu export metrics thô trước khi build dashboard
- Làm dashboard có thể export thành ảnh (dễ hơn cho chứng minh chấm điểm)

### Member F
- Phối hợp script demo với múi giờ Langfuse của Member B (nếu dùng traces live)
- Chuẩn bị ảnh chụp backup nếu demo live thất bại (chụp lúc 3:40, dùng nếu cần)

