from __future__ import annotations

import json
import os
import random
import time
from dataclasses import dataclass

from openai import OpenAI

from . import metrics
from .pii import hash_user_id, summarize_text
from .tools import TOOL_DEFINITIONS, TOOL_MAP
from .tracing import langfuse_context, observe

# Load system prompt
_PROMPT_PATH = os.path.join(os.path.dirname(__file__), "system_prompt.txt")
with open(_PROMPT_PATH, "r", encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read()

# ---------------------------------------------------------------------------
# Mock responses (used when VFCARE_MOCK=1 or no valid API key)
# ---------------------------------------------------------------------------
_MOCK_GREETING = (
    "Xin chào anh X2 đẹp trai! 😄 Em là VFCare, trợ lý AI của VinFast đây ạ!\n"
    "Để em kiểm tra tình trạng xe VF8 của anh ngay nhé...\n\n"
    "🔍 **Kết quả chẩn đoán:**\n"
    "- 🔴 **[KHẨN CẤP]** BAT-0012: Pin cao áp suy giảm bất thường - nguy cơ cháy pin!\n"
    "- 🟡 BRK-0045: Má phanh trước mòn 82% - nên thay sớm\n"
    "- 🟢 LGT-0003: Đèn hậu nhấp nháy - lỗi nhẹ\n\n"
    "Anh có muốn đặt lịch bảo dưỡng không ạ? (đặc biệt lỗi pin rất cần xử lý NGAY!) ⚡"
)
_MOCK_RESPONSES = [
    "Em đã tìm xưởng gần nhất cho anh: **VinFast Service Cầu Giấy** (2.1 km) – slot sớm nhất: 2026-04-09 lúc 09:00. Anh có muốn đặt không ạ? 🏪",
    "✅ Đặt lịch thành công! Mã booking: **BK-0001** | QR check-in: QR-VF8-001-WS-HN01-S001\nNhắc nhở: Anh có lịch bảo dưỡng ngày 2026-04-09 lúc 09:00 tại VinFast Service Cầu Giấy. Đừng quên nhé anh! 🎉",
    "Em hiểu anh bận rộn. Lỗi pin này khá nguy hiểm nếu trì hoãn, nhưng anh muốn hoãn thì anh cần xác nhận thêm nhé. Anh chọn lý do: (1) Mới bảo dưỡng xong, (2) Chưa cần thiết, (3) Lý do khác?",
    "Đã ghi nhận! Chi phí ước tính: BAT-0012 = 5.160.000đ (có giảm bảo hành 20%), BRK-0045 = 2.100.000đ, LGT-0003 = 800.000đ. Tổng: **8.060.000đ** 💰",
    "Anh cứ yên tâm! Hệ thống sẽ nhắc lại khi anh bật xe lần sau. Chúc anh lái xe an toàn! 🚗💨",
]
_mock_idx = 0


@dataclass
class AgentResult:
    answer: str
    latency_ms: int
    tokens_in: int
    tokens_out: int
    cost_usd: float
    quality_score: float


class VFCareAgent:
    def __init__(self, model: str = "gpt-4o-mini", mock: bool = False) -> None:
        self.model = os.environ.get("OPENAI_MODEL", model)
        self.mock = mock or os.environ.get("VFCARE_MOCK", "").lower() in ("1", "true")
        if not self.mock:
            self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        self.tool_names = sorted([
            t["function"]["name"]
            for t in TOOL_DEFINITIONS
            if t.get("type") == "function" and t.get("function", {}).get("name")
        ])
        self.messages: list[dict] = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]
        self._first_turn = True

    def chat(self, user_message: str) -> tuple[str, int, int]:
        """Send a user message, handle tool calls, return (answer, tokens_in, tokens_out)."""
        global _mock_idx

        if self.mock:
            time.sleep(0.15)
            tokens_in = max(20, len(user_message) // 4) + random.randint(50, 150)
            tokens_out = random.randint(80, 180)
            if self._first_turn:
                self._first_turn = False
                return _MOCK_GREETING, tokens_in, tokens_out
            answer = _MOCK_RESPONSES[_mock_idx % len(_MOCK_RESPONSES)]
            _mock_idx += 1
            return answer, tokens_in, tokens_out

        normalized = user_message.lower()
        if "tool" in normalized and any(k in normalized for k in ["có", "danh sách", "list", "available"]):
            reply = "Các tool hiện có: " + ", ".join(self.tool_names)
            return reply, 0, 0

        self.messages.append({"role": "user", "content": user_message})

        total_in = 0
        total_out = 0

        while True:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.messages,
                tools=TOOL_DEFINITIONS,
                tool_choice="auto",
            )

            usage = response.usage
            if usage:
                total_in += usage.prompt_tokens
                total_out += usage.completion_tokens

            message = response.choices[0].message
            self.messages.append(message)

            # No tool calls → final text response
            if not message.tool_calls:
                return message.content, total_in, total_out

            # Execute each tool call
            for tool_call in message.tool_calls:
                func_name = tool_call.function.name
                func_args = json.loads(tool_call.function.arguments)

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

    @observe()
    def run(self, user_id: str, feature: str, session_id: str, message: str) -> AgentResult:
        started = time.perf_counter()

        answer, tokens_in, tokens_out = self.chat(message)

        latency_ms = int((time.perf_counter() - started) * 1000)
        cost_usd = self._estimate_cost(tokens_in, tokens_out)
        quality_score = self._heuristic_quality(message, answer)

        langfuse_context.update_current_trace(
            user_id=hash_user_id(user_id),
            session_id=session_id,
            tags=["vfcare", feature, self.model],
        )
        langfuse_context.update_current_observation(
            metadata={"query_preview": summarize_text(message)},
            usage_details={"input": tokens_in, "output": tokens_out},
        )

        metrics.record_request(
            latency_ms=latency_ms,
            cost_usd=cost_usd,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            quality_score=quality_score,
        )

        return AgentResult(
            answer=answer,
            latency_ms=latency_ms,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            cost_usd=cost_usd,
            quality_score=quality_score,
        )

    def _estimate_cost(self, tokens_in: int, tokens_out: int) -> float:
        # gpt-4o-mini: $0.15/1M input, $0.60/1M output
        input_cost = (tokens_in / 1_000_000) * 0.15
        output_cost = (tokens_out / 1_000_000) * 0.60
        return round(input_cost + output_cost, 6)

    def _heuristic_quality(self, question: str, answer: str) -> float:
        if not answer:
            return 0.0
        score = 0.5
        if len(answer) > 100:
            score += 0.2
        keywords = question.lower().split()[:5]
        if any(k in answer.lower() for k in keywords):
            score += 0.2
        if "[REDACTED" in answer:
            score -= 0.2
        return round(max(0.0, min(1.0, score)), 2)


# Backward-compatible alias used by main.py
LabAgent = VFCareAgent
