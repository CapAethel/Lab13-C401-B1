"""
Tools cho VFCare Agent - các hàm mà LLM có thể gọi thông qua function calling.
Mỗi tool tương ứng 1 bước trong flowchart.
Chạy trên 1 xe duy nhất, xưởng Hà Nội, có khoảng cách.
"""

import json
from datetime import datetime
from .mock_data import VEHICLE, VEHICLE_ERRORS, WORKSHOPS, WORKSHOP_SLOTS, BOOKINGS


# ──────────────────────────────────────────────────────────────
# 0. get_user_info - Lấy thông tin người dùng + xe
# ──────────────────────────────────────────────────────────────
def get_user_info() -> str:
    """Trả về thông tin chủ xe và xe VinFast."""
    user_info = {
        "owner": VEHICLE["owner"],
        "phone": VEHICLE["phone"],
        "vehicle": {
            "id": VEHICLE["id"],
            "model": VEHICLE["model"],
            "year": VEHICLE["year"],
            "license_plate": VEHICLE["license_plate"],
            "odometer_km": VEHICLE["odometer_km"],
            "battery_health_pct": VEHICLE["battery_health_pct"],
            "last_maintenance": VEHICLE["last_maintenance"],
            "warranty_until": VEHICLE["warranty_until"],
        },
        "location": {
            "area": "Đống Đa, Hà Nội",
            "lat": VEHICLE["current_lat"],
            "lng": VEHICLE["current_lng"],
        },
    }
    return json.dumps(user_info, ensure_ascii=False)


# ──────────────────────────────────────────────────────────────
# 1. get_vehicle_info - Lấy thông tin xe (duy nhất)
# ──────────────────────────────────────────────────────────────
def get_vehicle_info() -> str:
    """Trả về thông tin chi tiết của xe VinFast."""
    return json.dumps(VEHICLE, ensure_ascii=False)


# ──────────────────────────────────────────────────────────────
# 2. run_diagnostic - Chạy diagnostic, trả về danh sách lỗi
# ──────────────────────────────────────────────────────────────
def run_diagnostic() -> str:
    """Chạy chẩn đoán xe, trả về danh sách lỗi hiện tại kèm mức độ nghiêm trọng."""
    errors = VEHICLE_ERRORS
    if not errors:
        return json.dumps({"vehicle_id": VEHICLE["id"], "status": "OK", "errors": [], "message": "Xe không có lỗi nào được phát hiện."}, ensure_ascii=False)

    severity_order = {"critical": 0, "medium": 1, "low": 2}
    sorted_errors = sorted(errors, key=lambda e: severity_order.get(e["severity"], 3))

    result = {
        "vehicle_id": VEHICLE["id"],
        "model": VEHICLE["model"],
        "license_plate": VEHICLE["license_plate"],
        "odometer_km": VEHICLE["odometer_km"],
        "total_errors": len(sorted_errors),
        "critical_count": sum(1 for e in sorted_errors if e["severity"] == "critical"),
        "medium_count": sum(1 for e in sorted_errors if e["severity"] == "medium"),
        "low_count": sum(1 for e in sorted_errors if e["severity"] == "low"),
        "errors": sorted_errors,
    }
    return json.dumps(result, ensure_ascii=False)


