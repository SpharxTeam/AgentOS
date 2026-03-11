# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 权限相关数据模型。

from enum import Enum
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
import re


class PermissionEffect(str, Enum):
    """权限效果。"""
    ALLOW = "allow"
    DENY = "deny"
    ALLOW_WITH_AUDIT = "allow_with_audit"  # 允许但需审计


@dataclass
class ResourcePattern:
    """资源模式定义。"""
    pattern: str  # 如 "file:read:/tmp/*"
    
    def match(self, resource: str) -> bool:
        """检查资源是否匹配模式。"""
        # 将模式转换为正则表达式
        regex = self.pattern.replace(".", "\\.").replace("*", ".*").replace("?", ".")
        return re.match(regex, resource) is not None


@dataclass
class PermissionRule:
    """权限规则。"""
    rule_id: str
    resource_pattern: ResourcePattern
    action: str  # read, write, execute, connect 等
    effect: PermissionEffect
    priority: int = 0  # 数字越大优先级越高
    conditions: Optional[Dict[str, Any]] = None  # 附加条件