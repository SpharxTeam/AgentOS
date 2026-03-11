# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# AgentOS CoreLoopThree 核心层。
# 包含认知层、行动层、记忆与进化层的所有核心组件。

# 认知层
from agentos_cta.coreloopthreeloopthreeloopthree.cognition import (
    Router,
    DualModelCoordinator,
    IncrementalPlanner,
    Dispatcher,
    Intent,
    ComplexityLevel,
    ResourceMatch,
    TaskPlan,
    TaskNode,
    TaskDAG,
)

# 行动层
from agentos_cta.coreloopthreeloopthreeloopthree.execution import (
    AgentPool,
    ExecutionUnit,
    ToolUnit,
    CodeUnit,
    APIUnit,
    FileUnit,
    BrowserUnit,
    DBUnit,
    CompensationManager,
    TraceabilityTracer,
    Task,
    TaskStatus,
    Result,
)

# 记忆与进化层
from agentos_cta.coreloopthreeloopthreeloopthree.memory_evolution import (
    # deep_memory
    Buffer,
    Summarizer,
    VectorStore,
    PatternMiner,
    # world_model
    SemanticSlicer,
    TemporalAligner,
    DriftDetector,
    # consensus
    QuorumFast,
    StabilityWindow,
    StreamingConsensus,
    # committees
    CoordinationCommittee,
    TechnicalCommittee,
    AuditCommittee,
    TeamCommittee,
    # shared_memory
    SharedMemory,
    # schemas
    MemoryRecord,
    EvolutionReport,
)

__all__ = [
    # cognition
    "Router",
    "DualModelCoordinator",
    "IncrementalPlanner",
    "Dispatcher",
    "Intent",
    "ComplexityLevel",
    "ResourceMatch",
    "TaskPlan",
    "TaskNode",
    "TaskDAG",
    # execution
    "AgentPool",
    "ExecutionUnit",
    "ToolUnit",
    "CodeUnit",
    "APIUnit",
    "FileUnit",
    "BrowserUnit",
    "DBUnit",
    "CompensationManager",
    "TraceabilityTracer",
    "Task",
    "TaskStatus",
    "Result",
    # memory_evolution
    "Buffer",
    "Summarizer",
    "VectorStore",
    "PatternMiner",
    "SemanticSlicer",
    "TemporalAligner",
    "DriftDetector",
    "QuorumFast",
    "StabilityWindow",
    "StreamingConsensus",
    "CoordinationCommittee",
    "TechnicalCommittee",
    "AuditCommittee",
    "TeamCommittee",
    "SharedMemory",
    "MemoryRecord",
    "EvolutionReport",
]