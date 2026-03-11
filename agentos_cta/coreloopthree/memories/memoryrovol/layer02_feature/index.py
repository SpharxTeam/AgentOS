# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 向量索引：支持 HNSW、IVF-Flat 等多种索引类型，实现近似最近邻搜索。

import os
import pickle
import tempfile
from typing import List, Optional, Dict, Any, Tuple
import numpy as np
import asyncio
from pathlib import Path
from agentos_cta.utils.observability import get_logger
from agentos_cta.utils.error import AgentOSError

logger = get_logger(__name__)

# 尝试导入 FAISS
try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    logger.warning("FAISS not installed, vector index will use fallback implementation")


class VectorIndex:
    """
    向量索引管理器。
    封装 FAISS 实现高性能 ANN 搜索，支持多种索引类型。
    参考 Aeon 的 Atlas 空间索引设计和 FAISS 最佳实践 [citation:1][citation:3][citation:7]。
    """

    INDEX_TYPES = {
        "flat": {"description": "精确检索，适合小规模数据", "type": "exact"},
        "ivf": {"description": "倒排文件索引，适合大规模数据", "type": "approximate"},
        "hnsw": {"description": "分层可导航小世界图，高召回率", "type": "approximate"},
    }

    def __init__(
        self,
        dimension: int,
        index_type: str = "hnsw",
        metric: str = "cosine",  # cosine, l2, ip (内积)
        config: Optional[Dict[str, Any]] = None,
        persist_path: Optional[str] = None,
    ):
        """
        初始化向量索引。

        Args:
            dimension: 向量维度。
            index_type: 索引类型 ("flat", "ivf", "hnsw")。
            metric: 距离度量。
            config: 索引特定参数。
            persist_path: 索引持久化路径。
        """
        if not FAISS_AVAILABLE:
            raise AgentOSError("FAISS is required for VectorIndex")

        if index_type not in self.INDEX_TYPES:
            raise AgentOSError(f"Unsupported index type: {index_type}")

        self.dimension = dimension
        self.index_type = index_type
        self.metric = metric
        self.config = config or {}
        self.persist_path = persist_path
        self.index = None
        self.vectors = []  # 存储原始向量（用于 IVF 训练等）
        self.ids = []      # 对应的记忆 ID 列表

        # 初始化索引
        self._build_index()

    def _get_faiss_metric(self) -> int:
        """获取 FAISS 对应的度量类型。"""
        if self.metric == "l2":
            return faiss.METRIC_L2
        elif self.metric == "ip":
            return faiss.METRIC_INNER_PRODUCT
        elif self.metric == "cosine":
            # 对于余弦相似度，需要对向量进行 L2 归一化，然后使用内积
            # 调用方需确保向量已归一化
            return faiss.METRIC_INNER_PRODUCT
        else:
            raise AgentOSError(f"Unsupported metric: {self.metric}")

    def _build_index(self):
        """根据配置构建索引。"""
        metric = self._get_faiss_metric()

        if self.index_type == "flat":
            # 精确索引
            self.index = faiss.IndexFlat(self.dimension, metric)
            logger.info(f"Built flat index (dim={self.dimension}, metric={self.metric})")

        elif self.index_type == "ivf":
            # IVF 索引
            nlist = self.config.get("nlist", 100)  # 聚类中心数量
            quantizer = faiss.IndexFlatL2(self.dimension)  # IVF 使用 L2 量化
            self.index = faiss.IndexIVFFlat(quantizer, self.dimension, nlist, metric)
            logger.info(f"Built IVF index with nlist={nlist}")

        elif self.index_type == "hnsw":
            # HNSW 索引
            m = self.config.get("m", 16)  # 每个节点的连接数
            ef_construction = self.config.get("ef_construction", 40)  # 构建时的搜索深度
            self.index = faiss.IndexHNSWFlat(self.dimension, m, metric)
            self.index.hnsw.efConstruction = ef_construction
            logger.info(f"Built HNSW index with m={m}, ef_construction={ef_construction}")

        # 如果存在持久化文件，尝试加载
        if self.persist_path and os.path.exists(self.persist_path):
            self.load()

    async def train(self, vectors: Optional[np.ndarray] = None) -> bool:
        """
        训练索引（对 IVF 等需要聚类的索引类型）。

        Args:
            vectors: 训练向量数组，形状 (n, dimension)。若不提供则使用已添加的向量。

        Returns:
            是否训练成功。
        """
        if self.index_type == "flat":
            # 扁平索引无需训练
            return True

        if vectors is None:
            if len(self.vectors) == 0:
                logger.error("No vectors available for training")
                return False
            vectors = np.array(self.vectors).astype('float32')

        if not self.index.is_trained:
            await asyncio.to_thread(self.index.train, vectors)
            logger.info(f"Index trained with {len(vectors)} vectors")
        return True

    async def add(self, ids: List[str], vectors: List[np.ndarray]):
        """
        添加向量到索引。

        Args:
            ids: 记忆 ID 列表。
            vectors: 向量列表。
        """
        if len(ids) != len(vectors):
            raise AgentOSError("ids and vectors must have same length")

        vec_array = np.array(vectors).astype('float32')
        start_idx = len(self.ids)

        if not self.index.is_trained and self.index_type != "flat":
            # 未训练，先存储向量用于后续训练
            self.vectors.extend(vec_array)
            self.ids.extend(ids)
            logger.info(f"Stored {len(vectors)} vectors for later training")
            return

        # 添加到索引
        await asyncio.to_thread(self.index.add, vec_array)
        self.ids.extend(ids)
        logger.info(f"Added {len(vectors)} vectors to index, total: {len(self.ids)}")

    async def search(
        self,
        query: np.ndarray,
        k: int = 10,
        probes: Optional[int] = None,
        threshold: Optional[float] = None,
    ) -> List[Tuple[str, float]]:
        """
        搜索最近邻。

        Args:
            query: 查询向量。
            k: 返回的最大结果数。
            probes: 搜索的聚类数（仅 IVF 有效）。
            threshold: 距离阈值，仅返回距离小于阈值的向量。

        Returns:
            (id, distance) 列表。
        """
        if len(self.ids) == 0:
            return []

        query = np.array([query]).astype('float32')

        # 设置 IVF 搜索参数
        if self.index_type == "ivf" and probes is not None:
            self.index.nprobe = probes

        # 执行搜索
        distances, indices = await asyncio.to_thread(self.index.search, query, k)

        results = []
        for i, idx in enumerate(indices[0]):
            if idx < 0 or idx >= len(self.ids):
                continue
            dist = distances[0][i]
            if threshold is None or dist < threshold:
                results.append((self.ids[idx], float(dist)))

        return results

    async def remove(self, ids: List[str]) -> int:
        """
        移除向量（需要重新构建索引，因为 FAISS 不支持直接删除）。

        Args:
            ids: 要移除的记忆 ID 列表。

        Returns:
            实际移除的数量。
        """
        remove_set = set(ids)
        keep_indices = [i for i, _id in enumerate(self.ids) if _id not in remove_set]
        keep_ids = [self.ids[i] for i in keep_indices]

        # 如果有向量存储用于训练，也需要更新
        if self.vectors:
            keep_vectors = [self.vectors[i] for i in keep_indices if i < len(self.vectors)]
            self.vectors = keep_vectors

        # 重建索引
        if keep_indices:
            # 重新添加剩余向量
            self.ids = keep_ids
            self._build_index()  # 重建空索引
            if keep_vectors:
                await self.add(keep_ids, [self.vectors[i] for i in range(len(keep_ids))])
            logger.info(f"Rebuilt index after removing {len(ids)} items")
        else:
            self.ids = []
            self.vectors = []
            self._build_index()

        return len(ids) - len(keep_indices)

    def save(self, path: Optional[str] = None):
        """保存索引到文件。"""
        save_path = path or self.persist_path
        if not save_path:
            raise AgentOSError("No save path specified")

        # 保存 FAISS 索引
        faiss.write_index(self.index, save_path)

        # 保存 ID 映射
        meta_path = save_path + ".meta"
        with open(meta_path, 'wb') as f:
            pickle.dump({
                'ids': self.ids,
                'vectors': self.vectors if self.vectors else None,
                'index_type': self.index_type,
                'dimension': self.dimension,
                'metric': self.metric,
                'config': self.config,
            }, f)

        logger.info(f"Index saved to {save_path}")

    def load(self, path: Optional[str] = None):
        """从文件加载索引。"""
        load_path = path or self.persist_path
        if not load_path or not os.path.exists(load_path):
            raise AgentOSError(f"Index file not found: {load_path}")

        # 加载 FAISS 索引
        self.index = faiss.read_index(load_path)

        # 加载元数据
        meta_path = load_path + ".meta"
        if os.path.exists(meta_path):
            with open(meta_path, 'rb') as f:
                meta = pickle.load(f)
                self.ids = meta.get('ids', [])
                self.vectors = meta.get('vectors', [])
                # 验证配置一致性
                if meta.get('dimension') != self.dimension:
                    logger.warning(f"Dimension mismatch: loaded {meta.get('dimension')}, expected {self.dimension}")

        logger.info(f"Index loaded from {load_path}, {len(self.ids)} vectors")