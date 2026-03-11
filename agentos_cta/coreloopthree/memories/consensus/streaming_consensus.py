# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# Streaming 共识机制：在 Token 流中持续检测共识状态，满足条件立即终止生成。
# 基于 arXiv:2512.20184 "Agentic Consensus" 中的 Streaming Consensus 设计。

import asyncio
import time
from typing import AsyncGenerator, Any, Optional, Dict
from dataclasses import dataclass
from agentos_cta.utils.structured_logger import get_logger
from agentos_cta.utils.error_types import ConsensusError

logger = get_logger(__name__)


@dataclass
class StreamingConsensusResult:
    """Streaming 共识结果。"""
    final_output: str
    consensus_reached_at: float  # 达成共识的时间点
    token_count: int  # 消耗的 token 数
    early_stopped: bool  # 是否提前终止


class StreamingConsensus:
    """
    Streaming 共识器。
    在多 Agent 流式生成过程中持续检测共识状态，一旦满足条件立即终止生成。
    极大节省 Token 消耗（论文中显示可节省 1.1-4.4 倍）。
    """

    def __init__(self, config: Dict[str, Any]):
        """
        初始化 Streaming 共识器。

        Args:
            config: 配置参数
                - similarity_threshold: 相似度阈值（默认 0.85）
                - window_size: 滑动窗口大小（默认 3）
                - min_tokens: 最小 token 数（避免过早停止，默认 10）
        """
        self.similarity_threshold = config.get("similarity_threshold", 0.85)
        self.window_size = config.get("window_size", 3)
        self.min_tokens = config.get("min_tokens", 10)

    async def run(
        self,
        generators: Dict[str, AsyncGenerator[str, None]],
        similarity_func: Optional[callable] = None
    ) -> StreamingConsensusResult:
        """
        运行 Streaming 共识。

        Args:
            generators: Agent ID 到异步生成器的映射。每个生成器逐步产生 token。
            similarity_func: 比较两个生成器当前输出的相似度函数。
                            输入为两个字符串，返回 [0,1] 相似度。
                            若不提供，则使用简单的字符串匹配。

        Returns:
            StreamingConsensusResult 对象。
        """
        start_time = time.time()
        # 初始化每个 Agent 的已收集输出
        outputs = {aid: "" for aid in generators}
        # 滑动窗口，存储最近各 Agent 的完整输出（用于相似度比较）
        window = []
        token_count = 0

        # 默认相似度函数（简单编辑距离，这里简化）
        if similarity_func is None:
            def similarity_func(a: str, b: str) -> float:
                if not a or not b:
                    return 0.0
                # 使用最长公共子序列比例，简化
                min_len = min(len(a), len(b))
                if min_len == 0:
                    return 0.0
                matches = sum(1 for i in range(min_len) if a[i] == b[i])
                return matches / min_len

        # 主循环
        try:
            while True:
                # 从每个生成器收集下一个 token
                tasks = []
                for aid, gen in generators.items():
                    tasks.append(asyncio.create_task(self._anext(gen, aid)))
                done, pending = await asyncio.wait(tasks, return_when=asyncio.ALL_COMPLETED)
                # 处理结果
                any_finished = False
                for task in done:
                    try:
                        aid, token = task.result()
                        if token is None:
                            # 该生成器已结束
                            any_finished = True
                            continue
                        outputs[aid] += token
                        token_count += 1
                    except Exception as e:
                        logger.error(f"Streaming error for {aid}: {e}")
                        any_finished = True

                # 检查是否所有生成器都已结束
                all_finished = all(gen.aclosed for gen in generators.values())  # 简化
                if all_finished:
                    break

                # 每收集到一定数量的 token 后检查共识
                if token_count % self.window_size == 0 and token_count >= self.min_tokens:
                    # 计算所有 Agent 当前输出两两之间的相似度
                    agents_list = list(outputs.keys())
                    similarities = []
                    for i in range(len(agents_list)):
                        for j in range(i+1, len(agents_list)):
                            a, b = agents_list[i], agents_list[j]
                            sim = similarity_func(outputs[a], outputs[b])
                            similarities.append(sim)
                    # 平均相似度
                    if similarities:
                        avg_sim = sum(similarities) / len(similarities)
                    else:
                        avg_sim = 1.0  # 只有一个 Agent 时

                    window.append(avg_sim)
                    if len(window) > self.window_size:
                        window.pop(0)

                    # 判断是否达到共识：最近窗口的平均相似度持续高于阈值
                    if len(window) == self.window_size and all(s >= self.similarity_threshold for s in window):
                        logger.info(f"Streaming consensus reached at token {token_count} with avg sim {avg_sim:.2f}")
                        # 选择任一 Agent 的当前输出作为最终结果（假设已收敛）
                        final_output = outputs[agents_list[0]]
                        # 终止所有生成器
                        for gen in generators.values():
                            await gen.aclose()
                        return StreamingConsensusResult(
                            final_output=final_output,
                            consensus_reached_at=time.time(),
                            token_count=token_count,
                            early_stopped=True
                        )
        except asyncio.CancelledError:
            # 清理
            for gen in generators.values():
                await gen.aclose()
            raise

        # 自然结束
        final_output = max(outputs.values(), key=len)  # 取最长输出
        return StreamingConsensusResult(
            final_output=final_output,
            consensus_reached_at=time.time(),
            token_count=token_count,
            early_stopped=False
        )

    async def _anext(self, gen: AsyncGenerator[str, None], aid: str):
        """安全地从异步生成器获取下一个 token。"""
        try:
            token = await gen.__anext__()
            return aid, token
        except StopAsyncIteration:
            return aid, None
        except Exception as e:
            raise e