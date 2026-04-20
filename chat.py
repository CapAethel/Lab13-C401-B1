"""
Quick terminal chat for testing VFCareAgent inside the app package.
Run:          python3 chat.py           # auto-detects mock/real mode
Run (mock):   VFCARE_MOCK=1 python3 chat.py
"""
import os
import sys

from dotenv import load_dotenv
load_dotenv()

sys.path.insert(0, os.path.dirname(__file__))

from app.agent import VFCareAgent
from app.logging_config import configure_logging, get_logger
from app.mock_data import VEHICLE, ERROR_CASES, get_active_case, set_active_case
from app.pii import hash_user_id, summarize_text

configure_logging()
log = get_logger()

SESSION_ID = "cli-session-001"
USER_ID = "cli-user"

USE_MOCK = os.environ.get("VFCARE_MOCK", "") in ("1", "true") or not bool(os.environ.get("OPENAI_API_KEY"))


def main():
    print("=" * 60)
    print("  🚗  VFCare – Trợ lý Bảo dưỡng Xe VinFast  🚗")
    if USE_MOCK:
        print("  ⚠️  MOCK MODE")
    print("=" * 60)
    print(f"  Xe: {VEHICLE['model']} | Biển số: {VEHICLE['license_plate']}")
    print(f"  Chủ xe: {VEHICLE['owner']}")
    print()
    print("  Cases có sẵn (gõ 'case <tên>' để đổi):")
    for k, v in ERROR_CASES.items():
        marker = "◀" if k == get_active_case() else " "
        print(f"   {marker} {k}: {v['label']}")
    print()
    print("  Gõ 'quit' để thoát")
    print("=" * 60)
    print()

    agent = VFCareAgent(mock=USE_MOCK)

    # Auto greeting + diagnostic
    greeting, _, _ = agent.chat(
        "Bắt đầu! Hãy lấy thông tin người dùng, chào chủ xe và chạy kiểm tra chẩn đoán xe."
    )
    print(f"🤖 VFCare: {greeting}\n")

    while True:
        try:
            user_input = input("👤 Bạn: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n👋 Tạm biệt! Chúc bạn lái xe an toàn!")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            print("👋 Tạm biệt! Chúc bạn lái xe an toàn!")
            break

        # Case switcher
        if user_input.lower().startswith("case "):
            case_name = user_input.split()[1].strip()
            try:
                set_active_case(case_name)
                agent = VFCareAgent(mock=USE_MOCK)
                print(f"✅ Đã chuyển sang case '{case_name}'. Bắt đầu hội thoại mới...\n")
                greeting, _, _ = agent.chat(
                    "Bắt đầu! Hãy lấy thông tin người dùng, chào chủ xe và chạy kiểm tra chẩn đoán xe."
                )
                print(f"🤖 VFCare: {greeting}\n")
            except ValueError as e:
                print(f"❌ {e}\n")
            continue

        print()
        log.info(
            "request_received",
            service="cli",
            session_id=SESSION_ID,
            user_id_hash=hash_user_id(USER_ID),
            env="dev",
            model=agent.model,
            payload={"message_preview": summarize_text(user_input)},
        )
        answer, tin, tout = agent.chat(user_input)
        log.info(
            "response_sent",
            service="cli",
            session_id=SESSION_ID,
            user_id_hash=hash_user_id(USER_ID),
            env="dev",
            model=agent.model,
            tokens_in=tin,
            tokens_out=tout,
            payload={"answer_preview": summarize_text(answer)},
        )
        print(f"🤖 VFCare: {answer}")
        print(f"   [tokens: in={tin} out={tout}]\n")


if __name__ == "__main__":
    main()
