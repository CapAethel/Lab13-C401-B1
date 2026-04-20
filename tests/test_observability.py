from __future__ import annotations

import json
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.agent import AgentResult

os.environ["VFCARE_MOCK"] = "1"

from app.main import app
from app.middleware import CorrelationIdMiddleware


def test_middleware_sets_and_echoes_correlation_id() -> None:
    test_app = FastAPI()
    test_app.add_middleware(CorrelationIdMiddleware)

    @test_app.get("/ping")
    async def ping() -> dict:
        return {"ok": True}

    client = TestClient(test_app)
    response = client.get("/ping", headers={"x-request-id": "req-manual-001"})
    assert response.status_code == 200
    assert response.headers["x-request-id"] == "req-manual-001"
    assert int(response.headers["x-response-time-ms"]) >= 0


def test_chat_logs_include_context_and_scrubbed_pii(monkeypatch) -> None:
    temp_log = Path("data/test_logs.jsonl")
    temp_log.write_text("", encoding="utf-8")

    class FakeAgent:
        model = "test-model"

        def run(self, *, user_id: str, feature: str, session_id: str, message: str) -> AgentResult:
            return AgentResult(
                answer="Safe answer",
                latency_ms=123,
                tokens_in=25,
                tokens_out=40,
                cost_usd=0.0023,
                quality_score=0.91,
            )

    monkeypatch.setattr("app.logging_config.LOG_PATH", temp_log)
    monkeypatch.setattr("app.main.agent", FakeAgent())

    client = TestClient(app)
    payload = {
        "user_id": "u01",
        "session_id": "s01",
        "feature": "qa",
        "message": "My email is student@vinuni.edu.vn and card 4111 1111 1111 1111",
    }

    r1 = client.post("/chat", json=payload, headers={"x-request-id": "req-aaa"})
    r2 = client.post("/chat", json=payload, headers={"x-request-id": "req-bbb"})
    assert r1.status_code == 200
    assert r2.status_code == 200

    lines = [line for line in temp_log.read_text(encoding="utf-8").splitlines() if line.strip()]
    records = [json.loads(line) for line in lines]
    api_records = [rec for rec in records if rec.get("service") == "api"]
    assert api_records

    correlation_ids = {rec.get("correlation_id") for rec in api_records}
    assert "req-aaa" in correlation_ids
    assert "req-bbb" in correlation_ids

    for rec in api_records:
        assert rec.get("user_id_hash")
        assert rec.get("session_id")
        assert rec.get("feature")
        assert rec.get("model")

    raw = "\n".join(lines)
    assert "student@vinuni.edu.vn" not in raw
    assert "4111 1111 1111 1111" not in raw
    assert "[REDACTED_EMAIL]" in raw

    metrics_response = client.get("/metrics/prometheus")
    assert metrics_response.status_code == 200
    assert "lab_requests_total" in metrics_response.text
    assert "lab_request_latency_ms_bucket" in metrics_response.text

    temp_log.unlink(missing_ok=True)
