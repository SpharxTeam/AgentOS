# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 相似度计算器：支持多种距离度量，并与遗忘曲线结合。

import numpy as np
from typing import List, Tuple, Optional, Union
from agentos_cta.utils.observability import get_logger

logger = get_logger(__name__)


class SimilarityCalculator:
    """
    相似度计算器。
    提供多种距离度量，支持遗忘曲线权重调整和混合检索。
    """

    METRICS = ["cosine", "l2", "ip"]  # 余弦、欧氏、内积

    def __init__(self, metric: str = "cosine", config: Optional[dict] = None):
        """
        初始化相似度计算器。

        Args:
            metric: 距离度量。
            config: 配置参数，如遗忘曲线强度、混合检索权重等。
        """
        if metric not in self.METRICS:
            raise ValueError(f"Unsupported metric: {metric}")

        self.metric = metric
        self.config = config or {}
        self.forgetting_lambda = self.config.get("forgetting_lambda", 0.01)  # 遗忘曲线参数
        self.vector_weight = self.config.get("vector_weight", 0.7)  # 向量检索权重
        self.bm25_weight = self.config.get("bm25_weight", 0.3)  # BM25 权重（混合检索用）

    def compute_distance(
        self,
        vec1: np.ndarray,
        vec2: np.ndarray,
        normalized: bool = True
    ) -> float:
        """
        计算两个向量之间的距离。

        Args:
            vec1: 向量1。
            vec2: 向量2。
            normalized: 是否已归一化。

        Returns:
            距离值（越小越相似）。
        """
        if self.metric == "cosine":
            # 余弦距离 = 1 - 余弦相似度
            if normalized:
                # 归一化后，内积即为余弦相似度
                sim = np.dot(vec1, vec2)
            else:
                norm1 = np.linalg.norm(vec1)
                norm2 = np.linalg.norm(vec2)
                if norm1 == 0 or norm2 == 0:
                    return 1.0
                sim = np.dot(vec1, vec2) / (norm1 * norm2)
            return 1.0 - sim

        elif self.metric == "l2":
            # 欧氏距离
            return float(np.linalg.norm(vec1 - vec2))

        elif self.metric == "ip":
            # 内积（越大越相似，但这里统一为距离形式）
            # 对于归一化向量，内积 = 余弦相似度
            return -float(np.dot(vec1, vec2))  # 取负使越小越相似

        else:
            raise ValueError(f"Metric {self.metric} not implemented")

    def compute_similarity(
        self,
        vec1: np.ndarray,
        vec2: np.ndarray,
        normalized: bool = True
    ) -> float:
        """
        计算相似度（0-1 之间，越大越相似）。
        """
        dist = self.compute_distance(vec1, vec2, normalized)

        if self.metric == "l2":
            # 欧氏距离转相似度：exp(-dist) 或其他映射
            return float(np.exp(-dist))
        elif self.metric in ["cosine", "ip"]:
            # 余弦距离 = 1 - sim，所以 sim = 1 - dist
            return max(0.0, min(1.0, 1.0 - dist))
        else:
            return max(0.0, min(1.0, 1.0 - dist))

    def apply_forgetting_curve(self, similarity: float, last_access_time: float, current_time: float) -> float:
        """
        应用艾宾浩斯遗忘曲线调整相似度。

        Args:
            similarity: 原始相似度。
            last_access_time: 上次访问时间（Unix 时间戳）。
            current_time: 当前时间。

        Returns:
            调整后的相似度。
        """
        time_diff_hours = (current_time - last_access_time) / 3600.0
        # 遗忘曲线公式：R = e^(-λt)
        decay = np.exp(-self.forgetting_lambda * time_diff_hours)
        # 相似度与遗忘因子结合
        adjusted = similarity * decay
        return float(adjusted)

    def hybrid_score(
        self,
        vector_score: float,
        bm25_score: float,
        vector_weight: Optional[float] = None,
        bm25_weight: Optional[float] = None
    ) -> float:
        """
        混合检索分数计算。

        Args:
            vector_score: 向量检索得分（0-1，越大越好）。
            bm25_score: BM25 检索得分（通常为原始 BM25 分数，需归一化）。
            vector_weight: 向量权重（覆盖默认）。
            bm25_weight: BM25 权重（覆盖默认）。

        Returns:
            混合得分。
        """
        vw = vector_weight if vector_weight is not None else self.vector_weight
        bw = bm25_weight if bm25_weight is not None else self.bm25_weight

        # BM25 分数归一化（假设 BM25 原始分数无界，用 sigmoid 归一化到 [0,1]）
        normalized_bm25 = 1.0 / (1.0 + np.exp(-bm25_score / 10.0))

        return vw * vector_score + bw * normalized_bm25

    def batch_compute_distances(
        self,
        query: np.ndarray,
        vectors: List[np.ndarray],
        normalized: bool = True
    ) -> List[float]:
        """
        批量计算查询向量与多个向量之间的距离。

        Args:
            query: 查询向量。
            vectors: 向量列表。
            normalized: 是否已归一化。

        Returns:
            距离列表。
        """
        if not vectors:
            return []

        # 向量化计算
        if self.metric == "l2":
            # 欧氏距离的平方
            diffs = vectors - query
            sq_dists = np.sum(diffs * diffs, axis=1)
            return list(np.sqrt(sq_dists))

        elif self.metric in ["cosine", "ip"]:
            if normalized:
                # 内积
                dots = np.dot(vectors, query)
                if self.metric == "cosine":
                    return [1.0 - d for d in dots]
                else:  # ip
                    return list(-dots)
            else:
                # 未归一化需先计算范数
                query_norm = np.linalg.norm(query)
                vector_norms = np.linalg.norm(vectors, axis=1)
                dots = np.dot(vectors, query)
                sims = dots / (vector_norms * query_norm)
                if self.metric == "cosine":
                    return [1.0 - s for s in sims]
                else:
                    return list(-sims)
        else:
            # 逐个计算
            return [self.compute_distance(query, v, normalized) for v in vectors]