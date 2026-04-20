"""
VFCare - Streamlit Web UI
Giao diện chat với AI Agent chẩn đoán xe VinFast.
"""

import streamlit as st
import json
import os
from openai import OpenAI
from tools import TOOL_DEFINITIONS, TOOL_MAP
from mock_data import VEHICLE, VEHICLE_ERRORS, ERROR_CASES, get_active_case, set_active_case

# ── Page config ───────────────────────────────────────────────
st.set_page_config(
    page_title="VFCare - Trợ lý Bảo dưỡng VinFast",
    page_icon="🚗",
    layout="centered",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────
st.markdown("""
<style>
    /* Main container */
    .block-container { max-width: 800px; padding-top: 1rem; }

    /* Severity badges */
    .severity-critical {
        background: #ff4b4b; color: white; padding: 2px 10px;
        border-radius: 12px; font-size: 0.8rem; font-weight: 600;
    }
    .severity-medium {
        background: #ffa726; color: white; padding: 2px 10px;
        border-radius: 12px; font-size: 0.8rem; font-weight: 600;
    }
    .severity-low {
        background: #66bb6a; color: white; padding: 2px 10px;
        border-radius: 12px; font-size: 0.8rem; font-weight: 600;
    }

    /* Vehicle info card */
    .vehicle-card {
        background: linear-gradient(135deg, #1a237e 0%, #283593 100%);
        color: white; padding: 1.2rem 1.5rem; border-radius: 12px;
        margin-bottom: 1rem;
    }
    .vehicle-card h3 { margin: 0 0 0.5rem 0; font-size: 1.1rem; }
    .vehicle-card .info-row { display: flex; justify-content: space-between; margin: 4px 0; font-size: 0.9rem; }
    .vehicle-card .label { opacity: 0.8; }

    /* Error summary cards */
    .error-summary {
        display: flex; gap: 0.5rem; margin: 0.5rem 0 1rem 0;
    }
    .error-badge {
        padding: 6px 14px; border-radius: 8px;
        font-weight: 600; font-size: 0.85rem; text-align: center;
    }
    .error-badge.critical { background: #ffebee; color: #c62828; border: 1px solid #ef9a9a; }
    .error-badge.medium { background: #fff3e0; color: #e65100; border: 1px solid #ffcc80; }
    .error-badge.low { background: #e8f5e9; color: #2e7d32; border: 1px solid #a5d6a7; }

    /* Tool call indicator */
    .tool-call {
        background: #f5f5f5; border-left: 3px solid #1976d2;
        padding: 6px 12px; margin: 4px 0; border-radius: 0 6px 6px 0;
        font-size: 0.8rem; color: #555; font-family: monospace;
    }

    /* Chat input area */
    .stChatInput { border-top: 1px solid #eee; }
</style>
""", unsafe_allow_html=True)


# ── Sidebar: Vehicle info ─────────────────────────────────────
with st.sidebar:
    # ── Case selector ─────────────────────────────────────────
    st.markdown("## 🧪 Chọn Case Test")
    case_keys = list(ERROR_CASES.keys())
    case_labels = [ERROR_CASES[k]["label"] for k in case_keys]

    if "active_case" not in st.session_state:
        st.session_state.active_case = get_active_case()

    selected_label = st.selectbox(
        "Kịch bản lỗi xe",
        case_labels,
        index=case_keys.index(st.session_state.active_case),
        key="case_selector",
    )
    selected_case = case_keys[case_labels.index(selected_label)]

    # Nếu user đổi case → reset conversation
    if selected_case != st.session_state.active_case:
        set_active_case(selected_case)
        st.session_state.active_case = selected_case
        st.session_state.messages = []
        st.session_state.agent_messages = []
        st.session_state.auto_diagnostic = False
        st.session_state.bookings = []
        st.rerun()

    # Show error summary for selected case
    case_errors = ERROR_CASES[selected_case]["errors"]
    if case_errors:
        for err in case_errors:
            sev = err["severity"]
            st.markdown(f'<span class="severity-{sev}">{sev.upper()}</span> <small>{err["error_code"]}</small>', unsafe_allow_html=True)
    else:
        st.markdown("*Xe không có lỗi nào* ✅")

    st.divider()
    st.markdown("## 🚗 Thông tin xe")
    st.markdown(f"""
    <div class="vehicle-card">
        <h3>🔋 {VEHICLE['model']} ({VEHICLE['year']})</h3>
        <div class="info-row"><span class="label">Chủ xe:</span> <span>{VEHICLE['owner']}</span></div>
        <div class="info-row"><span class="label">Biển số:</span> <span>{VEHICLE['license_plate']}</span></div>
        <div class="info-row"><span class="label">ODO:</span> <span>{VEHICLE['odometer_km']:,} km</span></div>
        <div class="info-row"><span class="label">Pin:</span> <span>{VEHICLE['battery_health_pct']}%</span></div>
        <div class="info-row"><span class="label">Bảo hành:</span> <span>{VEHICLE['warranty_until']}</span></div>
        <div class="info-row"><span class="label">Bảo dưỡng gần nhất:</span> <span>{VEHICLE['last_maintenance']}</span></div>
    </div>
    """, unsafe_allow_html=True)

    # ── Booking info ──────────────────────────────────────
    if st.session_state.get("bookings"):
        st.divider()
        st.markdown("### 📅 Lịch bảo dưỡng")
        for bk in st.session_state.bookings:
            st.markdown(f"""
            <div style="background: #e8f5e9; border: 1px solid #a5d6a7; border-radius: 10px; padding: 12px 14px; margin-bottom: 8px;">
                <div style="font-weight:600; color:#2e7d32; margin-bottom:6px;">✅ {bk['booking_id']}</div>
                <div style="font-size:0.85rem; color:#333;">
                    📍 {bk['workshop_name']}<br>
                    🗓️ {bk['date']} | ⏰ {bk['time']}<br>
                    🔧 Lỗi: {', '.join(bk['error_codes'])}<br>
                    📱 QR: <code>{bk['qr_checkin_code']}</code>
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.divider()
    if st.button("🔄 Cuộc hội thoại mới", use_container_width=True):
        st.session_state.messages = []
        st.session_state.agent_messages = []
        st.session_state.auto_diagnostic = False
        st.session_state.bookings = []
        st.rerun()


# ── Agent logic (reuse existing) ─────────────────────────────
from agent import SYSTEM_PROMPT


def get_agent_response(user_msg: str, agent_messages: list) -> tuple[str, list, list]:
    """
    Gửi tin nhắn, xử lý tool calls, trả về (response_text, updated_messages, tool_logs).
    """
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

    agent_messages.append({"role": "user", "content": user_msg})
    tool_logs = []

    while True:
        response = client.chat.completions.create(
            model=model,
            messages=agent_messages,
            tools=TOOL_DEFINITIONS,
            tool_choice="auto",
        )

        message = response.choices[0].message
        agent_messages.append(message)

        if not message.tool_calls:
            return message.content, agent_messages, tool_logs

        for tool_call in message.tool_calls:
            func_name = tool_call.function.name
            func_args = json.loads(tool_call.function.arguments)
            tool_logs.append({"name": func_name, "args": func_args})

            func = TOOL_MAP.get(func_name)
            if func:
                result = func(**func_args)
            else:
                result = json.dumps({"error": f"Tool {func_name} không tồn tại"})

            # Capture booking results
            if func_name == "book_appointment":
                try:
                    booking_data = json.loads(result)
                    if booking_data.get("success"):
                        if "bookings" not in st.session_state:
                            st.session_state.bookings = []
                        st.session_state.bookings.append(booking_data["booking"])
                except (json.JSONDecodeError, KeyError):
                    pass

            agent_messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result,
            })


# ── Session state init ────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []          # UI display messages
if "agent_messages" not in st.session_state or not st.session_state.agent_messages:
    st.session_state.agent_messages = [     # OpenAI API messages
        {"role": "system", "content": SYSTEM_PROMPT}
    ]
if "auto_diagnostic" not in st.session_state:
    st.session_state.auto_diagnostic = False
if "bookings" not in st.session_state:
    st.session_state.bookings = []


# ── Header ────────────────────────────────────────────────────
st.markdown("# 🚗 VFCare Assistant")
st.markdown("*Trợ lý AI chẩn đoán & bảo dưỡng xe VinFast*")
st.divider()


# ── Display chat history ──────────────────────────────────────
for msg in st.session_state.messages:
    if msg["role"] == "tool_log":
        # Show tool calls as small indicators
        with st.chat_message("assistant", avatar="🔧"):
            for log in msg["logs"]:
                args_str = ", ".join(f"{k}={json.dumps(v, ensure_ascii=False)}" for k, v in log["args"].items())
                st.markdown(f'<div class="tool-call">🔧 {log["name"]}({args_str})</div>', unsafe_allow_html=True)
    elif msg["role"] == "user":
        with st.chat_message("user", avatar="👤"):
            st.markdown(msg["content"])
    elif msg["role"] == "assistant":
        with st.chat_message("assistant", avatar="🤖"):
            st.markdown(msg["content"])


# ── Auto-diagnostic on first load ─────────────────────────────
if not st.session_state.auto_diagnostic:
    st.session_state.auto_diagnostic = True

    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("Đang kiểm tra tình trạng xe..."):
            greeting_prompt = "Bắt đầu! Hãy lấy thông tin người dùng, chào chủ xe và chạy kiểm tra chẩn đoán xe."
            response_text, st.session_state.agent_messages, tool_logs = get_agent_response(
                greeting_prompt, st.session_state.agent_messages
            )

        # Show tool logs
        if tool_logs:
            for log in tool_logs:
                args_str = ", ".join(f"{k}={json.dumps(v, ensure_ascii=False)}" for k, v in log["args"].items())
                st.markdown(f'<div class="tool-call">🔧 {log["name"]}({args_str})</div>', unsafe_allow_html=True)

        st.markdown(response_text)

    # Save to history
    if tool_logs:
        st.session_state.messages.append({"role": "tool_log", "logs": tool_logs})
    st.session_state.messages.append({"role": "assistant", "content": response_text})


# ── Chat input ────────────────────────────────────────────────
if user_input := st.chat_input("Nhập tin nhắn cho VFCare..."):
    # Show user message
    with st.chat_message("user", avatar="👤"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Get agent response
    bookings_before = len(st.session_state.bookings)
    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("Đang xử lý..."):
            response_text, st.session_state.agent_messages, tool_logs = get_agent_response(
                user_input, st.session_state.agent_messages
            )

        # Show tool logs
        if tool_logs:
            for log in tool_logs:
                args_str = ", ".join(f"{k}={json.dumps(v, ensure_ascii=False)}" for k, v in log["args"].items())
                st.markdown(f'<div class="tool-call">🔧 {log["name"]}({args_str})</div>', unsafe_allow_html=True)
            st.session_state.messages.append({"role": "tool_log", "logs": tool_logs})

        st.markdown(response_text)

    st.session_state.messages.append({"role": "assistant", "content": response_text})

    # Rerun to update sidebar with new booking
    if len(st.session_state.bookings) > bookings_before:
        st.rerun()
