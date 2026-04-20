from app.logging_config import scrub_event


def test_scrub_event_redacts_nested_payload() -> None:
    event_dict = {
        "event": "User email student@vinuni.edu.vn requested support",
        "payload": {
            "message": "Call me at 0912 345 678",
            "nested": {
                "owner_email": "owner@example.com",
                "addresses": [
                    "12 đường Láng",
                    {"passport": "B12345678"},
                ],
            },
            "items": [
                "CCCD 012345678901",
                "card 4111 1111 1111 1111",
            ],
        },
    }

    out = scrub_event(None, "info", event_dict)
    payload = out["payload"]

    assert "student@vinuni.edu.vn" not in out["event"]
    assert "REDACTED_EMAIL" in out["event"]

    assert "0912 345 678" not in payload["message"]
    assert "REDACTED_PHONE_VN" in payload["message"]

    assert "owner@example.com" not in payload["nested"]["owner_email"]
    assert "REDACTED_EMAIL" in payload["nested"]["owner_email"]

    assert "B12345678" not in payload["nested"]["addresses"][1]["passport"]
    assert "REDACTED_PASSPORT" in payload["nested"]["addresses"][1]["passport"]

    assert "012345678901" not in payload["items"][0]
    assert "REDACTED_CCCD" in payload["items"][0]

    assert "4111 1111 1111 1111" not in payload["items"][1]
    assert "REDACTED_CREDIT_CARD" in payload["items"][1]
