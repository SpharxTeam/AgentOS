# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 责任链追踪器。
# 为每个任务生成唯一 TraceID，贯穿所有子任务，记录执行路径、耗时、异常，支持事后归因分析。

import uuid
import time
import json
from typing import Dict, Any, Optional, List
from pathlib import Path
from dataclasses import dataclass, field, asdict
from agentos_cta.utils.structured_logger import get_logger, set_trace_id, get_trace_id

logger = get_logger(__name__)


@dataclass
class TraceSpan:
    """追踪跨度，表示一个子任务的执行。"""
    span_id: str
    parent_span_id: Optional[str]
    task_id: str
    agent_id: Optional[str]
    start_time: float
    end_time: Optional[float] = None
    status: str = "pending"  # pending, running, success, failure
    error: Optional[str] = None
    input_summary: Optional[str] = None
    output_summary: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class TraceabilityTracer:
    """
    责任链追踪器。
    管理 TraceID 和 Span，支持嵌套追踪，并将追踪记录持久化到文件。
    """

    def __init__(self, trace_id: Optional[str] = None, log_dir: str = "data/logs"):
        """
        初始化追踪器。

        Args:
            trace_id: 外部传入的 TraceID，若为 None 则自动生成。
            log_dir: 追踪日志存储目录。
        """
        self.trace_id = trace_id or str(uuid.uuid4())
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.spans: Dict[str, TraceSpan] = {}
        self.current_span_stack: List[str] = []  # 栈顶为当前 span_id
        set_trace_id(self.trace_id)  # 设置上下文变量

    def start_span(self, task_id: str, agent_id: Optional[str] = None,
                   input_summary: Optional[str] = None, metadata: Optional[Dict] = None) -> str:
        """
        开始一个新的追踪跨度。

        Args:
            task_id: 关联的任务 ID。
            agent_id: 执行 Agent 的 ID。
            input_summary: 输入摘要。
            metadata: 附加元数据。

        Returns:
            新 span 的 ID。
        """
        span_id = str(uuid.uuid4())
        parent_span_id = self.current_span_stack[-1] if self.current_span_stack else None
        span = TraceSpan(
            span_id=span_id,
            parent_span_id=parent_span_id,
            task_id=task_id,
            agent_id=agent_id,
            start_time=time.time(),
            status="running",
            input_summary=input_summary,
            metadata=metadata or {}
        )
        self.spans[span_id] = span
        self.current_span_stack.append(span_id)
        logger.info(f"Started span {span_id} for task {task_id}")
        return span_id

    def end_span(self, span_id: Optional[str] = None, status: str = "success",
                 output_summary: Optional[str] = None, error: Optional[str] = None):
        """
        结束一个追踪跨度。

        Args:
            span_id: 要结束的 span ID，若为 None 则结束栈顶的 span。
            status: 结束状态 ("success", "failure", "cancelled")。
            output_summary: 输出摘要。
            error: 错误信息（当 status 为 failure 时）。
        """
        if span_id is None:
            if not self.current_span_stack:
                logger.warning("No active span to end")
                return
            span_id = self.current_span_stack.pop()
        else:
            # 如果指定了 span_id，需要从栈中移除（可能不在栈顶，简单处理：尝试移除）
            if span_id in self.current_span_stack:
                self.current_span_stack.remove(span_id)

        span = self.spans.get(span_id)
        if not span:
            logger.warning(f"Span {span_id} not found")
            return

        span.end_time = time.time()
        span.status = status
        span.output_summary = output_summary
        span.error = error
        logger.info(f"Ended span {span_id} with status {status}")

    def get_current_span_id(self) -> Optional[str]:
        """返回当前活动的 span ID（栈顶）。"""
        return self.current_span_stack[-1] if self.current_span_stack else None

    def dump_to_file(self):
        """将当前追踪记录写入文件。"""
        file_path = self.log_dir / f"trace_{self.trace_id}.log"
        data = {
            "trace_id": self.trace_id,
            "spans": [asdict(span) for span in self.spans.values()]
        }
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"Trace dumped to {file_path}")

    @classmethod
    def load_from_file(cls, trace_id: str, log_dir: str = "data/logs") -> "TraceabilityTracer":
        """从文件加载追踪记录。"""
        file_path = Path(log_dir) / f"trace_{trace_id}.log"
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        tracer = cls(trace_id=trace_id, log_dir=log_dir)
        for span_data in data["spans"]:
            span = TraceSpan(**span_data)
            tracer.spans[span.span_id] = span
        return tracer

    def get_trace_tree(self) -> List[Dict]:
        """返回树形结构的追踪视图（按父子关系组织）。"""
        # 构建父子映射
        children_map: Dict[str, List[TraceSpan]] = {}
        for span in self.spans.values():
            parent = span.parent_span_id
            if parent not in children_map:
                children_map[parent] = []
            children_map[parent].append(span)

        def build_tree(parent_id: Optional[str]) -> List[Dict]:
            nodes = []
            for span in children_map.get(parent_id, []):
                node = asdict(span)
                node["children"] = build_tree(span.span_id)
                nodes.append(node)
            return nodes

        return build_tree(None)