# ──────────────────────────────────────────────────────────────
# 3. recommend_schedule - Gợi ý lịch bảo dưỡng dựa trên severity
# ──────────────────────────────────────────────────────────────
def recommend_schedule(error_code: str) -> str:
    """
    Dựa trên mức độ lỗi, gợi ý lịch bảo dưỡng:
    - critical → xưởng GẦN NHẤT hỗ trợ critical, slot sớm nhất
    - medium → xưởng gần có slot trống, sắp xếp theo khoảng cách
    - low → gợi ý thời gian sửa linh hoạt
    Trả về khoảng cách (km) từ vị trí hiện tại đến xưởng.
    """
    target_error = next((e for e in VEHICLE_ERRORS if e["error_code"] == error_code), None)
    if not target_error:
        return json.dumps({"error": f"Không tìm thấy lỗi {error_code}"}, ensure_ascii=False)

    severity = target_error["severity"]

    if severity == "critical":
        # Critical: CHỈ xưởng hỗ trợ critical, SẮP XẾP theo khoảng cách GẦN NHẤT
        eligible = [ws for ws in WORKSHOPS if ws["supports_critical"]]
        eligible.sort(key=lambda ws: ws["distance_km"])
        recommendations = []
        for ws in eligible:
            slots = WORKSHOP_SLOTS.get(ws["id"], [])
            available = [s for s in slots if s["available"]]
            if available:
                earliest = available[0]
                recommendations.append({
                    "workshop": ws["name"],
                    "workshop_id": ws["id"],
                    "address": ws["address"],
                    "phone": ws["phone"],
                    "rating": ws["rating"],
                    "distance_km": ws["distance_km"],
                    "earliest_slot": earliest,
                    "urgency": "KHẨN CẤP - Cần đến xưởng trong 24h",
                })
        return json.dumps({
            "error": target_error,
            "severity": "critical",
            "message": "⚠️ LỖI NGHIÊM TRỌNG - Cần xử lý NGAY. Xưởng gần nhất được ưu tiên.",
            "recommendations": recommendations,
        }, ensure_ascii=False)

    elif severity == "medium":
        # Medium: tất cả xưởng, sắp xếp theo khoảng cách, lọc có slot free
        sorted_ws = sorted(WORKSHOPS, key=lambda ws: ws["distance_km"])
        recommendations = []
        for ws in sorted_ws:
            slots = WORKSHOP_SLOTS.get(ws["id"], [])
            available = [s for s in slots if s["available"]]
            if available:
                recommendations.append({
                    "workshop": ws["name"],
                    "workshop_id": ws["id"],
                    "address": ws["address"],
                    "phone": ws["phone"],
                    "rating": ws["rating"],
                    "distance_km": ws["distance_km"],
                    "available_slots_count": len(available),
                    "next_3_slots": available[:3],
                    "urgency": "NÊN SỬA TRONG 3-5 NGÀY",
                })
        return json.dumps({
            "error": target_error,
            "severity": "medium",
            "message": "🔶 LỖI TRUNG BÌNH - Nên sửa trong 3-5 ngày tới",
            "recommendations": recommendations[:3],
        }, ensure_ascii=False)

    else:  # low
        sorted_ws = sorted(WORKSHOPS, key=lambda ws: ws["distance_km"])
        recommendations = []
        for ws in sorted_ws:
            slots = WORKSHOP_SLOTS.get(ws["id"], [])
            available = [s for s in slots if s["available"]]
            if available:
                weekend_slots = [s for s in available if datetime.strptime(s["date"], "%Y-%m-%d").weekday() >= 5]
                afternoon_slots = [s for s in available if int(s["start_time"].split(":")[0]) >= 14]
                recommendations.append({
                    "workshop": ws["name"],
                    "workshop_id": ws["id"],
                    "address": ws["address"],
                    "rating": ws["rating"],
                    "distance_km": ws["distance_km"],
                    "weekend_slots": weekend_slots[:3],
                    "afternoon_slots": afternoon_slots[:3],
                    "urgency": "LINH HOẠT - Sửa trong 1-2 tuần",
                })
        return json.dumps({
            "error": target_error,
            "severity": "low",
            "message": "🟢 LỖI NHẸ - Có thể lên lịch linh hoạt trong 1-2 tuần",
            "recommendations": recommendations[:3],
        }, ensure_ascii=False)


