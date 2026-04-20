# Báo cáo Lab Observability Day 13

> **Hướng dẫn**: Điền đầy đủ các mục bên dưới. Báo cáo này được thiết kế để hệ thống chấm tự động đọc được, vì vậy cần giữ nguyên các tag (ví dụ: `[GROUP_NAME]`).

## 1. Thông tin nhóm
- `[GROUP_NAME]`: B1-C401
- `[REPO_URL]`: https://github.com/CapAethel/Lab13-C401-B1.git
- `[MEMBERS]`:
  - Member A: Chu Thị Ngọc Huyền | Role: Logging & PII
  - Member B: Nguyễn Văn Lĩnh | Role: Tracing & Enrichment
  - Member C: Nguyễn Mai Phương | Role: SLO & Alerts
  - Member D: Hứa Quang Linh | Role: Load Test & Dashboard
  - Member E: Chu Bá Tuấn Anh | Role: Demo & Report
  - Member F: Nguyễn Thị Tuyết | Role: Blueprint & Demo Lead

---

## 2. Kết quả nhóm (xác minh tự động)
- `[VALIDATE_LOGS_FINAL_SCORE]`: 100/100
- `[TOTAL_TRACES_COUNT]`: 20
- `[PII_LEAKS_FOUND]`: 0

---

## 3. Bằng chứng kỹ thuật (nhóm)

### 3.1 Logging và Tracing
- `[EVIDENCE_CORRELATION_ID_SCREENSHOT]`: [evidence/correlation_id_flow.png]
- `[EVIDENCE_PII_REDACTION_SCREENSHOT]`: [evidence/pii_redaction_logs.png]
- `[EVIDENCE_TRACE_WATERFALL_SCREENSHOT]`: [evidence/trace_waterfall_req-a88c09f1.png]
- `[TRACE_WATERFALL_EXPLANATION]`: Trong trace `req-a88c09f1` (session `s01`), span chat chính cho thấy độ trễ end-to-end khoảng 150ms và khớp với log từ `request_received` đến `response_sent` bằng cùng `correlation_id`. Span con đáng chú ý nhất là bước chuẩn bị ngữ cảnh retrieval/tool trước khi sinh câu trả lời: bước này hoàn thành nhanh, cho thấy độ trễ chủ yếu đến từ thời gian phản hồi của model, không phải tiền xử lý. Kết quả này cũng nhất quán với độ trễ ổn định trên các session (`s01`-`s10`), nên có thể kết luận chưa có dấu hiệu hồi quy tail-latency trong lần chạy này.

### 3.2 Dashboard và SLO
- `[DASHBOARD_6_PANELS_SCREENSHOT]`: [evidence/dashboard_6_panels.png]
- `[SLO_TABLE]`:
| SLI | Mục tiêu | Cửa sổ | Giá trị hiện tại |
|---|---:|---|---:|
| Latency P95 | < 3000ms | 28d | 241ms |
| Error Rate | < 2% | 28d | chưa có dữ liệu |
| Cost Budget | < $2.5/day | 1d | chưa có dữ liệu |
- `[DASHBOARD_PANEL_NOTES]`:
  - Latency P50/P95/P99 (ms) có đường ngưỡng SLO
  - Traffic (requests/phút)
  - Error rate (%), có breakdown theo loại lỗi
  - Cost theo thời gian (USD/giờ hoặc USD/ngày)
  - Tokens in/out (tokens/phút)
  - Quality proxy (tỷ lệ người dùng chấp nhận khuyến nghị %)

