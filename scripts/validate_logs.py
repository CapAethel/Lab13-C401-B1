import argparse
import json
import sys
from pathlib import Path

DEFAULT_LOG_PATH = Path("data/logs.jsonl")
REQUIRED_FIELDS = {"ts", "level", "service", "event", "correlation_id"}
ENRICHMENT_FIELDS = {"user_id_hash", "session_id", "feature", "model"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate lab JSON logs against rubric checks.")
    parser.add_argument("--log-path", default=str(DEFAULT_LOG_PATH), help="Path to logs.jsonl file")
    parser.add_argument(
        "--service",
        default="api",
        help="Only validate records for this service. Use 'all' to validate every record.",
    )
    return parser.parse_args()


def load_records(log_path: Path) -> list[dict]:
    records: list[dict] = []
    for line in log_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            records.append(payload)
    return records


def main() -> None:
    args = parse_args()
    log_path = Path(args.log_path)
    if not log_path.exists():
        print(f"Error: {log_path} not found. Run the app and send some requests first.")
        sys.exit(1)

    records = load_records(log_path)
    if not records:
        print(f"Error: No valid JSON logs found in {log_path}")
        sys.exit(1)

    selected_records = (
        records if args.service == "all" else [rec for rec in records if rec.get("service") == args.service]
    )
    if not selected_records:
        print(f"Error: No records found for service='{args.service}'.")
        sys.exit(1)

    total = len(selected_records)
    missing_required = 0
    missing_enrichment = 0
    pii_hits: list[str] = []
    correlation_ids = set()

    for rec in selected_records:
        if not REQUIRED_FIELDS.issubset(rec.keys()):
            missing_required += 1

        if not ENRICHMENT_FIELDS.issubset(rec.keys()):
            missing_enrichment += 1

        raw = json.dumps(rec)
        if "@" in raw or "4111" in raw:
            pii_hits.append(rec.get("event", "unknown"))

        cid = rec.get("correlation_id")
        if cid and cid != "MISSING":
            correlation_ids.add(cid)

    print("--- Lab Verification Results ---")
    print(f"Log source: {log_path}")
    print(f"Service filter: {args.service}")
    print(f"Total log records analyzed: {total}")
    print(f"Records with missing required fields: {missing_required}")
    print(f"Records with missing enrichment (context): {missing_enrichment}")
    print(f"Unique correlation IDs found: {len(correlation_ids)}")
    print(f"Potential PII leaks detected: {len(pii_hits)}")
    if pii_hits:
        print(f"  Events with leaks: {set(pii_hits)}")

    print("\n--- Grading Scorecard (Estimates) ---")
    score = 100
    if missing_required > 0:
        score -= 30
        print("- [FAILED] Missing required fields (ts, level, service, event, correlation_id)")
    else:
        print("+ [PASSED] Basic JSON schema")

    if len(correlation_ids) < 2:
        score -= 20
        print("- [FAILED] Correlation ID propagation (less than 2 unique IDs)")
    else:
        print("+ [PASSED] Correlation ID propagation")

    if missing_enrichment > 0:
        score -= 20
        print("- [FAILED] Log enrichment (missing user_id_hash/session_id/feature/model)")
    else:
        print("+ [PASSED] Log enrichment")

    if pii_hits:
        score -= 30
        print("- [FAILED] PII scrubbing (found @ or test credit card)")
    else:
        print("+ [PASSED] PII scrubbing")

    print(f"\nEstimated Score: {max(0, score)}/100")


if __name__ == "__main__":
    main()
