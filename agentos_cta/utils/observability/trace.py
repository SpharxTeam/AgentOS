# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 追踪上下文管理。

import time
import uuid
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from contextlib import contextmanager


@dataclass
class Span:
    """追踪跨度。"""
    span_id: str
    trace_id: str
    name: str
    start_time: float
    end_time: Optional[float] = None
    parent_id: Optional[str] = None
    attributes: Dict[str, Any] = field(default_factory=dict)


class TraceContext:
    """
    追踪上下文管理器。
    用于手动创建和管理追踪跨度。
    """

    def __init__(self):
        self._spans: Dict[str, Span] = {}
        self._stack: list[str] = []

    def start_span(self, name: str, trace_id: Optional[str] = None) -> Span:
        """开始一个新的跨度。"""
        trace_id = trace_id or str(uuid.uuid4())
        span_id = str(uuid.uuid4())
        parent_id = self._stack[-1] if self._stack else None

        span = Span(
            span_id=span_id,
            trace_id=trace_id,
            name=name,
            start_time=time.time(),
            parent_id=parent_id,
        )
        self._spans[span_id] = span
        self._stack.append(span_id)
        return span

    def end_span(self) -> Optional[Span]:
        """结束当前跨度。"""
        if not self._stack:
            return None
        span_id = self._stack.pop()
        span = self._spans.get(span_id)
        if span:
            span.end_time = time.time()
        return span

    def get_current_span_id(self) -> Optional[str]:
        """获取当前跨度 ID。"""
        return self._stack[-1] if self._stack else None

    def get_trace_spans(self, trace_id: str) -> list[Span]:
        """获取指定追踪的所有跨度。"""
        return [s for s in self._spans.values() if s.trace_id == trace_id]

    @contextmanager
    def span(self, name: str, trace_id: Optional[str] = None):
        """上下文管理器风格的跨度。"""
        span = self.start_span(name, trace_id)
        try:
            yield span
        finally:
            self.end_span()