# ──────────────────────────────────────────────────────────────
# 4. check_slot_availability - Kiểm tra slot trống
# ──────────────────────────────────────────────────────────────
def check_slot_availability(workshop_id: str, date: str = None) -> str:
    """Kiểm tra các slot trống của xưởng, có thể lọc theo ngày."""
    slots = WORKSHOP_SLOTS.get(workshop_id, [])
    if not slots:
        return json.dumps({
            "error": f"Không tìm thấy xưởng {workshop_id}",
            "fallback": {
                "hotline": "1900 23 23 89",
                "message": "Vui lòng gọi hotline để được hỗ trợ đặt lịch trực tiếp.",
                "can_retry": True,
                "retry_suggestion": "Thử kiểm tra xưởng khác hoặc ngày khác.",
            },
        }, ensure_ascii=False)

    available = [s for s in slots if s["available"]]
    if date:
        available = [s for s in available if s["date"] == date]

    if not available:
        # Gợi ý ngày khác có slot
        all_available = [s for s in slots if s["available"]]
        other_dates = sorted(set(s["date"] for s in all_available))[:3]
        workshop = next((ws for ws in WORKSHOPS if ws["id"] == workshop_id), {})
        return json.dumps({
            "workshop_id": workshop_id,
            "workshop_name": workshop.get("name", ""),
            "total_available": 0,
            "slots": [],
            "fallback": {
                "hotline": "1900 23 23 89",
                "message": f"Ngày {date} không còn slot trống." if date else "Xưởng hiện không còn slot trống.",
                "can_retry": True,
                "retry_suggestion": "Thử chọn ngày hoặc xưởng khác.",
                "other_available_dates": other_dates,
            },
        }, ensure_ascii=False)

    workshop = next((ws for ws in WORKSHOPS if ws["id"] == workshop_id), {})
    return json.dumps({
        "workshop_id": workshop_id,
        "workshop_name": workshop.get("name", ""),
        "total_available": len(available),
        "slots": available[:10],
    }, ensure_ascii=False)


# ──────────────────────────────────────────────────────────────
# 5. book_appointment - Đặt lịch bảo dưỡng
# ──────────────────────────────────────────────────────────────
def book_appointment(workshop_id: str, slot_id: str, error_codes: list[str], note: str = "") -> str:
    """Đặt lịch bảo dưỡng cho xe tại xưởng, slot cụ thể."""
    vehicle = VEHICLE

    workshop = next((ws for ws in WORKSHOPS if ws["id"] == workshop_id), None)
    if not workshop:
        return json.dumps({
            "error": f"Không tìm thấy xưởng {workshop_id}",
            "fallback": {
                "hotline": "1900 23 23 89",
                "message": "Xưởng không tồn tại. Vui lòng gọi hotline để được hỗ trợ.",
                "can_retry": True,
                "retry_suggestion": "Gọi lại recommend_schedule để chọn xưởng khác.",
            },
        }, ensure_ascii=False)

    slots = WORKSHOP_SLOTS.get(workshop_id, [])
    target_slot = next((s for s in slots if s["slot_id"] == slot_id and s["available"]), None)
    if not target_slot:
        # Gợi ý slot trống khác tại cùng xưởng
        other_available = [s for s in slots if s["available"]][:3]
        return json.dumps({
            "error": f"Slot {slot_id} không khả dụng hoặc đã được đặt.",
            "fallback": {
                "hotline": "1900 23 23 89",
                "message": "Slot đã hết. Bạn có thể chọn slot khác hoặc gọi hotline.",
                "can_retry": True,
                "retry_suggestion": "Chọn slot trống khác tại cùng xưởng hoặc đổi xưởng.",
                "alternative_slots": other_available,
            },
        }, ensure_ascii=False)

    # Đánh dấu slot đã đặt
    target_slot["available"] = False

    booking = {
        "booking_id": f"BK-{len(BOOKINGS)+1:04d}",
        "vehicle_id": vehicle["id"],
        "vehicle_model": vehicle["model"],
        "owner": vehicle["owner"],
        "phone": vehicle["phone"],
        "license_plate": vehicle["license_plate"],
        "workshop_id": workshop_id,
        "workshop_name": workshop["name"],
        "workshop_address": workshop["address"],
        "date": target_slot["date"],
        "time": f'{target_slot["start_time"]} - {target_slot["end_time"]}',
        "error_codes": error_codes,
        "note": note,
        "status": "confirmed",
        "qr_checkin_code": f"QR-{vehicle['id']}-{target_slot['slot_id']}",
        "created_at": datetime.now().isoformat(),
    }
    BOOKINGS.append(booking)

    return json.dumps({
        "success": True,
        "message": "✅ Đặt lịch thành công!",
        "booking": booking,
        "reminder": f"Nhắc nhở: Bạn có lịch bảo dưỡng vào {target_slot['date']} lúc {target_slot['start_time']} tại {workshop['name']}",
    }, ensure_ascii=False)


