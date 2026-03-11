# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 意图理解相关数据模型。

from enum import Enum
from typing import Optional, Dict, Any
from dataclasses import dataclass, field


class ComplexityLevel(str, Enum):
    """任务复杂度等级。"""
    SIMPLE = "simple"          # 简单任务：可由轻量模型快速完成
    COMPLEX = "complex"        # 复杂任务：需要主思考者深度推理
    CRITICAL = "critical"      # 关键任务：需要双模型协同 + 审计


@dataclass
class Intent:
    """用户意图结构化表示。"""
    raw_text: str                     # 原始输入
    normalized_text: str = ""         # 标准化后文本
    goal: str = ""                    # 核心目标
    constraints: Dict[str, Any] = field(default_factory=dict)  # 约束条件（时间、质量、预算等）
    context: Dict[str, Any] = field(default_factory=dict)      # 附加上下文（如项目背景）
    complexity: ComplexityLevel = ComplexityLevel.SIMPLE       # 评估后的复杂度


@dataclass
class ResourceMatch:
    """资源匹配结果（模型选择与 Token 预算）。"""
    model_name: str                     # 选定的模型名称
    estimated_input_tokens: int         # 预估输入 token
    estimated_output_tokens: int        # 预估输出 token
    max_budget_tokens: int              # 允许的最大 token 数
    reason: str = ""                    # 选择理由