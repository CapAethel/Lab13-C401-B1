"""
VFCare - Main entry point
Chạy agent chatbot trong terminal, giao tiếp với user qua stdin/stdout.
"""

from agent import VFCareAgent
from mock_data import VEHICLE


def main():
    print("=" * 60)
    print("  🚗  VFCare - Trợ lý Bảo dưỡng Xe VinFast  🚗")
    print("=" * 60)
    print(f"  Xe: {VEHICLE['model']} | Biển số: {VEHICLE['license_plate']}")
    print(f"  Chủ xe: {VEHICLE['owner']}")
    print("  Gõ 'quit' hoặc 'exit' để thoát")
    print("  Bắt đầu trò chuyện với VFCare Assistant...")
    print("Chào bạn ! Chúc bạn một ngày tốt lành ! Mình sẽ kiểm tra tình trạng xe cho bạn nhé !")
    print("=" * 60)
    print()

    agent = VFCareAgent()

    # Agent tự chào chủ xe và chạy diagnostic luôn
    greeting = agent.chat("Bắt đầu! Hãy lấy thông tin người dùng, chào chủ xe và chạy kiểm tra chẩn đoán xe.")
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

        print()
        response = agent.chat(user_input)
        print(f"🤖 VFCare: {response}\n")


if __name__ == "__main__":
    main()
