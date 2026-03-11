# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 审计记录数据模型。

from enum import Enum
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
import time


class AuditSeverity(str, Enum):
    """审计严重程度。"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AuditEvent:
    """审计事件。"""
    event_id: str
    timestamp: float = field(default_factory=time.time)
    agent_id: str
    action: str  # 执行的操作
    resource: str  # 操作的资源
    decision: str  # allow/deny
    severity: AuditSeverity = AuditSeverity.INFO
    reason: Optional[str] = None
    input_preview: Optional[str] = None  # 输入预览（脱敏）
    trace_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)