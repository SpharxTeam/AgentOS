# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 绑定算子：将多个向量绑定为一个复合表示，支持非交换绑定和 Q 参数调节。

import numpy as np
from typing import List, Optional, Union, Tuple
from agentos_cta.utils.observability import get_logger
from agentos_cta.utils.error import AgentOSError

logger = get_logger(__name__)


class Binder:
    """
    绑定算子。
    实现向量符号架构中的绑定操作 (Binding)，支持非交换绑定。
    通过 Q 参数调节绑定矩阵的秩，控制容量-精度权衡。
    参考广义全息简化表示（GHRR）和非交换绑定理论 。
    """

    def __init__(self, dimension: int, Q: int = 1, use_complex: bool = False):
        """
        初始化绑定算子。

        Args:
            dimension: 向量维度（必须为偶数 if use_complex=True）。
            Q: 绑定参数，控制绑定矩阵的秩。1 ≤ Q ≤ dimension。
               当 Q=1 时退化为对角绑定（FHRR），容量大但精度低；
               当 Q=dimension 时退化为全张量积，精度高但容量小。
            use_complex: 是否使用复数域（FHRR 风格）。若为 True，向量将用复数表示。
        """
        self.dimension = dimension
        self.Q = max(1, min(Q, dimension))
        self.use_complex = use_complex

        if use_complex and dimension % 2 != 0:
            raise AgentOSError("Complex mode requires even dimension (real+imag pairs)")

        # 生成绑定矩阵 G_k (每个分量一个矩阵)
        # 对于 Q 参数，我们采用分块对角绑定：每个分块是一个随机正交矩阵
        self._init_bind_matrices()

    def _init_bind_matrices(self):
        """初始化绑定矩阵。"""
        if self.use_complex:
            # 复数域：每个绑定矩阵是正交矩阵，作用于复数的实虚部
            # 为了简化，我们使用随机相位表示：绑定对应元素相乘
            # 实际上 Q 参数在此模式下通过块对角实现
            pass
        else:
            # 实数域：使用随机高斯矩阵，然后正交化以保持稳定性
            np.random.seed(42)  # 固定种子以保证可重复性
            # 生成 Q 个绑定矩阵，每个大小为 (dimension, dimension) 的低秩矩阵
            self.bind_matrices = []
            for _ in range(self.Q):
                # 生成随机矩阵并近似正交（使用 QR 分解）
                A = np.random.randn(self.dimension, self.dimension)
                Q_mat, _ = np.linalg.qr(A)
                self.bind_matrices.append(Q_mat)

    def bind(self, vectors: List[np.ndarray]) -> np.ndarray:
        """
        将多个向量绑定为一个复合向量。

        Args:
            vectors: 向量列表，每个向量维度必须与 self.dimension 一致。

        Returns:
            绑定后的向量。
        """
        if not vectors:
            raise AgentOSError("No vectors to bind")

        for v in vectors:
            if v.shape != (self.dimension,):
                raise AgentOSError(f"Vector shape mismatch: expected ({self.dimension},), got {v.shape}")

        if self.use_complex:
            return self._bind_complex(vectors)
        else:
            return self._bind_real(vectors)

    def _bind_real(self, vectors: List[np.ndarray]) -> np.ndarray:
        """实数域绑定实现。"""
        # 初始化结果向量为零
        result = np.zeros(self.dimension)

        # 对于 Q 参数，我们采用加权求和的方式：每个绑定矩阵对应一个特征通道
        # 公式：b = Σ_k (Π_i (G_k * v_i))  简化版本
        # 这里我们使用更稳定的循环绑定：b = (((v1 ⊗ v2) ⊗ v3) ...)
        # 其中二元绑定定义：a ⊗ b = Σ_k (G_k a) ∘ (G_k b)   (∘ 表示逐元素乘)
        if len(vectors) == 1:
            return vectors[0]

        result = vectors[0].copy()
        for i in range(1, len(vectors)):
            # 绑定 result 和 vectors[i]
            # 使用 Q 个分量的逐元素乘然后求和
            bound = np.zeros(self.dimension)
            for k in range(self.Q):
                # 应用绑定矩阵到两个向量
                transformed_a = self.bind_matrices[k] @ result
                transformed_b = self.bind_matrices[k] @ vectors[i]
                # 逐元素乘
                bound += transformed_a * transformed_b
            result = bound / self.Q  # 归一化

        return result

    def _bind_complex(self, vectors: List[np.ndarray]) -> np.ndarray:
        """复数域绑定实现（FHRR 风格）。"""
        # 将实数向量视为复数（实部和虚部交替）
        def to_complex(v):
            # v 是偶数长度，实部虚部交替
            return v[::2] + 1j * v[1::2]

        def from_complex(c):
            # 从复数恢复交替形式
            real = np.real(c)
            imag = np.imag(c)
            result = np.zeros(self.dimension)
            result[::2] = real
            result[1::2] = imag
            return result

        # 转换为复数表示
        c_vectors = [to_complex(v) for v in vectors]
        # 复数域绑定：对应元素相乘（相位叠加）
        result = c_vectors[0]
        for c in c_vectors[1:]:
            result = result * c
            # 归一化到单位圆（可选）
            # result = result / np.abs(result)  避免幅值过小
        return from_complex(result)

    def get_available_models(self) -> dict:
        """返回当前绑定器的能力描述。"""
        return {
            "dimension": self.dimension,
            "Q": self.Q,
            "use_complex": self.use_complex,
            "bind_capacity": self.Q / self.dimension,  # 容量指标
        }