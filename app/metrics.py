from __future__ import annotations

from collections import Counter
from statistics import mean

from prometheus_client import CONTENT_TYPE_LATEST, Counter as PromCounter
from prometheus_client import Gauge, Histogram, generate_latest

REQUEST_LATENCIES: list[int] = []
REQUEST_COSTS: list[float] = []
REQUEST_TOKENS_IN: list[int] = []
REQUEST_TOKENS_OUT: list[int] = []
ERRORS: Counter[str] = Counter()
TRAFFIC: int = 0
QUALITY_SCORES: list[float] = []

REQUEST_TOTAL = PromCounter(
    "lab_requests_total",
    "Total number of processed requests",
    labelnames=("feature", "model", "status"),
)
ERROR_TOTAL = PromCounter(
    "lab_errors_total",
    "Total number of failed requests",
    labelnames=("error_type", "feature", "model"),
)
LATENCY_MS = Histogram(
    "lab_request_latency_ms",
    "Request latency in milliseconds",
    labelnames=("feature", "model"),
    buckets=(50, 100, 250, 500, 1000, 2000, 3000, 5000, 7500, 10000, float("inf")),
)
COST_TOTAL_USD = PromCounter(
    "lab_cost_usd_total",
    "Accumulated request cost in USD",
    labelnames=("feature", "model"),
)
TOKENS_IN_TOTAL = PromCounter(
    "lab_tokens_in_total",
    "Accumulated input tokens",
    labelnames=("feature", "model"),
)
TOKENS_OUT_TOTAL = PromCounter(
    "lab_tokens_out_total",
    "Accumulated output tokens",
    labelnames=("feature", "model"),
)
QUALITY_SCORE = Gauge(
    "lab_quality_score",
    "Most recent quality score by feature/model",
    labelnames=("feature", "model"),
)


def _norm(label: str | None, fallback: str) -> str:
    if not label:
        return fallback
    value = str(label).strip()
    return value if value else fallback


def record_request(
    latency_ms: int,
    cost_usd: float,
    tokens_in: int,
    tokens_out: int,
    quality_score: float,
    *,
    feature: str | None = None,
    model: str | None = None,
    status: str = "success",
) -> None:
    global TRAFFIC
    TRAFFIC += 1
    REQUEST_LATENCIES.append(latency_ms)
    REQUEST_COSTS.append(cost_usd)
    REQUEST_TOKENS_IN.append(tokens_in)
    REQUEST_TOKENS_OUT.append(tokens_out)
    QUALITY_SCORES.append(quality_score)

    feature_label = _norm(feature, "unknown")
    model_label = _norm(model, "unknown")
    status_label = _norm(status, "unknown")

    REQUEST_TOTAL.labels(feature=feature_label, model=model_label, status=status_label).inc()
    LATENCY_MS.labels(feature=feature_label, model=model_label).observe(latency_ms)
    COST_TOTAL_USD.labels(feature=feature_label, model=model_label).inc(max(cost_usd, 0.0))
    TOKENS_IN_TOTAL.labels(feature=feature_label, model=model_label).inc(max(tokens_in, 0))
    TOKENS_OUT_TOTAL.labels(feature=feature_label, model=model_label).inc(max(tokens_out, 0))
    QUALITY_SCORE.labels(feature=feature_label, model=model_label).set(max(0.0, min(1.0, quality_score)))


def record_error(error_type: str, *, feature: str | None = None, model: str | None = None) -> None:
    ERRORS[error_type] += 1
    ERROR_TOTAL.labels(
        error_type=_norm(error_type, "unknown_error"),
        feature=_norm(feature, "unknown"),
        model=_norm(model, "unknown"),
    ).inc()



def percentile(values: list[int], p: int) -> float:
    if not values:
        return 0.0
    items = sorted(values)
    idx = max(0, min(len(items) - 1, round((p / 100) * len(items) + 0.5) - 1))
    return float(items[idx])



def snapshot() -> dict:
    return {
        "traffic": TRAFFIC,
        "latency_p50": percentile(REQUEST_LATENCIES, 50),
        "latency_p95": percentile(REQUEST_LATENCIES, 95),
        "latency_p99": percentile(REQUEST_LATENCIES, 99),
        "avg_cost_usd": round(mean(REQUEST_COSTS), 4) if REQUEST_COSTS else 0.0,
        "total_cost_usd": round(sum(REQUEST_COSTS), 4),
        "tokens_in_total": sum(REQUEST_TOKENS_IN),
        "tokens_out_total": sum(REQUEST_TOKENS_OUT),
        "error_breakdown": dict(ERRORS),
        "quality_avg": round(mean(QUALITY_SCORES), 4) if QUALITY_SCORES else 0.0,
    }


def prometheus_payload() -> tuple[bytes, str]:
    return generate_latest(), CONTENT_TYPE_LATEST
