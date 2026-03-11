# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# AgentOS 安全隔离层（Saferoom）模块。
# 提供虚拟工位、权限裁决、工具审计、输入净化等安全机制。

from .virtual_workbench import VirtualWorkbench, WorkbenchSession
from .permission_engine import PermissionEngine, Permission, PermissionDecision
from .tool_audit import ToolAudit, AuditRecord
from .input_sanitizer import InputSanitizer, SanitizationResult
from .schemas import PermissionRule, AuditEvent, SandboxConfig

__all__ = [
    "VirtualWorkbench",
    "WorkbenchSession",
    "PermissionEngine",
    "Permission",
    "PermissionDecision",
    "ToolAudit",
    "AuditRecord",
    "InputSanitizer",
    "SanitizationResult",
    "PermissionRule",
    "AuditEvent",
    "SandboxConfig",
]