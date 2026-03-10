# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 时间对齐器：确保多Agent间的时序一致性，处理事件顺序和时间漂移。
# 基于 arXiv:2602.20934 "Architecting AgentOS" 中的 "Temporal Alignment" 概念。

import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
import threading
from agentos_cta.utils.structured_logger import get_logger

logger = get_logger(__name__)


@dataclass
class TimedEvent:
    """带时间戳的事件。"""
    event_id: str
    agent_id: str
    event_type: str
    data: Dict[str, Any]
    timestamp: float  # 事件发生时间（Unix时间戳）
    received_timestamp: float  # 系统接收时间
    sequence_id: Optional[str] = None  # 所属时序ID（如任务ID）
    causal_parents: List[str] = field(default_factory=list)  # 因果依赖的事件ID


class TemporalAligner:
    """
    时间对齐器。
    负责对齐多Agent产生的事件流，解决乱序、延迟和时钟漂移问题。
    """

    def __init__(self, config: Dict[str, Any]):
        """
        初始化时间对齐器。

        Args:
            config: 配置参数
                - max_drift_ms: 允许的最大时钟漂移（毫秒）
                - event_window_ms: 事件对齐窗口大小（毫秒）
                - max_latency_ms: 最大允许延迟（超过此值的事件将被标记为延迟）
        """
        self.max_drift_ms = config.get("max_drift_ms", 100)  # 100ms
        self.event_window_ms = config.get("event_window_ms", 500)  # 500ms
        self.max_latency_ms = config.get("max_latency_ms", 5000)  # 5秒
        
        # 事件缓冲区
        self.event_buffer: List[TimedEvent] = []
        self.buffer_lock = threading.Lock()
        
        # Agent时间偏移记录（用于检测和校正时钟漂移）
        self.agent_time_offset: Dict[str, float] = defaultdict(float)
        
        # 因果图：event_id -> set of dependent event_ids
        self.causal_graph: Dict[str, set] = defaultdict(set)

    def record_event(self, event: TimedEvent) -> None:
        """
        记录一个事件。
        事件可能来自不同Agent，可能乱序到达。
        """
        with self.buffer_lock:
            # 校正Agent时钟漂移
            corrected_timestamp = event.timestamp + self.agent_time_offset[event.agent_id]
            event.timestamp = corrected_timestamp
            
            self.event_buffer.append(event)
            
            # 记录因果依赖
            for parent_id in event.causal_parents:
                self.causal_graph[parent_id].add(event.event_id)

        logger.debug(f"Recorded event {event.event_id} from {event.agent_id}")

    def detect_clock_drift(self, agent_id: str, reference_timestamp: float) -> float:
        """
        检测Agent的时钟漂移。
        返回当前估计的漂移量（秒）。
        """
        # 简单实现：使用最近事件的平均偏差
        with self.buffer_lock:
            agent_events = [e for e in self.event_buffer if e.agent_id == agent_id]
            if len(agent_events) < 5:
                return self.agent_time_offset[agent_id]

            # 计算每个事件的延迟（接收时间 - 事件时间）
            latencies = [e.received_timestamp - e.timestamp for e in agent_events[-10:]]
            avg_latency = sum(latencies) / len(latencies)
            
            # 期望延迟（假设网络延迟为正态分布）
            expected_latency = 0.1  # 假设100ms平均网络延迟
            
            # 漂移 = 平均延迟 - 期望延迟
            drift = avg_latency - expected_latency
            
            # 更新偏移量（使用低通滤波）
            self.agent_time_offset[agent_id] = (
                0.9 * self.agent_time_offset[agent_id] + 0.1 * drift
            )

        return self.agent_time_offset[agent_id]

    def get_aligned_events(self, start_time: float, end_time: float) -> List[TimedEvent]:
        """
        获取时间对齐后的事件（按时间排序，处理乱序）。
        """
        with self.buffer_lock:
            # 筛选时间范围内的事件
            filtered = [
                e for e in self.event_buffer
                if start_time <= e.timestamp <= end_time
            ]
            
            # 按时间戳排序
            filtered.sort(key=lambda e: e.timestamp)
            
            return filtered

    def get_causal_chain(self, event_id: str) -> List[TimedEvent]:
        """
        获取事件的因果链（依赖此事件的所有后代事件）。
        """
        with self.buffer_lock:
            # BFS遍历因果图
            visited = set()
            queue = [event_id]
            result = []
            
            while queue:
                current = queue.pop(0)
                if current in visited:
                    continue
                visited.add(current)
                
                # 找到事件对象
                event = next((e for e in self.event_buffer if e.event_id == current), None)
                if event:
                    result.append(event)
                
                # 添加后代
                for child in self.causal_graph.get(current, []):
                    if child not in visited:
                        queue.append(child)
            
            # 按时间排序
            result.sort(key=lambda e: e.timestamp)
            return result

    def detect_inconsistencies(self) -> List[Dict[str, Any]]:
        """
        检测时序不一致性（如因果倒置、时间旅行等）。
        """
        inconsistencies = []
        
        with self.buffer_lock:
            # 检查因果一致性
            for parent_id, children in self.causal_graph.items():
                parent = next((e for e in self.event_buffer if e.event_id == parent_id), None)
                if not parent:
                    continue
                
                for child_id in children:
                    child = next((e for e in self.event_buffer if e.event_id == child_id), None)
                    if not child:
                        continue
                    
                    # 因果倒置：子事件发生在父事件之前
                    if child.timestamp < parent.timestamp - 0.001:  # 允许1ms误差
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
            for event in self.event_buffer[-100:]:  # 只检查最近100个事件
                age = now - event.timestamp
                if age < -1:  # 未来事件（超过1秒）
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

    def prune_old_events(self, max_age_seconds: float = 3600) -> int:
        """
        清理过旧的事件，释放内存。

        Args:
            max_age_seconds: 保留事件的最大时长（秒）

        Returns:
            移除的事件数量
        """
        cutoff = time.time() - max_age_seconds
        removed = 0
        
        with self.buffer_lock:
            # 移除旧事件
            self.event_buffer = [e for e in self.event_buffer if e.timestamp > cutoff]
            removed = len(self.event_buffer) - len(self.event_buffer)
            
            # 清理因果图（移除已不存在的事件）
            self.causal_graph = {
                k: {v for v in vs if any(e.event_id == v for e in self.event_buffer)}
                for k, vs in self.causal_graph.items()
                if any(e.event_id == k for e in self.event_buffer)
            }

        logger.info(f"Pruned {removed} old events")
        return removed