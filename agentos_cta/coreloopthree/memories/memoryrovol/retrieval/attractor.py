# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 吸引子网络：基于 Hopfield 网络的记忆检索。

import numpy as np
from typing import List, Optional, Tuple, Dict, Any
import asyncio
from agentos_cta.utils.observability import get_logger
from agentos_cta.utils.error import AgentOSError

logger = get_logger(__name__)


class AttractorNetwork:
    """
    吸引子网络。
    基于 Hopfield 网络实现联想记忆检索。
    支持连续状态和离散状态，引入自相互作用（autapses）以增强高负载稳定性。
    """

    def __init__(
        self,
        dimension: int,
        config: Dict[str, Any],
        similarity_calculator=None,
    ):
        """
        初始化吸引子网络。

        Args:
            dimension: 状态向量维度。
            config: 配置参数。
                - update_rule: 更新规则 ("async", "sync")
                - max_iterations: 最大迭代次数
                - convergence_threshold: 收敛阈值
                - use_autapse: 是否使用自相互作用
                - autapse_strength: 自相互作用强度
            similarity_calculator: 相似度计算器。
        """
        self.dimension = dimension
        self.config = config
        self.similarity = similarity_calculator

        self.update_rule = config.get("update_rule", "async")
        self.max_iterations = config.get("max_iterations", 100)
        self.convergence_threshold = config.get("convergence_threshold", 1e-4)
        self.use_autapse = config.get("use_autapse", True)
        self.autapse_strength = config.get("autapse_strength", 1.0)

        # 存储的记忆模式矩阵
        self.memory_vectors: List[np.ndarray] = []  # 存储的模式列表
        self.memory_ids: List[str] = []  # 对应的记忆 ID
        self.weight_matrix: Optional[np.ndarray] = None  # 权重矩阵

    async def store(self, vectors: List[np.ndarray], ids: List[str]) -> bool:
        """
        存储新的记忆模式。

        Args:
            vectors: 向量列表。
            ids: 对应的记忆 ID。

        Returns:
            是否成功。
        """
        if len(vectors) != len(ids):
            raise AgentOSError("Vectors and ids must have same length")

        # 添加新向量
        start_idx = len(self.memory_vectors)
        self.memory_vectors.extend(vectors)
        self.memory_ids.extend(ids)

        # 重建权重矩阵
        await self._rebuild_weights()

        logger.info(f"Stored {len(vectors)} patterns, total: {len(self.memory_vectors)}")
        return True

    async def _rebuild_weights(self):
        """
        重建 Hopfield 网络的权重矩阵。
        公式: W = (1/N) * Σ (ξ_i * ξ_i^T) - I * autapse_strength (可选)
        """
        n_patterns = len(self.memory_vectors)
        if n_patterns == 0:
            self.weight_matrix = None
            return

        # 将模式组成矩阵，每列是一个模式
        patterns = np.array(self.memory_vectors).T  # shape (dim, n_patterns)

        # 计算 Hebbian 权重
        # W = (1/n_patterns) * patterns @ patterns.T
        W = (1.0 / n_patterns) * (patterns @ patterns.T)

        if self.use_autapse:
            # 减去自相互作用（对角线设为 0 或减弱）
            np.fill_diagonal(W, self.autapse_strength * np.diag(W))

        self.weight_matrix = W

    async def retrieve(
        self,
        query: np.ndarray,
        k: int = 1,
        return_energy: bool = False,
    ) -> List[Tuple[str, float, Optional[float]]]:
        """
        从查询向量检索最近的吸引子状态。

        Args:
            query: 查询向量。
            k: 返回的最相似记忆数。
            return_energy: 是否返回最终能量值。

        Returns:
            (记忆 ID, 相似度, 可选能量值) 列表。
        """
        if len(self.memory_vectors) == 0:
            return []

        # 确保查询向量已归一化
        norm = np.linalg.norm(query)
        if norm > 0:
            query = query / norm

        # 运行吸引子动力学
        final_state, history = await self._run_dynamics(query)

        # 计算最终状态与所有存储模式的相似度
        similarities = []
        for mem_vec in self.memory_vectors:
            if self.similarity:
                sim = self.similarity.compute_similarity(final_state, mem_vec, normalized=True)
            else:
                # 默认余弦相似度
                sim = np.dot(final_state, mem_vec)
            similarities.append(sim)

        # 获取前 k 个
        indices = np.argsort(similarities)[-k:][::-1]
        results = []
        for idx in indices:
            mem_id = self.memory_ids[idx]
            sim = similarities[idx]
            if return_energy:
                energy = self._compute_energy(final_state)
                results.append((mem_id, float(sim), float(energy)))
            else:
                results.append((mem_id, float(sim), None))

        return results

    async def _run_dynamics(self, initial_state: np.ndarray) -> Tuple[np.ndarray, List[np.ndarray]]:
        """
        运行吸引子动力学直至收敛。

        Returns:
            (最终状态, 历史状态列表)
        """
        if self.weight_matrix is None:
            return initial_state, [initial_state]

        state = initial_state.copy()
        history = [state.copy()]

        for iteration in range(self.max_iterations):
            if self.update_rule == "async":
                # 异步更新：随机选择一个神经元更新
                idx = np.random.randint(self.dimension)
                # 计算局部场
                h = np.dot(self.weight_matrix[idx], state)
                # 更新（使用 sign 函数或连续激活）
                new_val = np.tanh(h)  # 连续激活
                state[idx] = new_val
            else:
                # 同步更新
                h = self.weight_matrix @ state
                state = np.tanh(h)

            history.append(state.copy())

            # 检查收敛
            if len(history) > 1:
                delta = np.linalg.norm(history[-1] - history[-2])
                if delta < self.convergence_threshold:
                    break

        return state, history

    def _compute_energy(self, state: np.ndarray) -> float:
        """
        计算 Hopfield 能量: E = -0.5 * state^T W state
        """
        if self.weight_matrix is None:
            return 0.0
        return -0.5 * (state @ self.weight_matrix @ state)

    async def remove(self, ids: List[str]) -> int:
        """
        移除指定的记忆模式。

        Args:
            ids: 要移除的记忆 ID 列表。

        Returns:
            实际移除的数量。
        """
        remove_set = set(ids)
        keep_indices = [i for i, _id in enumerate(self.memory_ids) if _id not in remove_set]
        self.memory_vectors = [self.memory_vectors[i] for i in keep_indices]
        self.memory_ids = [self.memory_ids[i] for i in keep_indices]

        await self._rebuild_weights()
        removed = len(ids) - len(keep_indices)
        logger.info(f"Removed {removed} patterns from attractor network")
        return removed