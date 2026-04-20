# Kịch bản Demo Member F (Blueprint + Demo Lead)

## 1) Mở đầu (20-30 giây)
- Xin chào giảng viên, nhóm B1-C401 xin demo hệ thống observability cho chatbot cảnh báo lỗi xe điện và hỗ trợ đặt lịch bảo dưỡng.
- Mục tiêu demo: chứng minh hệ thống đạt tiêu chí về Logging, Tracing, Dashboard, Alerting và có khả năng ứng phó sự cố.

## 2) Trình bày theo flow Metrics -> Traces -> Logs (90-120 giây)
- Metrics:
  - Mở dashboard 6 panels.
  - Chỉ các panel quan trọng: latency P95, traffic, quality proxy và nêu ngưỡng SLO.
- Traces:
  - Mở một trace waterfall đại diện.
  - Giải thích span tốn thời gian nhất và liên hệ với biến động trên panel latency.
- Logs:
  - Tìm log theo correlation_id của trace vừa mở.
  - Chỉ minh chứng PII đã được redact và các context field đã đầy đủ.

## 3) Mini-demo incident response (60-90 giây)
- Bật scenario `rag_slow` (nếu cần demo live), quan sát latency tăng.
- Trình bày root cause dựa trên traces + logs.
- Tắt incident, chạy lại request và xác nhận latency phục hồi.

## 4) Chốt kết quả (20-30 giây)
- `validate_logs` đạt target, traces >= 10, dashboard đủ 6 panels, runbook liên kết đầy đủ.
- Phân công thành viên rõ ràng, mỗi thành viên có evidence commit/PR.

## 5) Chiến lược Q&A (để Member F điều phối)
- Câu hỏi về PII -> chuyển Member A.
- Câu hỏi về tracing/span -> chuyển Member B.
- Câu hỏi về SLO/alerts/runbook -> chuyển Member C.
- Câu hỏi về load test/incident execution -> chuyển Member D.
- Câu hỏi tổng hợp report/demo -> Member F trả lời.
