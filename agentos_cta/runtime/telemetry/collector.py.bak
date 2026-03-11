# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 可观测性收集器。

import time
from typing import Dict, Any, Optional
from agentos_cta.utils.structured_logger import get_logger
from .metrics import MetricsCollector
from .trace import TraceCollector
from .exporter import OtlpExporter

logger = get_logger(__name__)


class TelemetryCollector:
    """
    可观测性收集器。
    整合指标、追踪和日志，提供统一的可观测性能力。
    借鉴 Aura 架构的认知完整性设计 [citation:1][citation:8]。
    """

    def __init__(self, otlp_endpoint: Optional[str] = None, service_name: str = "agentos"):
        self.service_name = service_name
        self.metrics = MetricsCollector()
        self.traces = TraceCollector()

        if otlp_endpoint:
            self.exporter = OtlpExporter(endpoint=otlp_endpoint)
        else:
            self.exporter = None

    async def record_request(self, gateway_type: str, request: Dict[str, Any]):
        """记录请求。"""
        self.metrics.increment(f"requests.{gateway_type}.total")
        self.metrics.record_timing("request.processing", 0)

        trace_id = request.get("trace_id")
        if trace_id:
            await self.traces.start_span(
                name=f"handle_{gateway_type}_request",
                trace_id=trace_id,
                attributes={
                    "gateway": gateway_type,
                    "method": request.get("method", "unknown"),
                },
            )

    async def record_response(self, response: Dict[str, Any]):
        """记录响应。"""
        self.metrics.increment("responses.total")
        if "error" in response:
            self.metrics.increment("responses.error")

        await self.traces.end_span()

    async def record_task(self, task_id: str, duration_ms: float, success: bool):
        """记录任务执行。"""
        self.metrics.record_timing("task.duration", duration_ms)
        if success:
            self.metrics.increment("task.success")
        else:
            self.metrics.increment("task.failure")

    async def flush(self):
        """刷新所有指标和追踪。"""
        if self.exporter:
            metrics_data = self.metrics.collect()
            traces_data = await self.traces.collect()
            await self.exporter.export(metrics_data, traces_data)

    async def shutdown(self):
        """关闭收集器。"""
        await self.flush()
        if self.exporter:
            await self.exporter.shutdown()