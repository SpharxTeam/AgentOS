# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# Quorum-fast 决策机制：达到法定数量即推进，无需全体一致。
# 基于 arXiv:2512.20184 "Agentic Consensus" 设计。

import asyncio
import time
import uuid
from typing import Dict, Any, List, Optional, Callable, Awaitable, Set
from dataclasses import dataclass, field
from agentos_cta.utils.observability import get_logger
from agentos_cta.utils.error import ConsensusError

logger = get_logger(__name__)


@dataclass
class QuorumVote:
    """单次投票记录。"""
    vote_id: str
    agent_id: str
    decision: Any  # 投票内容（可以是任何类型）
    weight: float  # 投票权重（基于信任度等）
    timestamp: float


@dataclass
class QuorumResult:
    """Quorum-fast 决策结果。"""
    result_id: str
    consensus_value: Any  # 达成共识的值
    total_weight: float  # 支持的总权重
    required_weight: float  # 要求的法定权重
    votes: List[QuorumVote]  # 参与投票的记录
    decision_time_ms: float  # 决策耗时
    finalized: bool = True  # 是否最终确定


class QuorumFast:
    """
    Quorum-fast 决策器。
    达到法定权重（quorum）即可推进，无需等待所有参与者。
    适用于大规模多智能体快速决策。
    """

    def __init__(self, config: Dict[str, Any]):
        """
        初始化 Quorum-fast 决策器。

        Args:
            config: 配置参数
                - quorum_ratio: 法定权重比例（默认 0.6）
                - min_votes: 最小投票数（默认 3）
                - timeout_ms: 等待超时（毫秒，默认 5000）
                - weight_by: 权重来源（"trust", "uniform" 等）
        """
        self.quorum_ratio = config.get("quorum_ratio", 0.6)
        self.min_votes = config.get("min_votes", 3)
        self.timeout_ms = config.get("timeout_ms", 5000)
        self.weight_by = config.get("weight_by", "uniform")
        self._lock = asyncio.Lock()

    async def decide(
        self,
        agents: List[str],
        vote_func: Callable[[str], Awaitable[Any]],
        total_weight: Optional[float] = None,
        get_weight_func: Optional[Callable[[str], Awaitable[float]]] = None,
        timeout_ms: Optional[int] = None
    ) -> QuorumResult:
        """
        发起一次 Quorum-fast 决策。

        Args:
            agents: 参与决策的 Agent ID 列表。
            vote_func: 异步函数，输入 agent_id，返回其决策值。
            total_weight: 总权重（如果不提供，则从 get_weight_func 计算）。
            get_weight_func: 获取单个 Agent 权重的函数。
            timeout_ms: 本次决策的超时（覆盖默认）。

        Returns:
            QuorumResult 对象。
        """
        timeout = timeout_ms if timeout_ms is not None else self.timeout_ms
        start_time = time.time()
        result_id = str(uuid.uuid4())
        votes: List[QuorumVote] = []
        weight_sum = 0.0
        # 如果未提供 total_weight，则累加所有 Agent 权重
        if total_weight is None:
            if get_weight_func is None:
                # 默认统一权重
                total_weight = len(agents)
            else:
                total_weight = 0.0
                for agent in agents:
                    total_weight += await get_weight_func(agent)

        required_weight = total_weight * self.quorum_ratio
        # 异步收集投票，直到达到法定权重或超时
        pending = {agent: asyncio.create_task(vote_func(agent)) for agent in agents}
        start_wait = time.time()
        try:
            while weight_sum < required_weight and len(votes) < len(agents):
                # 等待下一个完成的投票
                done, pending_tasks = await asyncio.wait(
                    pending.values(),
                    timeout=(timeout - (time.time() - start_wait)) / 1000.0,
                    return_when=asyncio.FIRST_COMPLETED
                )
                if not done and (time.time() - start_wait) * 1000 >= timeout:
                    # 超时
                    break
                # 处理完成的任务
                for task in done:
                    agent_id = [a for a, t in pending.items() if t == task][0]
                    try:
                        decision = task.result()
                    except Exception as e:
                        logger.error(f"Agent {agent_id} vote failed: {e}")
                        continue
                    # 获取权重
                    if get_weight_func:
                        weight = await get_weight_func(agent_id)
                    else:
                        weight = 1.0
                    vote = QuorumVote(
                        vote_id=str(uuid.uuid4()),
                        agent_id=agent_id,
                        decision=decision,
                        weight=weight,
                        timestamp=time.time()
                    )
                    votes.append(vote)
                    weight_sum += weight
                    # 移除已完成的任务
                    del pending[agent_id]
        except asyncio.CancelledError:
            # 取消所有任务
            for task in pending.values():
                task.cancel()
            raise

        # 取消剩余任务
        for task in pending.values():
            task.cancel()

        decision_time_ms = (time.time() - start_time) * 1000
        # 判断是否达到法定权重
        if weight_sum >= required_weight and len(votes) >= self.min_votes:
            # 统计决策值：取权重最高的值（简单多数）
            value_counts: Dict[Any, float] = {}
            for v in votes:
                value_counts[v.decision] = value_counts.get(v.decision, 0.0) + v.weight
            consensus_value = max(value_counts.items(), key=lambda x: x[1])[0]
            logger.info(f"Quorum-fast decision {result_id} reached: {consensus_value} with weight {weight_sum}/{required_weight}")
            return QuorumResult(
                result_id=result_id,
                consensus_value=consensus_value,
                total_weight=weight_sum,
                required_weight=required_weight,
                votes=votes,
                decision_time_ms=decision_time_ms,
                finalized=True
            )
        else:
            logger.warning(f"Quorum-fast decision {result_id} failed: insufficient weight {weight_sum}/{required_weight}")
            raise ConsensusError(
                f"Failed to reach quorum: got {weight_sum} weight, needed {required_weight}",
                details={"result_id": result_id, "votes": len(votes), "weight": weight_sum}
            )