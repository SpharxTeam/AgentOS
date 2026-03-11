# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 权限裁决引擎：基于规则（非LLM）判断操作权限。
# 遵循最小权限原则，权限请求必须显式声明，用户确认。

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import fnmatch
from agentos_cta.utils.structured_logger import get_logger
from agentos_cta.utils.error_types import SecurityError
from .schemas import PermissionRule, PermissionEffect, ResourcePattern

logger = get_logger(__name__)


@dataclass
class Permission:
    """权限请求。"""
    agent_id: str
    action: str  # read, write, execute, connect
    resource: str  # 资源标识，如 "file:/tmp/data.txt"
    context: Optional[Dict[str, Any]] = None


@dataclass
class PermissionDecision:
    """权限裁决结果。"""
    allowed: bool
    effect: PermissionEffect
    rule_id: Optional[str] = None
    reason: str = ""
    require_audit: bool = False


class PermissionEngine:
    """
    权限裁决引擎。
    基于预定义的规则集进行裁决，不依赖 LLM。
    支持通配符匹配、优先级和条件判断。
    """

    def __init__(self, rules: List[PermissionRule]):
        """
        初始化权限引擎。

        Args:
            rules: 权限规则列表。
        """
        # 按优先级排序（高的在前）
        self.rules = sorted(rules, key=lambda r: -r.priority)

    @classmethod
    def from_config(cls, config_path: str):
        """从配置文件加载规则。"""
        import yaml
        from pathlib import Path
        with open(Path(config_path), 'r') as f:
            data = yaml.safe_load(f)
        rules = []
        for item in data.get('permissions', []):
            pattern = ResourcePattern(item['resource'])
            rule = PermissionRule(
                rule_id=item.get('id', 'auto'),
                resource_pattern=pattern,
                action=item['action'],
                effect=PermissionEffect(item['default']),
                priority=item.get('priority', 0),
                conditions=item.get('conditions'),
            )
            rules.append(rule)
        return cls(rules)

    async def check(self, permission: Permission) -> PermissionDecision:
        """
        检查权限请求。
        """
        for rule in self.rules:
            # 匹配动作
            if rule.action != '*' and rule.action != permission.action:
                continue
            # 匹配资源
            if not rule.resource_pattern.match(permission.resource):
                continue
            # 检查条件
            if rule.conditions:
                if not self._check_conditions(rule.conditions, permission.context):
                    continue

            # 找到匹配规则
            if rule.effect == PermissionEffect.ALLOW:
                return PermissionDecision(
                    allowed=True,
                    effect=rule.effect,
                    rule_id=rule.rule_id,
                    reason=f"Allowed by rule {rule.rule_id}",
                    require_audit=False,
                )
            elif rule.effect == PermissionEffect.ALLOW_WITH_AUDIT:
                return PermissionDecision(
                    allowed=True,
                    effect=rule.effect,
                    rule_id=rule.rule_id,
                    reason=f"Allowed with audit by rule {rule.rule_id}",
                    require_audit=True,
                )
            elif rule.effect == PermissionEffect.DENY:
                return PermissionDecision(
                    allowed=False,
                    effect=rule.effect,
                    rule_id=rule.rule_id,
                    reason=f"Denied by rule {rule.rule_id}",
                    require_audit=False,
                )

        # 无匹配规则，默认拒绝
        return PermissionDecision(
            allowed=False,
            effect=PermissionEffect.DENY,
            reason="No matching rule, denied by default",
            require_audit=False,
        )

    def _check_conditions(self, conditions: Dict, context: Optional[Dict]) -> bool:
        """检查条件是否满足。"""
        if not context:
            return False
        for key, expected in conditions.items():
            actual = context.get(key)
            if actual != expected:
                return False
        return True