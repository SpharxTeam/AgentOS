# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 输入净化器：检测并过滤潜在恶意输入，防止提示词注入、路径遍历等攻击。

import re
from typing import Any, Dict, Optional, List
from dataclasses import dataclass
from agentos_cta.utils.observability import get_logger
from agentos_cta.utils.error import SecurityError

logger = get_logger(__name__)


@dataclass
class SanitizationResult:
    """净化结果。"""
    cleaned: Any
    original: Any
    was_modified: bool
    issues: List[str]
    risk_level: str  # "none", "low", "medium", "high"


class InputSanitizer:
    """
    输入净化器。
    检测并过滤恶意输入，防止提示词注入、路径遍历、XSS 等攻击。
    """

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.max_length = self.config.get("max_input_length", 100000)
        self.block_patterns = self.config.get("block_patterns", [
            r"ignore previous instructions",
            r"system prompt",
            r"you are now",
            r"bypass",
            r"\.\./",  # 路径遍历
            r"<script.*?>.*?</script>",  # XSS
            r"exec\s*\(",  # 命令执行
        ])
        self.warn_patterns = self.config.get("warn_patterns", [
            r"password",
            r"api[_-]?key",
            r"secret",
            r"token",
        ])

    def sanitize_string(self, text: str, context: Optional[Dict] = None) -> SanitizationResult:
        """
        净化单个字符串。
        """
        original = text
        issues = []
        risk_level = "none"
        was_modified = False

        # 长度检查
        if len(text) > self.max_length:
            text = text[:self.max_length]
            issues.append(f"Input truncated from {len(original)} to {self.max_length}")
            was_modified = True
            risk_level = "low"

        # 检查阻断模式
        for pattern in self.block_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                issues.append(f"Blocked pattern detected: {pattern}")
                risk_level = "high"
                # 直接拒绝，返回空或抛出异常？这里返回带有 high 风险的结果，由调用方决定是否拒绝
                # 可以替换为去除匹配部分，但更安全的是标记为高风险
                # 简单实现：移除匹配部分
                text = re.sub(pattern, "[REMOVED]", text, flags=re.IGNORECASE)
                was_modified = True

        # 检查警告模式
        for pattern in self.warn_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                issues.append(f"Warning: sensitive pattern '{pattern}' found")
                if risk_level == "none":
                    risk_level = "low"

        return SanitizationResult(
            cleaned=text,
            original=original,
            was_modified=was_modified,
            issues=issues,
            risk_level=risk_level,
        )

    def sanitize_dict(self, data: Dict[str, Any], context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        净化字典中的所有字符串字段。
        """
        cleaned = {}
        for key, value in data.items():
            if isinstance(value, str):
                result = self.sanitize_string(value, context)
                cleaned[key] = result.cleaned
                if result.risk_level == "high":
                    # 高风险，记录并可能拒绝
                    logger.warning(f"High risk input in key '{key}': {result.issues}")
                    # 可选：抛出异常
                    # raise SecurityError(f"High risk input detected: {result.issues}")
            elif isinstance(value, dict):
                cleaned[key] = self.sanitize_dict(value, context)
            elif isinstance(value, list):
                cleaned[key] = [self.sanitize_dict(item, context) if isinstance(item, dict) else item for item in value]
            else:
                cleaned[key] = value
        return cleaned

    def sanitize(self, data: Any, context: Optional[Dict] = None) -> SanitizationResult:
        """
        通用净化接口。
        """
        if isinstance(data, str):
            return self.sanitize_string(data, context)
        elif isinstance(data, dict):
            cleaned_dict = self.sanitize_dict(data, context)
            # 计算是否有修改和风险
            was_modified = cleaned_dict != data
            issues = []  # 简化为无 issues 列表
            risk_level = "none"  # 简化
            return SanitizationResult(
                cleaned=cleaned_dict,
                original=data,
                was_modified=was_modified,
                issues=issues,
                risk_level=risk_level,
            )
        else:
            return SanitizationResult(
                cleaned=data,
                original=data,
                was_modified=False,
                issues=[],
                risk_level="none",
            )