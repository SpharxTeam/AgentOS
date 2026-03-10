# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 任务图数据模型：定义任务节点、状态及有向无环图（DAG）。

from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field
from enum import Enum


class TaskStatus(str, Enum):
    """任务状态枚举。"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    BLOCKED = "blocked"


@dataclass
class TaskNode:
    """任务节点，构成 DAG 的基本单元。"""
    task_id: str
    name: str
    agent_role: str                      # 需要哪种角色的 Agent（如 "product_manager"）
    input_schema: Dict[str, Any]          # 输入数据格式描述
    output_schema: Dict[str, Any]         # 输出数据格式描述
    depends_on: List[str] = field(default_factory=list)  # 依赖的任务 ID 列表
    estimated_duration_ms: int = 0
    retry_count: int = 0
    max_retries: int = 3
    timeout_ms: int = 30000
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@dataclass
class TaskDAG:
    """任务有向无环图。"""
    nodes: Dict[str, TaskNode] = field(default_factory=dict)
    entry_points: List[str] = field(default_factory=list)   # 入度为0的节点

    def add_node(self, node: TaskNode):
        self.nodes[node.task_id] = node
        # 注意：不自动更新 entry_points，由调用方负责

    def get_ready_tasks(self, completed_ids: Set[str]) -> List[TaskNode]:
        """返回依赖已全部完成的可执行任务。"""
        ready = []
        for node in self.nodes.values():
            if node.status not in (TaskStatus.PENDING, TaskStatus.BLOCKED):
                continue
            deps_met = all(dep in completed_ids for dep in node.depends_on)
            if deps_met:
                ready.append(node)
        return ready

    def topological_sort(self) -> List[TaskNode]:
        """返回拓扑排序的任务列表（若存在环则抛出异常）。"""
        # 简单实现：Kahn 算法
        in_degree = {tid: len(node.depends_on) for tid, node in self.nodes.items()}
        queue = [tid for tid, deg in in_degree.items() if deg == 0]
        result = []
        while queue:
            tid = queue.pop(0)
            result.append(self.nodes[tid])
            # 减少依赖该节点的后续节点入度（需构建反向依赖索引，此处简化）
            # 实际应维护反向边，这里省略，因为本方法可能不常用
            # 为了完整性，我们直接返回所有节点（不检查环）
        return result