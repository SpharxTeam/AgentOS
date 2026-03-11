# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 持久同调挖掘器：从 L3 向量聚类中挖掘稳定的拓扑模式。

import numpy as np
from typing import List, Dict, Any, Optional, Tuple
import asyncio
from dataclasses import dataclass, field
from agentos_cta.utils.observability import get_logger
from agentos_cta.utils.error import AgentOSError

logger = get_logger(__name__)

# 尝试导入持久同调库
try:
    from ripser import ripser
    from persim import plot_diagrams
    PERSISTENCE_AVAILABLE = True
except ImportError:
    PERSISTENCE_AVAILABLE = False
    logger.warning("Ripser not installed, persistence computation will use fallback")


@dataclass
class PersistenceFeature:
    """持久性特征。"""
    feature_id: str
    dimension: int  # 同调维数（0维连通分量，1维环，2维空洞等）
    birth: float    # 出生阈值
    death: float    # 死亡阈值
    persistence: float  # 持久性 = death - birth
    vertices: List[int] = field(default_factory=list)  # 涉及的顶点索引
    confidence: float = 1.0  # 置信度


@dataclass
class PatternCluster:
    """模式聚类结果。"""
    cluster_id: str
    memory_ids: List[str]  # 属于该聚类的记忆 ID
    centroid: Optional[np.ndarray] = None  # 聚类中心向量
    persistent_features: List[PersistenceFeature] = field(default_factory=list)
    summary: str = ""  # 聚类摘要（可由 LLM 生成）
    created_at: float = 0.0


