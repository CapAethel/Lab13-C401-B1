"""
Mock data cho hệ thống VFCare - Diagnostic & Maintenance Scheduling Agent
Chạy trên 1 xe duy nhất, xưởng Hà Nội, có tính khoảng cách.
"""

from datetime import datetime, timedelta
import math
import random

# ══════════════════════════════════════════════════════════════
# THÔNG TIN XE DUY NHẤT + VỊ TRÍ HIỆN TẠI CỦA CHỦ XE
# ══════════════════════════════════════════════════════════════
VEHICLE = {
    "id": "VF8-001",
    "model": "VinFast VF8",
    "year": 2024,
    "owner": "X2 đẹp trai",
    "phone": "0901234567",
    "license_plate": "30A-12345",
    "odometer_km": 35200,
    "last_maintenance": "2025-11-15",
    "battery_health_pct": 87,
    "warranty_until": "2027-06-01",
    # Vị trí hiện tại của xe (khu vực Đống Đa, Hà Nội)
    "current_lat": 21.0170,
    "current_lng": 105.8230,
}

# ══════════════════════════════════════════════════════════════
# DANH SÁCH LỖI THEO TỪNG CASE (dùng để test agent)
# ══════════════════════════════════════════════════════════════

# Từng lỗi riêng lẻ
_ERR_CRITICAL = {
    "error_code": "BAT-0012",
    "description": "Pin cao áp suy giảm bất thường - cell #14 chênh lệch điện áp",
    "severity": "critical",
    "detected_at": "2026-04-08T14:30:00",
    "component": "Hệ thống pin cao áp",
    "risk_if_delayed": "Nguy cơ cháy / hỏng pin nghiêm trọng, mất khả năng vận hành",
}

_ERR_MEDIUM = {
    "error_code": "BRK-0045",
    "description": "Má phanh trước mòn 82% - cần thay thế sớm",
    "severity": "medium",
    "detected_at": "2026-04-07T09:15:00",
    "component": "Hệ thống phanh",
    "risk_if_delayed": "Giảm hiệu suất phanh, tăng quãng đường phanh",
}

_ERR_LOW = {
    "error_code": "LGT-0003",
    "description": "Đèn hậu bên phải nhấp nháy không đều",
    "severity": "low",
    "detected_at": "2026-04-06T18:00:00",
    "component": "Hệ thống chiếu sáng",
    "risk_if_delayed": "Ảnh hưởng tín hiệu giao thông, vi phạm luật",
}

# ── Định nghĩa các case test ─────────────────────────────────
ERROR_CASES = {
    "none":     {"label": "🟢 Không có lỗi (none)",               "errors": []},
    "low":      {"label": "🔵 Chỉ lỗi nhẹ (low)",                "errors": [_ERR_LOW]},
    "medium":   {"label": "🟡 Lỗi trung bình (medium)",          "errors": [_ERR_MEDIUM, _ERR_LOW]},
    "critical": {"label": "🔴 Có lỗi nghiêm trọng (critical)",   "errors": [_ERR_CRITICAL, _ERR_MEDIUM, _ERR_LOW]},
}

# ── Active errors (mutable list, tools.py tham chiếu trực tiếp) ──
VEHICLE_ERRORS: list[dict] = list(ERROR_CASES["critical"]["errors"])

# Default case name
_active_case: str = "critical"


def get_active_case() -> str:
    """Trả về tên case đang active."""
    return _active_case


def set_active_case(case_name: str) -> None:
    """Đổi case test. Cập nhật VEHICLE_ERRORS in-place để tools.py nhìn thấy ngay."""
    global _active_case
    if case_name not in ERROR_CASES:
        raise ValueError(f"Case '{case_name}' không hợp lệ. Chọn: {list(ERROR_CASES.keys())}")
    _active_case = case_name
    VEHICLE_ERRORS.clear()
    VEHICLE_ERRORS.extend(ERROR_CASES[case_name]["errors"])

