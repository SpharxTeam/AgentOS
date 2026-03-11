# AgentOS CoreLoopThree 核心组件 API 文档

**版本**: v1.0.0  
**最后更新**: 2026-03-11  
**语言**: Python 3.10+  

---

## 📋 目录

1. [认知层组件](#1-认知层组件)
   - [Router](#11-router)
   - [DualModelCoordinator](#12-dualmodelcoordinator)
   - [IncrementalPlanner](#13-incrementalplanner)
   - [Dispatcher](#14-dispatcher)
2. [行动层组件](#2-行动层组件)
   - [AgentPool](#21-agentpool)
   - [CompensationManager](#22-compensationmanager)
   - [TraceabilityTracer](#23-traceabilitytracer)
   - [ExecutionUnit](#24-executionunit)
3. [记忆与进化层组件](#3-记忆与进化层组件)
   - [MemoryRovol](#31-memoryrovol)
   - [WorldModel](#32-worldmodel)
   - [ConsensusEngine](#33-consensusengine)
4. [运行时组件](#4-运行时组件)
   - [AppServer](#41-appserver)
   - [SessionManager](#42-sessionmanager)
5. [安全组件](#5-安全组件)
   - [VirtualWorkbench](#51-virtualworkbench)
   - [PermissionEngine](#52-permissionengine)
6. [工具类](#6-工具类)
   - [TokenCounter](#61-tokencounter)
   - [CostEstimator](#62-costestimator)
   - [StructuredLogger](#63-structuredlogger)

---

## 1. 认知层组件

### 1.1 Router

**模块路径**: `agentos_cta.coreloopthree.cognition.router`

**职责**: 意图理解与资源匹配

#### 类定义

```python
class Router:
    """
    路由器：解析用户输入，匹配模型资源
    """
    
    def __init__(self, config: dict):
        """
        初始化路由器
        
        Args:
            config: 配置字典，包含复杂度阈值、模型路由规则等
        
        Example:
            >>> config = {
            ...     "complexity_thresholds": {
            ...         "simple": 1000,
            ...         "complex": 5000,
            ...         "critical": 5000
            ...     },
            ...     "models": [
            ...         {"name": "gpt-3.5-turbo", "context_window": 4096},
            ...         {"name": "gpt-4", "context_window": 8192}
            ...     ]
            ... }
            >>> router = Router(config)
        """
        pass
    
    async def parse_intent(self, raw_text: str, context: Optional[dict] = None) -> Intent:
        """
        将原始文本解析为结构化意图
        
        Args:
            raw_text: 用户原始输入文本
            context: 可选的上下文信息，包括用户 ID、历史对话等
        
        Returns:
            Intent: 结构化的意图对象
        
        Raises:
            ValueError: 当无法解析意图时
        
        Example:
            >>> intent = await router.parse_intent("帮我创建一个待办事项应用")
            >>> print(intent.goal)
            '创建待办事项应用'
            >>> print(intent.complexity)
            <ComplexityLevel.COMPLEX: 'complex'>
        """
        pass
    
    def match_resource(self, intent: Intent) -> ResourceMatch:
        """
        根据意图匹配合适的资源
        
        Args:
            intent: 已解析的意图对象
        
        Returns:
            ResourceMatch: 资源匹配结果，包含模型选择和 Token 预算
        
        Example:
            >>> resource = router.match_resource(intent)
            >>> print(resource.model_name)
            'gpt-4'
            >>> print(resource.token_budget)
            4000
        """
        pass
    
    def estimate_complexity(self, text: str) -> ComplexityLevel:
        """
        评估文本的复杂度等级
        
        Args:
            text: 输入文本
        
        Returns:
            ComplexityLevel: 复杂度等级 (SIMPLE/COMPLEX/CRITICAL)
        
        Example:
            >>> complexity = router.estimate_complexity("你好")
            >>> print(complexity)
            <ComplexityLevel.SIMPLE: 'simple'>
        """
        pass
```

#### 数据模型

```python
@dataclass
class Intent:
    """
    意图数据结构
    """
    raw_text: str                          # 原始输入文本
    goal: str                              # 目标描述
    constraints: List[str]                 # 约束条件列表
    context: dict                          # 上下文信息
    complexity: ComplexityLevel            # 复杂度等级
    estimated_tokens: int                  # 预估 Token 数量
    required_tools: List[str]              # 需要的工具列表
    metadata: dict = field(default_factory=dict)  # 额外元数据


class ComplexityLevel(str, Enum):
    """复杂度等级枚举"""
    SIMPLE = "simple"          # 简单任务：< 1000 tokens
    COMPLEX = "complex"        # 中等任务：1000-5000 tokens
    CRITICAL = "critical"      # 关键任务：> 5000 tokens


@dataclass
class ResourceMatch:
    """
    资源匹配结果
    """
    model_name: str            # 推荐的模型名称
    token_budget: int          # Token 预算上限
    confidence: float          # 匹配置信度 (0-1)
    reasoning: str             # 选择理由
    fallback_models: List[str] = field(default_factory=list)  # 备选模型列表
```

---

### 1.2 DualModelCoordinator

**模块路径**: `agentos_cta.coreloopthree.cognition.dual_model_coordinator`

**职责**: 多模型协同与交叉验证

#### 类定义

```python
class DualModelCoordinator:
    """
    双模型协同协调器：维护 1 个主思考者 + 2 个辅思考者
    """
    
    def __init__(
        self,
        primary_model: str,
        secondary_models: List[str],
        config: dict,
        consensus_threshold: float = 0.6
    ):
        """
        初始化协调器
        
        Args:
            primary_model: 主模型名称（强推理能力）
            secondary_models: 辅模型列表（轻量/专业模型）
            config: 配置字典
            consensus_threshold: 一致性阈值 (0-1)，默认 0.6
        
        Example:
            >>> coordinator = DualModelCoordinator(
            ...     primary_model="gpt-4",
            ...     secondary_models=["gpt-3.5-turbo", "claude-3-sonnet"],
            ...     config={"max_retries": 3}
            ... )
        """
        pass
    
    async def generate_plan(
        self,
        intent: Intent,
        context: dict,
        timeout_ms: Optional[int] = None
    ) -> TaskPlan:
        """
        生成任务计划
        
        Args:
            intent: 意图对象
            context: 上下文信息
            timeout_ms: 可选的超时时间（毫秒）
        
        Returns:
            TaskPlan: 生成的任务计划
        
        Raises:
            ModelUnavailableError: 当所有模型都不可用时
            ConsensusError: 当无法达成共识时
        
        Example:
            >>> plan = await coordinator.generate_plan(intent, context={})
            >>> print(plan.plan_id)
            'plan_abc123'
            >>> print(len(plan.tasks))
            5
        """
        pass
    
    async def validate_plan(
        self,
        plan: TaskPlan,
        context: dict
    ) -> ValidationResult:
        """
        验证计划的可行性
        
        Args:
            plan: 待验证的计划
            context: 上下文信息
        
        Returns:
            ValidationResult: 验证结果
        
        Example:
            >>> result = await coordinator.validate_plan(plan, context={})
            >>> print(result.is_valid)
            True
            >>> print(result.suggestions)
            ['建议增加错误处理步骤']
        """
        pass
    
    async def _call_model(
        self,
        model_name: str,
        prompt: str,
        max_tokens: int = 2000
    ) -> Tuple[str, float, dict]:
        """
        调用单个模型（内部方法）
        
        Args:
            model_name: 模型名称
            prompt: 提示词
            max_tokens: 最大输出 Token 数
        
        Returns:
            Tuple[str, float, dict]: (响应文本，置信度，元数据)
        """
        pass
    
    def _check_consensus(
        self,
        primary_output: str,
        secondary_outputs: List[str]
    ) -> ConsensusResult:
        """
        检查多个模型输出的一致性（内部方法）
        
        Args:
            primary_output: 主模型输出
            secondary_outputs: 辅模型输出列表
        
        Returns:
            ConsensusResult: 一致性检查结果
        """
        pass
```

#### 数据模型

```python
@dataclass
class ValidationResult:
    """
    计划验证结果
    """
    is_valid: bool                        # 是否有效
    confidence: float                     # 置信度 (0-1)
    suggestions: List[str]                # 改进建议
    risks: List[str]                      # 潜在风险
    missing_steps: List[str]              # 缺失的步骤
    metadata: dict = field(default_factory=dict)


@dataclass
class ConsensusResult:
    """
    一致性检查结果
    """
    reached: bool                         # 是否达成共识
    similarity_score: float               # 相似度 (0-1)
    conflicts: List[Conflict]             # 冲突列表
    recommended_output: str               # 推荐的输出
    reasoning: str                        # 仲裁理由


@dataclass
class Conflict:
    """
    冲突详情
    """
    aspect: str                           # 冲突方面（如任务顺序、资源选择等）
    primary_value: str                    # 主模型的值
    conflicting_values: List[str]         # 冲突的值
    severity: str                         # 严重程度：low/medium/high
```

---

### 1.3 IncrementalPlanner

**模块路径**: `agentos_cta.coreloopthree.cognition.incremental_planner`

**职责**: 增量式任务 DAG 生成与调整

#### 类定义

```python
class IncrementalPlanner:
    """
    增量规划器：动态生成和调整任务 DAG
    """
    
    def __init__(self, config: dict):
        """
        初始化规划器
        
        Args:
            config: 配置字典
        
        Example:
            >>> config = {
            ...     "max_tasks_per_level": 10,
            ...     "max_depth": 5,
            ...     "enable_parallel": True
            ... }
            >>> planner = IncrementalPlanner(config)
        """
        pass
    
    def create_initial_plan(
        self,
        goal: str,
        context: dict,
        constraints: Optional[List[str]] = None
    ) -> TaskPlan:
        """
        创建初始计划
        
        Args:
            goal: 任务目标
            context: 上下文信息
            constraints: 可选的约束条件列表
        
        Returns:
            TaskPlan: 初始任务计划
        
        Example:
            >>> plan = planner.create_initial_plan(
            ...     goal="开发待办事项应用",
            ...     context={"user_id": "123"}
            ... )
        """
        pass
    
    def extend_plan(
        self,
        current_plan: TaskPlan,
        completed_tasks: List[TaskNode],
        feedback: dict
    ) -> TaskPlan:
        """
        扩展计划（添加新任务）
        
        Args:
            current_plan: 当前计划
            completed_tasks: 已完成的任务列表
            feedback: 执行反馈
        
        Returns:
            TaskPlan: 扩展后的计划
        
        Example:
            >>> extended = planner.extend_plan(
            ...     current_plan=plan,
            ...     completed_tasks=[task1, task2],
            ...     feedback={"status": "success"}
            ... )
        """
        pass
    
    def revise_plan(
        self,
        plan: TaskPlan,
        failed_task_id: str,
        reason: str,
        alternative_approach: Optional[str] = None
    ) -> TaskPlan:
        """
        修订计划（处理失败任务）
        
        Args:
            plan: 原计划
            failed_task_id: 失败任务 ID
            reason: 失败原因
            alternative_approach: 可选的替代方案
        
        Returns:
            TaskPlan: 修订后的计划
        
        Raises:
            ValueError: 当无法修订计划时
        
        Example:
            >>> revised = planner.revise_plan(
            ...     plan=plan,
            ...     failed_task_id="task_003",
            ...     reason="API 限流",
            ...     alternative_approach="使用备用 API"
            ... )
        """
        pass
    
    def get_critical_path(self, plan: TaskPlan) -> List[str]:
        """
        获取关键路径（最长依赖链）
        
        Args:
            plan: 任务计划
        
        Returns:
            List[str]: 关键路径上的任务 ID 列表
        
        Example:
            >>> critical = planner.get_critical_path(plan)
            >>> print(critical)
            ['task_001', 'task_002', 'task_005']
        """
        pass
    
    def get_parallel_groups(self, plan: TaskPlan) -> List[List[str]]:
        """
        获取可并行执行的任务组
        
        Args:
            plan: 任务计划
        
        Returns:
            List[List[str]]: 任务组列表，每组内任务可并行执行
        
        Example:
            >>> groups = planner.get_parallel_groups(plan)
            >>> print(groups)
            [['task_001'], ['task_002', 'task_003'], ['task_004']]
        """
        pass
```

#### 数据模型

```python
@dataclass
class TaskPlan:
    """
    任务计划数据结构
    """
    plan_id: str                           # 计划唯一 ID
    dag: TaskDAG                           # 任务 DAG
    created_at: float                      # 创建时间戳
    updated_at: float                      # 更新时间戳
    status: str                            # 状态：draft/active/completed/cancelled
    metadata: dict = field(default_factory=dict)
    
    def get_topological_order(self) -> List[str]:
        """返回任务的拓扑排序"""
        pass
    
    def get_predecessors(self, task_id: str) -> List[str]:
        """获取指定任务的前置任务"""
        pass
    
    def get_successors(self, task_id: str) -> List[str]:
        """获取指定任务的后继任务"""
        pass


@dataclass
class TaskDAG:
    """
    任务有向无环图
    """
    nodes: Dict[str, TaskNode]             # 任务节点字典 {task_id: TaskNode}
    entry_points: List[str]                # 入口任务列表（无前置依赖的任务）
    
    def add_node(self, node: TaskNode):
        """添加任务节点"""
        pass
    
    def add_edge(self, from_id: str, to_id: str):
        """添加依赖边"""
        pass
    
    def remove_node(self, task_id: str):
        """删除任务节点"""
        pass


@dataclass
class TaskNode:
    """
    任务节点
    """
    task_id: str                           # 任务 ID
    name: str                              # 任务名称
    description: str                       # 任务描述
    role: str                              # 执行角色（如 product_manager, developer）
    input_schema: dict                     # 输入数据 Schema
    output_schema: dict                    # 输出数据 Schema
    dependencies: List[str]                # 依赖的任务 ID 列表
    estimated_duration_ms: int             # 预估耗时（毫秒）
    priority: int = 0                      # 优先级（数字越大优先级越高）
    metadata: dict = field(default_factory=dict)
    
    def is_ready(self, completed_tasks: Set[str]) -> bool:
        """判断任务是否就绪（所有依赖已完成）"""
        pass
```

---

### 1.4 Dispatcher

**模块路径**: `agentos_cta.coreloopthree.cognition.dispatcher`

**职责**: Agent 选择与任务分发

#### 类定义

```python
class Dispatcher:
    """
    调度官：选择合适的 Agent 并分发任务
    """
    
    def __init__(
        self,
        registry_client: Any,
        config: dict,
        weights: Optional[Dict[str, float]] = None
    ):
        """
        初始化调度官
        
        Args:
            registry_client: Agent 注册中心客户端
            config: 配置字典
            weights: 评分权重配置，默认 {'cost': 0.3, 'performance': 0.4, 'trust': 0.3}
        
        Example:
            >>> dispatcher = Dispatcher(
            ...     registry_client=registry,
            ...     config={"max_retries": 3},
            ...     weights={'cost': 0.2, 'performance': 0.5, 'trust': 0.3}
            ... )
        """
        pass
    
    async def select_agent(
        self,
        task: TaskNode,
        context: dict,
        top_k: int = 1
    ) -> Union[AgentInfo, List[AgentInfo]]:
        """
        选择最适合的 Agent
        
        Args:
            task: 任务节点
            context: 上下文信息
            top_k: 返回前 K 个 Agent（用于冗余执行）
        
        Returns:
            AgentInfo 或 AgentInfo 列表
        
        Example:
            >>> agent = await dispatcher.select_agent(task, context={})
            >>> print(agent.agent_id)
            'agent_dev_001'
            >>> print(agent.score)
            0.92
        """
        pass
    
    async def dispatch_task(
        self,
        task: TaskNode,
        agent: AgentInfo,
        context: dict,
        timeout_ms: Optional[int] = None
    ) -> TaskResult:
        """
        分发任务给指定 Agent
        
        Args:
            task: 任务节点
            agent: Agent 信息
            context: 上下文信息
            timeout_ms: 超时时间（毫秒）
        
        Returns:
            TaskResult: 任务执行结果
        
        Raises:
            AgentUnavailableError: 当 Agent 不可用时
            TaskTimeoutError: 当任务超时时
        
        Example:
            >>> result = await dispatcher.dispatch_task(task, agent, context={})
            >>> print(result.status)
            'success'
            >>> print(result.output)
            {'code': '...'}
        """
        pass
    
    async def dispatch_plan(
        self,
        plan: TaskPlan,
        context: dict,
        parallel_limit: int = 5
    ) -> PlanResult:
        """
        分发整个计划
        
        Args:
            plan: 任务计划
            context: 上下文信息
            parallel_limit: 最大并行执行数
        
        Returns:
            PlanResult: 计划执行结果
        
        Example:
            >>> plan_result = await dispatcher.dispatch_plan(plan, context={})
            >>> print(plan_result.status)
            'completed'
            >>> print(plan_result.task_results)
            {...}
        """
        pass
    
    def calculate_agent_score(
        self,
        agent: AgentInfo,
        task: TaskNode
    ) -> float:
        """
        计算 Agent 评分
        
        Args:
            agent: Agent 信息
            task: 任务节点
        
        Returns:
            float: 综合评分 (0-1)
        
        Example:
            >>> score = dispatcher.calculate_agent_score(agent, task)
            >>> print(f"{score:.2f}")
            0.85
        """
        pass
```

#### 数据模型

```python
@dataclass
class AgentInfo:
    """
    Agent 信息
    """
    agent_id: str                          # Agent 唯一 ID
    role: str                              # 角色类型
    skills: List[str]                      # 技能列表
    status: str                            # 状态：available/busy/offline
    performance_metrics: dict              # 性能指标
    trust_level: float                     # 信任度 (0-1)
    cost_per_task: float                   # 单次任务成本
    load: float                            # 当前负载 (0-1)
    metadata: dict = field(default_factory=dict)
    
    @property
    def success_rate(self) -> float:
        """获取历史成功率"""
        return self.performance_metrics.get('success_rate', 0.0)


@dataclass
class TaskResult:
    """
    任务执行结果
    """
    task_id: str                           # 任务 ID
    agent_id: str                          # 执行 Agent ID
    status: str                            # 状态：success/failure/timeout/cancelled
    output: Any                            # 输出数据
    error: Optional[str]                   # 错误信息
    duration_ms: int                       # 实际耗时（毫秒）
    token_usage: dict                      # Token 使用量
    timestamp: float                       # 时间戳


@dataclass
class PlanResult:
    """
    计划执行结果
    """
    plan_id: str                           # 计划 ID
    status: str                            # 状态：completed/failed/partially_completed
    task_results: Dict[str, TaskResult]    # 任务结果字典
    total_duration_ms: int                 # 总耗时
    total_token_usage: dict                # 总 Token 使用量
    summary: str                           # 执行摘要
```

---

## 2. 行动层组件

### 2.1 AgentPool

**模块路径**: `agentos_cta.coreloopthree.execution.agent_pool`

**职责**: Agent 实例管理

#### 类定义

```python
class AgentPool:
    """
    Agent 池：管理 Agent 实例的生命周期
    """
    
    def __init__(self, registry_client: Any, config: dict):
        """
        初始化 Agent 池
        
        Args:
            registry_client: Agent 注册中心客户端
            config: 配置字典
        
        Example:
            >>> config = {
            ...     "max_cached_agents": 100,
            ...     "idle_timeout_seconds": 1800,
            ...     "health_check_interval": 60
            ... }
            >>> pool = AgentPool(registry_client, config)
        """
        pass
    
    async def get_agent(self, agent_id: str) -> BaseAgent:
        """
        获取 Agent 实例
        
        Args:
            agent_id: Agent 唯一 ID
        
        Returns:
            BaseAgent: Agent 实例
        
        Raises:
            AgentNotFoundError: 当 Agent 不存在时
            AgentInitializationError: 当初始化失败时
        
        Example:
            >>> agent = await pool.get_agent("agent_dev_001")
            >>> result = await agent.execute(task)
        """
        pass
    
    async def release_agent(self, agent_id: str):
        """
        释放 Agent 实例（返回到池中）
        
        Args:
            agent_id: Agent 唯一 ID
        
        Example:
            >>> await pool.release_agent("agent_dev_001")
        """
        pass
    
    async def warmup_agents(self, role_list: List[str]):
        """
        预热 Agent（预先加载到缓存）
        
        Args:
            role_list: 需要预热的角色列表
        
        Example:
            >>> await pool.warmup_agents(["product_manager", "architect"])
        """
        pass
    
    def get_cache_stats(self) -> dict:
        """
        获取缓存统计信息
        
        Returns:
            dict: 统计信息
        
        Example:
            >>> stats = pool.get_cache_stats()
            >>> print(stats)
            {'cached_count': 45, 'hit_rate': 0.85, 'miss_count': 12}
        """
        pass
    
    async def health_check(self) -> Dict[str, bool]:
        """
        健康检查
        
        Returns:
            Dict[str, bool]: Agent ID 到健康状态的映射
        
        Example:
            >>> health = await pool.health_check()
            >>> print(health)
            {'agent_001': True, 'agent_002': False}
        """
        pass
```

---

### 2.2 CompensationManager

**模块路径**: `agentos_cta.coreloopthree.execution.compensation_manager`

**职责**: SAGA 模式事务管理

#### 类定义

```python
class CompensationManager:
    """
    补偿事务管理器：实现 SAGA 模式
    """
    
    def __init__(self, config: dict):
        """
        初始化补偿管理器
        
        Args:
            config: 配置字典
        
        Example:
            >>> config = {
            ...     "retry_policy": {
            ...         "max_retries": 3,
            ...         "backoff_multiplier": 2
            ...     },
            ...     "human_intervention": {
            ...         "enabled": True,
            ...         "timeout_hours": 24
            ...     }
            ... }
            >>> comp_mgr = CompensationManager(config)
        """
        pass
    
    async def register_action(
        self,
        action_id: str,
        task_id: str,
        unit_id: str,
        input_data: dict,
        result: dict,
        compensator_id: str
    ):
        """
        注册可补偿动作
        
        Args:
            action_id: 动作唯一 ID
            task_id: 关联任务 ID
            unit_id: 执行单元 ID
            input_data: 输入数据
            result: 执行结果
            compensator_id: 补偿器 ID
        
        Example:
            >>> await comp_mgr.register_action(
            ...     action_id="act_001",
            ...     task_id="task_001",
            ...     unit_id="file_unit",
            ...     input_data={"path": "/tmp/test.txt"},
            ...     result={"success": True},
            ...     compensator_id="file_delete"
            ... )
        """
        pass
    
    async def compensate(self, action_id: str) -> bool:
        """
        执行补偿操作
        
        Args:
            action_id: 动作 ID
        
        Returns:
            bool: 补偿是否成功
        
        Raises:
            CompensationError: 当补偿失败时
        
        Example:
            >>> success = await comp_mgr.compensate("act_001")
        """
        pass
    
    async def compensate_sequence(
        self,
        action_ids: List[str]
    ) -> CompensationReport:
        """
        按逆序补偿一系列动作
        
        Args:
            action_ids: 动作 ID 列表（按执行顺序）
        
        Returns:
            CompensationReport: 补偿报告
        
        Example:
            >>> report = await comp_mgr.compensate_sequence(
            ...     ["act_001", "act_002", "act_003"]
            ... )
            >>> print(report.successful)
            ['act_003', 'act_002']
            >>> print(report.failed)
            ['act_001']
        """
        pass
    
    async def add_to_human_queue(
        self,
        action_id: str,
        reason: str,
        priority: int = 0
    ):
        """
        加入人工介入队列
        
        Args:
            action_id: 动作 ID
            reason: 需要人工介入的原因
            priority: 优先级
        
        Example:
            >>> await comp_mgr.add_to_human_queue(
            ...     "act_001",
            ...     "不可自动补偿的操作",
            ...     priority=1
            ... )
        """
        pass
```

#### 数据模型

```python
@dataclass
class CompensableAction:
    """
    可补偿动作记录
    """
    action_id: str
    task_id: str
    unit_id: str
    input_data: dict
    result: dict
    compensator_id: str
    registered_at: float
    compensated: bool = False
    compensation_result: Optional[dict] = None


@dataclass
class CompensationReport:
    """
    补偿执行报告
    """
    saga_id: str                           # SAGA ID
    total_actions: int                     # 总动作数
    successful: List[str]                  # 成功的补偿 ID 列表
    failed: List[str]                      # 失败的补偿 ID 列表
    human_intervention: List[str]          # 需要人工介入的 ID 列表
    duration_ms: int                       # 总耗时
    status: str                            # 状态：completed/failed/partial
```

---

### 2.3 TraceabilityTracer

**模块路径**: `agentos_cta.coreloopthree.execution.traceability_tracer`

**职责**: 全链路追踪

#### 类定义

```python
class TraceabilityTracer:
    """
    责任链追踪器：管理 TraceID 和 Span
    """
    
    def __init__(self, config: dict):
        """
        初始化追踪器
        
        Args:
            config: 配置字典
        
        Example:
            >>> config = {
            ...     "log_dir": "data/logs/traces",
            ...     "enable_json_logging": True,
            ...     "retention_days": 7
            ... }
            >>> tracer = TraceabilityTracer(config)
        """
        pass
    
    def start_span(
        self,
        task_id: str,
        agent_id: Optional[str] = None,
        input_summary: Optional[str] = None,
        parent_span_id: Optional[str] = None
    ) -> str:
        """
        开始一个新的 Span
        
        Args:
            task_id: 任务 ID
            agent_id: Agent ID（可选）
            input_summary: 输入摘要（可选）
            parent_span_id: 父 Span ID（可选，用于嵌套追踪）
        
        Returns:
            str: Span ID
        
        Example:
            >>> span_id = tracer.start_span(
            ...     task_id="task_001",
            ...     agent_id="agent_pm_001",
            ...     input_summary="需求分析"
            ... )
        """
        pass
    
    def end_span(
        self,
        span_id: str,
        status: str,
        output_summary: Optional[str] = None,
        error: Optional[str] = None
    ):
        """
        结束一个 Span
        
        Args:
            span_id: Span ID
            status: 状态（pending/running/success/failure）
            output_summary: 输出摘要（可选）
            error: 错误信息（可选）
        
        Example:
            >>> tracer.end_span(
            ...     span_id="span_001",
            ...     status="success",
            ...     output_summary="生成需求文档"
            ... )
        """
        pass
    
    def dump_to_file(self, trace_id: Optional[str] = None):
        """
        将追踪日志持久化到文件
        
        Args:
            trace_id: 可选的 TraceID 过滤
        
        Example:
            >>> tracer.dump_to_file("trace_abc123")
        """
        pass
    
    def get_trace_tree(self, trace_id: str) -> List[TraceSpan]:
        """
        获取完整的追踪树（按父子关系排序）
        
        Args:
            trace_id: TraceID
        
        Returns:
            List[TraceSpan]: Span 列表（树形结构）
        
        Example:
            >>> tree = tracer.get_trace_tree("trace_abc123")
            >>> for span in tree:
            ...     print(f"{span.span_id}: {span.status}")
        """
        pass
    
    def get_current_trace_id(self) -> Optional[str]:
        """
        获取当前上下文的 TraceID
        
        Returns:
            Optional[str]: TraceID 或 None
        
        Example:
            >>> trace_id = tracer.get_current_trace_id()
        """
        pass
```

---

### 2.4 ExecutionUnit

**模块路径**: `agentos_cta.coreloopthree.execution.units.base_unit`

**职责**: 执行单元基类

#### 类定义

```python
class ExecutionUnit(ABC):
    """
    执行单元抽象基类
    """
    
    def __init__(self, config: dict):
        """
        初始化执行单元
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.unit_id = f"{self.__class__.__name__}_{uuid.uuid4().hex[:8]}"
    
    @abstractmethod
    async def execute(self, input_data: dict) -> dict:
        """
        执行单元核心逻辑
        
        Args:
            input_data: 输入数据
        
        Returns:
            dict: 执行结果
        
        Raises:
            ExecutionError: 当执行失败时
        """
        pass
    
    @abstractmethod
    def get_input_schema(self) -> dict:
        """
        返回输入数据的 JSON Schema
        
        Returns:
            dict: JSON Schema
        """
        pass
    
    @abstractmethod
    def get_output_schema(self) -> dict:
        """
        返回输出数据的 JSON Schema
        
        Returns:
            dict: JSON Schema
        """
        pass
    
    def validate_input(self, input_data: dict) -> Tuple[bool, Optional[str]]:
        """
        验证输入数据是否符合 Schema
        
        Args:
            input_data: 输入数据
        
        Returns:
            Tuple[bool, Optional[str]]: (是否有效，错误信息)
        
        Example:
            >>> is_valid, error = unit.validate_input(data)
            >>> if not is_valid:
            ...     print(f"Invalid input: {error}")
        """
        pass
    
    def compensate(self, input_data: dict, result: dict) -> Optional[dict]:
        """
        执行补偿操作（可选实现）
        
        Args:
            input_data: 原始输入数据
            result: 执行结果
        
        Returns:
            Optional[dict]: 补偿结果，None 表示不支持补偿
        """
        return None
```

#### 具体实现示例

```python
class CodeUnit(ExecutionUnit):
    """
    代码执行单元：安全执行 Python/JavaScript 代码
    """
    
    async def execute(self, input_data: dict) -> dict:
        """
        执行代码
        
        Args:
            input_data: 包含 code, language, timeout 等字段
        
        Returns:
            dict: 包含 stdout, stderr, exit_code
        
        Example:
            >>> result = await code_unit.execute({
            ...     "code": "print('Hello')",
            ...     "language": "python",
            ...     "timeout": 30
            ... })
        """
        language = input_data.get("language", "python")
        code = input_data.get("code")
        timeout = input_data.get("timeout", 30)
        
        if language == "python":
            return await self._run_python(code, timeout)
        elif language == "javascript":
            return await self._run_javascript(code, timeout)
        else:
            raise ValueError(f"Unsupported language: {language}")
    
    def get_input_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "要执行的代码"},
                "language": {
                    "type": "string",
                    "enum": ["python", "javascript"],
                    "default": "python"
                },
                "timeout": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 300,
                    "default": 30
                }
            },
            "required": ["code"]
        }
    
    def get_output_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "stdout": {"type": "string"},
                "stderr": {"type": "string"},
                "exit_code": {"type": "integer"}
            }
        }
    
    async def _run_python(self, code: str, timeout: int) -> dict:
        """在沙箱中运行 Python 代码"""
        # 实现细节
        pass
    
    async def _run_javascript(self, code: str, timeout: int) -> dict:
        """在沙箱中运行 JavaScript 代码"""
        # 实现细节
        pass
```

---

## 3. 记忆与进化层组件

### 3.1 MemoryRovol

**模块路径**: `agentos_cta.memory_evolution.memoryrovol`

**职责**: 多层记忆系统管理

#### 类定义

```python
class MemoryRovol:
    """
    多层记忆系统：Raw/Feature/Pattern三层架构
    """
    
    def __init__(self, config: dict):
        """
        初始化记忆系统
        
        Args:
            config: 配置字典
        
        Example:
            >>> config = {
            ...     "storage_backend": "sqlite",
            ...     "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
            ...     "retention_policy": {
            ...         "raw_days": 7,
            ...         "feature_days": 30,
            ...         "pattern_permanent": True
            ...     }
            ... }
            >>> memory = MemoryRovol(config)
        """
        pass
    
    async def store(
        self,
        content: Any,
        layer: str = "raw",
        metadata: Optional[dict] = None
    ) -> str:
        """
        存储记忆
        
        Args:
            content: 记忆内容
            layer: 记忆层级（raw/feature/pattern）
            metadata: 元数据
        
        Returns:
            str: 记忆记录 ID
        
        Example:
            >>> record_id = await memory.store(
            ...     content={"dialogue": "用户询问..."},
            ...     layer="raw",
            ...     metadata={"session_id": "sess_123"}
            ... )
        """
        pass
    
    async def retrieve(
        self,
        query: str,
        layer: str = "all",
        top_k: int = 10,
        filters: Optional[dict] = None
    ) -> List[MemoryRecord]:
        """
        检索记忆
        
        Args:
            query: 查询文本
            layer: 检索层级（raw/feature/pattern/all）
            top_k: 返回数量
            filters: 过滤条件
        
        Returns:
            List[MemoryRecord]: 记忆记录列表
        
        Example:
            >>> records = await memory.retrieve(
            ...     query="用户需求分析",
            ...     layer="feature",
            ...     top_k=5
            ... )
        """
        pass
    
    async def consolidate(self, source_layer: str, target_layer: str):
        """
        记忆巩固：从低层级提炼到高层级
        
        Args:
            source_layer: 源层级
            target_layer: 目标层级
        
        Example:
            >>> await memory.consolidate("raw", "feature")
        """
        pass
    
    async def forget(self, criteria: dict) -> int:
        """
        遗忘机制：删除符合条件的记忆
        
        Args:
            criteria: 筛选条件
        
        Returns:
            int: 删除的记忆数量
        
        Example:
            >>> count = await memory.forget({
            ...     "layer": "raw",
            ...     "older_than_days": 7,
            ...     "importance_below": 0.3
            ... })
        """
        pass
```

---

### 3.2 WorldModel

**模块路径**: `agentos_cta.memory_evolution.world_model`

**职责**: 维护和更新世界认知

#### 类定义

```python
class WorldModel:
    """
    世界模型：语义切片、时间对齐、漂移检测
    """
    
    def __init__(self, config: dict):
        """
        初始化世界模型
        
        Args:
            config: 配置字典
        """
        pass
    
    async def update_from_event(self, event: TimedEvent):
        """
        根据事件更新世界模型
        
        Args:
            event: 时间事件
        
        Example:
            >>> event = TimedEvent(...)
            >>> await world_model.update_from_event(event)
        """
        pass
    
    async def get_current_state(self) -> dict:
        """
        获取当前世界状态
        
        Returns:
            dict: 状态快照
        """
        pass
    
    def detect_inconsistencies(self) -> List[Inconsistency]:
        """
        检测不一致性
        
        Returns:
            List[Inconsistency]: 不一致性列表
        """
        pass
```

---

### 3.3 ConsensusEngine

**模块路径**: `agentos_cta.memory_evolution.consensus`

**职责**: 共识决策

#### 类定义

```python
class ConsensusEngine:
    """
    共识引擎：Quorum-fast 决策、稳定性窗口
    """
    
    def __init__(self, config: dict):
        """
        初始化共识引擎
        
        Args:
            config: 配置字典
        """
        pass
    
    async def decide(
        self,
        participants: List[str],
        votes: Dict[str, Any],
        quorum_ratio: float = 0.6
    ) -> ConsensusResult:
        """
        进行决策
        
        Args:
            participants: 参与者列表
            votes: 投票字典
            quorum_ratio: 法定比例
        
        Returns:
            ConsensusResult: 决策结果
        """
        pass
```

---

## 4. 运行时组件

### 4.1 AppServer

**模块路径**: `agentos_cta.runtime.server`

**职责**: 应用服务器

#### 类定义

```python
class AppServer:
    """
    应用服务器：管理网关和会话
    """
    
    def __init__(self, config: dict):
        """
        初始化服务器
        
        Args:
            config: 配置字典
        """
        pass
    
    def register_gateway(self, name: str, gateway: BaseGateway):
        """
        注册网关
        
        Args:
            name: 网关名称
            gateway: 网关实例
        """
        pass
    
    async def start(self):
        """启动服务器"""
        pass
    
    async def stop(self):
        """停止服务器"""
        pass
    
    async def handle_request(
        self,
        gateway_name: str,
        request: dict
    ) -> dict:
        """
        处理请求
        
        Args:
            gateway_name: 网关名称
            request: 请求数据
        
        Returns:
            dict: 响应数据
        """
        pass
```

---

### 4.2 SessionManager

**模块路径**: `agentos_cta.runtime.session_manager`

**职责**: 会话管理

#### 类定义

```python
class SessionManager:
    """
    会话管理器
    """
    
    def __init__(self, config: dict):
        """
        初始化会话管理器
        
        Args:
            config: 配置字典
        """
        pass
    
    async def create_session(self, metadata: dict) -> Session:
        """
        创建会话
        
        Args:
            metadata: 会话元数据
        
        Returns:
            Session: 会话对象
        """
        pass
    
    async def get_session(self, session_id: str) -> Optional[Session]:
        """
        获取会话
        
        Args:
            session_id: 会话 ID
        
        Returns:
            Optional[Session]: 会话对象或 None
        """
        pass
    
    async def delete_session(self, session_id: str):
        """
        删除会话
        
        Args:
            session_id: 会话 ID
        """
        pass
```

---

## 5. 安全组件

### 5.1 VirtualWorkbench

**模块路径**: `agentos_cta.saferoom.virtual_workbench`

**职责**: 虚拟工位（沙箱）

#### 类定义

```python
class VirtualWorkbench:
    """
    虚拟工位：为 Agent 提供隔离的沙箱环境
    """
    
    def __init__(self, config: dict):
        """
        初始化虚拟工位
        
        Args:
            config: 配置字典
        """
        pass
    
    async def create(
        self,
        agent_id: str,
        resource_limits: Optional[dict] = None
    ) -> str:
        """
        创建工位
        
        Args:
            agent_id: Agent ID
            resource_limits: 资源限制配置
        
        Returns:
            str: Workbench ID
        """
        pass
    
    async def destroy(self, workbench_id: str):
        """
        销毁工位
        
        Args:
            workbench_id: Workbench ID
        """
        pass
    
    async def execute_in_sandbox(
        self,
        workbench_id: str,
        cmd: List[str],
        timeout_sec: int = 300
    ) -> dict:
        """
        在沙箱中执行命令
        
        Args:
            workbench_id: Workbench ID
            cmd: 命令列表
            timeout_sec: 超时时间（秒）
        
        Returns:
            dict: 执行结果
        """
        pass
```

---

### 5.2 PermissionEngine

**模块路径**: `agentos_cta.saferoom.permission_engine`

**职责**: 权限裁决

#### 类定义

```python
class PermissionEngine:
    """
    权限裁决引擎
    """
    
    def __init__(self, rules: List[dict]):
        """
        初始化权限引擎
        
        Args:
            rules: 规则列表
        """
        pass
    
    def check_permission(
        self,
        agent_id: str,
        resource: str,
        action: str
    ) -> PermissionAction:
        """
        检查权限
        
        Args:
            agent_id: Agent ID
            resource: 资源标识
            action: 操作类型
        
        Returns:
            PermissionAction: ALLOW/DENY/PROMPT
        """
        pass
    
    def request_permission(
        self,
        agent_id: str,
        resource: str,
        action: str,
        context: dict
    ) -> Permission:
        """
        请求权限
        
        Args:
            agent_id: Agent ID
            resource: 资源标识
            action: 操作类型
            context: 上下文信息
        
        Returns:
            Permission: 权限对象
        """
        pass
```

---

## 6. 工具类

### 6.1 TokenCounter

**模块路径**: `agentos_cta.utils.token_counter`

**职责**: Token 计数

#### 类定义

```python
class TokenCounter:
    """
    Token 计数器：基于 tiktoken
    """
    
    def __init__(self, default_encoding: str = "cl100k_base"):
        """
        初始化计数器
        
        Args:
            default_encoding: 默认编码
        """
        pass
    
    def count_tokens(self, text: Union[str, List[str]]) -> int:
        """
        计算文本 Token 数
        
        Args:
            text: 文本或文本列表
        
        Returns:
            int: Token 数量
        """
        pass
    
    def count_messages_tokens(self, messages: List[dict]) -> int:
        """
        计算对话消息的 Token 数
        
        Args:
            messages: 消息列表
        
        Returns:
            int: Token 数量
        """
        pass
    
    def adaptive_truncate(self, text: str, max_tokens: int) -> str:
        """
        自适应截断文本
        
        Args:
            text: 原始文本
            max_tokens: 最大 Token 数
        
        Returns:
            str: 截断后的文本
        """
        pass
```

---

### 6.2 CostEstimator

**模块路径**: `agentos_cta.utils.cost_estimator`

**职责**: 成本预估

#### 类定义

```python
class CostEstimator:
    """
    成本预估器
    """
    
    def __init__(self, pricing_config: Optional[dict] = None):
        """
        初始化预估器
        
        Args:
            pricing_config: 定价配置
        """
        pass
    
    def estimate_cost(
        self,
        model_name: str,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """
        预估成本
        
        Args:
            model_name: 模型名称
            input_tokens: 输入 Token 数
            output_tokens: 输出 Token 数
        
        Returns:
            float: 成本（美元）
        """
        pass
```

---

### 6.3 StructuredLogger

**模块路径**: `agentos_cta.utils.structured_logger`

**职责**: 结构化日志

#### 函数定义

```python
def set_trace_id(trace_id: str):
    """
    设置当前上下文的 TraceID
    
    Args:
        trace_id: TraceID
    """
    pass


def get_trace_id() -> Optional[str]:
    """
    获取当前上下文的 TraceID
    
    Returns:
        Optional[str]: TraceID 或 None
    """
    pass


def get_logger(name: str) -> logging.Logger:
    """
    获取结构化日志器
    
    Args:
        name: 日志器名称
    
    Returns:
        logging.Logger: 日志器
    
    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Processing request", extra={
        ...     "task_id": "123",
        ...     "user_id": "456"
        ... })
    """
    pass
```

---

## 附录

### A. 错误类型

```python
class AgentOSError(Exception):
    """基础异常类"""
    code = 500


class ConfigurationError(AgentOSError):
    """配置错误"""
    code = 400


class ResourceLimitError(AgentOSError):
    """资源超限"""
    code = 429


class ConsensusError(AgentOSError):
    """共识失败"""
    code = 409


class SecurityError(AgentOSError):
    """安全违规"""
    code = 403


class ToolExecutionError(AgentOSError):
    """工具执行失败"""
    code = 500


class ModelUnavailableError(AgentOSError):
    """模型不可用"""
    code = 503
```

---

**文档维护**: SpharxWorks Team  
**联系方式**: lidecheng@spharx.cn, wangliren@spharx.cn
