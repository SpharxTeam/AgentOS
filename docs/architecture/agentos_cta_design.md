# AgentOS CoreLoopThree (agentos_cta) 架构设计说明

**版本**: v1.0.0  
**最后更新**: 2026-03-11  
**状态**: 生产就绪  
**维护者**: SpharxWorks Team

---

## 📋 目录

1. [概述](#1-概述)
2. [核心架构](#2-核心架构)
3. [认知层设计](#3-认知层设计)
4. [行动层设计](#4-行动层设计)
5. [记忆与进化层设计](#5-记忆与进化层设计)
6. [运行时管理](#6-运行时管理)
7. [安全隔离层](#7-安全隔离层)
8. [技术栈与依赖](#8-技术栈与依赖)
9. [性能指标](#9-性能指标)
10. [扩展性设计](#10-扩展性设计)

---

## 1. 概述

### 1.1 模块定位

`agentos_cta` 是 AgentOS 的核心执行引擎，实现了基于 **CoreLoopThree** 三层循环架构的智能体协作系统。该模块负责：

- **意图理解与任务规划**：将用户输入转化为可执行的任务计划
- **多智能体调度**：协调多个专业 Agent 协同完成复杂任务
- **执行管理**：提供统一的执行单元抽象和事务保证
- **记忆进化**：通过多层记忆系统和共识机制实现持续学习

### 1.2 设计原则

| 原则 | 说明 |
|------|------|
| **分层解耦** | 认知、行动、记忆进化三层职责清晰，接口明确 |
| **冗余容错** | 双模型协同（1 大 +2 小）提供故障降级能力 |
| **增量迭代** | 支持动态任务规划和执行反馈调整 |
| **全链路追踪** | TraceID 贯穿所有子任务，确保可追溯性 |
| **安全隔离** | 沙箱环境和权限控制保障系统安全 |
| **可观测性** | 完善的指标、日志、追踪体系 |

### 1.3 核心概念

```
┌─────────────────────────────────────────────────────────┐
│                    用户请求输入                          │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│  🔵 认知层 (Cognition Layer)                            │
│  - Router: 意图理解、复杂度评估、资源匹配                │
│  - DualModelCoordinator: 双模型协同 (1 大 +2 小冗余)     │
│  - IncrementalPlanner: 增量式任务 DAG 生成               │
│  - Dispatcher: Agent 调度与任务分配                      │
└────────────────────┬────────────────────────────────────┘
                     │ 任务计划 (TaskPlan)
                     ▼
┌─────────────────────────────────────────────────────────┐
│  🟢 行动层 (Execution Layer)                            │
│  - AgentPool: Agent 实例管理与缓存                       │
│  - ExecutionUnits: 7 大执行单元 (Tool/Code/API/File...)  │
│  - CompensationManager: 补偿事务管理器                   │
│  - TraceabilityTracer: 责任链追踪 (TraceID/Span)        │
└────────────────────┬────────────────────────────────────┘
                     │ 执行结果 + 反馈
                     ▼
┌─────────────────────────────────────────────────────────┐
│  🟣 记忆与进化层 (Memory & Evolution Layer)             │
│  - MemoryRovol: 多层记忆系统 (Raw/Feature/Pattern)      │
│  - WorldModel: 世界模型 (语义切片/时间对齐/漂移检测)     │
│  - Consensus: 共识机制 (Quorum-fast/稳定性窗口)          │
│  - Committees: 四大进化委员会                            │
└────────────────────┬────────────────────────────────────┘
                     │ 进化反馈
                     └──────────► 回到认知层优化下一轮
```

---

## 2. 核心架构

### 2.1 目录结构

```
agentos_cta/
├── __init__.py                 # 包入口，导出核心类型
├── coreloopthree/              # 核心三层架构
│   ├── __init__.py
│   ├── cognition/              # 认知层
│   │   ├── __init__.py
│   │   ├── router.py                      # 意图理解与资源匹配
│   │   ├── dual_model_coordinator.py      # 双模型协同
│   │   ├── incremental_planner.py         # 增量式任务规划
│   │   ├── dispatcher.py                  # Agent 调度官
│   │   └── schemas/
│   │       ├── intent.py                  # 意图定义
│   │       ├── task_graph.py              # 任务 DAG
│   │       ├── plan.py                    # 任务计划
│   │       └── __init__.py
│   ├── execution/              # 行动层
│   │   ├── __init__.py
│   │   ├── agent_pool.py                  # Agent 池管理
│   │   ├── compensation_manager.py        # 补偿事务管理器
│   │   ├── traceability_tracer.py         # 责任链追踪器
│   │   ├── units/                         # 执行单元
│   │   │   ├── __init__.py
│   │   │   ├── base_unit.py               # 执行单元基类
│   │   │   ├── tool_unit.py               # 工具单元
│   │   │   ├── code_unit.py               # 代码执行单元
│   │   │   ├── api_unit.py                # API 调用单元
│   │   │   ├── file_unit.py               # 文件操作单元
│   │   │   ├── browser_unit.py            # 浏览器操作单元
│   │   │   └── db_unit.py                 # 数据库操作单元
│   │   └── schemas/
│   │       ├── __init__.py
│   │       ├── task.py                    # 任务实体
│   │       └── result.py                  # 执行结果
│   └── memory_evolution/       # 记忆与进化层
│       ├── __init__.py
│       ├── memoryrovol/                   # MemoryRovol 记忆系统
│       │   ├── __init__.py
│       │   ├── raw_volume.py              # 原始记忆存储
│       │   ├── feature_layer.py           # 特征提取层
│       │   ├── pattern_layer.py           # 模式挖掘层
│       │   ├── structure_layer.py         # 结构组织层
│       │   ├── retrieval.py               # 记忆检索
│       │   ├── consolidation.py           # 记忆巩固
│       │   ├── forgetting.py              # 遗忘机制
│       │   └── schemas/
│       │       ├── memory_record.py       # 记忆记录
│       │       └── pattern.py             # 记忆模式
│       ├── world_model/                   # 世界模型
│       │   ├── __init__.py
│       │   ├── semantic_slicer.py         # 语义切片器
│       │   ├── temporal_aligner.py        # 时间对齐器
│       │   └── drift_detector.py          # 认知漂移检测器
│       ├── consensus/                     # 共识层
│       │   ├── __init__.py
│       │   ├── quorum_fast.py             # Quorum-fast 决策
│       │   ├── stability_window.py        # 稳定性窗口
│       │   └── streaming_consensus.py     # 流式共识
│       ├── committees/                    # 进化委员会
│       │   ├── __init__.py
│       │   ├── coordination_committee.py  # 协调委员会
│       │   ├── technical_committee.py     # 技术委员会
│       │   ├── audit_committee.py         # 审计委员会
│       │   └── team_committee.py          # 团队委员会
│       ├── shared_memory.py               # 共享内存
│       └── schemas/
│           ├── __init__.py
│           ├── memory_record.py           # 记忆记录
│           └── evolution_report.py        # 进化报告
├── runtime/                    # 运行时管理
│   ├── __init__.py
│   ├── server.py                        # 应用服务器
│   ├── session_manager.py               # 会话管理器
│   ├── health_checker.py                # 健康检查器
│   ├── gateway/                         # 网关层
│   │   ├── __init__.py
│   │   ├── http_gateway.py              # HTTP 网关
│   │   ├── websocket_gateway.py         # WebSocket 网关
│   │   └── stdio_gateway.py             # 标准输入输出网关
│   ├── protocol/                        # 协议层
│   │   ├── __init__.py
│   │   ├── json_rpc.py                  # JSON-RPC 2.0
│   │   ├── message_serializer.py        # 消息序列化
│   │   └── codec.py                     # 编解码器
│   └── telemetry/                       # 可观测性
│       ├── __init__.py
│       ├── otel_collector.py            # OpenTelemetry 收集器
│       ├── metrics.py                   # Prometheus 指标
│       └── tracing.py                   # 分布式追踪
├── saferoom/                   # 安全隔离层
│   ├── __init__.py
│   ├── virtual_workbench.py             # 虚拟工位 (沙箱)
│   ├── permission_engine.py             # 权限裁决引擎
│   ├── tool_audit.py                    # 工具审计
│   ├── input_sanitizer.py               # 输入净化器
│   └── schemas/
│       ├── __init__.py
│       ├── permission.py                # 权限定义
│       └── audit_record.py              # 审计记录
└── utils/                      # 通用工具
    ├── __init__.py
    ├── token_counter.py                 # Token 计数
    ├── token_uniqueness.py              # Token 唯一性预测
    ├── cost_estimator.py                # 成本预估
    ├── latency_monitor.py               # 延迟监控
    ├── structured_logger.py             # 结构化日志
    ├── error_types.py                   # 错误类型定义
    └── file_utils.py                    # 文件工具
```

### 2.2 数据流

```
用户请求 → HTTP/WebSocket/Stdio Gateway
         ↓
     JSON-RPC 解析
         ↓
     SessionManager 创建会话
         ↓
     Router 意图解析
         ↓
     DualModelCoordinator 生成计划
         ↓
     Dispatcher 分发任务
         ↓
     AgentPool 获取 Agent
         ↓
     ExecutionUnit 执行
         ↓
     TraceabilityTracer 追踪
         ↓
     CompensationManager 记录
         ↓
     MemoryRovol 存储记忆
         ↓
     WorldModel 更新认知
         ↓
     Consensus 达成共识
         ↓
     Committees 进化优化
         ↓
     响应返回给用户
```

---

## 3. 认知层设计

### 3.1 Router - 路由器

**职责**: 意图理解与资源匹配

**核心流程**:
1. 接收用户原始输入文本
2. 使用 NLP 模型解析为结构化 Intent
3. 评估任务复杂度（SIMPLE/COMPLEX/CRITICAL）
4. 根据复杂度匹配合适的模型资源
5. 返回 ResourceMatch 包含模型选择和 Token 预算

**关键算法**:
- 基于规则 + 机器学习的混合意图分类
- 多维度复杂度评分（Token 需求、工具数量、依赖深度）
- 资源匹配启发式算法（成本、性能、可用性权衡）

**配置参数**:
```yaml
router:
  complexity_thresholds:
    simple: 1000      # tokens < 1000 为简单任务
    complex: 5000     # 1000 <= tokens < 5000 为中等任务
    critical: 5000    # tokens >= 5000 为关键任务
  model_routing_rules:
    - complexity: SIMPLE
      models: ["gpt-3.5-turbo", "claude-3-haiku"]
    - complexity: COMPLEX
      models: ["gpt-4", "claude-3-sonnet"]
    - complexity: CRITICAL
      models: ["gpt-4-turbo", "claude-3-opus"]
```

### 3.2 DualModelCoordinator - 双模型协同协调器

**职责**: 多模型协同与交叉验证

**工作模式**:
```
主模型 (Primary)          辅模型 1 (Secondary-1)      辅模型 2 (Secondary-2)
     │                          │                          │
     ├──────────┬───────────────┤                          │
     │          │               │                          │
     ▼          ▼               ▼                          ▼
 初始规划    异步验证 1      异步验证 2
     │          │               │
     └──────────┴───────────────┘
                │
                ▼
         一致性检查与仲裁
                │
                ▼
           最终规划输出
```

**一致性检查算法**:
1. 计算输出相似度（基于 Embedding 余弦相似度）
2. 相似度 > 0.8：直接采用主模型输出
3. 0.5 < 相似度 <= 0.8：触发仲裁逻辑（选择置信度最高者）
4. 相似度 <= 0.5：标记为高风险，需要人工确认

**故障降级策略**:
- 主模型失败 → 使用辅模型 1
- 主模型 + 辅模型 1 失败 → 使用辅模型 2
- 全部失败 → 抛出 ModelUnavailableError

### 3.3 IncrementalPlanner - 增量规划器

**职责**: 动态任务 DAG 生成与调整

**核心特性**:
- **分阶段生成**: 不一次性生成全部计划，而是先生成顶层目标
- **执行反馈驱动**: 根据已完成任务的反馈动态扩展后续步骤
- **异常修订**: 任务失败时自动重新规划替代路径

**DAG 结构示例**:
```
Goal: 开发待办事项应用
│
├─ Task 1: 需求分析 (无依赖)
│   └─ 输出：requirements.md
│
├─ Task 2: 架构设计 (依赖 Task 1)
│   └─ 输出：architecture.md
│
├─ Task 3: 前端开发 (依赖 Task 2)
│   ├─ SubTask 3.1: UI 组件开发
│   └─ SubTask 3.2: 状态管理
│
└─ Task 4: 后端开发 (依赖 Task 2)
    ├─ SubTask 4.1: API 设计
    └─ SubTask 4.2: 数据库建模
```

### 3.4 Dispatcher - 调度官

**职责**: Agent 选择与任务分发

**评分模型**:
```python
score = (
    weights['cost'] * normalize(cost_score) +
    weights['performance'] * normalize(performance_score) +
    weights['trust'] * normalize(trust_score)
)
```

**默认权重**:
- `cost`: 0.3 (成本越低分越高)
- `performance`: 0.4 (历史成功率)
- `trust`: 0.3 (认证等级、合作时长)

**调度策略**:
1. 查询注册中心获取可用 Agent 列表
2. 过滤不满足要求的 Agent（技能不匹配、负载过高）
3. 对剩余 Agent 进行多目标评分
4. 选择 Top-K 个 Agent（K=1 单任务，K>1 冗余任务）
5. 分发任务并等待执行结果

---

## 4. 行动层设计

### 4.1 AgentPool - Agent 池

**职责**: Agent 生命周期管理

**管理机制**:
- **懒加载**: 首次请求时才加载 Agent 实例
- **LRU 缓存**: 最多缓存 100 个 Agent 实例
- **健康检查**: 定期 ping 检测 Agent 存活状态
- **自动回收**: 超过 30 分钟未使用的 Agent 自动卸载

**支持的角色类型**:
| 角色 | 描述 | 典型技能 |
|------|------|----------|
| `product_manager` | 产品经理 | 需求分析、原型设计 |
| `architect` | 架构师 | 系统设计、技术选型 |
| `frontend` | 前端开发 | React/Vue、TypeScript |
| `backend` | 后端开发 | Python/Node.js、数据库 |
| `devops` | 运维工程师 | Docker、K8s、CI/CD |
| `qa_engineer` | 测试工程师 | 单元测试、E2E 测试 |

### 4.2 ExecutionUnit - 执行单元体系

**基类接口**:
```python
class ExecutionUnit(ABC):
    @abstractmethod
    async def execute(self, input_data: dict) -> dict:
        """执行单元核心逻辑"""
        pass
    
    @abstractmethod
    def get_input_schema(self) -> dict:
        """返回输入数据 JSON Schema"""
        pass
    
    @abstractmethod
    def get_output_schema(self) -> dict:
        """返回输出数据 JSON Schema"""
        pass
    
    def validate_input(self, input_data: dict) -> bool:
        """验证输入数据是否符合 Schema"""
        pass
    
    def compensate(self, input_data: dict, result: dict) -> dict:
        """执行补偿操作（可选实现）"""
        pass
```

**7 大执行单元详解**:

#### ToolUnit - 工具调用单元
- **用途**: 调用预定义的工具函数
- **输入**: `{tool_name: str, arguments: dict}`
- **输出**: `{result: Any, success: bool, error: str}`
- **示例工具**: 计算器、日期处理、文本加密等

#### CodeUnit - 代码执行单元
- **用途**: 安全执行用户提供的代码
- **支持语言**: Python 3.10+, JavaScript (Node.js 18+)
- **输入**: `{code: str, language: str, timeout: int}`
- **输出**: `{stdout: str, stderr: str, exit_code: int}`
- **安全措施**: 沙箱环境、资源限制、白名单导入

#### APIUnit - API 调用单元
- **用途**: 发送 HTTP 请求
- **支持方法**: GET, POST, PUT, DELETE, PATCH
- **输入**: `{url: str, method: str, headers: dict, body: dict}`
- **输出**: `{status_code: int, headers: dict, body: str}`
- **特性**: 自动重试、超时控制、SSL 验证

#### FileUnit - 文件操作单元
- **用途**: 文件读写和管理
- **支持操作**: read, write, append, delete, move, copy
- **输入**: `{operation: str, path: str, content?: str}`
- **输出**: `{success: bool, content?: str, error?: str}`
- **限制**: 仅允许访问 `/tmp/agentos/*` 目录

#### BrowserUnit - 浏览器操作单元
- **用途**: 自动化浏览器操作
- **基于**: Playwright
- **支持操作**: navigate, click, fill, screenshot, evaluate
- **输入**: `{action: str, selector: str, value?: str}`
- **输出**: `{success: bool, result?: Any, screenshot?: bytes}`

#### DBUnit - 数据库操作单元
- **用途**: 数据库 CRUD 操作
- **支持数据库**: PostgreSQL, MySQL, SQLite, MongoDB
- **输入**: `{db_type: str, connection_string: str, query: str}`
- **输出**: `{rows: List[dict], affected_rows: int, error?: str}`
- **安全**: SQL 注入检测、只读模式可选

### 4.3 CompensationManager - 补偿事务管理器

**职责**: SAGA 模式长事务管理

**核心概念**:
- **CompensableAction**: 可补偿动作记录
- **SAGA**: 将长事务分解为一系列可补偿的子任务
- **正向执行**: 按顺序执行所有子任务
- **反向补偿**: 任一任务失败时，逆序执行已完成任务的补偿操作

**执行流程示例**:
```
正向执行:
T1 (预订酒店) → T2 (预订机票) → T3 (租车) ✗ 失败

反向补偿:
补偿 T2 (取消机票) → 补偿 T1 (取消酒店)
```

**补偿策略配置**:
```yaml
compensation:
  retry_policy:
    max_retries: 3
    backoff_multiplier: 2
    initial_delay_ms: 1000
  human_intervention:
    enabled: true
    queue_name: "manual_compensation_queue"
    timeout_hours: 24
```

### 4.4 TraceabilityTracer - 责任链追踪器

**职责**: 全链路执行追踪

**TraceID 生成规则**:
```
{session_id}_{timestamp_ms}_{random_6chars}
例：sess_abc123_1710123456789_xyz789
```

**Span 数据结构**:
```python
@dataclass
class TraceSpan:
    span_id: str                    # Span 唯一标识
    parent_span_id: Optional[str]   # 父 Span ID（根节点为 None）
    task_id: str                    # 关联任务 ID
    agent_id: Optional[str]         # 执行 Agent ID
    start_time: float               # 开始时间戳（秒）
    end_time: Optional[float]       # 结束时间戳
    status: str                     # pending/running/success/failure
    error: Optional[str]            # 错误信息
    input_summary: Optional[str]    # 输入摘要
    output_summary: Optional[str]   # 输出摘要
    metadata: dict                  # 额外元数据
```

**追踪日志格式**:
```json
{
  "trace_id": "abc-123-def",
  "span_id": "span-001",
  "parent_span_id": null,
  "task_id": "task-001",
  "agent_id": "agent-pm-001",
  "start_time": 1710123456.789,
  "end_time": 1710123458.123,
  "status": "success",
  "input_summary": "用户需求：开发待办事项应用",
  "output_summary": "生成需求文档 requirements.md",
  "duration_ms": 1334,
  "token_usage": {"input": 150, "output": 800}
}
```

---

## 5. 记忆与进化层设计

### 5.1 MemoryRovol - 多层记忆系统

**三层架构**:
```
┌─────────────────────────────────────┐
│   Pattern Layer (模式层)            │  ← 高频访问
│   - 行为模式、决策规则、最佳实践    │
│   - 保留周期：永久（除非主动遗忘）  │
└─────────────────┬───────────────────┘
                  │ 抽象概括
┌─────────────────▼───────────────────┐
│   Feature Layer (特征层)            │  ← 中频访问
│   - 语义特征、关联关系、统计信息    │
│   - 保留周期：30 天（可延长）        │
└─────────────────┬───────────────────┘
                  │ 特征提取
┌─────────────────▼───────────────────┐
│   Raw Volume (原始层)               │  ← 低频访问
│   - 原始对话、执行日志、观测数据    │
│   - 保留周期：7 天（自动清理）       │
└─────────────────────────────────────┘
```

**记忆记录结构**:
```python
@dataclass
class MemoryRecord:
    record_id: str              # 记忆 ID
    layer: str                  # raw/feature/pattern
    content: Any                # 记忆内容
    embedding: List[float]      # 向量嵌入
    importance_score: float     # 重要性评分 (0-1)
    access_count: int           # 访问次数
    last_accessed: float        # 最后访问时间戳
    created_at: float           # 创建时间戳
    expires_at: Optional[float] # 过期时间戳
    tags: List[str]             # 标签列表
    metadata: dict              # 元数据
```

### 5.2 WorldModel - 世界模型

**职责**: 维护和更新系统对世界的认知

#### SemanticSlicer - 语义切片器

**切片策略**:
- **基础大小**: 512 tokens
- **重叠区域**: 50 tokens（避免语义断裂）
- **最小块**: 100 tokens（过小块合并到相邻块）
- **边界检测**: 优先在段落、句子边界切割

**重要性评分算法**:
```python
def calculate_importance(chunk: SemanticChunk) -> float:
    score = 1.0
    
    # 错误/失败内容权重更高
    if contains_error(chunk):
        score *= 1.5
    
    # 开头内容更重要（首因效应）
    if is_in_beginning(chunk):
        score *= 1.2
    
    # 包含关键实体（人名、地名、术语）
    if contains_key_entities(chunk):
        score *= 1.3
    
    return min(score, 3.0)  # 上限 3.0
```

#### TemporalAligner - 时间对齐器

**职责**: 解决多 Agent 事件流的时间不一致问题

**不一致类型检测**:
1. **因果倒置**: 子事件时间戳早于父事件
2. **未来事件**: 时间戳晚于当前时间 + 时钟漂移阈值
3. **过度延迟**: 事件产生时间与上报时间差异过大

**时钟漂移校准**:
```python
def detect_clock_drift(agent_id: str, reference_timestamp: float) -> float:
    """
    通过与参考时间戳对比，计算 Agent 的时钟漂移
    返回漂移值（秒），正数表示 Agent 时钟快，负数表示慢
    """
    agent_events = get_recent_events(agent_id, limit=10)
    reference_events = get_reference_events(limit=10)
    
    # 匹配相同事件，计算时间差平均值
    time_diffs = []
    for agent_event in agent_events:
        matching_ref = find_matching_event(agent_event, reference_events)
        if matching_ref:
            diff = agent_event.timestamp - matching_ref.timestamp
            time_diffs.append(diff)
    
    return statistics.mean(time_diffs) if time_diffs else 0.0
```

#### DriftDetector - 认知漂移检测器

**职责**: 检测不同 Agent 对同一事实的理解偏差

**漂移计算**:
- **数值类型**: 相对差异百分比
  ```python
  drift = abs(value1 - value2) / max(abs(value1), abs(value2))
  ```
- **字符串**: Jaccard 相似度
  ```python
  similarity = len(set1 ∩ set2) / len(set1 ∪ set2)
  drift = 1 - similarity
  ```
- **布尔/集合**: 直接比较差异

**漂移解决策略**:
1. **多数投票**: 选择超过 50% Agent 认同的值
2. **加权平均**: 根据 Agent 信任度加权
3. **置信度优先**: 选择平均置信度最高的值
4. **人工仲裁**: 无法自动解决时加入人工队列

### 5.3 Consensus - 共识机制

#### QuorumFast - 快速法定决策

**核心思想**: 不等待所有参与者，达到法定比例即推进决策

**配置参数**:
```yaml
quorum_fast:
  quorum_ratio: 0.6          # 60% 完成即可决策
  timeout_ms: 5000           # 5 秒超时
  min_participants: 3        # 最少参与人数
```

**决策流程**:
```
1. 发起决策请求给所有参与者
2. 启动定时器（timeout_ms）
3. 收集响应，实时更新完成率
4. 如果 completion_rate >= quorum_ratio:
   - 立即返回已收集的结果
5. 如果超时且未达到法定比例:
   - 返回已收集的结果 + 超时标记
6. 如果所有参与者都响应:
   - 正常返回全部结果
```

#### StabilityWindow - 稳定性窗口

**职责**: 防止频繁变更决策

**工作原理**:
- 维护一个滑动时间窗口（默认 5 分钟）
- 记录窗口内的所有决策变更
- 如果变更频率超过阈值（如 3 次/分钟），触发稳定化措施：
  - 延长决策确认时间
  - 要求更高的共识比例
  - 暂停自动决策，转人工审核

### 5.4 Committees - 进化委员会

**四大委员会职责**:

#### CoordinationCommittee - 协调委员会
- **职责**: 流程优化、瓶颈分析、协作效率提升
- **分析维度**:
  - 各阶段耗时统计
  - 任务排队长度趋势
  - Agent 利用率分析
- **输出建议**:
  - 资源调配建议（增加/减少某类 Agent）
  - 流程优化建议（并行化、裁剪冗余步骤）

#### TechnicalCommittee - 技术委员会
- **职责**: 技术规范更新、最佳实践提炼
- **工作内容**:
  - 分析成功任务的共性特征
  - 识别反模式和常见错误
  - 更新编码规范和设计模式库
- **输出产物**:
  - 技术规范更新提案
  - 最佳实践文档
  - 反模式警示列表

#### AuditCommittee - 审计委员会
- **职责**: 合规审计、风险评估
- **审计范围**:
  - 权限使用合规性
  - 数据安全与隐私保护
  - 资源使用合理性
- **风险检测**:
  - 异常高频的工具调用
  - 越权访问尝试
  - 资源滥用行为

#### TeamCommittee - 团队委员会
- **职责**: 团队协作规则制定
- **工作焦点**:
  - Agent 间通信协议优化
  - 冲突解决机制改进
  - 知识共享策略
- **产出成果**:
  - 协作规则更新
  - 沟通模板标准化
  - 知识图谱构建

---

## 6. 运行时管理

### 6.1 AppServer - 应用服务器

**职责**: 启动和管理所有运行时组件

**启动流程**:
```python
async def start(self):
    # 1. 初始化配置
    self.config = load_config()
    
    # 2. 创建核心组件
    self.session_manager = SessionManager(self.config)
    self.health_checker = HealthChecker(self.config)
    
    # 3. 注册网关
    if self.config.get('http_enabled'):
        http_gw = HTTPGateway(self.config)
        self.register_gateway('http', http_gw)
    
    if self.config.get('websocket_enabled'):
        ws_gw = WebSocketGateway(self.config)
        self.register_gateway('websocket', ws_gw)
    
    if self.config.get('stdio_enabled'):
        stdio_gw = StdioGateway(self.config)
        self.register_gateway('stdio', stdio_gw)
    
    # 4. 启动后台任务
    self.start_health_check_loop()
    self.start_session_cleanup_loop()
    
    # 5. 启动所有网关
    await asyncio.gather(*[gw.start() for gw in self.gateways.values()])
```

### 6.2 SessionManager - 会话管理器

**会话生命周期**:
```
创建 → 活跃 → (可选：挂起) → 恢复 → 销毁
  │                              ↑
  └──────────── 超时 ────────────┘
```

**会话状态**:
- **ACTIVE**: 活跃状态，可处理请求
- **SUSPENDED**: 挂起状态，保留上下文但暂停处理
- **EXPIRED**: 过期状态，等待清理
- **TERMINATED**: 已终止，资源已释放

**清理策略**:
```yaml
session:
  timeout_seconds: 3600       # 1 小时无操作自动过期
  cleanup_interval_seconds: 300  # 每 5 分钟清理一次
  max_sessions_per_user: 10   # 单用户最大会话数
  suspend_idle_after: 600     # 空闲 10 分钟后挂起
```

### 6.3 Gateway - 网关层

#### HTTPGateway - HTTP 网关

**路由表**:
| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/api/v1/process` | 处理请求 |
| GET | `/api/v1/session/{session_id}` | 获取会话状态 |
| DELETE | `/api/v1/session/{session_id}` | 删除会话 |
| GET | `/health` | 健康检查 |
| GET | `/metrics` | Prometheus 指标 |

**请求格式**:
```json
POST /api/v1/process
{
  "jsonrpc": "2.0",
  "method": "process",
  "params": {
    "input": "帮我开发一个待办事项应用",
    "context": {
      "user_id": "user_123",
      "project_id": "proj_456"
    }
  },
  "id": "req_789"
}
```

**响应格式**:
```json
{
  "jsonrpc": "2.0",
  "result": {
    "session_id": "sess_abc123",
    "output": "已为您生成待办事项应用...",
    "trace_id": "trace_xyz789"
  },
  "id": "req_789"
}
```

#### WebSocketGateway - WebSocket 网关

**消息类型**:
- `REQUEST`: 客户端请求
- `RESPONSE`: 服务端响应
- `STREAM_CHUNK`: 流式输出片段
- `PROGRESS_UPDATE`: 进度更新
- `ERROR`: 错误通知

**连接生命周期**:
```
连接建立 → 握手验证 → 心跳保活 → 消息收发 → 连接关闭
```

**心跳配置**:
```yaml
websocket:
  ping_interval_seconds: 30
  pong_timeout_seconds: 10
  max_message_size_bytes: 1048576  # 1MB
```

#### StdioGateway - 标准输入输出网关

**用途**: CLI 工具集成和本地调试

**输入格式** (JSON Lines):
```
{"jsonrpc":"2.0","method":"process","params":{"input":"..."},"id":"1"}
{"jsonrpc":"2.0","method":"process","params":{"input":"..."},"id":"2"}
```

**输出格式**:
```
{"jsonrpc":"2.0","result":{...},"id":"1"}
{"jsonrpc":"2.0","result":{...},"id":"2"}
```

### 6.4 Protocol - 协议层

#### JsonRpcProtocol - JSON-RPC 2.0 实现

**消息格式规范**:
```python
# 请求
{
  "jsonrpc": "2.0",
  "method": "process",
  "params": {...},  # 可选
  "id": "unique_id"
}

# 成功响应
{
  "jsonrpc": "2.0",
  "result": {...},
  "id": "unique_id"
}

# 错误响应
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32600,
    "message": "Invalid Request",
    "data": {...}  # 可选
  },
  "id": "unique_id"
}
```

**错误码定义**:
| 错误码 | 含义 |
|--------|------|
| -32700 | Parse error (解析错误) |
| -32600 | Invalid Request (无效请求) |
| -32601 | Method not found (方法不存在) |
| -32602 | Invalid params (参数错误) |
| -32603 | Internal error (内部错误) |
| -32000 ~ -32099 | 保留给服务器自定义错误 |

### 6.5 Telemetry - 可观测性

#### MetricsCollector - 指标收集器

**Prometheus 指标定义**:
```python
# 请求指标
request_count = Counter(
    'agentos_requests_total',
    'Total number of requests',
    ['gateway', 'method', 'status']
)

request_duration = Histogram(
    'agentos_request_duration_seconds',
    'Request duration in seconds',
    ['gateway', 'method'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 5.0, 10.0, 30.0, 60.0]
)

# 会话指标
active_sessions = Gauge(
    'agentos_active_sessions',
    'Number of active sessions'
)

# Token 指标
token_usage = Counter(
    'agentos_token_usage_total',
    'Total token usage',
    ['model', 'type']  # type: input/output
)
```

#### Tracing - 分布式追踪

**OpenTelemetry 集成**:
```python
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

def setup_tracing(otel_endpoint: str):
    provider = TracerProvider()
    processor = BatchSpanProcessor(
        OTLPSpanExporter(endpoint=otel_endpoint)
    )
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)
```

**Span 属性约定**:
```python
span.set_attribute('agentos.session_id', session_id)
span.set_attribute('agentos.task_id', task_id)
span.set_attribute('agentos.agent_id', agent_id)
span.set_attribute('agentos.trace_id', trace_id)
span.set_attribute('token.usage.input', input_tokens)
span.set_attribute('token.usage.output', output_tokens)
```

---

## 7. 安全隔离层

### 7.1 VirtualWorkbench - 虚拟工位

**职责**: 为每个 Agent 提供独立的沙箱环境

**沙箱特性**:
- **文件系统隔离**: 每个 Workbench 有独立的临时目录
- **进程隔离**: 子进程在独立的用户命名空间运行
- **网络隔离**: 可选的网络访问控制（白名单）
- **资源限制**: CPU、内存、磁盘配额

**资源配置示例**:
```yaml
virtual_workbench:
  resource_limits:
    cpu_cores: 2
    memory_mb: 1024
    disk_mb: 512
    timeout_seconds: 300
  allowed_commands:
    - python
    - node
    - npm
    - pip
  forbidden_paths:
    - /etc
    - /home
    - /root
  network_policy:
    enabled: true
    allowed_hosts:
      - api.openai.com
      - api.anthropic.com
```

### 7.2 PermissionEngine - 权限裁决引擎

**权限模型**:
```
Subject (Agent) → Action (操作) → Resource (资源) → Effect (效果)
```

**规则匹配算法**:
```python
def check_permission(self, agent_id: str, resource: str, action: str) -> PermissionAction:
    # 按优先级排序规则（具体规则优先）
    sorted_rules = sorted(
        self.rules,
        key=lambda r: (r.specificity, r.priority),
        reverse=True
    )
    
    for rule in sorted_rules:
        if rule.matches(agent_id, resource, action):
            return rule.effect
    
    # 默认拒绝
    return PermissionAction.DENY
```

**规则示例**:
```yaml
permissions:
  rules:
    - name: "allow_temp_file_read"
      resource_pattern: "file:/tmp/agentos/*"
      action: "read"
      effect: "allow"
    
    - name: "deny_etc_access"
      resource_pattern: "file:/etc/*"
      action: "*"
      effect: "deny"
    
    - name: "prompt_execute"
      resource_pattern: "*"
      action: "execute"
      effect: "prompt"
```

### 7.3 ToolAudit - 工具审计

**审计记录结构**:
```python
@dataclass
class AuditRecord:
    record_id: str
    agent_id: str
    tool_name: str
    input_data: dict
    result: dict
    success: bool
    error: Optional[str]
    timestamp: float
    trace_id: str
    permission_granted: bool
    permission_check_id: str
    duration_ms: float
    resource_usage: dict  # CPU, memory, etc.
```

**异常检测规则**:
```yaml
anomaly_detection:
  rules:
    - name: "high_frequency_calls"
      condition: "count(tool_calls) > 100 within 60s"
      severity: "warning"
      action: "throttle"
    
    - name: "forbidden_resource_access"
      condition: "resource matches '/etc/*'"
      severity: "critical"
      action: "block_and_alert"
    
    - name: "long_running_command"
      condition: "duration > 300s"
      severity: "warning"
      action: "terminate"
```

---

## 8. 技术栈与依赖

### 8.1 核心技术栈

| 类别 | 技术 | 版本 | 用途 |
|------|------|------|------|
| **编程语言** | Python | 3.10+ | 主要开发语言 |
| **异步框架** | asyncio | built-in | 异步编程 |
| **HTTP 服务** | FastAPI | 0.100+ | RESTful API |
| **WebSocket** | websockets | 11.0+ | 实时通信 |
| **序列化** | pydantic | 2.0+ | 数据验证 |
| **日志** | structlog | 23.0+ | 结构化日志 |
| **监控** | prometheus-client | 0.17+ | 指标收集 |
| **追踪** | opentelemetry | 1.18+ | 分布式追踪 |

### 8.2 AI 相关依赖

| 依赖 | 版本 | 用途 |
|------|------|------|
| tiktoken | 0.4+ | Token 计数 |
| langchain | 0.0.300+ | LLM 抽象层 |
| sentence-transformers | 2.2+ | Embedding 生成 |
| faiss-cpu | 1.7+ | 向量检索 |

### 8.3 执行单元依赖

| 依赖 | 版本 | 用途 |
|------|------|------|
| playwright | 1.35+ | 浏览器自动化 |
| sqlalchemy | 2.0+ | 数据库 ORM |
| requests | 2.31+ | HTTP 客户端 |
| aiohttp | 3.8+ | 异步 HTTP |

### 8.4 安全相关依赖

| 依赖 | 版本 | 用途 |
|------|------|------|
| bleach | 6.0+ | HTML 清理 |
| python-jose | 3.3+ | JWT 处理 |
| passlib | 1.7+ | 密码哈希 |

---

## 9. 性能指标

### 9.1 基准测试

**测试环境**:
- CPU: Intel Xeon E5-2680 v4 (14 核 28 线程)
- 内存：64GB DDR4
- 存储：NVMe SSD 1TB
- 网络：1Gbps

**测试结果**:

| 场景 | 并发数 | P50 延迟 | P95 延迟 | P99 延迟 | 吞吐量 |
|------|--------|----------|----------|----------|--------|
| 简单任务 (Router only) | 100 | 15ms | 45ms | 120ms | 6500 req/s |
| 中等任务 (含规划) | 50 | 250ms | 800ms | 1.5s | 180 req/s |
| 复杂任务 (完整流程) | 10 | 2.5s | 8s | 15s | 36 req/s |
| 记忆检索 | 100 | 8ms | 25ms | 60ms | 12000 req/s |
| 向量相似度搜索 | 100 | 12ms | 35ms | 80ms | 8000 req/s |

### 9.2 资源消耗

**单实例资源占用**:
- **基础内存**: ~500MB (空载)
- **活跃会话**: ~50MB/会话
- **Agent 缓存**: ~100MB/缓存 Agent
- **向量索引**: ~200MB (10 万条记忆)

**推荐配置**:
- **开发环境**: 4 核 8GB
- **生产环境**: 16 核 32GB (支持 100+ 并发)
- **高负载环境**: 32 核 64GB (支持 500+ 并发)

### 9.3 扩展性

**水平扩展策略**:
1. **网关层**: 多实例 + 负载均衡 (Nginx/HAProxy)
2. **认知层**: 无状态设计，可任意扩缩容
3. **行动层**: AgentPool 支持分布式部署
4. **记忆层**: 向量数据库集群 (Milvus/Weaviate)

**扩展极限测试**:
- 单集群最大支持：10,000+ 并发会话
- 记忆容量：1 亿+ 条记忆记录
- 向量检索延迟：< 100ms (P99)

---

## 10. 扩展性设计

### 10.1 插件化架构

**执行单元扩展**:
```python
# 自定义执行单元示例
class CustomUnit(ExecutionUnit):
    async def execute(self, input_data: dict) -> dict:
        # 实现自定义逻辑
        return {"result": "custom"}
    
    def get_input_schema(self) -> dict:
        return {"type": "object", "properties": {...}}

# 注册到系统
agent_pool.register_unit_type("custom", CustomUnit)
```

**Agent 角色扩展**:
```yaml
# 配置文件中定义新角色
agent_roles:
  data_scientist:
    description: "数据科学家"
    skills:
      - pandas
      - numpy
      - scikit-learn
    tools:
      - jupyter
      - matplotlib
    permissions:
      - "file:/data/*:read"
      - "exec:python:*"
```

### 10.2 记忆存储扩展

**支持的存储后端**:
- **内置**: SQLite (开发/测试)
- **生产**: PostgreSQL + pgvector
- **大规模**: Milvus / Weaviate / Pinecone

**配置切换**:
```yaml
memory_storage:
  backend: "postgresql"  # sqlite | postgresql | milvus
  connection:
    host: localhost
    port: 5432
    database: agentos_memory
    user: agentos
    password: ${DB_PASSWORD}
```

### 10.3 模型适配器扩展

**支持的模型提供商**:
- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude 系列)
- Google (PaLM, Gemini)
- 自部署模型 (vLLM, TGI)

**添加新模型**:
```python
class CustomModelAdapter(BaseModelAdapter):
    def __init__(self, config: dict):
        self.api_key = config['api_key']
        self.endpoint = config['endpoint']
    
    async def generate(self, prompt: str, **kwargs) -> str:
        # 实现自定义模型调用逻辑
        pass
```

### 10.4 网关协议扩展

**自定义网关示例**:
```python
class GRPCGateway(BaseGateway):
    async def start(self):
        # 启动 gRPC 服务器
        self.server = grpc.server(...)
        self.server.start()
    
    async def handle_request(self, request: dict) -> dict:
        # 处理 gRPC 请求
        pass
```

---

## 附录

### A. 术语表

| 术语 | 英文 | 定义 |
|------|------|------|
| 意图 | Intent | 用户请求的结构化表示 |
| 任务 DAG | Task DAG | 有向无环图表示的任务依赖关系 |
| TraceID | TraceID | 全链路追踪唯一标识符 |
| Span | Span | 追踪树中的一个节点 |
| SAGA | SAGA | 长事务分解为可补偿子事务的模式 |
| Quorum | Quorum | 法定多数决策机制 |
| Embedding | Embedding | 文本的向量表示 |

### B. 参考资料

1. [SAGA 模式详解](https://microservices.io/patterns/data/saga.html)
2. [OpenTelemetry 官方文档](https://opentelemetry.io/)
3. [Prometheus 最佳实践](https://prometheus.io/docs/practices/)
4. [JSON-RPC 2.0 规范](https://www.jsonrpc.org/specification)

### C. 版本历史

| 版本 | 日期 | 变更说明 |
|------|------|----------|
| v1.0.0 | 2026-03-11 | 初始版本，完整架构文档发布 |

---

**文档维护**: SpharxWorks Team  
**联系方式**: lidecheng@spharx.cn, wangliren@spharx.cn  
**项目地址**: https://github.com/spharx/spharxworks
