# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 延迟监控模块。
# 实时监控 LLM 调用延迟，计算 p95 等指标，用于动态调度和资源调整。

import time
import statistics
from collections import deque
import threading
from typing import Optional


class LatencyMonitor:
    """延迟监控器，维护滑动窗口延迟统计。"""

    def __init__(self, window_size: int = 100):
        """
        初始化监控器。

        Args:
            window_size: 滑动窗口大小，保留最近 window_size 次调用延迟。
        """
        self.window_size = window_size
        self.latencies = deque(maxlen=window_size)
        self._lock = threading.Lock()
        self._total_calls = 0

    def record(self, latency_ms: float):
        """
        记录一次调用的延迟（毫秒）。
        """
        with self._lock:
            self.latencies.append(latency_ms)
            self._total_calls += 1

    def percentile(self, p: float) -> Optional[float]:
        """
        计算当前窗口内延迟的 p 百分位数（如 95）。

        Args:
            p: 百分位，如 95 表示 95 百分位。

        Returns:
            百分位数值（毫秒），若窗口为空则返回 None。
        """
        with self._lock:
            if not self.latencies:
                return None
            sorted_lat = sorted(self.latencies)
            idx = int(p / 100.0 * len(sorted_lat))
            if idx >= len(sorted_lat):
                idx = len(sorted_lat) - 1
            return sorted_lat[idx]

    def p95(self) -> Optional[float]:
        """获取当前 p95 延迟。"""
        return self.percentile(95)

    def p99(self) -> Optional[float]:
        """获取当前 p99 延迟。"""
        return self.percentile(99)

    def average(self) -> Optional[float]:
        """获取当前窗口平均延迟。"""
        with self._lock:
            if not self.latencies:
                return None
            return statistics.mean(self.latencies)

    def max(self) -> Optional[float]:
        """获取当前窗口最大延迟。"""
        with self._lock:
            if not self.latencies:
                return None
            return max(self.latencies)

    def total_calls(self) -> int:
        """返回历史总调用次数。"""
        return self._total_calls