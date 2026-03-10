# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 执行结果数据模型。

from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class Result:
    """任务执行结果。"""
    task_id: str
    success: bool
    output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time_ms: int = 0
    token_usage: Optional[Dict[str, int]] = None  # 例如 {"input": 100, "output": 50}
    metadata: Dict[str, Any] = None