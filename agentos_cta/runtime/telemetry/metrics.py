# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 指标收集器。

import time
from collections import defaultdict
from typing import Dict, List
from dataclasses import dataclass, field


@dataclass
class MetricPoint:
    """指标数据点。"""
    timestamp: float
    value: float


class MetricsCollector:
    """
    指标收集器。
    支持计数器、定时器等基础指标类型。
    """

    def __init__(self):
        self._counters: Dict[str, int] = defaultdict(int)
        self._timings: Dict[str, List[MetricPoint]] = defaultdict(list)
        self._gauges: Dict[str, float] = {}

    def increment(self, name: str, value: int = 1):
        """增加计数器。"""
        self._counters[name] += value

    def record_timing(self, name: str, duration_ms: float):
        """记录耗时。"""
        self._timings[name].append(MetricPoint(
            timestamp=time.time(),
            value=duration_ms,
        ))

    def set_gauge(self, name: str, value: float):
        """设置仪表值。"""
        self._gauges[name] = value

    def collect(self) -> Dict[str, Any]:
        """收集所有指标。"""
        result = {
            "counters": dict(self._counters),
            "gauges": dict(self._gauges),
        }

        # 计算耗时统计
        timings_summary = {}
        for name, points in self._timings.items():
            if points:
                values = [p.value for p in points]
                timings_summary[name] = {
                    "count": len(values),
                    "avg": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values),
                }
        result["timings"] = timings_summary

        return result