# ══════════════════════════════════════════════════════════════
# HÀM TÍNH KHOẢNG CÁCH (Haversine)
# ══════════════════════════════════════════════════════════════
def calc_distance_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Tính khoảng cách theo đường chim bay (km) giữa 2 toạ độ."""
    R = 6371  # bán kính Trái Đất (km)
    d_lat = math.radians(lat2 - lat1)
    d_lng = math.radians(lng2 - lng1)
    a = (math.sin(d_lat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(d_lng / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ══════════════════════════════════════════════════════════════
# DANH SÁCH XƯỞNG VINFAST - CHỈ HÀ NỘI
# ══════════════════════════════════════════════════════════════
WORKSHOPS = [
    {
        "id": "WS-HN01",
        "name": "VinFast Service Cầu Giấy",
        "address": "219 Trần Duy Hưng, Cầu Giấy, Hà Nội",
        "lat": 21.0085,
        "lng": 105.7961,
        "phone": "1900 23 23 89 (nhánh 1)",
        "rating": 4.7,
        "specialties": ["pin cao áp", "hệ thống phanh", "hệ thống treo", "tổng quát"],
        "supports_critical": True,
    },
    {
        "id": "WS-HN02",
        "name": "VinFast Service Long Biên",
        "address": "45 Nguyễn Văn Cừ, Long Biên, Hà Nội",
        "lat": 21.0452,
        "lng": 105.8733,
        "phone": "1900 23 23 89 (nhánh 2)",
        "rating": 4.5,
        "specialties": ["hệ thống điện", "hệ thống chiếu sáng", "điều hoà", "tổng quát"],
        "supports_critical": False,
    },
    {
        "id": "WS-HN03",
        "name": "VinFast Service Thanh Xuân",
        "address": "86 Nguyễn Trãi, Thanh Xuân, Hà Nội",
        "lat": 20.9930,
        "lng": 105.8140,
        "phone": "1900 23 23 89 (nhánh 3)",
        "rating": 4.8,
        "specialties": ["pin cao áp", "hệ thống phanh", "hệ thống treo", "tổng quát"],
        "supports_critical": True,
    },
    {
        "id": "WS-HN04",
        "name": "VinFast Service Hà Đông",
        "address": "212 Quang Trung, Hà Đông, Hà Nội",
        "lat": 20.9720,
        "lng": 105.7780,
        "phone": "1900 23 23 89 (nhánh 4)",
        "rating": 4.3,
        "specialties": ["hệ thống phanh", "hệ thống chiếu sáng", "lốp", "tổng quát"],
        "supports_critical": False,
    },
    {
        "id": "WS-HN05",
        "name": "VinFast Service Gia Lâm",
        "address": "Km5 Quốc lộ 5, Gia Lâm, Hà Nội",
        "lat": 21.0310,
        "lng": 105.9410,
        "phone": "1900 23 23 89 (nhánh 5)",
        "rating": 4.6,
        "specialties": ["pin cao áp", "hệ thống phanh", "tổng quát"],
        "supports_critical": True,
    },
]

# Gắn khoảng cách từ vị trí hiện tại của xe đến từng xưởng
for ws in WORKSHOPS:
    ws["distance_km"] = round(calc_distance_km(
        VEHICLE["current_lat"], VEHICLE["current_lng"],
        ws["lat"], ws["lng"],
    ), 1)

# ══════════════════════════════════════════════════════════════
# DANH SÁCH SLOT TRỐNG THEO XƯỞNG (7 ngày tới)
# ══════════════════════════════════════════════════════════════

def _generate_slots(workshop_id: str, days: int = 7) -> list[dict]:
    """Tạo slot ngẫu nhiên cho xưởng: mỗi ngày chọn 2-4 slot trống từ 8h-17h."""
    rng = random.Random(hash(workshop_id))  # deterministic per workshop
    slots = []
    base = datetime(2026, 4, 9, 8, 0)  # hôm nay
    slot_id = 1
    for d in range(days):
        day = base + timedelta(days=d)
        all_hours = list(range(8, 17))  # 9 khung giờ
        num_available = rng.randint(2, 4)  # 2-4 slot trống mỗi ngày
        available_hours = set(rng.sample(all_hours, num_available))
        for hour in all_hours:
            start = day.replace(hour=hour, minute=0)
            end = day.replace(hour=hour + 1, minute=0)
            slots.append({
                "slot_id": f"{workshop_id}-S{slot_id:03d}",
                "workshop_id": workshop_id,
                "date": start.strftime("%Y-%m-%d"),
                "start_time": start.strftime("%H:%M"),
                "end_time": end.strftime("%H:%M"),
                "available": hour in available_hours,
            })
            slot_id += 1
    return slots


WORKSHOP_SLOTS = {ws["id"]: _generate_slots(ws["id"]) for ws in WORKSHOPS}

# ══════════════════════════════════════════════════════════════
# BOOKINGS (lưu trữ trong memory)
# ══════════════════════════════════════════════════════════════
BOOKINGS: list[dict] = []
