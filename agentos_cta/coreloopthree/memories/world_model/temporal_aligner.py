# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 时间对齐器：解决多 Agent 间的时序不一致和时钟漂移问题。

import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
import asyncio
from agentos_cta.utils.observability import get_logger

logger = get_logger(__name__)


@dataclass
class TimedEvent:
    """带时间戳的事件。"""
    event_id: str
    agent_id: str
    event_type: str
    data: Dict[str, Any]
    timestamp: float  # 事件发生时间（Agent 本地时间）
    received_timestamp: float  # 系统接收时间
    sequence_id: Optional[str] = None  # 所属时序ID（如任务ID）
    causal_parents: List[str] = field(default_factory=list)  # 因果依赖的事件ID


class TemporalAligner:
    """
    时间对齐器。
    负责对齐多 Agent 产生的事件流，解决乱序、延迟和时钟漂移问题。
    """

    def __init__(self, config: Dict[str, Any]):
        """
        初始化时间对齐器。

        Args:
            config: 配置参数
                - max_drift_ms: 允许的最大时钟漂移（毫秒）
                - event_window_ms: 事件对齐窗口大小（毫秒）
                - max_latency_ms: 最大允许延迟
        """
        self.max_drift_ms = config.get("max_drift_ms", 100)
        self.event_window_ms = config.get("event_window_ms", 500)
        self.max_latency_ms = config.get("max_latency_ms", 5000)

        self.event_buffer: List[TimedEvent] = []
        self.agent_time_offset: Dict[str, float] = defaultdict(float)  # 时钟漂移校正值
        self.causal_graph: Dict[str, set] = defaultdict(set)  # event_id -> set of dependent event_ids
        self._lock = asyncio.Lock()

    async def record_event(self, event: TimedEvent) -> None:
        """记录一个事件，自动校正时钟漂移。"""
        async with self._lock:
            # 校正 Agent 时钟漂移
            corrected_timestamp = event.timestamp + self.agent_time_offset[event.agent_id]
            event.timestamp = corrected_timestamp
            self.event_buffer.append(event)

            # 记录因果依赖
            for parent_id in event.causal_parents:
                self.causal_graph[parent_id].add(event.event_id)

        logger.debug(f"Recorded event {event.event_id} from {event.agent_id}")

    async def detect_clock_drift(self, agent_id: str, reference_timestamp: float) -> float:
        """
        检测 Agent 的时钟漂移。
        使用最近事件的平均偏差估计漂移。
        """
        async with self._lock:
            agent_events = [e for e in self.event_buffer if e.agent_id == agent_id]
            if len(agent_events) < 5:
                return self.agent_time_offset[agent_id]

            # 计算每个事件的延迟（接收时间 - 事件时间）
            latencies = [e.received_timestamp - e.timestamp for e in agent_events[-10:]]
            avg_latency = sum(latencies) / len(latencies)

            # 期望延迟（假设平均网络延迟 100ms）
            expected_latency = 0.1
            drift = avg_latency - expected_latency

            # 低通滤波更新
            self.agent_time_offset[agent_id] = 0.9 * self.agent_time_offset[agent_id] + 0.1 * drift

        return self.agent_time_offset[agent_id]

    async def get_aligned_events(self, start_time: float, end_time: float) -> List[TimedEvent]:
        """获取时间对齐后的事件（按时间排序）。"""
        async with self._lock:
            filtered = [e for e in self.event_buffer if start_time <= e.timestamp <= end_time]
            filtered.sort(key=lambda e: e.timestamp)
            return filtered

    async def get_causal_chain(self, event_id: str) -> List[TimedEvent]:
        """获取事件的因果链（依赖此事件的所有后代事件）。"""
        async with self._lock:
            visited = set()
            queue = [event_id]
            result = []

            while queue:
                current = queue.pop(0)
                if current in visited:
                    continue
                visited.add(current)

                event = next((e for e in self.event_buffer if e.event_id == current), None)
                if event:
                    result.append(event)

                for child in self.causal_graph.get(current, []):
                    if child not in visited:
                        queue.append(child)

            result.sort(key=lambda e: e.timestamp)
            return result

    async def detect_inconsistencies(self) -> List[Dict[str, Any]]:
        """
        检测时序不一致性（如因果倒置、时间旅行等）。
        """
        inconsistencies = []
        async with self._lock:
            # 检查因果一致性
            for parent_id, children in self.causal_graph.items():
                parent = next((e for e in self.event_buffer if e.event_id == parent_id), None)
                if not parent:
                    continue

                for child_id in children:
                    child = next((e for e in self.event_buffer if e.event_id == child_id), None)
                    if not child:
                        continue

                    if child.timestamp < parent.timestamp - 0.001:  # 允许 1ms 误差
                        inconsistencies.append({
                            "type": "causality_inversion",
                            "parent": parent_id,
                            "child": child_id,
                            "parent_time": parent.timestamp,
                            "child_time": child.timestamp,
                            "drift": parent.timestamp - child.timestamp
                        })

            # 检查时间旅行（事件时间远早于或晚于系统时间）
            now = time.time()
            for event in self.event_buffer[-100:]:
                age = now - event.timestamp
                if age < -1:  # 未来事件
                    inconsistencies.append({
                        "type": "future_event",
                        "event_id": event.event_id,
                        "agent_id": event.agent_id,
                        "event_time": event.timestamp,
                        "now": now,
                        "drift": event.timestamp - now
                    })
                elif age > self.max_latency_ms / 1000:
                    inconsistencies.append({
                        "type": "excessive_latency",
                        "event_id": event.event_id,
                        "agent_id": event.agent_id,
                        "latency": age,
                        "threshold": self.max_latency_ms / 1000
                    })

        return inconsistencies

    async def prune_old_events(self, max_age_seconds: float = 3600) -> int:
        """清理过旧的事件，释放内存。"""
        cutoff = time.time() - max_age_seconds
        async with self._lock:
            before = len(self.event_buffer)
            self.event_buffer = [e for e in self.event_buffer if e.timestamp > cutoff]
            removed = before - len(self.event_buffer)

            # 清理因果图
            self.causal_graph = {
                k: {v for v in vs if any(e.event_id == v for e in self.event_buffer)}
                for k, vs in self.causal_graph.items()
                if any(e.event_id == k for e in self.event_buffer)
            }

        logger.info(f"Pruned {removed} old events")
        return removed