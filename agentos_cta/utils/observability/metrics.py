# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 指标收集器。

import time
from collections import defaultdict
from typing import Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class MetricPoint:
    """指标数据点。"""
    value: float
    timestamp: float
    tags: Dict[str, str] = field(default_factory=dict)


class MetricsCollector:
    """
    指标收集器。
    支持计数器、仪表、直方图等类型。
    """

    def __init__(self):
        self._counters: Dict[str, int] = defaultdict(int)
        self._gauges: Dict[str, float] = {}
        self._histograms: Dict[str, List[MetricPoint]] = defaultdict(list)

    def increment(self, name: str, value: int = 1, tags: Optional[Dict[str, str]] = None):
        """增加计数器。"""
        key = self._key_with_tags(name, tags)
        self._counters[key] += value

    def set_gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """设置仪表值。"""
        key = self._key_with_tags(name, tags)
        self._gauges[key] = value

    def record_histogram(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """记录直方图值。"""
        key = self._key_with_tags(name, tags)
        self._histograms[key].append(MetricPoint(
            value=value,
            timestamp=time.time(),
            tags=tags or {}
        ))

    def _key_with_tags(self, name: str, tags: Optional[Dict[str, str]]) -> str:
        """生成带标签的键。"""
        if not tags:
            return name
        tag_str = ",".join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{name}[{tag_str}]"

    def collect(self) -> Dict[str, Any]:
        """收集所有指标。"""
        return {
            "counters": dict(self._counters),
            "gauges": dict(self._gauges),
            "histograms": {
                name: [{"value": p.value, "timestamp": p.timestamp} for p in points]
                for name, points in self._histograms.items()
            }
        }

    def reset(self):
        """重置所有指标。"""
        self._counters.clear()
        self._gauges.clear()
        self._histograms.clear()


class Timer:
    """
    计时器上下文管理器。
    用于测量代码块执行时间。
    """

    def __init__(self, metrics_collector: MetricsCollector, name: str, tags: Optional[Dict[str, str]] = None):
        self.metrics = metrics_collector
        self.name = name
        self.tags = tags
        self.start_time = None

    def __enter__(self):
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, *args):
        duration = (time.perf_counter() - self.start_time) * 1000  # 毫秒
        self.metrics.record_histogram(self.name, duration, self.tags)