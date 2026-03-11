# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 进化报告数据模型。

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import time
import uuid


@dataclass
class CommitteeFinding:
    """委员会发现项。"""
    finding_id: str
    committee: str  # "coordination", "technical", "audit", "team"
    title: str
    description: str
    severity: str  # "info", "warning", "critical"
    affected_components: List[str]  # 影响的组件（如 Agent ID, 规则文件等）
    evidence: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    resolved_at: Optional[float] = None
    proposal_id: Optional[str] = None  # 关联的优化提案 ID


@dataclass
class EvolutionReport:
    """进化报告，记录一轮进化中的各项发现和建议。"""
    report_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    round_id: str  # 关联的轮次 ID
    created_at: float = field(default_factory=time.time)
    findings: List[CommitteeFinding] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)  # 流程度量等
    summary: str = ""
    applied_rules: List[str] = field(default_factory=list)  # 已应用的规则 ID