# VFCare - Trợ lý AI Bảo dưỡng Xe VinFast

Agent AI sử dụng OpenAI function calling để chẩn đoán xe VinFast và gợi ý lịch bảo dưỡng.

## Architecture

```
flowchart:
  Hệ thống phát hiện lỗi → AI gợi ý lịch → User phản hồi:
    ├─ Chấp nhận → check_slot → book_appointment → QR check-in
    ├─ Xem thêm → explainability + confidence → chọn slot → book
    ├─ Từ chối  → hỏi lý do → dừng nhắc X ngày → learning signal
    └─ Chỉnh sửa → re-run recommend → confirm → book
```

## Cấu trúc file

| File | Mô tả |
|------|--------|
| `main.py` | Entry point - chạy chatbot trong terminal |
| `agent.py` | VFCareAgent class - OpenAI function calling loop |
| `tools.py` | 7 tools (diagnostic, recommend, check_slot, book, cancel, explainability) |
| `mock_data.py` | Dữ liệu mock: xe, lỗi, xưởng, slot |

## Cài đặt & Chạy

```bash
# 1. Cài thư viện
pip install -r requirements.txt

# 2. Set API key
set OPENAI_API_KEY=sk-your-key-here

# 3. (Tuỳ chọn) Đổi model
set OPENAI_MODEL=gpt-4o-mini

# 4. Chạy
cd VFCare
python main.py
```

## Mock Data

### Xe có sẵn
| Mã xe | Model | Chủ xe | Lỗi |
|-------|-------|--------|------|
| VF8-001 | VF8 | Nguyễn Văn An | 🔴 Pin cao áp + 🟡 Phanh mòn + 🟢 Đèn hậu |
| VF9-002 | VF9 | Trần Thị Bình | 🟡 Cửa không khít + 🟢 Điều hoà yếu |
| VFe34-003 | VFe34 | Lê Hoàng Cường | 🔴 Pin giảm dung lượng + 🟡 Giảm xóc rò + 🟢 Áp suất lốp |

### Xưởng
- WS-HN01: Cầu Giấy, Hà Nội (hỗ trợ critical)
- WS-HN02: Long Biên, Hà Nội
- WS-HCM01: Quận 7, TP.HCM (hỗ trợ critical)
- WS-HCM02: Thủ Đức, TP.HCM
- WS-HP01: Hải Phòng (hỗ trợ critical)

## Tools (Function Calling)

| Tool | Mô tả | Trigger |
|------|--------|---------|
| `get_vehicle_info` | Lấy thông tin xe | User cung cấp mã xe |
| `run_diagnostic` | Chẩn đoán lỗi xe | Tự động khi có mã xe |
| `recommend_schedule` | Gợi ý lịch theo severity | Sau diagnostic |
| `check_slot_availability` | Xem slot trống xưởng | User chọn xưởng |
| `book_appointment` | Đặt lịch bảo dưỡng | User xác nhận slot |
| `cancel_or_postpone` | Từ chối/hoãn | User từ chối |
| `get_explainability` | Giải thích AI + confidence | User muốn xem thêm |

## Ví dụ hội thoại

```
👤 Bạn: Xe tôi mã VF8-001, kiểm tra giúp tôi

🔧 Gọi tool: get_vehicle_info({"vehicle_id": "VF8-001"})
🔧 Gọi tool: run_diagnostic({"vehicle_id": "VF8-001"})

🤖 VFCare: Kết quả chẩn đoán xe VF8 (30A-12345) của anh An:

🔴 CRITICAL - BAT-0012: Pin cao áp suy giảm bất thường
   → Cần xử lý NGAY trong 24h

🟡 MEDIUM - BRK-0045: Má phanh trước mòn 82%
   → Nên sửa trong 3-5 ngày

🟢 LOW - LGT-0003: Đèn hậu phải nhấp nháy
   → Sửa linh hoạt trong 1-2 tuần

Anh muốn đặt lịch sửa lỗi nào trước?

👤 Bạn: Đặt lịch sửa pin gấp
🔧 Gọi tool: recommend_schedule({"vehicle_id":"VF8-001","error_code":"BAT-0012"})
...
```