### 3.3 Alerts và Runbook
- `[ALERT_RULES_SCREENSHOT]`: [evidence/alert_rules_runbook.png]
- `[ALERT_RULES_REFERENCE]`: [docs/alert_rules.md](docs/alert_rules.md) — điều kiện kích hoạt, mức độ nghiêm trọng, PromQL, owner và chính sách escalation cho 5 cảnh báo
- `[SAMPLE_RUNBOOK_LINK]`: [docs/runbook.md#1-high-latency-p95](docs/runbook.md) — hướng dẫn chẩn đoán và khắc phục theo từng bước cho 5 kịch bản

---

## 4. Ứng phó sự cố (nhóm)
- `[SCENARIO_NAME]`: rag_slow
- `[SYMPTOMS_OBSERVED]`:
  - Dashboard cho thấy thay đổi rõ ở panel latency: P95 tăng so với baseline khi kích hoạt incident.
  - Trace vẫn thành công nhưng thời gian xử lý tăng, phù hợp với triệu chứng "hệ thống chậm".
  - Log giữ nguyên correlation_id xuyên suốt, không có lỗi runtime 500 trong đợt kiểm tra này.
- `[ROOT_CAUSE_PROVED_BY]`:
  - Endpoint health ghi nhận incident toggle `rag_slow=true` trong thời gian test.
  - Trace waterfall cho thấy span truy xuất/chuẩn bị context kéo dài hơn baseline.
  - Sau khi tắt toggle `rag_slow`, latency quay về mức ổn định.
- `[FIX_ACTION]`:
  - Tắt incident toggle: `POST /incidents/rag_slow/disable`.
  - Chạy lại load test để xác nhận latency giảm về baseline.
  - Đối chiếu dashboard, trace, log theo luồng Metrics -> Traces -> Logs.
- `[PREVENTIVE_MEASURE]`:
  - Giữ alert latency P95 để phát hiện sớm regression.
  - Bổ sung checklist "incident flags OFF" trước demo.
  - Duy trì runbook xử lý rag_slow và diễn tập quy trình response định kỳ.

---

## 5. Đóng góp cá nhân và bằng chứng

### Chu Thị Ngọc Huyền
- `[TASKS_COMPLETED]`:
  - Triển khai và tinh chỉnh pipeline logging dạng JSON theo schema của lab.
  - Thực hiện che giấu PII trong log (email, số điện thoại, CCCD, thẻ, passport, địa chỉ) và kiểm tra không rò rỉ.
  - Bổ sung/điều chỉnh xử lý scrub để đảm bảo dữ liệu nhạy cảm được làm sạch trước khi ghi log.
- `[EVIDENCE_LINK]`: https://github.com/CapAethel/Lab13-C401-B1/commit/4511a2f8f0994574bfc928fe792a022f82a17c42
  - `[PR_MEMBER_A_LOGGING_PII]`
  - `[COMMIT_MEMBER_A_1]`
  - `[COMMIT_MEMBER_A_2]`

### Nguyễn Văn Lĩnh
- `[TASKS_COMPLETED]`: 
  - Tích hợp tracing và metadata tags cho các request chính trong luồng chat.
  - Xác minh trace list đạt tối thiểu 10 traces và cung cấp trace waterfall phục vụ báo cáo.
  - Đối chiếu span timing với log theo correlation_id để hỗ trợ phân tích nguyên nhân sự cố.
- `[EVIDENCE_LINK]`: https://github.com/CapAethel/Lab13-C401-B1/commit/d2f96cd7337736ae21f068ec475584bf4799604b 
  - `[PR_MEMBER_B_TRACING]`
  - `[COMMIT_MEMBER_B_1]`
  - `[COMMIT_MEMBER_B_2]`

### Nguyễn Mai Phương
- `[TASKS_COMPLETED]`: 
  - Thiết lập và hiệu chỉnh SLO cho latency, error rate, cost/quality theo mục tiêu nhóm.
  - Cấu hình alert rules và liên kết runbook cho các kịch bản cảnh báo chính.
  - Kiểm tra ngưỡng cảnh báo bằng dữ liệu test và cập nhật tài liệu vận hành.
- `[EVIDENCE_LINK]`: https://github.com/CapAethel/Lab13-C401-B1/commit/abec0f54c59f63b1a3df8f56430416a5b1f425b3 
  - `[PR_MEMBER_C_SLO_ALERTS]`
  - `[COMMIT_MEMBER_C_1]`
  - `[COMMIT_MEMBER_C_2]`

### Hứa Quang Linh
- `[TASKS_COMPLETED]`: 
  - Thực thi load test nhiều mức concurrency và thu thập baseline metrics.
  - Chạy các kịch bản incident injection (`rag_slow`, `tool_fail`, `cost_spike`) và lưu execution artifacts.
  - Bàn giao dữ liệu tổng hợp để nhóm dùng cho dashboard, incident response và evidence.
- `[EVIDENCE_LINK]`: https://github.com/CapAethel/Lab13-C401-B1/commit/830d135d0e728ff669a62d6eb367d276d0c2846f 
  - `[PR_MEMBER_D_LOADTEST_INCIDENT]`
  - `[COMMIT_MEMBER_D_1]`
  - `[COMMIT_MEMBER_D_2]`

### Chu Bá Tuấn Anh
- `[TASKS_COMPLETED]`:
  - Chuẩn bị và hoàn thiện bộ dashboard 6 panel theo checklist kỹ thuật của lab.
  - Tổng hợp ảnh chụp evidence (dashboard, trace, log, alert) và kiểm tra tính nhất quán nội dung.
  - Hỗ trợ phần trình bày demo/report theo luồng quan sát, đảm bảo thông điệp ngắn gọn và đúng trọng tâm.
- `[EVIDENCE_LINK]`: https://github.com/CapAethel/Lab13-C401-B1/commit/94859f3097d0c6fede03f29a223a9a4b29476635
  - `[PR_MEMBER_E_DASHBOARD_EVIDENCE]`
  - `[COMMIT_MEMBER_E_1]`
  - `[COMMIT_MEMBER_E_2]`

### Nguyễn Thị Tuyết
- `[TASKS_COMPLETED]`:
  - Tổng hợp và chuẩn hóa blueprint report, đảm bảo đầy đủ metadata, technical evidence, incident response và phân công thành viên.
  - Điều phối demo theo flow observability: Metrics -> Traces -> Logs, phân bổ người trình bày theo role và cảnh báo rủi ro trước demo.
  - Kiểm tra tính nhất quán giữa dashboard, traces, logs, alert/runbook links để đảm bảo bài demo có logic và có thể defend khi vấn đáp.
  - Chốt bộ tài liệu demo và checklist pass-safe cho buổi báo cáo.
- `[EVIDENCE_LINK]`: https://github.com/CapAethel/Lab13-C401-B1/commit/f2490270d76a7543d3b9f49355c5907a31023a5c 
  - `[PR_BLUEPRINT_AND_DEMO_LEAD_LINK]`
  - `[COMMIT_LINK_MEMBER_F_1]`
  - `[COMMIT_LINK_MEMBER_F_2]`
---

## 6. Hạng mục cộng điểm (tùy chọn)
- `[BONUS_COST_OPTIMIZATION]`: (Mô tả + bằng chứng)
- `[BONUS_AUDIT_LOGS]`: (Mô tả + bằng chứng)
- `[BONUS_CUSTOM_METRIC]`: (Mô tả + bằng chứng)
