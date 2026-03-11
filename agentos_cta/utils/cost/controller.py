# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 预算控制器。

import asyncio
import time
from typing import Dict, Optional
from dataclasses import dataclass
from agentos_cta.utils.error import ResourceLimitError


@dataclass
class BudgetConfig:
    """预算配置。"""
    max_cost_usd: float
    max_tokens: int
    alert_threshold: float = 0.8  # 达到 80% 时报警
    period_seconds: int = 3600    # 周期（小时）


@dataclass
class BudgetUsage:
    """预算使用情况。"""
    cost_usd: float = 0.0
    tokens: int = 0
    start_time: float = 0.0
    last_reset: float = 0.0


class BudgetController:
    """
    预算控制器。
    管理任务、用户或项目的预算消耗。
    """

    def __init__(self, config: BudgetConfig):
        self.config = config
        self.usage = BudgetUsage(start_time=time.time())
        self._lock = asyncio.Lock()
        self._alert_callbacks = []

    def register_alert(self, callback):
        """注册报警回调。"""
        self._alert_callbacks.append(callback)

    async def consume(self, cost_usd: float, tokens: int):
        """消耗预算。"""
        async with self._lock:
            self._check_reset()

            self.usage.cost_usd += cost_usd
            self.usage.tokens += tokens

            if self.usage.cost_usd > self.config.max_cost_usd:
                raise ResourceLimitError(
                    f"Budget exceeded: ${self.usage.cost_usd:.2f} > ${self.config.max_cost_usd}"
                )

            if self.usage.cost_usd / self.config.max_cost_usd > self.config.alert_threshold:
                await self._trigger_alert()

    def _check_reset(self):
        """检查是否需要重置周期。"""
        if time.time() - self.usage.start_time > self.config.period_seconds:
            self.usage = BudgetUsage(start_time=time.time())

    async def _trigger_alert(self):
        """触发预算报警。"""
        usage_ratio = self.usage.cost_usd / self.config.max_cost_usd
        for callback in self._alert_callbacks:
            if asyncio.iscoroutinefunction(callback):
                await callback(self.usage, usage_ratio)
            else:
                callback(self.usage, usage_ratio)

    def remaining(self) -> Dict[str, float]:
        """剩余预算。"""
        return {
            "cost_usd": max(0, self.config.max_cost_usd - self.usage.cost_usd),
            "tokens": max(0, self.config.max_tokens - self.usage.tokens),
            "ratio": self.usage.cost_usd / self.config.max_cost_usd,
        }