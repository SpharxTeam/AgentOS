# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# AgentOS CoreLoopThree 核心包。
# 提供智能体操作系统的三层核心架构：认知层、行动层、记忆与进化层。

__version__ = "3.0.0"
__author__ = "SPHARX"
__license__ = "GPL-3.0"

# 导出核心类型，方便用户直接导入
from agentos_cta.coreloopthree.cognition import (
    Router,
    DualModelCoordinator,
    IncrementalPlanner,
    Dispatcher,
)
from agentos_cta.coreloopthree.execution import (
    AgentPool,
    CompensationManager,
    TraceabilityTracer,
    ExecutionUnit,
    ToolUnit,
    CodeUnit,
    APIUnit,
    FileUnit,
    BrowserUnit,
    DBUnit,
)
from agentos_cta.coreloopthree.memories import (
    MemoryRovol,
    MemoryRecord,
    Query,
    Pattern,
)

__all__ = [
    "__version__",
    "Router",
    "DualModelCoordinator",
    "IncrementalPlanner",
    "Dispatcher",
    "AgentPool",
    "CompensationManager",
    "TraceabilityTracer",
    "ExecutionUnit",
    "ToolUnit",
    "CodeUnit",
    "APIUnit",
    "FileUnit",
    "BrowserUnit",
    "DBUnit",
    "MemoryRovol",
    "MemoryRecord",
    "Query",
    "Pattern",
]