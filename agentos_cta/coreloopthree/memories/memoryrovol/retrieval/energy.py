# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 能量函数：管理记忆的能量景观，集成遗忘衰减。

import numpy as np
from typing import List, Optional, Dict, Any
from agentos_cta.utils.structured_logger import get_logger

logger = get_logger(__name__)


class EnergyFunction:
    """
    能量函数管理器。
    负责计算记忆模式的能量，并集成遗忘衰减，实现能量景观的动态调整。
    """

    def __init__(self, config: Dict[str, Any]):
        """
        初始化能量函数管理器。

        Args:
            config: 配置参数。
                - energy_type: 能量类型 ("hopfield", "ising")
                - base_energy: 基础能量
                - forgetting_lambda: 遗忘曲线参数
                - temperature: 温度（用于玻尔兹曼分布）
        """
        self.config = config
        self.energy_type = config.get("energy_type", "hopfield")
        self.base_energy = config.get("base_energy", 0.0)
        self.forgetting_lambda = config.get("forgetting_lambda", 0.01)
        self.temperature = config.get("temperature", 1.0)

    def compute_energy(
        self,
        state: np.ndarray,
        weight_matrix: Optional[np.ndarray] = None,
        memory_index: Optional[int] = None,
        last_access_time: Optional[float] = None,
        current_time: Optional[float] = None,
    ) -> float:
        """
        计算状态的能量。

        Args:
            state: 状态向量。
            weight_matrix: 权重矩阵（Hopfield 网络用）。
            memory_index: 记忆模式索引（用于计算与特定记忆相关的能量）。
            last_access_time: 上次访问时间（用于遗忘衰减）。
            current_time: 当前时间。

        Returns:
            能量值。
        """
        if self.energy_type == "hopfield":
            if weight_matrix is None:
                return self.base_energy
            energy = -0.5 * (state @ weight_matrix @ state)
        elif self.energy_type == "ising":
            # 简化的 Ising 能量
            energy = -np.sum(state[:-1] * state[1:])  # 最近邻耦合
        else:
            energy = self.base_energy

        # 应用遗忘衰减
        if last_access_time is not None and current_time is not None:
            time_diff_hours = (current_time - last_access_time) / 3600.0
            decay = np.exp(-self.forgetting_lambda * time_diff_hours)
            # 能量增加（记忆变浅）
            energy = energy + (1 - decay) * self.base_energy

        return float(energy)

    def compute_energy_landscape(
        self,
        states: List[np.ndarray],
        weight_matrix: np.ndarray,
        time_factors: Optional[List[float]] = None,
    ) -> np.ndarray:
        """
        计算多个状态的能量景观。

        Args:
            states: 状态向量列表。
            weight_matrix: 权重矩阵。
            time_factors: 时间衰减因子列表。

        Returns:
            能量数组。
        """
        energies = []
        for i, state in enumerate(states):
            energy = self.compute_energy(state, weight_matrix)
            if time_factors:
                energy *= time_factors[i]
            energies.append(energy)
        return np.array(energies)

    def compute_probability(self, energy: float) -> float:
        """
        根据玻尔兹曼分布计算状态概率。
        """
        return np.exp(-energy / self.temperature)

    def energy_gradient(
        self,
        state: np.ndarray,
        weight_matrix: np.ndarray,
    ) -> np.ndarray:
        """
        计算能量梯度（用于动力学）。
        """
        if self.energy_type == "hopfield":
            # E = -0.5 * state^T W state
            # dE/dstate = -W state
            return -weight_matrix @ state
        else:
            # 简单梯度下降
            return -state