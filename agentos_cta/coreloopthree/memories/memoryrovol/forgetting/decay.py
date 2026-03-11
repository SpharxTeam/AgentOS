# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 遗忘衰减：基于艾宾浩斯遗忘曲线。

import numpy as np
import time
from typing import Optional, Dict, Any
from agentos_cta.utils.structured_logger import get_logger

logger = get_logger(__name__)


class DecayFunction:
    """
    遗忘衰减函数。
    基于艾宾浩斯遗忘曲线，为记忆随时间衰减提供数学形式。
    支持多种衰减模型。
    """

    def __init__(self, config: Dict[str, Any]):
        """
        初始化遗忘衰减函数。

        Args:
            config: 配置参数。
                - decay_model: 衰减模型 ("exponential", "power", "logistic")
                - lambda_: 指数衰减参数（默认 0.01）
                - alpha: 幂律衰减指数（默认 0.5）
                - k: 逻辑斯蒂衰减斜率（默认 0.1）
                - reference_time: 参考时间（默认 1 小时）
        """
        self.decay_model = config.get("decay_model", "exponential")
        self.lambda_ = config.get("lambda_", 0.01)  # 指数衰减率
        self.alpha = config.get("alpha", 0.5)      # 幂律指数
        self.k = config.get("k", 0.1)              # 逻辑斯蒂斜率
        self.reference_time = config.get("reference_time", 3600.0)  # 1 小时

    def compute_decay_factor(self, last_access: float, current_time: Optional[float] = None) -> float:
        """
        计算衰减因子（0~1 之间，越小代表遗忘越多）。

        Args:
            last_access: 上次访问时间（Unix 时间戳）。
            current_time: 当前时间（默认为当前时间）。

        Returns:
            衰减因子。
        """
        if current_time is None:
            current_time = time.time()

        time_diff = current_time - last_access  # 秒
        if time_diff <= 0:
            return 1.0

        # 归一化时间单位
        t = time_diff / self.reference_time

        if self.decay_model == "exponential":
            # R = e^{-λ t}
            decay = np.exp(-self.lambda_ * t)

        elif self.decay_model == "power":
            # R = t^{-α}
            decay = t ** (-self.alpha) if t > 0 else 1.0

        elif self.decay_model == "logistic":
            # R = 1 / (1 + e^{k(t - t0)})
            t0 = 1.0  # 半衰期位置
            decay = 1.0 / (1.0 + np.exp(self.k * (t - t0)))

        else:
            # 默认无遗忘
            decay = 1.0

        return float(decay)

    def apply_decay_to_weight(self, weight: float, last_access: float, current_time: Optional[float] = None) -> float:
        """
        将衰减因子应用到权重上。
        """
        factor = self.compute_decay_factor(last_access, current_time)
        return weight * factor

    def compute_forgetting_curve(self, times: np.ndarray) -> np.ndarray:
        """
        计算给定时间点的遗忘曲线值。
        """
        t = times / self.reference_time
        if self.decay_model == "exponential":
            return np.exp(-self.lambda_ * t)
        elif self.decay_model == "power":
            return t ** (-self.alpha)
        elif self.decay_model == "logistic":
            t0 = 1.0
            return 1.0 / (1.0 + np.exp(self.k * (t - t0)))
        else:
            return np.ones_like(t)