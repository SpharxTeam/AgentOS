# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 权限数据模型。

from dataclasses import dataclass
from typing import Optional
from enum import Enum


class PermissionAction(str, Enum):
    ALLOW = "allow"
    DENY = "deny"
    PROMPT = "prompt"  # 需要用户确认


@dataclass
class Permission:
    """权限实体。"""
    resource: str          # 资源标识，如 "file:/tmp/xxx"
    action: str            # 操作，如 "read", "write", "execute"
    effect: PermissionAction
    reason: Optional[str] = None
    ttl_seconds: Optional[int] = None  # 有效期（临时授权）