# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 输入净化器：检测并过滤潜在恶意输入。

import re
from typing import Dict, Any, Optional
from agentos_cta.utils.error_types import SecurityError
from agentos_cta.utils.structured_logger import get_logger

logger = get_logger(__name__)


class InputSanitizer:
    """
    输入净化器。
    检查输入中是否包含潜在的恶意内容（如提示词注入、路径遍历等）。
    """

    # 简单的黑名单模式
    BLACKLIST_PATTERNS = [
        r"ignore previous instructions",
        r"system prompt:",
        r"you are now",
        r"\.\./",           # 路径遍历
        r"`.*`",            # 代码执行
        r"\${.*}",          # 环境变量注入
        r"<!--.*-->",       # HTML 注释
    ]

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.enabled = self.config.get("enabled", True)
        self.custom_patterns = self.config.get("custom_patterns", [])
        self.all_patterns = self.BLACKLIST_PATTERNS + self.custom_patterns

    def sanitize(self, text: str) -> str:
        """
        净化输入文本，返回净化后的版本（或抛出异常）。
        """
        if not self.enabled:
            return text

        # 检查黑名单
        for pattern in self.all_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                logger.warning(f"Detected suspicious pattern: {pattern}")
                if self.config.get("strict", True):
                    raise SecurityError(f"Input contains forbidden pattern: {pattern}")
                else:
                    # 替换为安全占位
                    text = re.sub(pattern, "[FILTERED]", text, flags=re.IGNORECASE)

        # 额外的净化（如去除控制字符）
        text = ''.join(ch for ch in text if ord(ch) >= 32 or ch in '\n\r\t')
        return text

    def sanitize_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """递归净化字典中的所有字符串值。"""
        if not self.enabled:
            return data

        result = {}
        for key, value in data.items():
            if isinstance(value, str):
                result[key] = self.sanitize(value)
            elif isinstance(value, dict):
                result[key] = self.sanitize_dict(value)
            elif isinstance(value, list):
                result[key] = [self.sanitize(item) if isinstance(item, str) else item for item in value]
            else:
                result[key] = value
        return result