# ──────────────────────────────────────────────────────────────
# 6. cancel_or_postpone - Từ chối / Hoãn bảo dưỡng
#    Hành vi khác nhau theo severity:
#    - critical: cảnh báo mạnh, hỏi xác nhận lần nữa, nhắc lần bật xe sau
#    - medium: user chọn số ngày nhắc lại
#    - low: nhắn nhẹ nhàng đến sớm nhất
# ──────────────────────────────────────────────────────────────
def cancel_or_postpone(error_code: str, reason: str = "", snooze_days: int = 0, confirm_critical: bool = False) -> str:
    """Ghi nhận user từ chối/hoãn bảo dưỡng. Hành vi phụ thuộc severity của lỗi."""
    from datetime import timedelta

    target_error = next((e for e in VEHICLE_ERRORS if e["error_code"] == error_code), None)
    if not target_error:
        return json.dumps({"error": f"Không tìm thấy lỗi {error_code}"}, ensure_ascii=False)

    severity = target_error["severity"]

    # ── BƯỚC 1: Hỏi lý do hoãn (áp dụng cho cả 3 severity) ──
    valid_reasons = ["moi_bao_duong", "chua_can", "khac"]
    if not reason or reason not in valid_reasons:
        return json.dumps({
            "vehicle_id": VEHICLE["id"],
            "error": target_error,
            "action": "awaiting_reason",
            "severity": severity,
            "message": "Trước tiên, cho tôi biết lý do bạn muốn hoãn bảo dưỡng nhé?",
            "reason_options": [
                {"value": "moi_bao_duong", "label": "Mới bảo dưỡng xong gần đây"},
                {"value": "chua_can", "label": "Chưa cần thiết / chưa tiện"},
                {"value": "khac", "label": "Lý do khác"},
            ],
        }, ensure_ascii=False)

    # ── BƯỚC 2: Đã có lý do → xử lý theo severity ───────────

    # ── CRITICAL ──────────────────────────────────────────────
    if severity == "critical":
        if not confirm_critical:
            # Lần gọi đầu: cảnh báo mạnh, yêu cầu xác nhận
            return json.dumps({
                "vehicle_id": VEHICLE["id"],
                "error": target_error,
                "action": "pending_confirmation",
                "severity": "critical",
                "warning": "⚠️ ĐÂY LÀ LỖI NGHIÊM TRỌNG! Việc hoãn bảo dưỡng có thể gây nguy hiểm cho bạn và xe.",
                "message": "Lỗi này rất nghiêm trọng và có nguy cơ gây hỏng nặng hơn. Bạn thật sự muốn hoãn bảo dưỡng không?",
                "options": ["Không, tôi sẽ đặt lịch ngay", "Có, tôi muốn hoãn"],
            }, ensure_ascii=False)
        else:
            # User xác nhận hoãn → nhắc lại lần bật xe sau
            return json.dumps({
                "vehicle_id": VEHICLE["id"],
                "error": target_error,
                "action": "postponed_critical",
                "severity": "critical",
                "reason": reason,
                "snooze_type": "next_ignition",
                "message": "Đã ghi nhận. Hệ thống sẽ nhắc lại ngay khi bạn bật xe lần sau. Xin hãy cân nhắc sửa chữa sớm nhất có thể!",
                "learning_signal": {"type": "override", "reason": reason, "severity": "critical", "vehicle_id": VEHICLE["id"]},
            }, ensure_ascii=False)

    # ── MEDIUM ────────────────────────────────────────────────
    elif severity == "medium":
        if snooze_days <= 0:
            # Chưa có số ngày → yêu cầu user chọn
            return json.dumps({
                "vehicle_id": VEHICLE["id"],
                "error": target_error,
                "action": "awaiting_snooze_days",
                "severity": "medium",
                "message": "Tôi sẽ nhắc lại sau một số ngày. Bạn muốn được nhắc lại sau bao nhiêu ngày?",
                "suggested_days": [3, 5, 7, 14],
            }, ensure_ascii=False)
        else:
            # Có số ngày → ghi nhận
            snooze_until = (datetime.now().replace(hour=0, minute=0, second=0) +
                            timedelta(days=snooze_days)).strftime("%Y-%m-%d")
            return json.dumps({
                "vehicle_id": VEHICLE["id"],
                "error": target_error,
                "action": "postponed",
                "severity": "medium",
                "reason": reason,
                "snooze_days": snooze_days,
                "snooze_until": snooze_until,
                "message": f"Đã ghi nhận. Tôi sẽ nhắc lại sau {snooze_days} ngày (vào ngày {snooze_until}) nhé!",
                "learning_signal": {"type": "override", "reason": reason, "severity": "medium", "vehicle_id": VEHICLE["id"]},
            }, ensure_ascii=False)

    # ── LOW ───────────────────────────────────────────────────
    else:
        return json.dumps({
            "vehicle_id": VEHICLE["id"],
            "error": target_error,
            "action": "noted",
            "severity": "low",
            "reason": reason,
            "message": "Đã ghi nhận! Lỗi này không quá gấp, nhưng bạn hãy đến cơ sở bảo dưỡng trong thời gian gần nhất nhé!",
            "learning_signal": {"type": "override", "reason": reason, "severity": "low", "vehicle_id": VEHICLE["id"]},
        }, ensure_ascii=False)


