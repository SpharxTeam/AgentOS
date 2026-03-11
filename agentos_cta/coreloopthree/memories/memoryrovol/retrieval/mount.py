# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 挂载算子：将检索到的原始记忆注入工作记忆，适配上下文窗口约束。

from typing import List, Dict, Any, Optional, Tuple
import asyncio
from agentos_cta.utils.structured_logger import get_logger
from agentos_cta.utils.token_counter import TokenCounter
from agentos_cta.utils.error_types import ResourceLimitError

logger = get_logger(__name__)


class Mounter:
    """
    挂载算子。
    负责将检索到的原始记忆从 L1 加载，并根据工作记忆约束进行选择、压缩和注入。
    """

    def __init__(
        self,
        raw_storage,
        metadata_manager,
        summarizer=None,
        config: Dict[str, Any] = None,
    ):
        """
        初始化挂载算子。

        Args:
            raw_storage: L1 原始存储实例。
            metadata_manager: 元数据管理器。
            summarizer: L2 摘要生成器（可选）。
            config: 配置参数。
                - token_budget: 默认 Token 预算
                - max_memories_per_mount: 每次最多挂载的记忆数
                - mount_strategy: 挂载策略 ("greedy", "weighted", "diversity")
        """
        self.raw_storage = raw_storage
        self.metadata = metadata_manager
        self.summarizer = summarizer
        self.config = config or {}
        self.token_budget = self.config.get("token_budget", 4096)
        self.max_memories = self.config.get("max_memories_per_mount", 5)
        self.mount_strategy = self.config.get("mount_strategy", "greedy")
        self.token_counter = TokenCounter()

    async def mount(
        self,
        memory_ids: List[str],
        query: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        token_budget: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        将指定记忆挂载到工作记忆。

        Args:
            memory_ids: 要挂载的记忆 ID 列表。
            query: 原始查询（用于相关性排序）。
            context: 当前上下文（用于策略决策）。
            token_budget: 本次挂载的 Token 预算（覆盖默认）。

        Returns:
            挂载后的记忆列表，每个元素包含原始内容、元数据和挂载信息。
        """
        budget = token_budget if token_budget is not None else self.token_budget
        mounted = []
        total_tokens = 0

        # 根据策略选择记忆顺序
        ordered_ids = await self._select_memories(memory_ids, query, context)

        for mem_id in ordered_ids:
            if len(mounted) >= self.max_memories:
                break

            # 获取元数据
            meta = await self.metadata.get(mem_id)
            if not meta:
                continue

            # 读取原始数据
            location = f"{meta.memory_id}.bin:{meta.offset}"  # 需要实际格式
            raw_data = await self.raw_storage.read(location)
            if not raw_data:
                continue

            # 解码为文本（假设是文本记忆）
            try:
                content = raw_data.decode('utf-8')
            except UnicodeDecodeError:
                content = str(raw_data)

            # 估算 token 数
            tokens = self.token_counter.count_tokens(content)

            # 如果超出预算，尝试摘要
            if total_tokens + tokens > budget:
                if self.summarizer and tokens > 100:
                    # 尝试摘要
                    summary = await self.summarizer.summarize(content, max_tokens=budget - total_tokens)
                    if summary:
                        summary_tokens = self.token_counter.count_tokens(summary)
                        if total_tokens + summary_tokens <= budget:
                            mounted.append({
                                "memory_id": mem_id,
                                "content": summary,
                                "metadata": meta,
                                "truncated": True,
                                "original_tokens": tokens,
                                "final_tokens": summary_tokens,
                            })
                            total_tokens += summary_tokens
                        # 即使放不下也跳过
                # 放不下则跳过
                continue

            # 正常挂载
            mounted.append({
                "memory_id": mem_id,
                "content": content,
                "metadata": meta,
                "truncated": False,
                "tokens": tokens,
            })
            total_tokens += tokens

            # 更新访问计数
            await self.metadata.update_access(mem_id)

        logger.info(f"Mounted {len(mounted)} memories, total tokens: {total_tokens}")
        return mounted

    async def _select_memories(
        self,
        memory_ids: List[str],
        query: Optional[str],
        context: Optional[Dict[str, Any]],
    ) -> List[str]:
        """
        根据策略选择挂载顺序。
        """
        if self.mount_strategy == "greedy":
            # 按检索分数排序（假设 memory_ids 已按分数降序）
            return memory_ids

        elif self.mount_strategy == "weighted":
            # 按元数据权重排序（如最近访问、重要性等）
            scored = []
            for mem_id in memory_ids:
                meta = await self.metadata.get(mem_id)
                if meta:
                    # 权重 = 1/(当前时间-最后访问+1) * 访问次数
                    import time
                    now = time.time()
                    recency = 1.0 / (now - meta.last_access + 1) if meta.last_access else 0
                    score = recency * (meta.access_count + 1)
                    scored.append((score, mem_id))
            scored.sort(reverse=True)
            return [mem_id for _, mem_id in scored]

        elif self.mount_strategy == "diversity":
            # 简单的多样性选择：取前几个，但跳过语义相似的
            # 这里简化：直接取前 self.max_memories 个
            return memory_ids[: self.max_memories]

        else:
            return memory_ids

    async def mount_best(
        self,
        candidates: List[Tuple[str, float]],
        query: str,
        token_budget: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        从带分数的候选中选择并挂载最佳记忆。
        """
        # 按分数降序
        sorted_candidates = sorted(candidates, key=lambda x: x[1], reverse=True)
        mem_ids = [mem_id for mem_id, _ in sorted_candidates]
        return await self.mount(mem_ids, query, token_budget=token_budget)