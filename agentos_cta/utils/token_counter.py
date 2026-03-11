# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# Token 计数与预算管理模块。
# 基于 tiktoken 实现多种模型的 token 计数，并提供预算检查与动态调整功能。

import tiktoken
from typing import Dict, Optional, List, Union
import logging

logger = logging.getLogger(__name__)


class TokenCounter:
    """Token 计数器，支持主流模型编码。"""

    _ENCODING_CACHE: Dict[str, tiktoken.Encoding] = {}

    def __init__(self, model_name: str = "gpt-4"):
        """
        初始化 TokenCounter。

        Args:
            model_name: 模型名称，用于确定编码。默认为 "gpt-4"。
        """
        self.model_name = model_name
        self.encoding = self._get_encoding(model_name)

    @classmethod
    def _get_encoding(cls, model_name: str) -> tiktoken.Encoding:
        """获取或缓存模型的编码器。"""
        if model_name not in cls._ENCODING_CACHE:
            try:
                encoding = tiktoken.encoding_for_model(model_name)
            except KeyError:
                # 若未知模型，默认使用 cl100k_base（gpt-4/gpt-3.5 系列）
                logger.warning(f"Model {model_name} not found, using cl100k_base encoding.")
                encoding = tiktoken.get_encoding("cl100k_base")
            cls._ENCODING_CACHE[model_name] = encoding
        return cls._ENCODING_CACHE[model_name]

    def count_tokens(self, text: Union[str, List[str]]) -> int:
        """
        计算文本的 token 数量。

        Args:
            text: 单个字符串或字符串列表。

        Returns:
            token 总数。
        """
        if isinstance(text, str):
            return len(self.encoding.encode(text))
        elif isinstance(text, list):
            return sum(len(self.encoding.encode(t)) for t in text)
        else:
            raise TypeError(f"Expected str or list of str, got {type(text)}")

    def count_messages_tokens(self, messages: List[Dict[str, str]]) -> int:
        """
        计算对话消息列表的 token 数量（适用于 Chat 模型）。

        Args:
            messages: 消息列表，格式如 [{"role": "user", "content": "..."}]

        Returns:
            token 总数（包括格式占位）。
        """
        # 近似计算：每消息增加固定 overhead，具体值参考 OpenAI 官方文档
        tokens_per_message = 3
        tokens_per_name = 1
        total = 0
        for msg in messages:
            total += tokens_per_message
            for key, value in msg.items():
                total += len(self.encoding.encode(value))
                if key == "name":
                    total += tokens_per_name
        total += 3  # 回复起始占位
        return total

    def check_budget(self, current_usage: int, budget: int) -> bool:
        """
        检查当前 token 使用量是否超过预算。

        Args:
            current_usage: 当前已使用 token 数。
            budget: 预算上限。

        Returns:
            True 表示未超预算，False 表示已超。
        """
        return current_usage <= budget

    def adaptive_truncate(self, text: str, max_tokens: int) -> str:
        """
        自适应截断文本，确保不超过 max_tokens。

        Args:
            text: 输入文本。
            max_tokens: 最大允许 token 数。

        Returns:
            截断后的文本（可能保留开头和结尾的关键部分，但简单起见先做尾部截断）。
        """
        tokens = self.encoding.encode(text)
        if len(tokens) <= max_tokens:
            return text
        truncated = tokens[:max_tokens]
        return self.encoding.decode(truncated)