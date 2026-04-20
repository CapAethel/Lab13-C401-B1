from __future__ import annotations

import argparse
import json
from pathlib import Path

import httpx

BASE_URL = "http://127.0.0.1:8000"
INCIDENTS_FILE = Path("data/incidents.json")


def load_incident_descriptions() -> dict[str, str]:
    if not INCIDENTS_FILE.exists():
        return {}
    try:
        raw = json.loads(INCIDENTS_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    if not isinstance(raw, dict):
        return {}
    return {str(key): str(value) for key, value in raw.items()}


def get_status(base_url: str) -> dict[str, bool]:
    response = httpx.get(f"{base_url}/health", timeout=10.0)
    response.raise_for_status()
    data = response.json()
    incidents = data.get("incidents", {})
    if not isinstance(incidents, dict):
        raise ValueError("Invalid incidents status payload")
    return {str(key): bool(value) for key, value in incidents.items()}


def toggle(base_url: str, scenario: str, disable: bool) -> dict:
    path = f"/incidents/{scenario}/disable" if disable else f"/incidents/{scenario}/enable"
    response = httpx.post(f"{base_url}{path}", timeout=10.0)
    response.raise_for_status()
    return response.json()


def main() -> None:
    parser = argparse.ArgumentParser()
    descriptions = load_incident_descriptions()
    known_scenarios = sorted(descriptions.keys() or ["rag_slow", "tool_fail", "cost_spike"])

    parser.add_argument("--base-url", default=BASE_URL)
    parser.add_argument("--scenario", choices=known_scenarios + ["all"])
    parser.add_argument("--disable", action="store_true")
    parser.add_argument("--status", action="store_true", help="Show incident state from /health")
    parser.add_argument("--list", action="store_true", help="List available scenarios")
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")

    if args.list:
        print("Available incident scenarios:")
        for name in known_scenarios:
            detail = descriptions.get(name, "No description")
            print(f"- {name}: {detail}")
        return

    if args.status:
        incidents = get_status(base_url)
        print(json.dumps({"ok": True, "incidents": incidents}, indent=2))
        return

    if not args.scenario:
        parser.error("--scenario is required unless using --list or --status")

    if args.scenario == "all":
        if not args.disable:
            parser.error("--scenario all requires --disable to avoid enabling all incidents at once")
        for name in known_scenarios:
            response = toggle(base_url, name, disable=True)
            print(json.dumps({"scenario": name, "response": response}, indent=2))
        return

    response = toggle(base_url, args.scenario, disable=args.disable)
    print(json.dumps(response, indent=2))


if __name__ == "__main__":
    main()
