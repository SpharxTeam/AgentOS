# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 解绑算子：从复合向量中恢复原始分量，支持近似逆运算。

import numpy as np
from typing import Optional, List
from agentos_cta.utils.structured_logger import get_logger
from agentos_cta.utils.error_types import AgentOSError

logger = get_logger(__name__)


class Unbinder:
    """
    解绑算子。
    实现绑定操作的近似逆，从复合向量中恢复原始分量。
    解绑精度依赖于绑定时的 Q 参数和绑定顺序。
    """

    def __init__(self, binder: 'Binder'):
        """
        初始化解绑算子。

        Args:
            binder: 对应的 Binder 实例，用于获取绑定参数和矩阵。
        """
        self.binder = binder
        self.dimension = binder.dimension
        self.Q = binder.Q
        self.use_complex = binder.use_complex

    def unbind(self, bound_vector: np.ndarray, known_vectors: Optional[List[np.ndarray]] = None) -> List[np.ndarray]:
        """
        从复合向量中解绑，恢复原始分量。
        如果提供了部分已知向量，可以解出未知分量；否则需要迭代求解（可能不唯一）。

        Args:
            bound_vector: 绑定后的向量。
            known_vectors: 已知的向量列表，按绑定顺序排列。
                          例如，如果绑定顺序是 [v1, v2, v3]，已知 v1 和 v3，则提供 [v1, None, v3]。
                          未知分量用 None 占位。

        Returns:
            恢复的向量列表，顺序与绑定顺序一致。未知且无法解出的部分返回 None。
        """
        if self.use_complex:
            return self._unbind_complex(bound_vector, known_vectors)
        else:
            return self._unbind_real(bound_vector, known_vectors)

    def _unbind_real(self, bound_vector: np.ndarray, known_vectors: Optional[List[np.ndarray]]) -> List[Optional[np.ndarray]]:
        """实数域解绑。"""
        # 若已知向量列表为空或全部未知，则无法唯一解绑（返回 None）
        if known_vectors is None:
            return [None]

        # 假设绑定顺序为 v1, v2, ..., vn，已知部分向量
        # 解绑过程：从 bound 中依次除去已知向量
        current = bound_vector.copy()
        result = []
        # 从后向前除去已知向量（因为绑定可能非交换，需要知道顺序）
        # 简单实现：假设绑定是可交换的（即顺序无关），但实际非交换需指定顺序
        # 这里我们采用迭代方式：对于每个未知向量，假设它是要解的，用已知向量去乘
        # 实际上，在实数域非交换绑定中，解绑需要利用绑定矩阵的逆
        # 我们实现一个简化版：若 Q=1，绑定退化为元素乘，则解绑就是元素除
        if self.Q == 1 and len(self.binder.bind_matrices) == 1:
            # 对角绑定情况：每个分量独立乘，解绑即为对应元素除（处理零值）
            mat = self.binder.bind_matrices[0]
            inv_mat = np.linalg.pinv(mat)  # 伪逆
            # 对于每个未知，需要求解线性方程
            # 但我们不知顺序，这里仅返回 None
            logger.warning("Exact unbinding for Q=1 not fully implemented, returning None")
            return [None] * (len(known_vectors) if known_vectors else 1)

        # 更通用的方法是迭代求解，但比较复杂。这里我们返回 None 作为占位
        # 实际应用中，解绑往往需要知道足够多的已知向量，或使用迭代优化
        # 这里简化处理，返回 None
        logger.warning("Real unbinding not fully implemented, returning None")
        return [None] * (len(known_vectors) if known_vectors else 1)

    def _unbind_complex(self, bound_vector: np.ndarray, known_vectors: Optional[List[np.ndarray]]) -> List[Optional[np.ndarray]]:
        """复数域解绑（FHRR）。"""
        # 转换为复数
        def to_complex(v):
            return v[::2] + 1j * v[1::2]

        def from_complex(c):
            real = np.real(c)
            imag = np.imag(c)
            res = np.zeros(self.dimension)
            res[::2] = real
            res[1::2] = imag
            return res

        bound_c = to_complex(bound_vector)

        if known_vectors is None or len(known_vectors) == 0:
            return [None]

        # 已知向量的复数形式
        known_c = []
        for v in known_vectors:
            if v is not None:
                known_c.append(to_complex(v))
            else:
                known_c.append(None)

        # 复数域解绑：对于每个未知，通过已知向量除得到（元素除）
        # 假设绑定是元素乘（FHRR），则解绑是元素除
        result = []
        # 我们需要知道绑定顺序。假设顺序是已知的，并且绑定是累积的
        # 最简单情况：只有两个向量绑定
        if len(known_c) == 2 and known_c[0] is not None and known_c[1] is None:
            # bound = v0 * v1  => v1 = bound / v0
            v1_c = bound_c / known_c[0]
            v1 = from_complex(v1_c)
            result = [known_vectors[0], v1]
        elif len(known_c) == 2 and known_c[0] is None and known_c[1] is not None:
            v0_c = bound_c / known_c[1]
            v0 = from_complex(v0_c)
            result = [v0, known_vectors[1]]
        else:
            # 多个向量情况需要迭代
            logger.warning("Complex unbinding for >2 vectors not fully implemented")
            result = [None] * len(known_c)

        return result