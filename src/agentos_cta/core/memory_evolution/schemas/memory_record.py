# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 记忆记录数据模型。

from typing import Dict, Any, Optional
from dataclasses import dataclass, field
import time


@dataclass
class MemoryRecord:
    """
    记忆记录，代表一条存储在记忆系统中的信息。
    可对应 L1-L4 的不同层级。
    """
    record_id: str
    content: str
    record_type: str  # "buffer", "summary", "vector", "pattern"
    source: str  # 来源（如任务ID、Agent ID等）
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[list] = None  # 向量表示
    importance: float = 1.0  # 重要性评分
    access_count: int = 0  # 访问次数
    last_accessed: Optional[float] = None