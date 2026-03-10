# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 稳定性窗口 β 机制。
# 用于过滤暂时性多数，确保决策鲁棒性，防止因瞬时波动导致错误决策。
# 基于 arXiv:2512.20184 "Agentic Consensus" 中的 Stability Window 概念。

import time
import asyncio
from typing import List, Dict, Any, Optional, Callable, Awaitable, Tuple
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from agentos_cta.utils.structured_logger import get_logger
from agentos_cta.utils.error_types import ConsensusError

logger = get_logger(__name__)


class WindowState(Enum):
    STABLE = "stable"
    FLUCTUATING = "fluctuating"
    CONVERGING = "converging"


@dataclass
class Observation:
    """窗口内的观测值。"""
    value: Any
    timestamp: float
    weight: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StabilityResult:
    """稳定性判断结果。"""
    is_stable: bool
    stable_value: Optional[Any] = None
    state: WindowState = WindowState.STABLE
    confidence: float = 1.0
    window_duration: float = 0.0
    sample_count: int = 0
    details: Dict[str, Any] = field(default_factory=dict)


class StabilityWindow:
    """
    稳定性窗口 β。
    维护一个时间窗口内的观测值，评估其稳定性，过滤暂时性多数。
    支持时间窗口和计数窗口两种模式。
    """

    def __init__(self, config: Dict[str, Any]):
        """
        初始化稳定性窗口。

        Args:
            config: 配置参数
                - window_type: "time" 或 "count"
                - window_size: 窗口大小（秒 或 样本数）
                - stability_threshold: 稳定性阈值 (0-1)
                - min_samples: 最小样本数要求
                - majority_ratio: 多数比例要求
        """
        self.window_type = config.get("window_type", "time")  # "time" 或 "count"
        self.window_size = config.get("window_size", 5.0)  # 5秒 或 5个样本
        self.stability_threshold = config.get("stability_threshold", 0.8)  # 80% 相同视为稳定
        self.min_samples = config.get("min_samples", 3)
        self.majority_ratio = config.get("majority_ratio", 0.6)  # 60% 多数
        
        # 滑动窗口
        self.window: deque = deque()
        self.latest_value: Optional[Any] = None
        self.latest_timestamp: float = 0.0

    def add_observation(self, value: Any, weight: float = 1.0, metadata: Optional[Dict] = None):
        """
        向窗口添加一个观测值。
        """
        obs = Observation(
            value=value,
            timestamp=time.time(),
            weight=weight,
            metadata=metadata or {}
        )
        self.window.append(obs)
        self.latest_value = value
        self.latest_timestamp = obs.timestamp
        
        # 清理窗口
        self._prune_window()
        
        logger.debug(f"Added observation: {value}, window size now {len(self.window)}")

    def _prune_window(self):
        """根据窗口类型清理过期观测。"""
        now = time.time()
        while self.window:
            if self.window_type == "time":
                # 移除超出时间窗口的观测
                if now - self.window[0].timestamp > self.window_size:
                    self.window.popleft()
                else:
                    break
            else:  # "count"
                # 保留最多 window_size 个观测
                while len(self.window) > self.window_size:
                    self.window.popleft()
                break

    def evaluate_stability(self) -> StabilityResult:
        """
        评估当前窗口的稳定性。
        """
        if len(self.window) < self.min_samples:
            return StabilityResult(
                is_stable=False,
                state=WindowState.FLUCTUATING,
                confidence=0.0,
                window_duration=self._get_window_duration(),
                sample_count=len(self.window),
                details={"reason": "insufficient_samples"}
            )
        
        # 统计各值的加权频次
        value_counts: Dict[Any, float] = {}
        total_weight = 0.0
        
        for obs in self.window:
            key = self._value_key(obs.value)
            value_counts[key] = value_counts.get(key, 0) + obs.weight
            total_weight += obs.weight
        
        if total_weight == 0:
            return StabilityResult(
                is_stable=False,
                state=WindowState.FLUCTUATING,
                confidence=0.0,
                window_duration=self._get_window_duration(),
                sample_count=len(self.window),
                details={"reason": "zero_weight"}
            )
        
        # 找出权重最大的值
        max_key, max_weight = max(value_counts.items(), key=lambda x: x[1])
        majority_ratio = max_weight / total_weight
        
        # 判断是否稳定
        if majority_ratio >= self.stability_threshold:
            # 稳定
            is_stable = True
            state = WindowState.STABLE
            stable_value = self._recover_value(max_key, value_counts)
            confidence = majority_ratio
        elif max_weight >= self.majority_ratio * total_weight:
            # 有明确多数，但未达稳定阈值，可能正在收敛
            is_stable = False
            state = WindowState.CONVERGING
            stable_value = self._recover_value(max_key, value_counts)
            confidence = majority_ratio
        else:
            # 无明显多数
            is_stable = False
            state = WindowState.FLUCTUATING
            stable_value = None
            confidence = 0.0
        
        return StabilityResult(
            is_stable=is_stable,
            stable_value=stable_value,
            state=state,
            confidence=confidence,
            window_duration=self._get_window_duration(),
            sample_count=len(self.window),
            details={
                "value_counts": {str(k): v for k, v in value_counts.items()},
                "majority_ratio": majority_ratio,
                "threshold": self.stability_threshold,
                "total_weight": total_weight,
            }
        )

    def _get_window_duration(self) -> float:
        """获取窗口的时间跨度。"""
        if not self.window:
            return 0.0
        return self.window[-1].timestamp - self.window[0].timestamp

    def _value_key(self, value: Any) -> str:
        """将值转换为可哈希键。"""
        try:
            hash(value)
            return value
        except TypeError:
            return str(value)

    def _recover_value(self, key: str, value_counts: Dict) -> Any:
        """从键恢复原始值（简化）。"""
        # 如果 key 不是字符串，说明是原始值
        if not isinstance(key, str):
            return key
        # 否则可能是字符串化的值，尝试找到原始值
        for val in value_counts.keys():
            if str(val) == key:
                return val
        return key

    def get_recent_values(self, n: int = 5) -> List[Any]:
        """获取最近的 n 个观测值。"""
        return [obs.value for obs in list(self.window)[-n:]]

    def clear(self):
        """清空窗口。"""
        self.window.clear()
        logger.info("Stability window cleared")

    def get_latest(self) -> Optional[Any]:
        """获取最新观测值。"""
        return self.latest_value

    async def wait_for_stability(
        self,
        timeout_ms: Optional[int] = None,
        check_interval_ms: float = 100,
    ) -> StabilityResult:
        """
        异步等待窗口达到稳定状态。
        
        Args:
            timeout_ms: 超时毫秒
            check_interval_ms: 检查间隔

        Returns:
            最终稳定性评估
        """
        start = time.time()
        timeout = timeout_ms / 1000 if timeout_ms else float('inf')
        
        while time.time() - start < timeout:
            result = self.evaluate_stability()
            if result.is_stable:
                return result
            await asyncio.sleep(check_interval_ms / 1000)
        
        # 超时
        return StabilityResult(
            is_stable=False,
            state=WindowState.FLUCTUATING,
            window_duration=self._get_window_duration(),
            sample_count=len(self.window),
            details={"reason": "timeout"}
        )