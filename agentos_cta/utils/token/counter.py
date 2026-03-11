# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# Token 计数器 - 支持主流模型编码。

import tiktoken
from typing import Dict, Optional, List, Union
import logging

logger = logging.getLogger(__name__)


class TokenCounter:
    """Token 计数器，支持主流模型编码。"""

    _ENCODING_CACHE: Dict[str, tiktoken.Encoding] = {}
    _MODEL_PREFIX_MAP = {
        "gpt-4": "cl100k_base",
        "gpt-3.5": "cl100k_base",
        "text-embedding-3": "cl100k_base",
        "claude": "cl100k_base",  # Claude 也使用类似编码
    }

    def __init__(self, model_name: str = "gpt-4"):
        """
        初始化 TokenCounter。

        Args:
            model_name: 模型名称，用于确定编码。
        """
        self.model_name = model_name
        self.encoding = self._get_encoding(model_name)

    @classmethod
    def _get_encoding(cls, model_name: str) -> tiktoken.Encoding:
        """获取或缓存模型的编码器。"""
        if model_name in cls._ENCODING_CACHE:
            return cls._ENCODING_CACHE[model_name]

        try:
            encoding = tiktoken.encoding_for_model(model_name)
        except KeyError:
            # 若未知模型，根据前缀猜测编码
            encoding_name = cls._guess_encoding(model_name)
            encoding = tiktoken.get_encoding(encoding_name)
            logger.warning(f"Model {model_name} not found, using {encoding_name} encoding.")

        cls._ENCODING_CACHE[model_name] = encoding
        return encoding

    @classmethod
    def _guess_encoding(cls, model_name: str) -> str:
        """根据模型名称猜测编码。"""
        model_lower = model_name.lower()
        for prefix, enc in cls._MODEL_PREFIX_MAP.items():
            if prefix in model_lower:
                return enc
        return "cl100k_base"  # 默认

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

    def truncate(self, text: str, max_tokens: int, side: str = "right") -> str:
        """
        截断文本到指定 token 数。

        Args:
            text: 输入文本。
            max_tokens: 最大允许 token 数。
            side: 截断侧边 ("left", "right", "middle")

        Returns:
            截断后的文本。
        """
        tokens = self.encoding.encode(text)
        if len(tokens) <= max_tokens:
            return text

        if side == "right":
            truncated = tokens[:max_tokens]
        elif side == "left":
            truncated = tokens[-max_tokens:]
        elif side == "middle":
            # 保留开头和结尾
            half = max_tokens // 2
            truncated = tokens[:half] + tokens[-(max_tokens - half):]
        else:
            raise ValueError(f"Invalid side: {side}")

        return self.encoding.decode(truncated)