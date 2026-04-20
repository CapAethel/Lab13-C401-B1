# Checklist Member E (Dashboard + Evidence)

## 1) Các việc có thể hoàn thành ngay (không phụ thuộc)
- Chốt 6 panel dashboard bắt buộc và đơn vị đo.
- Chuẩn bị quy ước đặt tên file bằng chứng và danh sách ảnh cần chụp.
- Soạn sẵn phần đóng góp cá nhân trong `docs/blueprint-template.md`.
- Chuẩn bị lời thoại demo ngắn cho phần dashboard.

## 2) Chuẩn thiết kế dashboard
- Latency: P50/P95/P99 theo milliseconds, có line SLO.
- Traffic: requests/phút (hoặc QPS), bật auto-refresh.
- Error rate: tỷ lệ % và breakdown theo loại lỗi.
- Cost: chi phí USD theo thời gian.
- Tokens: số token input/output theo thời gian.
- Quality proxy: tỷ lệ người dùng chấp nhận khuyến nghị (hoặc heuristic tương đương).

## 3) Quy ước tên file bằng chứng (khuyến nghị)
- `evidence/langfuse_trace_list_10plus.png`
- `evidence/langfuse_trace_waterfall.png`
- `evidence/log_correlation_id.png`
- `evidence/log_pii_redaction.png`
- `evidence/dashboard_6_panels.png`
- `evidence/alert_rules_runbook.png`

## 4) Lời thoại demo (60-90 giây)
- Mở đầu bằng tổng quan dashboard (6 panel và lý do tồn tại của từng panel).
- Chỉ ra một điểm vượt ngưỡng hoặc xu hướng bất thường.
- Chuyển sang bằng chứng trace (một trace waterfall đại diện).
- Xác nhận root cause bằng logs (correlation_id và chất lượng redaction).
- Kết thúc bằng tác động và alert/runbook cần được kích hoạt.

## 5) Handoff cần xin từ đồng đội
- Member A: 1 mẫu log sạch có correlation_id + 1 mẫu log đã redact PII.
- Member B: 1 màn hình danh sách trace ổn định + 1 trace waterfall đại diện.
- Member C: target SLO cuối cùng + ngưỡng alert đã chốt.
- Member D: thời điểm chạy load/incident để bạn chụp ảnh evidence bản cuối.