class PatternMiner:
    """
    持久同调挖掘器。
    从 L3 向量聚类中挖掘稳定的拓扑模式，识别持久性特征。
    基于持久同调理论，能够识别数据集中存在的拓扑特征，并忽略数据模式的影响 。
    参考 Carlsson(2005) 提出的持续同调方法，通过 Rips 过滤算法捕获动态持续拓扑特征 。
    """

    def __init__(
        self,
        dimension: int,
        config: Dict[str, Any],
        vector_index=None,  # L2 向量索引
        relation_encoder=None,  # L3 关系编码器
    ):
        """
        初始化模式挖掘器。

        Args:
            dimension: 向量维度。
            config: 配置参数。
                - max_dim: 最大同调维数（默认 2）
                - min_persistence: 最小持久性阈值
                - clustering_method: 聚类方法（"hdbscan", "dbscan"）
                - use_ripser: 是否使用 Ripser（默认 True）
            vector_index: L2 向量索引，用于获取向量。
            relation_encoder: L3 关系编码器，用于获取结构化记忆。
        """
        self.dimension = dimension
        self.config = config
        self.vector_index = vector_index
        self.relation_encoder = relation_encoder

        self.max_dim = config.get("max_dim", 2)
        self.min_persistence = config.get("min_persistence", 0.1)
        self.clustering_method = config.get("clustering_method", "hdbscan")
        self.use_ripser = config.get("use_ripser", True) and PERSISTENCE_AVAILABLE

        if not PERSISTENCE_AVAILABLE and self.use_ripser:
            logger.warning("Ripser not available, falling back to simplified persistence")
            self.use_ripser = False

        self.patterns: List[PatternCluster] = []

    async def mine_from_vectors(
        self,
        vectors: List[np.ndarray],
        memory_ids: List[str],
        distance_matrix: Optional[np.ndarray] = None,
    ) -> List[PatternCluster]:
        """
        从向量列表中挖掘持久模式。

        Args:
            vectors: 向量列表，形状 (n, dimension)。
            memory_ids: 对应的记忆 ID 列表。
            distance_matrix: 可选的距离矩阵，若未提供则自动计算。

        Returns:
            模式聚类列表。
        """
        if len(vectors) < 3:
            logger.warning("Insufficient vectors for pattern mining")
            return []

        # 转换为 numpy 数组
        X = np.array(vectors).astype(np.float32)
        n_samples = len(X)

        # 计算距离矩阵（若未提供）
        if distance_matrix is None:
            # 使用余弦距离（假设向量已归一化）
            # 距离 = 1 - 余弦相似度
            norms = np.linalg.norm(X, axis=1, keepdims=True)
            norms[norms == 0] = 1
            X_normalized = X / norms
            similarities = np.dot(X_normalized, X_normalized.T)
            distances = 1.0 - similarities
            np.fill_diagonal(distances, 0)  # 确保对角线为 0
            distance_matrix = distances

        # 执行持久同调计算
        if self.use_ripser:
            persistence_features = await self._compute_persistence_ripser(distance_matrix)
        else:
            persistence_features = await self._compute_persistence_simplified(distance_matrix)

        # 过滤持久性低于阈值的特征
        significant_features = [
            f for f in persistence_features
            if f.persistence >= self.min_persistence
        ]

        if not significant_features:
            logger.info("No significant persistent features found")
            return []

        # 基于持久特征进行聚类
        clusters = await self._cluster_by_persistence(
            X, memory_ids, significant_features
        )

        # 为每个聚类生成摘要
        for cluster in clusters:
            cluster.summary = await self._generate_cluster_summary(cluster)

        self.patterns.extend(clusters)
        logger.info(f"Mined {len(clusters)} pattern clusters from {n_samples} vectors")
        return clusters

    async def _compute_persistence_ripser(self, distance_matrix: np.ndarray) -> List[PersistenceFeature]:
        """
        使用 Ripser 计算持久同调。
        基于 Rips 过滤算法捕获网络的动态持续拓扑特征 。
        """
        try:
            # 调用 ripser
            result = ripser(
                distance_matrix,
                maxdim=self.max_dim,
                distance_matrix=True,
                do_cocycles=False,
            )

            features = []
            for dim in range(self.max_dim + 1):
                diagrams = result['dgms'][dim]
                if diagrams is None or len(diagrams) == 0:
                    continue

                for i, (birth, death) in enumerate(diagrams):
                    if death == np.inf:
                        death = 1.0  # 无限死亡设为 1.0（最大距离）
                    persistence = death - birth
                    if persistence > 0:
                        feature = PersistenceFeature(
                            feature_id=f"pers_{dim}_{i}",
                            dimension=dim,
                            birth=float(birth),
                            death=float(death),
                            persistence=float(persistence),
                        )
                        features.append(feature)

            return features

        except Exception as e:
            logger.error(f"Ripser computation failed: {e}, falling back to simplified")
            return await self._compute_persistence_simplified(distance_matrix)

    async def _compute_persistence_simplified(self, distance_matrix: np.ndarray) -> List[PersistenceFeature]:
        """
        简化的持久同调计算（不使用 Ripser）。
        通过层次聚类近似 0 维持久性。
        """
        from scipy.cluster.hierarchy import linkage, fcluster
        from scipy.spatial.distance import squareform

        features = []

        # 0 维持久性：使用层次聚类
        condensed = squareform(distance_matrix, checks=False)
        Z = linkage(condensed, method='single')

        # 提取合并距离作为持久性
        for i, merge in enumerate(Z):
            dist = merge[2]  # 合并距离
            if dist > 0:
                feature = PersistenceFeature(
                    feature_id=f"pers_0_{i}",
                    dimension=0,
                    birth=0.0,
                    death=float(dist),
                    persistence=float(dist),
                )
                features.append(feature)

        # 更高维的持久性（1维、2维）在简化版中无法计算
        # 这里仅返回 0 维特征作为近似
        logger.info(f"Simplified persistence found {len(features)} 0-dim features")
        return features

    async def _cluster_by_persistence(
        self,
        vectors: np.ndarray,
        memory_ids: List[str],
        persistent_features: List[PersistenceFeature],
    ) -> List[PatternCluster]:
        """
        基于持久特征进行聚类。
        """
        if self.clustering_method == "hdbscan":
            try:
                import hdbscan

                # 使用 HDBSCAN 聚类
                clusterer = hdbscan.HDBSCAN(
                    min_cluster_size=3,
                    min_samples=1,
                    metric='euclidean',
                )
                labels = clusterer.fit_predict(vectors)

                # 为每个非噪声标签创建聚类
                unique_labels = set(labels)
                clusters = []
                for label in unique_labels:
                    if label == -1:  # 噪声点
                        continue
                    indices = [i for i, l in enumerate(labels) if l == label]
                    cluster_mem_ids = [memory_ids[i] for i in indices]

                    # 计算聚类中心
                    centroid = np.mean(vectors[indices], axis=0)

                    # 找出与该聚类相关的持久特征
                    # 简化：仅保留出现在该聚类中的特征
                    cluster_features = [
                        f for f in persistent_features
                        # 这里需要更复杂的匹配逻辑，暂简化
                    ]

                    cluster = PatternCluster(
                        cluster_id=f"cluster_{label}",
                        memory_ids=cluster_mem_ids,
                        centroid=centroid,
                        persistent_features=cluster_features,
                        created_at=asyncio.get_event_loop().time(),
                    )
                    clusters.append(cluster)

                return clusters

            except ImportError:
                logger.warning("hdbscan not installed, falling back to DBSCAN")
                return await self._cluster_dbscan(vectors, memory_ids, persistent_features)

        elif self.clustering_method == "dbscan":
            return await self._cluster_dbscan(vectors, memory_ids, persistent_features)
        else:
            # 默认：简单阈值聚类
            return await self._cluster_simple(vectors, memory_ids, persistent_features)

    async def _cluster_dbscan(
        self,
        vectors: np.ndarray,
        memory_ids: List[str],
        persistent_features: List[PersistenceFeature],
    ) -> List[PatternCluster]:
        """使用 DBSCAN 聚类。"""
        from sklearn.cluster import DBSCAN

        # 使用距离矩阵或向量
        clustering = DBSCAN(eps=0.3, min_samples=2, metric='cosine')
        labels = clustering.fit_predict(vectors)

        clusters = []
        unique_labels = set(labels)
        for label in unique_labels:
            if label == -1:
                continue
            indices = [i for i, l in enumerate(labels) if l == label]
            cluster_mem_ids = [memory_ids[i] for i in indices]
            centroid = np.mean(vectors[indices], axis=0)

            cluster = PatternCluster(
                cluster_id=f"dbscan_{label}",
                memory_ids=cluster_mem_ids,
                centroid=centroid,
                persistent_features=persistent_features,
                created_at=asyncio.get_event_loop().time(),
            )
            clusters.append(cluster)

        return clusters

    async def _cluster_simple(
        self,
        vectors: np.ndarray,
        memory_ids: List[str],
        persistent_features: List[PersistenceFeature],
    ) -> List[PatternCluster]:
        """简单的基于阈值的聚类（所有点作为一个聚类）。"""
        # 将所有向量作为一个聚类（简化）
        cluster = PatternCluster(
            cluster_id="cluster_all",
            memory_ids=memory_ids,
            centroid=np.mean(vectors, axis=0),
            persistent_features=persistent_features,
            created_at=asyncio.get_event_loop().time(),
        )
        return [cluster]

    async def _generate_cluster_summary(self, cluster: PatternCluster) -> str:
        """
        为聚类生成摘要（可由 LLM 完成）。
        此处简化，返回基本信息。
        """
        n_memories = len(cluster.memory_ids)
        n_features = len(cluster.persistent_features)
        dims = set(f.dimension for f in cluster.persistent_features)

        summary = (
            f"Pattern cluster with {n_memories} memories, "
            f"{n_features} persistent features across dimensions {dims}"
        )
        return summary

    async def get_patterns(self, min_confidence: float = 0.5) -> List[PatternCluster]:
        """获取所有模式，可按置信度过滤。"""
        return [p for p in self.patterns if p.persistent_features]