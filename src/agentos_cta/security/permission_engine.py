# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 权限裁决引擎：基于规则（非LLM）判断操作权限。

import re
from typing import Dict, Any, Optional, List
import fnmatch
from dataclasses import dataclass
from agentos_cta.utils.structured_logger import get_logger
from agentos_cta.utils.error_types import SecurityError
from .schemas import Permission, PermissionAction

logger = get_logger(__name__)


class PermissionEngine:
    """
    权限裁决引擎。
    使用规则列表进行匹配，遵循最小权限原则。
    """

    def __init__(self, rules: List[Dict[str, Any]]):
        """
        初始化。

        Args:
            rules: 规则列表，每个规则包含 resource_pattern, action, effect。
        """
        self.rules = rules
        self._compile_rules()

    def _compile_rules(self):
        """预处理规则（如编译正则）。"""
        self.compiled_rules = []
        for rule in self.rules:
            pattern = rule.get("resource_pattern", "*")
            action = rule.get("action", "*")
            effect = PermissionAction(rule.get("effect", "deny"))
            # 将通配符转换为 fnmatch 模式
            self.compiled_rules.append({
                "resource_pattern": pattern,
                "action_pattern": action,
                "effect": effect,
            })

    def check_permission(self, agent_id: str, resource: str, action: str) -> PermissionAction:
        """
        检查指定 Agent 对资源的操作权限。

        Returns:
            PermissionAction: allow/deny/prompt
        """
        # 按顺序匹配第一条规则
        for rule in self.compiled_rules:
            if fnmatch.fnmatch(resource, rule["resource_pattern"]) and \
               fnmatch.fnmatch(action, rule["action_pattern"]):
                logger.debug(f"Rule matched: {rule}")
                return rule["effect"]

        # 默认拒绝
        return PermissionAction.DENY

    def request_permission(self, agent_id: str, resource: str, action: str,
                           context: Optional[Dict[str, Any]] = None) -> Permission:
        """
        请求权限，返回权限对象。
        """
        effect = self.check_permission(agent_id, resource, action)
        return Permission(
            resource=resource,
            action=action,
            effect=effect,
            reason=f"Rule matched: {effect.value}"
        )