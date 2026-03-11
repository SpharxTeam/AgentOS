# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 记忆记录数据模型。

from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
import time
import uuid


@dataclass
class MemoryMetadata:
    """记忆元数据。"""
    memory_id: str
    trace_id: str
    agent_id: str
    task_id: Optional[str] = None
    round_id: Optional[str] = None
    timestamp: float = field(default_factory=time.time)
    access_count: int = 0
    last_access: Optional[float] = None
    size_bytes: int = 0
    format: str = "json"
    tags: Dict[str, Any] = field(default_factory=dict)
    importance: float = 1.0  # 重要性权重，用于遗忘曲线


@dataclass
class MemoryRecord:
    """完整记忆记录，包含原始数据、特征和元数据。"""
    memory_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    raw_data: Optional[Any] = None  # 原始数据（反序列化后）
    raw_location: Optional[str] = None  # L1 存储位置
    feature_vector: Optional[List[float]] = None  # L2 特征向量
    bound_vector: Optional[List[float]] = None  # L3 绑定向量（如果有）
    metadata: MemoryMetadata = field(default_factory=MemoryMetadata)
    l4_pattern_ids: List[str] = field(default_factory=list)  # 关联的 L4 模式 ID
    embedding_model: Optional[str] = None  # 生成 feature_vector 的模型

    def __post_init__(self):
        if not hasattr(self.metadata, 'memory_id') or not self.metadata.memory_id:
            self.metadata.memory_id = self.memory_id