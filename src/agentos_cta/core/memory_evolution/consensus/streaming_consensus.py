# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# Streaming 共识机制。
# 在 Token 流式生成过程中持续检测共识状态，满足条件立即终止生成。
# 基于 arXiv:2512.20184 "Agentic Consensus" 中的 Streaming Consensus 概念。

import asyncio
import time
from typing import AsyncGenerator, List, Dict, Any, Optional, Callable, Awaitable, Set
from dataclasses import dataclass, field
from enum import Enum
from agentos_cta.utils.structured_logger import get_logger
from agentos_cta.utils.error_types import ConsensusError
from .stability_window import StabilityWindow, StabilityResult

logger = get_logger(__name__)


class ConsensusState(Enum):
    SEARCHING = "searching"       # 正在收集 token
    CONVERGING = "converging"     # 发现趋势，继续确认
    ACHIEVED = "achieved"         # 达成共识
    FAILED = "failed"             # 无法达成共识
    CANCELLED = "cancelled"       # 取消


@dataclass
class TokenProposal:
    """单个 token 的提议（来自某个节点）。"""
    node_id: str
    token: str
    sequence: int
    timestamp: float
    weight: float = 1.0


@dataclass
class ConsensusResult:
    """Streaming 共识结果。"""
    consensus_id: str
    state: ConsensusState
    consensus_text: Optional[str] = None  # 达成共识的完整文本
    tokens_generated: int = 0
    tokens_saved: int = 0  # 提前终止节省的 token 数
    duration_ms: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)