# ──────────────────────────────────────────────────────────────
# 7. get_explainability - Giải thích confidence score
# ──────────────────────────────────────────────────────────────
def get_explainability(error_code: str) -> str:
    """Trả về thông tin giải thích tại sao AI gợi ý bảo dưỡng, confidence score, lịch sử."""
    vehicle = VEHICLE
    target = next((e for e in VEHICLE_ERRORS if e["error_code"] == error_code), None)

    if not target:
        return json.dumps({"error": "Không tìm thấy dữ liệu"}, ensure_ascii=False)

    # Mock confidence và risk
    severity_confidence = {"critical": 0.95, "medium": 0.82, "low": 0.68}
    severity_risk = {
        "critical": "RẤT CAO - 89% xe có lỗi tương tự gặp sự cố trong 7 ngày nếu không sửa",
        "medium": "TRUNG BÌNH - 45% xe có lỗi tương tự cần sửa chữa nặng hơn sau 30 ngày",
        "low": "THẤP - 12% xe có lỗi tương tự phát sinh thêm vấn đề trong 60 ngày",
    }

    return json.dumps({
        "error": target,
        "confidence_score": severity_confidence.get(target["severity"], 0.5),
        "risk_analysis": severity_risk.get(target["severity"], "Không xác định"),
        "vehicle_history": {
            "total_km": vehicle["odometer_km"],
            "last_maintenance": vehicle["last_maintenance"],
            "battery_health": f'{vehicle["battery_health_pct"]}%',
            "days_since_last_maintenance": (datetime(2026, 4, 9) - datetime.strptime(vehicle["last_maintenance"], "%Y-%m-%d")).days,
        },
        "similar_cases": "Trong 1000 xe VinFast cùng model, {} xe đã gặp sự cố khi trì hoãn.".format(
            {"critical": 890, "medium": 450, "low": 120}.get(target["severity"], 0)
        ),"recommendation": "Dựa trên phân tích AI với dữ liệu từ hàng nghìn xe VinFast, chúng tôi khuyến nghị xử lý lỗi này theo mức ưu tiên đã đề xuất.",}, ensure_ascii=False)


