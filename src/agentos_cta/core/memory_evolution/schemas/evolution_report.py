# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 进化报告数据模型。

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
import time


@dataclass
class EvolutionReport:
    """
    进化报告，记录一次进化周期的成果。
    由团队委员会生成，包含各委员会的建议和最终规则更新。
    """
    round_id: str
    timestamp: float = field(default_factory=time.time)
    coordination_report: Optional[Dict[str, Any]] = None
    technical_report: Optional[Dict[str, Any]] = None
    audit_report: Optional[Dict[str, Any]] = None
    rule_updates: List[Dict[str, Any]] = field(default_factory=list)
    summary: str = ""