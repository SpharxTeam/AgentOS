# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 任务规划相关数据模型（依赖 task_graph 中的基础类）。

from typing import Dict, Any
from dataclasses import dataclass, field
from .task_graph import TaskDAG  # 从新文件导入


@dataclass
class TaskPlan:
    """完整的任务规划，包含 DAG 和元信息。"""
    plan_id: str
    dag: TaskDAG
    created_at: float
    updated_at: float
    metadata: Dict[str, Any] = field(default_factory=dict)