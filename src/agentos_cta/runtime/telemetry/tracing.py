# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 分布式追踪封装。

from opentelemetry import trace
from opentelemetry.trace import Span, Status, StatusCode
from contextlib import contextmanager
from typing import Optional, Dict, Any
import time


class Tracer:
    """
    分布式追踪器，封装 OpenTelemetry Span 操作。
    """

    def __init__(self, tracer_name: str = "agentos"):
        self.tracer = trace.get_tracer(tracer_name)

    @contextmanager
    def start_span(self, name: str, attributes: Optional[Dict[str, Any]] = None):
        """启动一个新 span。"""
        with self.tracer.start_as_current_span(name) as span:
            if attributes:
                span.set_attributes(attributes)
            try:
                yield span
            except Exception as e:
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                raise

    def add_event(self, span: Span, name: str, attributes: Optional[Dict[str, Any]] = None):
        """在 span 上添加事件。"""
        span.add_event(name, attributes or {})

    def set_attribute(self, span: Span, key: str, value: Any):
        span.set_attribute(key, value)