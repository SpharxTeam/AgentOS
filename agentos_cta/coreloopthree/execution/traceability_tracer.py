# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 责任链追踪器。

import uuid
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from agentos_cta.utils.structured_logger import get_logger, set_trace_id, get_trace_id

logger = get_logger(__name__)


@dataclass
class TraceSpan:
    """追踪跨度，记录一个任务的执行片段。"""
    span_id: str
    parent_id: Optional[str]
    trace_id: str
    name: str
    start_time: float
    end_time: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


class TraceabilityTracer:
    """
    责任链追踪器。
    为每个任务生成唯一 TraceID，并记录所有子任务的执行路径。
    支持 OpenTelemetry 集成。
    """

    def __init__(self, enable_otel: bool = False):
        self.enable_otel = enable_otel
        self.spans: Dict[str, TraceSpan] = {}
        self.trace_tree: Dict[str, List[str]] = {}  # trace_id -> list of span_ids

    def start_trace(self, name: str, metadata: Optional[Dict] = None) -> str:
        """开始一个新的追踪，生成 TraceID。"""
        trace_id = str(uuid.uuid4())
        set_trace_id(trace_id)
        span = TraceSpan(
            span_id=trace_id,  # 根 span 使用 trace_id 作为 span_id
            parent_id=None,
            trace_id=trace_id,
            name=name,
            start_time=time.time(),
            metadata=metadata or {}
        )
        self.spans[trace_id] = span
        self.trace_tree[trace_id] = [trace_id]
        logger.info(f"Started trace {trace_id}: {name}")
        return trace_id

    def start_span(self, name: str, parent_id: Optional[str] = None,
                   metadata: Optional[Dict] = None) -> str:
        """在当前追踪中开始一个新的跨度。"""
        trace_id = get_trace_id()
        if not trace_id:
            # 如果没有活跃的 trace，自动创建一个
            trace_id = self.start_trace(name, metadata)
            return trace_id

        span_id = str(uuid.uuid4())
        span = TraceSpan(
            span_id=span_id,
            parent_id=parent_id or trace_id,
            trace_id=trace_id,
            name=name,
            start_time=time.time(),
            metadata=metadata or {}
        )
        self.spans[span_id] = span
        self.trace_tree[trace_id].append(span_id)
        return span_id

    def end_span(self, span_id: str, error: Optional[str] = None):
        """结束一个跨度。"""
        span = self.spans.get(span_id)
        if span:
            span.end_time = time.time()
            span.error = error
            duration = span.end_time - span.start_time
            if error:
                logger.error(f"Span {span_id} failed after {duration:.3f}s: {error}")
            else:
                logger.info(f"Span {span_id} completed in {duration:.3f}s")

    def get_trace(self, trace_id: str) -> List[TraceSpan]:
        """获取指定追踪的所有跨度。"""
        span_ids = self.trace_tree.get(trace_id, [])
        return [self.spans[sid] for sid in span_ids if sid in self.spans]

    def get_span(self, span_id: str) -> Optional[TraceSpan]:
        """获取指定跨度。"""
        return self.spans.get(span_id)

    def get_current_trace_id(self) -> Optional[str]:
        """获取当前上下文的 TraceID。"""
        return get_trace_id()