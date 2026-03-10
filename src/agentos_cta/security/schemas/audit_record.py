# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 审计记录数据模型。

from dataclasses import dataclass
from typing import Optional, Dict, Any
import time


@dataclass
class AuditRecord:
    """工具调用审计记录。"""
    record_id: str
    agent_id: str
    tool_name: str
    input_data: Dict[str, Any]
    result: Optional[Dict[str, Any]] = None
    success: bool = False
    error: Optional[str] = None
    timestamp: float = time.time()
    trace_id: Optional[str] = None
    permission_granted: bool = False
    permission_check_id: Optional[str] = None