# ──────────────────────────────────────────────────────────────
# 8. estimate_maintenance_cost - Ước tính chi phí bảo dưỡng
# ──────────────────────────────────────────────────────────────
def estimate_maintenance_cost(error_codes: list[str], workshop_id: str = "") -> str:
    """
    Ước tính chi phí sửa chữa theo danh sách mã lỗi.
    - Áp dụng giảm giá bảo hành cho hạng mục pin cao áp nếu xe còn bảo hành.
    - Trả về breakdown từng lỗi + tổng tiền tạm tính.
    """
    if not error_codes:
        return json.dumps({"error": "Vui lòng cung cấp ít nhất 1 mã lỗi."}, ensure_ascii=False)

    # Bảng giá mock theo mã lỗi
    base_price_map = {
        "BAT-0012": {"label": "Kiểm tra/cân bằng pin cao áp", "parts": 4200000, "labor": 1200000},
        "BRK-0045": {"label": "Thay má phanh trước", "parts": 1450000, "labor": 650000},
        "LGT-0003": {"label": "Sửa/thay cụm đèn hậu", "parts": 550000, "labor": 250000},
    }

    now_date = datetime.now().date()
    warranty_until = datetime.strptime(VEHICLE["warranty_until"], "%Y-%m-%d").date()
    in_warranty = now_date <= warranty_until

    selected_workshop = next((ws for ws in WORKSHOPS if ws["id"] == workshop_id), None) if workshop_id else None
    workshop_name = selected_workshop["name"] if selected_workshop else "Chưa chọn xưởng"

    line_items = []
    subtotal_parts = 0
    subtotal_labor = 0
    total_discount = 0
    unknown_codes = []

    for code in error_codes:
        pricing = base_price_map.get(code)
        if not pricing:
            unknown_codes.append(code)
            continue

        parts_cost = pricing["parts"]
        labor_cost = pricing["labor"]
        discount = 0

        # Giảm 20% tiền công cho lỗi pin nếu còn bảo hành
        if code == "BAT-0012" and in_warranty:
            discount = int(labor_cost * 0.2)

        subtotal_parts += parts_cost
        subtotal_labor += labor_cost
        total_discount += discount

        line_items.append({
            "error_code": code,
            "service": pricing["label"],
            "parts_cost_vnd": parts_cost,
            "labor_cost_vnd": labor_cost,
            "discount_vnd": discount,
            "line_total_vnd": parts_cost + labor_cost - discount,
        })

    if not line_items:
        return json.dumps({
            "error": "Không có mã lỗi hợp lệ để tính chi phí.",
            "unknown_error_codes": unknown_codes,
        }, ensure_ascii=False)

    total_estimated = subtotal_parts + subtotal_labor - total_discount

    return json.dumps({
        "vehicle_id": VEHICLE["id"],
        "workshop_id": workshop_id or None,
        "workshop_name": workshop_name,
        "in_warranty": in_warranty,
        "warranty_until": VEHICLE["warranty_until"],
        "currency": "VND",
        "line_items": line_items,
        "summary": {
            "subtotal_parts_vnd": subtotal_parts,
            "subtotal_labor_vnd": subtotal_labor,
            "total_discount_vnd": total_discount,
            "estimated_total_vnd": total_estimated,
        },
        "unknown_error_codes": unknown_codes,
        "note": "Chi phí chỉ mang tính ước tính trước khi kỹ thuật viên kiểm tra trực tiếp.",
    }, ensure_ascii=False)


