# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 持久性计算器：计算持久性阈值、持久性图差异、稳定性分析。

import numpy as np
from typing import List, Tuple, Optional, Dict, Any
import asyncio
from agentos_cta.utils.observability import get_logger
from agentos_cta.utils.error import AgentOSError

logger = get_logger(__name__)


class PersistenceCalculator:
    """
    持久性计算器。
    负责计算持久性阈值、比较持久性图、分析特征稳定性。
    基于持久同调理论，通过 Bottleneck 距离和 Wasserstein 距离分析持久特征的稳定性 。
    """

    def __init__(self, config: Dict[str, Any]):
        """
        初始化持久性计算器。

        Args:
            config: 配置参数。
                - noise_level: 预期噪声水平
                - alpha: 显著性水平（默认 0.05）
                - bootstrap_samples: 自助法采样次数（默认 100）
        """
        self.config = config
        self.noise_level = config.get("noise_level", 0.05)
        self.alpha = config.get("alpha", 0.05)
        self.bootstrap_samples = config.get("bootstrap_samples", 100)

    def compute_noise_threshold(self, distances: np.ndarray) -> float:
        """
        基于随机拓扑理论计算噪声阈值。
        对于满足泊松点过程的随机噪声，持久同调生成元的期望寿命可解析计算。
        将阈值设为期望值加上若干标准差，可在给定置信水平下区分信号与噪声 。
        """
        if len(distances) == 0:
            return self.noise_level

        # 将距离矩阵转换为上三角
        triu_indices = np.triu_indices_from(distances, k=1)
        unique_distances = distances[triu_indices]

        if len(unique_distances) == 0:
            return self.noise_level

        # 假设噪声服从指数分布
        # 估计噪声的参数
        mean_dist = np.mean(unique_distances)
        std_dist = np.std(unique_distances)

        # 噪声阈值：均值 + 3 * 标准差
        # 这对应于 99.7% 置信水平下区分信号
        threshold = mean_dist + 3.0 * std_dist

        return float(threshold)

    def compute_persistence_threshold(
        self,
        persistences: List[float],
        method: str = "statistical"
    ) -> float:
        """
        计算持久性阈值。

        Args:
            persistences: 持久性值列表。
            method: 计算方法。
                - "statistical": 基于统计分布
                - "elbow": 基于肘部法则
                - "percentile": 基于百分位数

        Returns:
            持久性阈值。
        """
        if not persistences:
            return self.noise_level

        persistences = np.array(persistences)

        if method == "statistical":
            # 基于统计分布：假设持久性服从指数分布
            # 使用自助法估计置信区间
            thresholds = []
            for _ in range(self.bootstrap_samples):
                sample = np.random.choice(persistences, size=len(persistences), replace=True)
                # 取 95 百分位数
                th = np.percentile(sample, 95)
                thresholds.append(th)

            return float(np.mean(thresholds))

        elif method == "elbow":
            # 肘部法则：找到曲率变化最大的点
            sorted_pers = np.sort(persistences)[::-1]
            if len(sorted_pers) < 3:
                return self.noise_level

            # 计算二阶差分
            diffs = np.diff(sorted_pers)
            if len(diffs) < 2:
                return self.noise_level

            # 找到二阶差分最大的点
            second_diffs = np.abs(np.diff(diffs))
            elbow_idx = np.argmax(second_diffs) + 1

            return float(sorted_pers[elbow_idx])

        elif method == "percentile":
            # 基于百分位数（例如取 80 百分位数）
            return float(np.percentile(persistences, 80))

        else:
            return self.noise_level

    def compute_bottleneck_distance(
        self,
        diagram1: List[Tuple[float, float]],
        diagram2: List[Tuple[float, float]]
    ) -> float:
        """
        计算两个持久性图之间的 Bottleneck 距离。
        Bottleneck 距离是匹配两个图中点所需的最大 L∞ 移动距离 。
        """
        # 转换为 numpy 数组
        dgm1 = np.array(diagram1)
        dgm2 = np.array(diagram2)

        if len(dgm1) == 0 and len(dgm2) == 0:
            return 0.0

        try:
            from persim import bottleneck

            # 使用 persim 库计算
            distance = bottleneck(dgm1, dgm2)
            return float(distance)

        except ImportError:
            # 简化实现
            return self._simplified_bottleneck(dgm1, dgm2)

    def _simplified_bottleneck(
        self,
        dgm1: np.ndarray,
        dgm2: np.ndarray
    ) -> float:
        """简化的 Bottleneck 距离计算。"""
        if len(dgm1) == 0 or len(dgm2) == 0:
            return float('inf')

        # 计算所有点对之间的 L∞ 距离
        max_distances = []
        for p1 in dgm1:
            for p2 in dgm2:
                linf = max(abs(p1[0] - p2[0]), abs(p1[1] - p2[1]))
                max_distances.append(linf)

        if not max_distances:
            return float('inf')

        # Bottleneck 距离是最大最小距离
        # 这只是一个近似，实际需要匈牙利算法
        return float(np.min(max_distances))

    def compute_wasserstein_distance(
        self,
        diagram1: List[Tuple[float, float]],
        diagram2: List[Tuple[float, float]],
        p: int = 2
    ) -> float:
        """
        计算两个持久性图之间的 Wasserstein 距离。
        Wasserstein 距离考虑了点对之间的总移动代价 。
        """
        dgm1 = np.array(diagram1)
        dgm2 = np.array(diagram2)

        if len(dgm1) == 0 and len(dgm2) == 0:
            return 0.0

        try:
            from persim import wasserstein

            distance = wasserstein(dgm1, dgm2, p=p)
            return float(distance)

        except ImportError:
            return self._simplified_wasserstein(dgm1, dgm2, p)

    def _simplified_wasserstein(
        self,
        dgm1: np.ndarray,
        dgm2: np.ndarray,
        p: int
    ) -> float:
        """简化的 Wasserstein 距离计算。"""
        if len(dgm1) == 0 or len(dgm2) == 0:
            return float('inf')

        # 计算所有点对之间的 p 范数距离
        from scipy.spatial.distance import cdist

        # 使用 L∞ 距离作为基础
        # 对于每个点，距离是 max(|x1-x2|, |y1-y2|)
        distances = np.zeros((len(dgm1), len(dgm2)))
        for i, p1 in enumerate(dgm1):
            for j, p2 in enumerate(dgm2):
                distances[i, j] = max(abs(p1[0] - p2[0]), abs(p1[1] - p2[1]))

        # 使用贪心匹配（非最优，仅近似）
        min_total = 0.0
        used_j = set()
        for i in range(len(dgm1)):
            best_j = None
            best_dist = float('inf')
            for j in range(len(dgm2)):
                if j not in used_j and distances[i, j] < best_dist:
                    best_dist = distances[i, j]
                    best_j = j
            if best_j is not None:
                min_total += best_dist ** p
                used_j.add(best_j)

        return float(min_total ** (1.0 / p))

    def analyze_stability(
        self,
        diagrams: List[List[Tuple[float, float]]],
        method: str = "bottleneck"
    ) -> Dict[str, Any]:
        """
        分析持久性图的稳定性。
        通过计算图间距离的统计量评估特征稳定性。

        Args:
            diagrams: 持久性图列表。
            method: 距离度量方法 ("bottleneck" 或 "wasserstein")。

        Returns:
            稳定性分析结果。
        """
        n_diagrams = len(diagrams)
        if n_diagrams < 2:
            return {
                "stable": True,
                "mean_distance": 0.0,
                "std_distance": 0.0,
                "max_distance": 0.0,
            }

        # 计算所有图对之间的距离
        distances = []
        for i in range(n_diagrams):
            for j in range(i + 1, n_diagrams):
                if method == "bottleneck":
                    dist = self.compute_bottleneck_distance(diagrams[i], diagrams[j])
                else:
                    dist = self.compute_wasserstein_distance(diagrams[i], diagrams[j], p=2)
                distances.append(dist)

        distances = np.array(distances)

        # 判断稳定性
        # 如果距离的变异系数小于阈值，则认为稳定
        mean_dist = np.mean(distances)
        std_dist = np.std(distances)
        cv = std_dist / (mean_dist + 1e-10)  # 变异系数

        stable = cv < 0.3  # 阈值可调

        return {
            "stable": stable,
            "mean_distance": float(mean_dist),
            "std_distance": float(std_dist),
            "max_distance": float(np.max(distances)),
            "cv": float(cv),
            "n_pairs": len(distances),
        }