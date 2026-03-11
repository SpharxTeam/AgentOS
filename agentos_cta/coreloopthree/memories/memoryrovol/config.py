# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# MemoryRovol 配置类。

from typing import Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class MemoryRovolConfig:
    """MemoryRovol 全局配置。"""
    # 原始卷 L1
    raw_storage_dir: str = "data/workspace/memory/raw"
    raw_max_file_size_mb: int = 100

    # 特征层 L2
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dim: int = 384
    index_type: str = "hnsw"
    similarity_metric: str = "cosine"

    # 结构层 L3
    binder_Q: int = 4
    binder_use_complex: bool = False

    # 模式层 L4
    persistence_max_dim: int = 2
    persistence_min_persistence: float = 0.1
    clustering_method: str = "hdbscan"

    # 检索
    attractor_update_rule: str = "async"
    attractor_max_iterations: int = 100
    attractor_convergence_threshold: float = 1e-4

    # 遗忘
    decay_model: str = "exponential"
    decay_lambda: float = 0.01
    prune_interval: int = 86400  # 1 day
    prune_access_threshold: int = 2

    # 挂载
    mount_token_budget: int = 4096
    mount_max_memories: int = 5

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典。"""
        return {k: v for k, v in self.__dict__.items() if not k.startswith('_')}