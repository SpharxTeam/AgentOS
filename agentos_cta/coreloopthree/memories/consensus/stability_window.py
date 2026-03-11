# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 稳定性窗口 β：过滤暂时性多数，确保决策鲁棒性。

import asyncio
import time
from typing import Any, List, Optional
from collections import deque
from agentos_cta.utils.observability import get_logger

logger = get_logger(__name__)


class StabilityWindow:
    """
    稳定性窗口。
    维护一个滑动窗口，记录最近多次决策的共识值。
    只有当某个值在窗口内稳定出现（满足频率阈值）时，才被接受。
    用于过滤暂时性多数，避免因少数异常导致的决策抖动。
    """

    def __init__(self, window_size: int = 5, stability_ratio: float = 0.6):
        """
        初始化稳定性窗口。

        Args:
            window_size: 窗口大小（记录最近几次决策）。
            stability_ratio: 稳定性阈值，值在窗口中出现比例需大于此值。
        """
        self.window_size = window_size
        self.stability_ratio = stability_ratio
        self.window: deque = deque(maxlen=window_size)

    def add_decision(self, decision: Any):
        """向窗口添加一次决策值。"""
        self.window.append(decision)
        logger.debug(f"Stability window updated: {list(self.window)}")

    def is_stable(self) -> bool:
        """
        判断当前窗口是否达到稳定。

        Returns:
            True 表示窗口已满且某个值的出现频率超过稳定性阈值。
        """
        if len(self.window) < self.window_size:
            return False
        counts = {}
        for d in self.window:
            counts[d] = counts.get(d, 0) + 1
        max_count = max(counts.values())
        return max_count / self.window_size >= self.stability_ratio

    def get_stable_value(self) -> Optional[Any]:
        """
        返回当前窗口中的稳定值（如果存在），否则返回 None。
        """
        if not self.is_stable():
            return None
        counts = {}
        for d in self.window:
            counts[d] = counts.get(d, 0) + 1
        stable_val = max(counts.items(), key=lambda x: x[1])[0]
        return stable_val

    def clear(self):
        """清空窗口。"""
        self.window.clear()