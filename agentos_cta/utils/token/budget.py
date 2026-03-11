# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# Token 预算管理。

import time
from typing import Optional, Dict, Any
from dataclasses import dataclass
from agentos_cta.utils.error import ResourceLimitError


@dataclass
class TokenUsage:
    """Token 使用情况。"""
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    timestamp: float = 0.0


class TokenBudget:
    """
    Token 预算管理器。
    跟踪任务级别的 Token 消耗，支持预算控制和预警。
    """

    def __init__(self, max_tokens: int, soft_limit: Optional[int] = None):
        """
        初始化预算管理器。

        Args:
            max_tokens: 硬性上限，超过则抛出异常。
            soft_limit: 软性上限，超过则记录警告。
        """
        self.max_tokens = max_tokens
        self.soft_limit = soft_limit or int(max_tokens * 0.8)
        self.usage = TokenUsage()
        self.history: list[TokenUsage] = []

    def add(self, input_tokens: int, output_tokens: int):
        """添加 Token 消耗。"""
        self.usage.input_tokens += input_tokens
        self.usage.output_tokens += output_tokens
        self.usage.total_tokens += input_tokens + output_tokens
        self.usage.timestamp = time.time()

        if self.usage.total_tokens > self.max_tokens:
            raise ResourceLimitError(
                f"Token budget exceeded: {self.usage.total_tokens} > {self.max_tokens}"
            )
        elif self.usage.total_tokens > self.soft_limit:
            # 记录警告，但不中断
            pass

    def checkpoint(self) -> TokenUsage:
        """创建检查点并记录历史。"""
        self.history.append(self.usage)
        self.usage = TokenUsage()
        return self.history[-1]

    def remaining(self) -> int:
        """剩余可用 Token。"""
        return max(0, self.max_tokens - self.usage.total_tokens)

    def reset(self):
        """重置当前使用量。"""
        self.usage = TokenUsage()