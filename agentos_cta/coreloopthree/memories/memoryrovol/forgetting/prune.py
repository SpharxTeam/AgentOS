# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 记忆裁剪：低频记忆归档或删除。

from typing import List, Dict, Any, Optional
import asyncio
import time
from agentos_cta.utils.structured_logger import get_logger
from agentos_cta.utils.file_utils import FileUtils

logger = get_logger(__name__)


class Pruner:
    """
    记忆裁剪器。
    根据遗忘阈值、访问频率等条件，对低频记忆进行归档或删除。
    """

    def __init__(
        self,
        metadata_manager,
        raw_storage,
        vector_index,
        attractor_network,
        config: Dict[str, Any],
    ):
        """
        初始化记忆裁剪器。

        Args:
            metadata_manager: 元数据管理器。
            raw_storage: 原始存储。
            vector_index: 向量索引。
            attractor_network: 吸引子网络。
            config: 配置参数。
                - prune_interval: 裁剪间隔（秒）
                - access_threshold: 访问次数阈值
                - decay_threshold: 衰减阈值
                - archive_enabled: 是否启用归档（而非删除）
                - archive_dir: 归档目录
        """
        self.metadata = metadata_manager
        self.raw_storage = raw_storage
        self.vector_index = vector_index
        self.attractor = attractor_network
        self.config = config
        self.prune_interval = config.get("prune_interval", 86400)  # 默认1天
        self.access_threshold = config.get("access_threshold", 2)  # 访问次数少于2次
        self.decay_threshold = config.get("decay_threshold", 0.1)  # 衰减因子小于0.1
        self.archive_enabled = config.get("archive_enabled", True)
        self.archive_dir = config.get("archive_dir", "data/archive")
        self._last_prune_time = 0

        if self.archive_enabled:
            FileUtils.ensure_dir(self.archive_dir)

    async def should_prune(self, memory_id: str, current_time: float) -> bool:
        """
        判断记忆是否应被裁剪。
        """
        meta = await self.metadata.get(memory_id)
        if not meta:
            return False

        # 访问次数低于阈值
        if meta.access_count < self.access_threshold:
            return True

        # 计算衰减因子
        from .decay import DecayFunction
        decay_func = DecayFunction(self.config)
        factor = decay_func.compute_decay_factor(meta.last_access or meta.timestamp, current_time)
        if factor < self.decay_threshold:
            return True

        return False

    async def prune_once(self, force: bool = False) -> int:
        """
        执行一次裁剪操作。
        """
        current_time = time.time()
        if not force and current_time - self._last_prune_time < self.prune_interval:
            logger.debug("Prune interval not reached, skipping")
            return 0

        # 获取所有记忆 ID（需要从元数据管理器获取）
        # 这里简化：假设 metadata 有一个 get_all_ids 方法
        if not hasattr(self.metadata, 'get_all_ids'):
            logger.warning("Metadata manager does not support get_all_ids, cannot prune")
            return 0

        all_ids = await self.metadata.get_all_ids()
        prune_candidates = []
        for mem_id in all_ids:
            if await self.should_prune(mem_id, current_time):
                prune_candidates.append(mem_id)

        if not prune_candidates:
            logger.info("No memories to prune")
            return 0

        logger.info(f"Pruning {len(prune_candidates)} memories")

        if self.archive_enabled:
            # 归档
            archived = await self._archive(prune_candidates)
            logger.info(f"Archived {archived} memories")
        else:
            # 直接删除
            removed = await self._delete(prune_candidates)
            logger.info(f"Deleted {removed} memories")

        self._last_prune_time = current_time
        return len(prune_candidates)

    async def _archive(self, memory_ids: List[str]) -> int:
        """
        将记忆移动到归档存储。
        """
        archived_count = 0
        for mem_id in memory_ids:
            try:
                # 读取原始数据
                meta = await self.metadata.get(mem_id)
                if not meta:
                    continue
                location = f"{mem_id}.bin:{meta.offset}"  # 简化
                data = await self.raw_storage.read(location)
                if data:
                    # 写入归档目录
                    archive_path = f"{self.archive_dir}/{mem_id}.bin"
                    FileUtils.safe_write(archive_path, data)
                    archived_count += 1

                # 从各模块移除
                await self.vector_index.remove([mem_id])
                await self.attractor.remove([mem_id])
                # 从元数据删除或标记
                # await self.metadata.delete(mem_id)  # 假设有删除方法

            except Exception as e:
                logger.error(f"Failed to archive memory {mem_id}: {e}")

        return archived_count

    async def _delete(self, memory_ids: List[str]) -> int:
        """
        永久删除记忆。
        """
        removed = 0
        for mem_id in memory_ids:
            try:
                await self.vector_index.remove([mem_id])
                await self.attractor.remove([mem_id])
                # 从元数据删除
                # await self.metadata.delete(mem_id)
                removed += 1
            except Exception as e:
                logger.error(f"Failed to delete memory {mem_id}: {e}")
        return removed