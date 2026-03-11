# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 指标收集器（基于 Prometheus 客户端）。

from prometheus_client import Counter, Histogram, Gauge, generate_latest
from typing import Dict, Any, Optional
import time


class MetricsCollector:
    """
    指标收集器，封装 Prometheus 指标。
    """

    def __init__(self, namespace: str = "agentos"):
        self.namespace = namespace
        # 定义常用指标
        self.request_count = Counter(
            name=f"{namespace}_requests_total",
            documentation="Total requests",
            labelnames=["gateway", "method", "status"]
        )
        self.request_duration = Histogram(
            name=f"{namespace}_request_duration_seconds",
            documentation="Request duration in seconds",
            labelnames=["gateway", "method"],
            buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10)
        )
        self.active_sessions = Gauge(
            name=f"{namespace}_active_sessions",
            documentation="Number of active sessions"
        )
        self.token_usage = Counter(
            name=f"{namespace}_token_usage_total",
            documentation="Total token usage",
            labelnames=["model", "type"]  # type: input/output
        )

    def record_request(self, gateway: str, method: str, status: str, duration: float):
        """记录请求。"""
        self.request_count.labels(gateway=gateway, method=method, status=status).inc()
        self.request_duration.labels(gateway=gateway, method=method).observe(duration)

    def set_active_sessions(self, count: int):
        self.active_sessions.set(count)

    def record_tokens(self, model: str, token_type: str, count: int):
        self.token_usage.labels(model=model, type=token_type).inc(count)

    def export(self) -> bytes:
        """返回 Prometheus 格式的指标数据。"""
        return generate_latest()