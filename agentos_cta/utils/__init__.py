# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# AgentOS 通用工具模块 - 内核可观测性基石。
# 提供 token 管理、成本控制、结构化日志、错误处理等核心工具。

from .core import (
    VERSION,
    get_agentos_version,
    is_windows,
    is_linux,
    is_macos,
    get_platform,
    get_cpu_count,
    get_memory_info,
)
from .token import TokenCounter, TokenBudget, TokenUsage
from .cost import CostEstimator, BudgetController, ModelPricing
from .observability import (
    StructuredLogger,
    get_logger,
    set_trace_id,
    get_trace_id,
    MetricsCollector,
    Timer,
    TraceContext,
)
from .error import (
    AgentOSError,
    ConfigurationError,
    ResourceLimitError,
    ConsensusError,
    SecurityError,
    ToolExecutionError,
    ModelUnavailableError,
    ContractValidationError,
    handle_exception,
)
from .types import (
    TraceID,
    SessionID,
    TaskID,
    AgentID,
    MemoryID,
    JSONDict,
    TimeInterval,
)

__all__ = [
    # core
    "VERSION",
    "get_agentos_version",
    "is_windows",
    "is_linux",
    "is_macos",
    "get_platform",
    "get_cpu_count",
    "get_memory_info",
    # token
    "TokenCounter",
    "TokenBudget",
    "TokenUsage",
    # cost
    "CostEstimator",
    "BudgetController",
    "ModelPricing",
    # observability
    "StructuredLogger",
    "get_logger",
    "set_trace_id",
    "get_trace_id",
    "MetricsCollector",
    "Timer",
    "TraceContext",
    # error
    "AgentOSError",
    "ConfigurationError",
    "ResourceLimitError",
    "ConsensusError",
    "SecurityError",
    "ToolExecutionError",
    "ModelUnavailableError",
    "ContractValidationError",
    "handle_exception",
    # types
    "TraceID",
    "SessionID",
    "TaskID",
    "AgentID",
    "MemoryID",
    "JSONDict",
    "TimeInterval",
]