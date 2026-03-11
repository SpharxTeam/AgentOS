# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 追踪收集器。

import time
import uuid
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field


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
    events: List[Dict[str, Any]] = field(default_factory=list)


class TraceCollector:
    """
    追踪收集器。
    支持分布式追踪，与 TraceabilityTracer 集成。
    """

    def __init__(self):
        self._spans: Dict[str, Span] = {}
        self._current_span: Optional[Span] = None

    async def start_span(self, name: str, trace_id: Optional[str] = None,
                         parent_id: Optional[str] = None,
                         attributes: Optional[Dict[str, Any]] = None) -> str:
        """开始一个新跨度。"""
        span_id = str(uuid.uuid4())
        if not trace_id:
            trace_id = str(uuid.uuid4())

        span = Span(
            span_id=span_id,
            trace_id=trace_id,
            name=name,
            start_time=time.time(),
            parent_id=parent_id,
            attributes=attributes or {},
        )
        self._spans[span_id] = span
        self._current_span = span
        return span_id

    async def end_span(self, span_id: Optional[str] = None):
        """结束一个跨度。"""
        if span_id is None and self._current_span:
            span_id = self._current_span.span_id

        if span_id and span_id in self._spans:
            self._spans[span_id].end_time = time.time()
            if self._current_span and self._current_span.span_id == span_id:
                self._current_span = None

    async def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None):
        """向当前跨度添加事件。"""
        if self._current_span:
            self._current_span.events.append({
                "name": name,
                "timestamp": time.time(),
                "attributes": attributes or {},
            })

    async def collect(self) -> List[Dict[str, Any]]:
        """收集所有已完成跨度。"""
        completed = []
        for span_id, span in list(self._spans.items()):
            if span.end_time is not None:
                completed.append({
                    "span_id": span.span_id,
                    "trace_id": span.trace_id,
                    "name": span.name,
                    "start_time": span.start_time,
                    "end_time": span.end_time,
                    "duration_ms": (span.end_time - span.start_time) * 1000,
                    "parent_id": span.parent_id,
                    "attributes": span.attributes,
                    "events": span.events,
                })
                del self._spans[span_id]
        return completed