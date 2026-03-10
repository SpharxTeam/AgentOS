# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# Quorum-fast 决策机制。
# 不等待所有节点达成一致，达到法定数量即推进，大幅降低延迟。
# 基于 arXiv:2512.20184 "Agentic Consensus" 中的 Quorum-fast 概念。

import asyncio
import time
from typing import List, Dict, Any, Optional, Callable, Awaitable, Set
from dataclasses import dataclass, field
from enum import Enum
from agentos_cta.utils.structured_logger import get_logger
from agentos_cta.utils.error_types import ConsensusError

logger = get_logger(__name__)


class DecisionStatus(Enum):
    PENDING = "pending"
    QUORUM_REACHED = "quorum_reached"
    COMPLETED = "completed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


@dataclass
class Vote:
    """单个节点的投票。"""
    node_id: str
    value: Any
    weight: float = 1.0
    timestamp: float = field(default_factory=time.time)


@dataclass
class QuorumResult:
    """Quorum-fast 决策结果。"""
    decision_id: str
    status: DecisionStatus
    final_value: Optional[Any] = None
    votes: List[Vote] = field(default_factory=list)
    quorum_threshold: float = 0.0
    total_weight: float = 0.0
    reached_at: Optional[float] = None
    completed_at: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class QuorumFast:
    """
    Quorum-fast 决策引擎。
    允许在达到法定票数后立即做出决策，无需等待所有节点。
    支持加权投票、超时、动态节点集。
    """

    def __init__(self, config: Dict[str, Any]):
        """
        初始化 Quorum-fast 决策器。

        Args:
            config: 配置参数
                - quorum_ratio: 法定比例（如 0.6 表示 60% 权重）
                - default_node_weight: 节点默认权重
                - decision_timeout_ms: 决策超时（毫秒）
                - enable_dynamic_quorum: 是否允许动态调整法定比例
        """
        self.quorum_ratio = config.get("quorum_ratio", 0.6)
        self.default_node_weight = config.get("default_node_weight", 1.0)
        self.decision_timeout_ms = config.get("decision_timeout_ms", 5000)
        self.enable_dynamic_quorum = config.get("enable_dynamic_quorum", False)
        
        # 节点权重表（可动态更新）
        self.node_weights: Dict[str, float] = {}
        
        # 进行中的决策
        self._pending_decisions: Dict[str, Dict] = {}

    def register_node(self, node_id: str, weight: Optional[float] = None):
        """注册节点及其权重。"""
        self.node_weights[node_id] = weight if weight is not None else self.default_node_weight
        logger.info(f"Registered node {node_id} with weight {self.node_weights[node_id]}")

    def unregister_node(self, node_id: str):
        """注销节点。"""
        self.node_weights.pop(node_id, None)

    async def decide(
        self,
        decision_id: str,
        nodes: List[str],
        vote_func: Callable[[str], Awaitable[Any]],
        quorum_ratio: Optional[float] = None,
        timeout_ms: Optional[int] = None,
        initial_value: Any = None
    ) -> QuorumResult:
        """
        发起一次 Quorum-fast 决策。

        Args:
            decision_id: 决策唯一标识
            nodes: 参与决策的节点列表
            vote_func: 异步函数，输入 node_id，返回该节点的投票值
            quorum_ratio: 可选，覆盖默认法定比例
            timeout_ms: 可选，覆盖默认超时
            initial_value: 初始值（用于合并投票）

        Returns:
            决策结果
        """
        quorum = quorum_ratio or self.quorum_ratio
        timeout = timeout_ms or self.decision_timeout_ms
        
        # 计算总权重
        total_weight = sum(self.node_weights.get(n, self.default_node_weight) for n in nodes)
        quorum_weight = total_weight * quorum
        
        logger.info(f"Starting decision {decision_id} with quorum {quorum:.2f} "
                   f"({quorum_weight:.1f}/{total_weight:.1f} weight)")
        
        # 初始化结果
        result = QuorumResult(
            decision_id=decision_id,
            status=DecisionStatus.PENDING,
            quorum_threshold=quorum_weight,
            total_weight=total_weight,
        )
        
        # 记录投票
        votes: Dict[str, Vote] = {}
        vote_counts: Dict[Any, float] = {}  # 值 -> 累计权重
        if initial_value is not None:
            vote_counts[initial_value] = 0.0  # 占位
        
        # 创建异步投票任务
        async def vote_task(node: str):
            try:
                value = await vote_func(node)
                weight = self.node_weights.get(node, self.default_node_weight)
                vote = Vote(node_id=node, value=value, weight=weight)
                return vote
            except Exception as e:
                logger.error(f"Node {node} vote failed: {e}")
                return None

        tasks = [vote_task(node) for node in nodes]
        
        # 使用 asyncio.wait 逐步收集结果
        pending = set(asyncio.create_task(t) for t in tasks)
        start_time = time.time()
        deadline = start_time + timeout / 1000.0
        
        self._pending_decisions[decision_id] = {
            "result": result,
            "votes": votes,
            "vote_counts": vote_counts,
            "quorum_weight": quorum_weight,
        }
        
        try:
            while pending and time.time() < deadline:
                done, pending = await asyncio.wait(
                    pending, timeout=max(0, deadline - time.time()),
                    return_when=asyncio.FIRST_COMPLETED
                )
                
                for task in done:
                    vote = task.result()
                    if vote is None:
                        continue
                    
                    # 记录投票
                    votes[vote.node_id] = vote
                    result.votes.append(vote)
                    
                    # 更新累计权重
                    key = self._value_key(vote.value)
                    vote_counts[key] = vote_counts.get(key, 0) + vote.weight
                    
                    logger.debug(f"Decision {decision_id}: node {vote.node_id} voted {vote.value} "
                                f"(weight {vote.weight}, cumulative {vote_counts[key]})")
                    
                    # 检查是否达到法定票数
                    for val_key, cum_weight in vote_counts.items():
                        if cum_weight >= quorum_weight:
                            # 达到法定票数
                            result.status = DecisionStatus.QUORUM_REACHED
                            result.final_value = self._recover_value(val_key, vote_counts)
                            result.reached_at = time.time()
                            logger.info(f"Decision {decision_id} reached quorum with value {result.final_value}")
                            
                            # 取消剩余任务
                            for t in pending:
                                t.cancel()
                            return result
                
            # 超时或全部完成
            if time.time() >= deadline:
                result.status = DecisionStatus.TIMEOUT
                logger.warning(f"Decision {decision_id} timed out")
            else:
                # 所有节点都投票了，但未达到法定票数
                result.status = DecisionStatus.COMPLETED
                # 选择累计权重最高的值
                if vote_counts:
                    best_val_key = max(vote_counts.items(), key=lambda x: x[1])[0]
                    result.final_value = self._recover_value(best_val_key, vote_counts)
                logger.info(f"Decision {decision_id} completed without quorum, best value: {result.final_value}")
            
            result.completed_at = time.time()
            return result
            
        finally:
            self._pending_decisions.pop(decision_id, None)

    def _value_key(self, value: Any) -> str:
        """将值转换为可哈希的键（用于字典）。"""
        # 简单实现：对于不可哈希的类型，使用字符串表示
        try:
            hash(value)
            return value  # 如果可哈希，直接返回
        except TypeError:
            return str(value)

    def _recover_value(self, key: str, vote_counts: Dict) -> Any:
        """从键恢复原始值（如果可能）。"""
        # 由于键可能是原始值或字符串，这里简单处理
        # 实际上可能需要存储映射，但通常值是可哈希的
        return key

    def get_decision_status(self, decision_id: str) -> Optional[QuorumResult]:
        """获取进行中决策的状态。"""
        pending = self._pending_decisions.get(decision_id)
        return pending["result"] if pending else None

    def cancel_decision(self, decision_id: str) -> bool:
        """取消进行中的决策。"""
        pending = self._pending_decisions.get(decision_id)
        if pending:
            # 取消所有任务（需外部支持）
            # 这里简单标记
            pending["result"].status = DecisionStatus.CANCELLED
            logger.info(f"Decision {decision_id} cancelled")
            return True
        return False

    def set_node_weight(self, node_id: str, weight: float):
        """动态调整节点权重。"""
        self.node_weights[node_id] = weight
        logger.info(f"Node {node_id} weight updated to {weight}")