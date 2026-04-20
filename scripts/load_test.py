import argparse
import concurrent.futures
import json
import math
import time
from collections import Counter
from pathlib import Path
from typing import Any

import httpx

BASE_URL = "http://127.0.0.1:8000"
QUERIES = Path("data/sample_queries.jsonl")
LOG_PATH = Path("data/logs.jsonl")


def percentile(values: list[float], p: int) -> float:
    if not values:
        return 0.0
    if len(values) == 1:
        return values[0]
    sorted_values = sorted(values)
    rank = (p / 100) * (len(sorted_values) - 1)
    low = math.floor(rank)
    high = math.ceil(rank)
    if low == high:
        return sorted_values[low]
    weight = rank - low
    return sorted_values[low] * (1 - weight) + sorted_values[high] * weight


def send_request(client: httpx.Client, payload: dict[str, Any], base_url: str) -> dict[str, Any]:
    started = time.perf_counter()
    try:
        r = client.post(f"{base_url}/chat", json=payload)
        latency = (time.perf_counter() - started) * 1000
        body: dict[str, Any] = {}
        if r.headers.get("content-type", "").startswith("application/json"):
            try:
                parsed = r.json()
                if isinstance(parsed, dict):
                    body = parsed
            except ValueError:
                body = {}
        correlation_id = body.get("correlation_id", "-")
        print(f"[{r.status_code}] {correlation_id} | {payload.get('feature', '-')} | {latency:.1f}ms")
        return {
            "ok": r.status_code < 400,
            "status": r.status_code,
            "latency_ms": latency,
            "error": None,
        }
    except Exception as e:
        latency = (time.perf_counter() - started) * 1000
        print(f"[ERR] - | {payload.get('feature', '-')} | {latency:.1f}ms | {e}")
        return {
            "ok": False,
            "status": "ERR",
            "latency_ms": latency,
            "error": str(e),
        }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--concurrency", type=int, default=1, help="Number of concurrent requests")
    parser.add_argument("--reset-logs", action="store_true", help="Clear data/logs.jsonl before sending requests")
    parser.add_argument("--repeat", type=int, default=1, help="Repeat the input dataset N times")
    parser.add_argument("--timeout", type=float, default=30.0, help="HTTP timeout in seconds")
    parser.add_argument("--base-url", default=BASE_URL, help="Target API base URL")
    parser.add_argument("--input", default=str(QUERIES), help="Path to JSONL request payloads")
    parser.add_argument("--summary-json", default="", help="Optional output path for JSON summary")
    args = parser.parse_args()

    lines = [line for line in QUERIES.read_text(encoding="utf-8").splitlines() if line.strip()]
    if args.reset_logs:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        LOG_PATH.write_text("", encoding="utf-8")
        print(f"Reset log file: {LOG_PATH}")
    
    with httpx.Client(timeout=30.0) as client:
    if args.concurrency < 1:
        raise ValueError("--concurrency must be >= 1")
    if args.repeat < 1:
        raise ValueError("--repeat must be >= 1")

    query_path = Path(args.input)
    lines = [line for line in query_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    payloads = [json.loads(line) for line in lines] * args.repeat
    if not payloads:
        raise ValueError("Input dataset is empty")

    started = time.perf_counter()
    results: list[dict[str, Any]] = []
    base_url = args.base_url.rstrip("/")

    with httpx.Client(timeout=args.timeout) as client:
        if args.concurrency > 1:
            with concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrency) as executor:
                futures = [executor.submit(send_request, client, payload, base_url) for payload in payloads]
                for future in concurrent.futures.as_completed(futures):
                    results.append(future.result())
        else:
            for payload in payloads:
                results.append(send_request(client, payload, base_url))

    elapsed = max(time.perf_counter() - started, 0.001)
    latencies = [result["latency_ms"] for result in results]
    ok_count = sum(1 for result in results if result["ok"])
    error_count = len(results) - ok_count
    status_counter = Counter(str(result["status"]) for result in results)

    summary = {
        "base_url": args.base_url,
        "input": str(query_path),
        "total_requests": len(results),
        "concurrency": args.concurrency,
        "repeat": args.repeat,
        "duration_sec": round(elapsed, 3),
        "qps": round(len(results) / elapsed, 2),
        "ok": ok_count,
        "errors": error_count,
        "success_rate": round((ok_count / len(results)) * 100, 2),
        "latency_ms": {
            "min": round(min(latencies), 2),
            "avg": round(sum(latencies) / len(latencies), 2),
            "p50": round(percentile(latencies, 50), 2),
            "p95": round(percentile(latencies, 95), 2),
            "p99": round(percentile(latencies, 99), 2),
            "max": round(max(latencies), 2),
        },
        "status_breakdown": dict(status_counter),
    }

    print("\n=== Load Test Summary ===")
    print(json.dumps(summary, indent=2))

    if args.summary_json:
        output_path = Path(args.summary_json)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print(f"Saved summary to {output_path}")


if __name__ == "__main__":
    main()
