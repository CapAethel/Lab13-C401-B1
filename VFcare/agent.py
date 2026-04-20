"""
VFCare Agent - AI Agent sử dụng OpenAI function calling
để chẩn đoán xe VinFast và gợi ý lịch bảo dưỡng.
Chạy trên 1 xe duy nhất, xưởng Hà Nội.
"""

import json
import os
from openai import OpenAI
from tools import TOOL_DEFINITIONS, TOOL_MAP

# Load system prompt từ file txt
_PROMPT_PATH = os.path.join(os.path.dirname(__file__), "system_prompt.txt")
with open(_PROMPT_PATH, "r", encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read()


class VFCareAgent:
    def __init__(self):
        self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        self.model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
        self.tool_names = sorted([
            t["function"]["name"]
            for t in TOOL_DEFINITIONS
            if t.get("type") == "function" and t.get("function", {}).get("name")
        ])
        self.messages: list[dict] = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]

    def chat(self, user_message: str) -> str:
        """Gửi tin nhắn từ user, xử lý tool calls, trả về response cuối cùng."""
        normalized = user_message.lower()
        if "tool" in normalized and any(k in normalized for k in ["có", "danh sách", "list", "available"]):
            return "Các tool hiện có: " + ", ".join(self.tool_names)

        self.messages.append({"role": "user", "content": user_message})

        while True:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.messages,
                tools=TOOL_DEFINITIONS,
                tool_choice="auto",
            )

            message = response.choices[0].message
            self.messages.append(message)

            # Nếu không có tool call → trả về text response
            if not message.tool_calls:
                return message.content

            # Xử lý từng tool call
            for tool_call in message.tool_calls:
                func_name = tool_call.function.name
                func_args = json.loads(tool_call.function.arguments)

                print(f"  🔧 Gọi tool: {func_name}({json.dumps(func_args, ensure_ascii=False)})")

                func = TOOL_MAP.get(func_name)
                if func:
                    result = func(**func_args)
                else:
                    result = json.dumps({"error": f"Tool {func_name} không tồn tại"})

                self.messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result,
                })

            # Tiếp tục loop để LLM xử lý kết quả tool
