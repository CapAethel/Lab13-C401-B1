# VFCare Agent — Flow Overview

> Tài liệu tổng quát flow của AI Agent, dành cho dev đọc nhanh trước khi code.

---

## Kiến trúc

```text
User (Streamlit / Terminal)
  │
  ▼
┌─────────────┐    OpenAI API     ┌──────────────────┐
│  agent.py   │ ◄──────────────► │  gpt-4o-mini     │
│  (chat loop)│   function calling │  (hoặc model khác)│
└──────┬──────┘                   └──────────────────┘
       │
       ▼
┌─────────────┐     ┌────────────────┐
│  tools.py   │ ◄── │ mock_data.py   │
│  (8 tools)  │     │ (xe, lỗi, xưởng)│
└─────────────┘     └────────────────┘
```

**Files chính:**

| File | Mô tả |
|------|--------|
| `system_prompt.txt` | System prompt (tag-based), tone cute hài hước |
| `agent.py` | VFCareAgent class, load prompt từ txt, chat loop xử lý tool calls |
| `tools.py` | 8 tool functions + TOOL_DEFINITIONS + TOOL_MAP |
| `mock_data.py` | Dữ liệu mock: 1 xe, 3 lỗi, 5 xưởng HN, slots, bookings |
| `app.py` | Streamlit Web UI |
| `main.py` | Terminal chatbot |

---

## Flow chính

```
┌──────────────────────────────────────────────────────────┐
│ BƯỚC 1: get_user_info (auto)                             │
│ → Lấy thông tin chủ xe + xe + vị trí                     │
│ → Chào user                                              │
├──────────────────────────────────────────────────────────┤
│ BƯỚC 2: run_diagnostic (auto)                            │
│ → Quét tất cả lỗi xe, sắp xếp theo severity              │
│ → Trả về: critical → medium → low                        │
├──────────────────────────────────────────────────────────┤
│ BƯỚC 3: Báo cáo kết quả                                  │
│ → [CRITICAL] nhấn mạnh khẩn cấp                          │
│ → [MEDIUM] nhắc nhẹ                                      │
│ → [LOW] pha trò                                          │
├──────────────────────────────────────────────────────────┤
│ BƯỚC 4: Hỏi user "Có muốn đặt lịch không?"               │
│ ⚠ KHÔNG tự gọi recommend_schedule. CHỜ user trả lời.    │
└─────────────────┬────────────────────────────────────────┘
                  │
        ┌─────────┴──────────┐
        ▼                    ▼
   User ĐỒNG Ý         User TỪ CHỐI / HOÃN
        │                    │
        ▼                    ▼
┌───────────────┐    ┌──────────────────────┐
│ BƯỚC 5:       │    │ cancel_or_postpone   │
│ recommend_    │    │ (xem chi tiết bên    │
│ schedule      │    │  dưới)               │
│ → xưởng gần   │    └──────────────────────┘
│ → khoảng cách │
└───────┬───────┘
        │
  ┌─────┴──────────────────┐
  ▼                        ▼
User CHẤP NHẬN       User XEM THÊM
  │                        │
  ▼                        ▼
check_slot_availability   get_explainability
  │                        (confidence, rủi ro)
  ▼
book_appointment
  │
  ▼
Thông báo QR check-in ✅
```

---

## Flow Hoãn / Từ chối (cancel_or_postpone)

Flow này có **2-3 bước** tuỳ severity:

```
User muốn hoãn
  │
  ▼
BƯỚC 1: cancel_or_postpone(error_code)     ← chưa có reason
  │     → trả về 3 lựa chọn lý do
  │
  ▼
Agent hỏi user chọn lý do:
  ┌─ "Mới bảo dưỡng xong"  (moi_bao_duong)
  ├─ "Chưa cần thiết"       (chua_can)
  └─ "Lý do khác"           (khac)
  │
  ▼
BƯỚC 2: cancel_or_postpone(error_code, reason)
  │
  ├─── [CRITICAL] ──────────────────────────────┐
  │    → Cảnh báo nguy hiểm                     │
  │    → 2 lựa chọn:                            │
  │      a) Đặt lịch ngay → recommend_schedule  │
  │      b) Vẫn hoãn → BƯỚC 3                   │
  │                        │                    │
  │                        ▼                    │
  │    BƯỚC 3: cancel_or_postpone(              │
  │              error_code, reason,            │
  │              confirm_critical=true)         │
  │    → "Nhắc lại khi bật xe lần sau"          │
  │                                             │
  ├─── [MEDIUM] ────────────────────────────────┐
  │    → hỏi nhắc lại sau bao nhiêu ngày        │
  │      (gợi ý: 3 / 5 / 7 / 14)                │
  │    → cancel_or_postpone(snooze_days=N)      │
  │    → "Nhắc lại sau N ngày"                  │
  │                                             │
  └─── [LOW] ───────────────────────────────────┘
       → Ghi nhận, nhắn nhẹ đến sớm nhất
```

---

## Danh sách Tools (8 tools)

| # | Tool | Params | Mô tả |
|---|------|--------|--------|
| 0 | `get_user_info` | — | Thông tin chủ xe + xe + vị trí. Gọi đầu tiên. |
| 1 | `get_vehicle_info` | — | Thông tin chi tiết xe (raw VEHICLE dict) |
| 2 | `run_diagnostic` | — | Quét lỗi xe, trả danh sách theo severity |
| 3 | `recommend_schedule` | `error_code` | Gợi ý xưởng + slot theo severity + khoảng cách |
| 4 | `check_slot_availability` | `workshop_id`, `date?` | Xem slot trống của xưởng |
| 5 | `book_appointment` | `workshop_id`, `slot_id`, `error_codes[]`, `note?` | Đặt lịch, trả QR code |
| 6 | `cancel_or_postpone` | `error_code`, `reason?`, `snooze_days?`, `confirm_critical?` | Hoãn/từ chối, logic theo severity |
| 7 | `get_explainability` | `error_code` | Confidence score, rủi ro, lịch sử xe tương tự |

---

## Mock Data

| Dữ liệu | Chi tiết |
|----------|----------|
| Xe | VF8-001, 2024, biển 30A-12345, ODO 35,200km, pin 87% |
| Vị trí | Đống Đa, Hà Nội (21.017, 105.823) |
| Lỗi | `BAT-0012` critical (pin), `BRK-0045` medium (phanh), `LGT-0003` low (đèn) |
| Xưởng | 5 xưởng HN, khoảng cách 2.8km → 12.3km (Haversine) |
| Slots | Auto-generated 3 ngày, 4 slot/ngày, random available |

---

## Chạy nhanh

```bash
# Terminal
cd VFCare
pip install -r requirements.txt
cp .env.example .env  # thêm OPENAI_API_KEY
python main.py

# Web UI
streamlit run app.py
```