# ══════════════════════════════════════════════════════════════
# TOOL DEFINITIONS cho OpenAI function calling
# ══════════════════════════════════════════════════════════════
TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "get_user_info",
            "description": "Lấy thông tin người dùng (chủ xe) và xe VinFast: tên, SĐT, model, biển số, ODO, pin, vị trí hiện tại. Gọi đầu tiên để biết đang nói chuyện với ai.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_vehicle_info",
            "description": "Lấy thông tin chi tiết của xe VinFast hiện tại (model, chủ xe, ODO, tình trạng pin, bảo hành, vị trí...)",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_diagnostic",
            "description": "Chạy chẩn đoán lỗi xe VinFast hiện tại. Trả về danh sách tất cả lỗi kèm mức độ nghiêm trọng (critical/medium/low)",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "recommend_schedule",
            "description": "Gợi ý lịch bảo dưỡng dựa trên mức độ lỗi. Critical→xưởng GẦN NHẤT (theo km) có slot sớm nhất, Medium→xưởng gần có slot 3-5 ngày, Low→linh hoạt. Trả về khoảng cách từ vị trí hiện tại.",
            "parameters": {
                "type": "object",
                "properties": {
                    "error_code": {"type": "string", "description": "Mã lỗi cần gợi ý lịch, ví dụ: BAT-0012"}
                },
                "required": ["error_code"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_slot_availability",
            "description": "Kiểm tra slot trống của xưởng VinFast Hà Nội. Có thể lọc theo ngày cụ thể.",
            "parameters": {
                "type": "object",
                "properties": {
                    "workshop_id": {"type": "string", "description": "Mã xưởng, ví dụ: WS-HN01"},
                    "date": {"type": "string", "description": "Ngày cần kiểm tra (YYYY-MM-DD), bỏ trống để xem tất cả"}
                },
                "required": ["workshop_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "book_appointment",
            "description": "Đặt lịch bảo dưỡng xe tại xưởng và slot cụ thể. Trả về mã booking và QR check-in.",
            "parameters": {
                "type": "object",
                "properties": {
                    "workshop_id": {"type": "string", "description": "Mã xưởng"},
                    "slot_id": {"type": "string", "description": "Mã slot thời gian"},
                    "error_codes": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Danh sách mã lỗi cần sửa"
                    },
                    "note": {"type": "string", "description": "Ghi chú thêm từ khách hàng"}
                },
                "required": ["workshop_id", "slot_id", "error_codes"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "cancel_or_postpone",
            "description": "Hoãn/từ chối bảo dưỡng cho 1 lỗi cụ thể. Gọi lần 1 (chỉ error_code) → hỏi lý do. Gọi lần 2 (có reason) → xử lý theo severity: critical→cảnh báo+xác nhận, medium→chọn ngày nhắc, low→nhắn nhẹ.",
            "parameters": {
                "type": "object",
                "properties": {
                    "error_code": {
                        "type": "string",
                        "description": "Mã lỗi mà user muốn hoãn, ví dụ: BAT-0012"
                    },
                    "reason": {
                        "type": "string",
                        "enum": ["moi_bao_duong", "chua_can", "khac"],
                        "description": "Lý do hoãn: moi_bao_duong (Mới bảo dưỡng xong), chua_can (Chưa cần), khac (Lý do khác). Bỏ trống lần đầu để hỏi user."
                    },
                    "snooze_days": {
                        "type": "integer",
                        "description": "Số ngày nhắc lại (chỉ dùng cho medium, do user chọn). Bỏ trống hoặc 0 nếu chưa biết."
                    },
                    "confirm_critical": {
                        "type": "boolean",
                        "description": "Chỉ dùng cho lỗi critical: true = user đã xác nhận muốn hoãn, false/bỏ trống = lần đầu gọi (sẽ cảnh báo)"
                    }
                },
                "required": ["error_code"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_explainability",
            "description": "Xem giải thích chi tiết: confidence score, phân tích rủi ro, so sánh lịch sử xe tương tự",
            "parameters": {
                "type": "object",
                "properties": {
                    "error_code": {"type": "string", "description": "Mã lỗi cần giải thích"}
                },
                "required": ["error_code"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "estimate_maintenance_cost",
            "description": "Ước tính chi phí bảo dưỡng/sửa chữa theo danh sách mã lỗi, có breakdown vật tư, công sửa và giảm giá bảo hành (nếu có).",
            "parameters": {
                "type": "object",
                "properties": {
                    "error_codes": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Danh sách mã lỗi cần ước tính chi phí, ví dụ: [\"BAT-0012\", \"BRK-0045\"]"
                    },
                    "workshop_id": {
                        "type": "string",
                        "description": "Mã xưởng (tuỳ chọn), ví dụ: WS-HN01"
                    }
                },
                "required": ["error_codes"]
            }
        }
    },
]

# Map tên function → callable
TOOL_MAP = {
    "get_user_info": get_user_info,
    "get_vehicle_info": get_vehicle_info,
    "run_diagnostic": run_diagnostic,
    "recommend_schedule": recommend_schedule,
    "check_slot_availability": check_slot_availability,
    "book_appointment": book_appointment,
    "cancel_or_postpone": cancel_or_postpone,
    "get_explainability": get_explainability,
    "estimate_maintenance_cost": estimate_maintenance_cost,
}
