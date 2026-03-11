# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# L2 Summary：轮次摘要生成器，使用 LLM 压缩原始日志。

from typing import List, Dict, Any, Optional
import asyncio
from agentos_cta.utils.structured_logger import get_logger
from agentos_cta.utils.token_counter import TokenCounter

logger = get_logger(__name__)


class Summarizer:
    """
    L2 Summary：将一批原始日志压缩为摘要。
    实际可使用 LLM 生成摘要，此处提供接口和模拟实现。
    """

    def __init__(self, model_name: str = "gpt-3.5-turbo", max_summary_tokens: int = 500):
        self.model_name = model_name
        self.max_summary_tokens = max_summary_tokens
        self.token_counter = TokenCounter(model_name)

    async def generate_summary(self, logs: List[Dict[str, Any]], context: Optional[Dict] = None) -> str:
        """
        生成摘要。
        实际应调用 LLM，这里返回简单统计信息。
        """
        # 模拟：统计日志条数和关键事件
        event_count = len(logs)
        # 提取关键事件（例如包含 "error" 或 "failed" 的日志）
        errors = [log for log in logs if "error" in str(log).lower() or "fail" in str(log).lower()]
        summary = f"Total events: {event_count}, Errors: {len(errors)}. First log: {logs[0] if logs else 'None'}"
        return summary

    async def summarize_round(self, round_id: str, logs: List[Dict[str, Any]]) -> str:
        """为整个轮次生成摘要。"""
        summary = await self.generate_summary(logs, {"round": round_id})
        # 可存储摘要到文件
        return summary