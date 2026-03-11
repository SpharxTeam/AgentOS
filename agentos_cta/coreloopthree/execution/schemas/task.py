# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 任务数据模型。

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum


class TaskStatus(str, Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


@dataclass
class Task:
    """任务实体，用于在行动层内部流转。"""
    task_id: str
    name: str
    agent_role: str
    input_data: Dict[str, Any]
    context: Dict[str, Any] = field(default_factory=dict)
    status: TaskStatus = TaskStatus.PENDING
    assigned_agent_id: Optional[str] = None
    created_at: float = 0.0
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    retry_count: int = 0
    max_retries: int = 3
    timeout_ms: int = 30000
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    trace_span_id: Optional[str] = None  # 关联的追踪跨度