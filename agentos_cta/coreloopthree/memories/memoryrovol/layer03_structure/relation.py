# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 关系编码器：将事件-属性对、时序关系等编码为结构化向量。

from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from agentos_cta.utils.observability import get_logger
from .binder import Binder
from .unbinder import Unbinder

logger = get_logger(__name__)


class RelationEncoder:
    """
    关系编码器。
    将结构化关系（如事件-属性对、时序关系）编码为绑定后的向量。
    支持关系组合和查询。
    """

    def __init__(self, binder: Binder):
        """
        初始化关系编码器。

        Args:
            binder: Binder 实例，用于执行绑定操作。
        """
        self.binder = binder
        self.unbinder = Unbinder(binder)

    def encode_triple(self, subject: np.ndarray, predicate: np.ndarray, object: np.ndarray) -> np.ndarray:
        """
        编码三元组 (subject, predicate, object)。

        典型绑定方式：relation = bind(subject, predicate, object)
        或者使用 role-filler 绑定：role ⊗ filler
        """
        # 采用角色-填充者绑定：relation = bind(subject, predicate, object)
        return self.binder.bind([subject, predicate, object])

    def encode_event(self, event_attributes: Dict[str, np.ndarray]) -> np.ndarray:
        """
        编码事件，其中包含多个属性（如 time, location, agent, action 等）。

        Args:
            event_attributes: 属性名到属性向量的映射。

        Returns:
            事件的整体表示。
        """
        # 对每个属性进行角色-填充者绑定，然后叠加
        # 角色向量可以预定义（例如 "time_role", "location_role" 等）
        # 这里假设传入的已经是角色向量？不，我们需定义角色向量。
        # 简化：属性名哈希成随机向量作为角色
        role_vectors = self._generate_role_vectors(list(event_attributes.keys()))

        bound_pairs = []
        for attr_name, attr_vec in event_attributes.items():
            role_vec = role_vectors[attr_name]
            # 绑定角色和填充值
            bound = self.binder.bind([role_vec, attr_vec])
            bound_pairs.append(bound)

        # 叠加所有绑定的角色-填充者对（无序叠加）
        # 注意：叠加操作不是绑定，而是求和（需归一化）
        if not bound_pairs:
            return np.zeros(self.binder.dimension)

        result = np.sum(bound_pairs, axis=0)
        # 可选归一化
        norm = np.linalg.norm(result)
        if norm > 0:
            result = result / norm
        return result

    def _generate_role_vectors(self, role_names: List[str]) -> Dict[str, np.ndarray]:
        """为角色名生成固定的随机向量。"""
        # 简单哈希：使用随机种子保证一致性
        np.random.seed(42)  # 固定种子
        role_vectors = {}
        for name in role_names:
            # 生成随机单位向量
            vec = np.random.randn(self.binder.dimension)
            vec = vec / np.linalg.norm(vec)
            role_vectors[name] = vec
        return role_vectors

    def query_by_role(self, event_vector: np.ndarray, role_name: str, role_vectors: Dict[str, np.ndarray]) -> Optional[np.ndarray]:
        """
        从事件向量中查询指定角色的填充值（近似解绑）。
        需要已知事件向量和角色向量，使用解绑算子。
        """
        role_vec = role_vectors.get(role_name)
        if role_vec is None:
            return None

        # 假设事件向量是多个角色-填充者绑定的叠加
        # 解绑需要迭代，这里简化：尝试用 unbinder 解绑，但需要知道顺序，不好做
        # 实际应用中，可能需要训练一个网络或使用谐振器网络
        # 我们这里返回 None，表示需要更高级的解码
        logger.warning("Query by role not fully implemented, returning None")
        return None

    def encode_sequence(self, items: List[np.ndarray], temporal_weights: Optional[List[float]] = None) -> np.ndarray:
        """
        编码时序序列，使用位置编码或时序绑定。
        """
        # 一种简单方法：使用位置角色绑定
        # 生成位置向量
        n = len(items)
        if temporal_weights is None:
            temporal_weights = [1.0] * n

        # 对每个位置，绑定位置向量和项向量，然后加权叠加
        pos_vectors = self._generate_position_vectors(n)
        bound_items = []
        for i, item in enumerate(items):
            pos_vec = pos_vectors[i]
            bound = self.binder.bind([pos_vec, item])
            bound_items.append(bound * temporal_weights[i])

        result = np.sum(bound_items, axis=0)
        norm = np.linalg.norm(result)
        if norm > 0:
            result = result / norm
        return result

    def _generate_position_vectors(self, n: int) -> List[np.ndarray]:
        """生成 n 个位置向量（随机正交）。"""
        np.random.seed(43)  # 不同种子避免与角色冲突
        vectors = []
        for i in range(n):
            vec = np.random.randn(self.binder.dimension)
            vec = vec / np.linalg.norm(vec)
            vectors.append(vec)
        return vectors