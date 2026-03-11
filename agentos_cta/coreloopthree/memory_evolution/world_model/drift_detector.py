# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 认知漂移检测器：识别并修正Agent对同一事实的理解偏差。
# 基于 arXiv:2602.20934 "Architecting AgentOS" 中的 "Cognitive Drift" 概念。

from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
import time
import hashlib
from collections import defaultdict
import numpy as np
from agentos_cta.utils.structured_logger import get_logger
from agentos_cta.utils.error_types import ConsensusError

logger = get_logger(__name__)


@dataclass
class FactAssertion:
    """Agent对某个事实的断言。"""
    fact_id: str
    agent_id: str
    fact_key: str  # 事实的键（如 "project_name"）
    fact_value: Any  # 事实的值
    confidence: float  # 置信度 (0-1)
    timestamp: float
    context: Dict[str, Any] = field(default_factory=dict)
    source: Optional[str] = None  # 信息来源


@dataclass
class DriftEvent:
    """漂移事件记录。"""
    drift_id: str
    fact_key: str
    agent_id: str
    previous_value: Any
    current_value: Any
    drift_magnitude: float
    timestamp: float
    resolved: bool = False
    resolution: Optional[str] = None


class DriftDetector:
    """
    认知漂移检测器。
    监控各Agent对关键事实的断言，检测理解偏差和漂移，并提供修正机制。
    """

    def __init__(self, config: Dict[str, Any]):
        """
        初始化漂移检测器。

        Args:
            config: 配置参数
                - drift_threshold: 漂移检测阈值（0-1）
                - consistency_window: 一致性检测窗口大小
                - auto_correct: 是否自动尝试修正
        """
        self.drift_threshold = config.get("drift_threshold", 0.3)
        self.consistency_window = config.get("consistency_window", 10)
        self.auto_correct = config.get("auto_correct", False)
        
        # 事实断言存储
        self.assertions: Dict[str, List[FactAssertion]] = defaultdict(list)  # fact_key -> assertions
        
        # 漂移事件记录
        self.drift_events: List[DriftEvent] = []
        
        # Agent间一致性矩阵
        self.consistency_matrix: Dict[Tuple[str, str], float] = defaultdict(float)

    def _compute_fact_id(self, agent_id: str, fact_key: str, timestamp: float) -> str:
        """计算事实ID。"""
        content = f"{agent_id}:{fact_key}:{timestamp}"
        return hashlib.md5(content.encode()).hexdigest()[:16]

    def record_assertion(self, agent_id: str, fact_key: str, fact_value: Any,
                        confidence: float, context: Optional[Dict] = None) -> FactAssertion:
        """
        记录Agent对某个事实的断言。
        """
        assertion = FactAssertion(
            fact_id=self._compute_fact_id(agent_id, fact_key, time.time()),
            agent_id=agent_id,
            fact_key=fact_key,
            fact_value=fact_value,
            confidence=confidence,
            timestamp=time.time(),
            context=context or {}
        )
        
        self.assertions[fact_key].append(assertion)
        
        # 检测是否发生漂移
        self._check_drift(fact_key, agent_id, assertion)
        
        # 更新一致性矩阵
        self._update_consistency_matrix(fact_key)
        
        logger.debug(f"Recorded assertion: {agent_id} -> {fact_key} = {fact_value}")
        return assertion

    def _check_drift(self, fact_key: str, agent_id: str, new_assertion: FactAssertion) -> Optional[DriftEvent]:
        """
        检查Agent对特定事实的断言是否发生漂移。
        """
        # 获取该Agent对该事实的历史断言
        agent_assertions = [
            a for a in self.assertions[fact_key]
            if a.agent_id == agent_id
        ]
        
        if len(agent_assertions) < 2:
            return None
        
        # 获取最新的前一个断言
        previous = max(
            [a for a in agent_assertions if a.timestamp < new_assertion.timestamp],
            key=lambda a: a.timestamp,
            default=None
        )
        
        if not previous:
            return None
        
        # 计算漂移幅度
        drift_magnitude = self._compute_drift_magnitude(
            previous.fact_value, new_assertion.fact_value
        )
        
        if drift_magnitude >= self.drift_threshold:
            drift = DriftEvent(
                drift_id=self._compute_fact_id(agent_id, fact_key, new_assertion.timestamp),
                fact_key=fact_key,
                agent_id=agent_id,
                previous_value=previous.fact_value,
                current_value=new_assertion.fact_value,
                drift_magnitude=drift_magnitude,
                timestamp=new_assertion.timestamp
            )
            self.drift_events.append(drift)
            
            logger.warning(
                f"Drift detected: {agent_id} changed {fact_key} "
                f"from {previous.fact_value} to {new_assertion.fact_value} "
                f"(magnitude: {drift_magnitude:.2f})"
            )
            
            if self.auto_correct:
                self._attempt_correction(drift)
            
            return drift
        
        return None

    def _compute_drift_magnitude(self, value1: Any, value2: Any) -> float:
        """
        计算两个值之间的差异幅度。
        对于不同类型采用不同策略。
        """
        # 数值类型
        if isinstance(value1, (int, float)) and isinstance(value2, (int, float)):
            if value1 == 0:
                return abs(value2 - value1)
            return abs(value2 - value1) / max(abs(value1), 1)
        
        # 字符串类型
        elif isinstance(value1, str) and isinstance(value2, str):
            # 简单编辑距离比例
            if value1 == value2:
                return 0.0
            # 使用Jaccard相似度
            set1 = set(value1.lower().split())
            set2 = set(value2.lower().split())
            if not set1 and not set2:
                return 0.0
            intersection = set1.intersection(set2)
            union = set1.union(set2)
            return 1.0 - (len(intersection) / len(union))
        
        # 布尔类型
        elif isinstance(value1, bool) and isinstance(value2, bool):
            return 1.0 if value1 != value2 else 0.0
        
        # 列表/集合类型
        elif isinstance(value1, (list, set, tuple)) and isinstance(value2, (list, set, tuple)):
            set1 = set(value1)
            set2 = set(value2)
            if not set1 and not set2:
                return 0.0
            intersection = set1.intersection(set2)
            union = set1.union(set2)
            return 1.0 - (len(intersection) / len(union))
        
        # 默认：不同则视为完全漂移
        return 1.0 if value1 != value2 else 0.0

    def _update_consistency_matrix(self, fact_key: str):
        """
        更新Agent间一致性矩阵。
        基于最近窗口内的断言计算一致性。
        """
        assertions = self.assertions[fact_key]
        if len(assertions) < 2:
            return
        
        # 取最近窗口内的断言
        recent = sorted(assertions, key=lambda a: a.timestamp)[-self.consistency_window:]
        
        # 按Agent分组
        agent_groups: Dict[str, List[FactAssertion]] = defaultdict(list)
        for a in recent:
            agent_groups[a.agent_id].append(a)
        
        # 计算每对Agent的一致性
        agents = list(agent_groups.keys())
        for i in range(len(agents)):
            for j in range(i+1, len(agents)):
                a1, a2 = agents[i], agents[j]
                assertions1 = agent_groups[a1]
                assertions2 = agent_groups[a2]
                
                if not assertions1 or not assertions2:
                    continue
                
                # 使用最新断言
                latest1 = max(assertions1, key=lambda a: a.timestamp)
                latest2 = max(assertions2, key=lambda a: a.timestamp)
                
                # 计算一致性
                drift = self._compute_drift_magnitude(
                    latest1.fact_value, latest2.fact_value
                )
                consistency = 1.0 - drift
                
                self.consistency_matrix[(a1, a2)] = consistency
                self.consistency_matrix[(a2, a1)] = consistency

    def _attempt_correction(self, drift: DriftEvent) -> bool:
        """
        尝试自动修正漂移。
        基于多数一致性和置信度。
        """
        # 获取该事实的所有最近断言
        recent = self.get_recent_assertions(drift.fact_key, window=5)
        
        if not recent:
            return False
        
        # 按值分组
        value_groups: Dict[str, List[FactAssertion]] = defaultdict(list)
        for a in recent:
            # 将值转为字符串作为分组键
            key = str(a.fact_value)
            value_groups[key].append(a)
        
        # 找到最一致的组（多数派）
        majority_value = max(value_groups.items(), key=lambda x: len(x[1]))[0]
        majority_size = len(value_groups[majority_value])
        
        # 如果多数派足够大（超过半数），尝试修正
        if majority_size > len(recent) / 2:
            # 这里可以触发修正机制，例如：
            # - 向Agent发送纠正信息
            # - 更新共享记忆
            logger.info(
                f"Auto-correction candidate: {drift.agent_id} on {drift.fact_key} "
                f"should be {majority_value} (supported by {majority_size}/{len(recent)} agents)"
            )
            
            drift.resolved = True
            drift.resolution = f"Corrected to majority value: {majority_value}"
            return True
        
        return False

    def get_recent_assertions(self, fact_key: str, window: int = 10) -> List[FactAssertion]:
        """获取最近的对某个事实的断言。"""
        assertions = self.assertions.get(fact_key, [])
        sorted_assertions = sorted(assertions, key=lambda a: a.timestamp, reverse=True)
        return sorted_assertions[:window]

    def get_consensus_value(self, fact_key: str, min_confidence: float = 0.7) -> Tuple[Optional[Any], float]:
        """
        获取关于某个事实的共识值。

        Returns:
            (共识值, 共识强度)
        """
        recent = self.get_recent_assertions(fact_key, window=10)
        if not recent:
            return None, 0.0
        
        # 过滤低置信度断言
        filtered = [a for a in recent if a.confidence >= min_confidence]
        if not filtered:
            filtered = recent
        
        # 按值加权投票（置信度作为权重）
        vote_weights: Dict[str, float] = defaultdict(float)
        total_weight = 0.0
        
        for a in filtered:
            key = str(a.fact_value)
            vote_weights[key] += a.confidence
            total_weight += a.confidence
        
        if total_weight == 0:
            return None, 0.0
        
        # 找出权重最大的值
        consensus_value = max(vote_weights.items(), key=lambda x: x[1])[0]
        consensus_strength = vote_weights[consensus_value] / total_weight
        
        return consensus_value, consensus_strength

    def detect_cross_agent_drift(self, fact_key: str) -> List[Dict[str, Any]]:
        """
        检测不同Agent间对同一事实的理解偏差。
        """
        recent = self.get_recent_assertions(fact_key, window=20)
        if len(recent) < 2:
            return []
        
        # 按Agent分组
        agent_values: Dict[str, Any] = {}
        for a in recent:
            agent_values[a.agent_id] = a.fact_value
        
        # 检测偏差
        drifts = []
        agents = list(agent_values.keys())
        for i in range(len(agents)):
            for j in range(i+1, len(agents)):
                a1, a2 = agents[i], agents[j]
                v1, v2 = agent_values[a1], agent_values[a2]
                
                drift = self._compute_drift_magnitude(v1, v2)
                if drift >= self.drift_threshold:
                    drifts.append({
                        "fact_key": fact_key,
                        "agent1": a1,
                        "agent2": a2,
                        "value1": v1,
                        "value2": v2,
                        "drift_magnitude": drift
                    })
        
        return drifts

    def get_unresolved_drifts(self) -> List[DriftEvent]:
        """获取所有未解决的漂移事件。"""
        return [d for d in self.drift_events if not d.resolved]

    def resolve_drift(self, drift_id: str, resolution: str) -> bool:
        """手动解决一个漂移事件。"""
        for d in self.drift_events:
            if d.drift_id == drift_id:
                d.resolved = True
                d.resolution = resolution
                logger.info(f"Drift {drift_id} resolved: {resolution}")
                return True
        return False