class StreamingConsensus:
    """
    Streaming 共识引擎。
    在多节点流式生成 token 的过程中，实时检测不同节点生成内容的一致性，
    一旦达到共识阈值即可提前终止生成，节省 token。
    """

    def __init__(self, config: Dict[str, Any]):
        """
        初始化 Streaming 共识引擎。

        Args:
            config: 配置参数
                - consensus_threshold: 共识阈值 (0-1)
                - window_size: 用于检测的 token 窗口大小
                - min_tokens: 最小 token 数要求
                - early_termination: 是否允许提前终止
                - tie_breaker: 平局时选择策略 ("first", "longest", "random")
        """
        self.consensus_threshold = config.get("consensus_threshold", 0.8)
        self.window_size = config.get("window_size", 5)  # 检测最近几个 token
        self.min_tokens = config.get("min_tokens", 10)
        self.early_termination = config.get("early_termination", True)
        self.tie_breaker = config.get("tie_breaker", "first")
        
        # 每个节点的稳定性窗口
        self.node_windows: Dict[str, StabilityWindow] = {}
        
        # 当前进行中的共识
        self._active_consensus: Dict[str, Dict] = {}

    def register_node(self, node_id: str, weight: float = 1.0):
        """注册参与共识的节点。"""
        window = StabilityWindow({
            "window_type": "count",
            "window_size": self.window_size,
            "stability_threshold": self.consensus_threshold,
            "min_samples": 3,
        })
        self.node_windows[node_id] = window
        logger.info(f"Registered node {node_id} for streaming consensus")

    def unregister_node(self, node_id: str):
        """注销节点。"""
        self.node_windows.pop(node_id, None)

    async def run_consensus(
        self,
        consensus_id: str,
        nodes: List[str],
        generators: Dict[str, AsyncGenerator[str, None]],
        max_tokens: int = 1000,
        timeout_ms: int = 10000,
    ) -> ConsensusResult:
        """
        运行一次 Streaming 共识。

        Args:
            consensus_id: 共识唯一标识
            nodes: 参与节点列表
            generators: 每个节点的异步生成器，产生 token 流
            max_tokens: 最大 token 数限制
            timeout_ms: 超时

        Returns:
            共识结果
        """
        start_time = time.time()
        deadline = start_time + timeout_ms / 1000.0

        # 初始化每个节点的状态
        node_tokens: Dict[str, List[str]] = {node: [] for node in nodes}
        node_finished: Set[str] = set()
        node_weights = {node: self.node_windows.get(node, 1.0) for node in nodes}
        
        # 用于同步的队列
        queues = {node: asyncio.Queue() for node in nodes}
        
        # 启动每个节点的 token 生成任务
        async def token_producer(node: str, gen: AsyncGenerator[str, None]):
            try:
                async for token in gen:
                    await queues[node].put(token)
                    # 将 token 加入节点自己的稳定性窗口
                    if node in self.node_windows:
                        self.node_windows[node].add_observation(token, weight=node_weights[node])
                # 生成结束，放入结束标记
                await queues[node].put(None)
            except Exception as e:
                logger.error(f"Node {node} generator error: {e}")
                await queues[node].put(None)
            finally:
                node_finished.add(node)

        producer_tasks = [
            asyncio.create_task(token_producer(node, generators[node]))
            for node in nodes if node in generators
        ]

        # 主循环：不断从各队列获取 token，检测共识
        collected_tokens: List[str] = []
        consensus_text = ""
        final_state = ConsensusState.SEARCHING
        tokens_generated = 0
        tokens_saved = 0

        try:
            while time.time() < deadline and tokens_generated < max_tokens:
                # 从每个未完成的节点获取一个 token
                got_any = False
                for node in nodes:
                    if node in node_finished:
                        continue
                    try:
                        # 非阻塞获取
                        token = await asyncio.wait_for(queues[node].get(), timeout=0.1)
                        got_any = True
                        if token is None:
                            node_finished.add(node)
                            continue
                        
                        node_tokens[node].append(token)
                        tokens_generated += 1
                        
                        # 检测共识
                        consensus_state = self._detect_consensus(node_tokens, nodes, node_weights)
                        
                        if consensus_state == ConsensusState.ACHIEVED:
                            # 达成共识，生成共识文本
                            consensus_text = self._build_consensus_text(node_tokens, nodes)
                            final_state = ConsensusState.ACHIEVED
                            tokens_saved = max_tokens - tokens_generated
                            logger.info(f"Consensus achieved after {tokens_generated} tokens")
                            return ConsensusResult(
                                consensus_id=consensus_id,
                                state=final_state,
                                consensus_text=consensus_text,
                                tokens_generated=tokens_generated,
                                tokens_saved=tokens_saved,
                                duration_ms=(time.time() - start_time) * 1000,
                                details={"method": "streaming"}
                            )
                        elif consensus_state == ConsensusState.FAILED:
                            # 无法达成共识
                            final_state = ConsensusState.FAILED
                            logger.warning(f"Consensus failed after {tokens_generated} tokens")
                            return ConsensusResult(
                                consensus_id=consensus_id,
                                state=final_state,
                                tokens_generated=tokens_generated,
                                duration_ms=(time.time() - start_time) * 1000,
                                details={"reason": "divergence"}
                            )
                    except asyncio.TimeoutError:
                        continue
                
                # 如果所有节点都完成，退出循环
                if len(node_finished) == len(nodes):
                    break
                
                if not got_any:
                    await asyncio.sleep(0.01)
            
            # 超时或达到最大 token 数
            if tokens_generated >= max_tokens:
                final_state = ConsensusState.FAILED
                reason = "max_tokens_exceeded"
            else:
                final_state = ConsensusState.FAILED
                reason = "timeout"
            
            # 尝试生成一个最佳猜测
            consensus_text = self._build_consensus_text(node_tokens, nodes)
            
            return ConsensusResult(
                consensus_id=consensus_id,
                state=final_state,
                consensus_text=consensus_text,
                tokens_generated=tokens_generated,
                duration_ms=(time.time() - start_time) * 1000,
                details={"reason": reason}
            )
            
        finally:
            # 取消所有生产者任务
            for task in producer_tasks:
                task.cancel()
            await asyncio.gather(*producer_tasks, return_exceptions=True)

    def _detect_consensus(
        self,
        node_tokens: Dict[str, List[str]],
        nodes: List[str],
        node_weights: Dict[str, float]
    ) -> ConsensusState:
        """
        检测当前是否达成共识。
        基于每个节点的稳定性窗口和跨节点一致性。
        """
        # 要求至少有 min_tokens 个 token
        min_len = min(len(node_tokens[node]) for node in nodes)
        if min_len < self.min_tokens:
            return ConsensusState.SEARCHING
        
        # 检查每个节点的稳定性窗口
        stable_nodes = 0
        total_weight = 0.0
        node_stable_values = {}
        
        for node in nodes:
            if node not in self.node_windows:
                continue
            window = self.node_windows[node]
            stability = window.evaluate_stability()
            if stability.is_stable:
                stable_nodes += 1
                node_stable_values[node] = stability.stable_value
                total_weight += node_weights.get(node, 1.0)
        
        # 计算稳定节点的比例（按权重）
        if total_weight == 0:
            return ConsensusState.SEARCHING
        
        # 检查稳定节点是否对最终值达成一致
        if stable_nodes >= 2:
            # 统计稳定节点预测的值
            value_counts: Dict[Any, float] = {}
            for node, val in node_stable_values.items():
                key = self._value_key(val)
                value_counts[key] = value_counts.get(key, 0) + node_weights.get(node, 1.0)
            
            # 最大权重值
            max_key, max_weight = max(value_counts.items(), key=lambda x: x[1])
            if max_weight / total_weight >= self.consensus_threshold:
                # 达成共识
                return ConsensusState.ACHIEVED
        
        # 检查是否明显分歧（比如稳定节点各持己见）
        if stable_nodes >= 2 and len(value_counts) == stable_nodes:
            # 所有稳定节点都不同，无法达成共识
            return ConsensusState.FAILED
        
        return ConsensusState.CONVERGING

    def _build_consensus_text(self, node_tokens: Dict[str, List[str]], nodes: List[str]) -> str:
        """
        根据各节点的 token 流构建共识文本。
        可采用多种策略：取最长、多数投票等。
        """
        # 简单策略：取第一个节点的完整文本
        if nodes and nodes[0] in node_tokens:
            return "".join(node_tokens[nodes[0]])
        
        # 否则取最长
        longest = max(node_tokens.values(), key=len, default=[])
        return "".join(longest)

    def _value_key(self, value: Any) -> str:
        """将值转换为可哈希键。"""
        try:
            hash(value)
            return value
        except TypeError:
            return str(value)

    def get_node_window(self, node_id: str) -> Optional[StabilityWindow]:
        """获取节点的稳定性窗口。"""
        return self.node_windows.get(node_id)