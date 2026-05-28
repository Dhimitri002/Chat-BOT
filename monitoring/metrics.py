"""
Flora Platform — Metrics Collector
====================================

Collects and aggregates application metrics for dashboards
and alerting. Integrates with the health monitoring system.
"""
from __future__ import annotations

import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class RequestMetrics:
    """Tracks HTTP request metrics."""
    total_requests: int = 0
    requests_by_method: dict = field(default_factory=lambda: defaultdict(int))
    requests_by_path: dict = field(default_factory=lambda: defaultdict(int))
    requests_by_status: dict = field(default_factory=lambda: defaultdict(int))
    error_count: int = 0
    total_response_time_ms: float = 0.0
    max_response_time_ms: float = 0.0
    min_response_time_ms: float = float("inf")

    @property
    def avg_response_time_ms(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return round(self.total_response_time_ms / self.total_requests, 2)

    @property
    def error_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return round(self.error_count / self.total_requests * 100, 2)

    def record(self, method: str, path: str, status_code: int, duration_ms: float):
        self.total_requests += 1
        self.requests_by_method[method] += 1
        self.requests_by_path[path] += 1
        self.requests_by_status[str(status_code)] += 1
        self.total_response_time_ms += duration_ms
        self.max_response_time_ms = max(self.max_response_time_ms, duration_ms)
        self.min_response_time_ms = min(self.min_response_time_ms, duration_ms)
        if status_code >= 400:
            self.error_count += 1

    def to_dict(self) -> dict:
        return {
            "total_requests": self.total_requests,
            "avg_response_time_ms": self.avg_response_time_ms,
            "max_response_time_ms": self.max_response_time_ms,
            "min_response_time_ms": self.min_response_time_ms if self.min_response_time_ms != float("inf") else 0,
            "error_count": self.error_count,
            "error_rate_pct": self.error_rate,
            "by_method": dict(self.requests_by_method),
            "by_status": dict(self.requests_by_status),
            "top_paths": dict(sorted(
                self.requests_by_path.items(),
                key=lambda x: x[1],
                reverse=True,
            )[:10]),
        }


# ─── Global metrics singleton ─────────────────────────────────────────────────
request_metrics = RequestMetrics()

# ─── Application counters ─────────────────────────────────────────────────────
_app_counters: dict[str, int] = defaultdict(int)


def increment_counter(name: str, value: int = 1):
    """Increment an application counter."""
    _app_counters[name] += value


def get_counter(name: str) -> int:
    """Get current counter value."""
    return _app_counters.get(name, 0)


def get_all_metrics() -> dict:
    """Get all collected metrics."""
    return {
        "requests": request_metrics.to_dict(),
        "counters": dict(_app_counters),
        "timestamp": time.time(),
    }
