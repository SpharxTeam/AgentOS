# AgentOS 项目目录结构（20260311）

本目录结构基于“工程两论”（反馈闭环、层次分解）与“思维双系统”（双通道认知）设计，遵循内核纯净、生态开放、命名统一的哲学原则。

## 一、根目录
```
AgentOS/
├── README.md                     # 项目首页：概述、核心理念、快速开始、许可证、致谢
├── LICENSE                       # GPL-3.0 许可证全文
├── CONTRIBUTING.md               # 贡献指南：代码风格、PR 流程、契约验证、社区公约
├── CHANGELOG.md                  # 版本历史：记录各版本重大变更（v3.0.0 起）
├── pyproject.toml                # Poetry 配置：项目依赖、构建系统、工具配置
├── .env.example                  # 环境变量模板：API 密钥、路径配置
├── .gitignore                    # Git 忽略规则：Python 缓存、数据目录、本地配置
├── Makefile                      # 常用命令集：install, test, docs, doctor, quickstart
├── quickstart.sh                 # 极速体验脚本：一键运行示例
└── validate.sh                   # 环境验证脚本：调用 `scripts/doctor.py`
```
## 二、内核模块 `agentos_cta/`

内核是 CoreLoopThree 架构的核心，仅包含最基础的调度、认知、记忆、安全机制，不依赖外部市场组件。
```
agentos_cta/
├── __init__.py                   # 导出内核公开 API：核心类、函数
│
├── coreloopthree/                 # 三层核心实现（工程两论 + 思维双系统）
│   ├── __init__.py                # 导出认知、行动、记忆进化三层
│   │
│   ├── cognition/                  # 认知层（Cognition）
│   │   ├── __init__.py
│   │   ├── router.py                # 路由层：意图理解、复杂度评估、资源匹配
│   │   ├── dual_model_coordinator.py # 双模型协调器（1 大 +2 小冗余，思维双系统）
│   │   ├── incremental_planner.py   # 增量规划器：生成阶段任务 DAG，动态调整
│   │   ├── dispatcher.py             # 调度官：从 Agent 市场查询匹配并分配任务
│   │   └── schemas/                  # 认知层数据模型
│   │       ├── intent.py
│   │       ├── plan.py
│   │       └── task_graph.py
│   │
│   ├── execution/                   # 行动层（Execution）
│   │   ├── __init__.py
│   │   ├── agent_pool.py             # 专业 Agent 池管理（加载、缓存、释放）
│   │   ├── units/                     # 执行单元池（可验证、可审计）
│   │   │   ├── base_unit.py           # 执行单元基类
│   │   │   ├── tool_unit.py           # 工具调用单元（shell, API 等）
│   │   │   ├── code_unit.py           # 代码执行单元（沙箱化）
│   │   │   ├── api_unit.py            # API 调用单元（HTTP 客户端）
│   │   │   ├── file_unit.py           # 文件操作单元（安全路径）
│   │   │   ├── browser_unit.py        # 浏览器控制单元（Playwright 封装）
│   │   │   └── db_unit.py             # 数据库操作单元（SQL 执行）
│   │   ├── compensation_manager.py    # 补偿事务管理器（可逆/不可逆操作处理）
│   │   ├── traceability_tracer.py     # 责任链追踪器（TraceID 贯穿）
│   │   └── schemas/                   # 行动层数据模型
│   │       ├── task.py
│   │       └── result.py
│   │
│   └── memory_evolution/             # 记忆与进化层（Memory & Evolution）
│       ├── __init__.py
│       ├── deep_memory/               # 深层记忆系统（L1-L4）
│       │   ├── buffer.py               # L1 Buffer：实时日志存储
│       │   ├── summarizer.py           # L2 Summary：摘要生成器（LLM 压缩）
│       │   ├── vector_store.py         # L3 Vector：向量检索（混合检索）
│       │   └── pattern_miner.py        # L4 Pattern：规则挖掘
│       ├── world_model/                # 世界模型抽象层（arXiv:2602.20934）
│       │   ├── semantic_slicer.py      # 语义切片：将上下文转为可寻址空间
│       │   ├── temporal_aligner.py     # 时间对齐：处理多 Agent 时序不一致
│       │   └── drift_detector.py       # 认知漂移检测：识别理解偏差
│       ├── consensus/                  # 共识语义层（arXiv:2512.20184）
│       │   ├── quorum_fast.py          # Quorum-fast 决策：达到法定数量即推进
│       │   ├── stability_window.py     # 稳定性窗口：过滤暂时性多数
│       │   └── streaming_consensus.py  # Streaming 共识：Token 流中早停
│       ├── committees/                 # 进化委员会（四委员会）
│       │   ├── coordination_committee.py # 协调委员会：流程优化
│       │   ├── technical_committee.py    # 技术委员会：规范更新
│       │   ├── audit_committee.py        # 审计委员会：交叉验证、识别共识妥协
│       │   └── team_committee.py         # 团队委员会：个体规则进化、Agent 契约更新
│       ├── shared_memory.py             # 共享内存空间（中央看板、Agent 注册中心）
│       └── schemas/                     # 记忆层数据模型
│           ├── memory_record.py
│           └── evolution_report.py
│
├── runtime/                         # 运行时管理（借鉴 OpenClaw Gateway）
│   ├── __init__.py
│   ├── server.py                     # App Server：管理会话生命周期、并发控制
│   ├── session_manager.py             # 会话管理器（Thread/Turn/Item）
│   ├── gateway/                       # 网关层（多协议接入）
│   │   ├── http_gateway.py            # HTTP/HTTPS 网关
│   │   ├── websocket_gateway.py       # WebSocket 实时通信网关
│   │   └── stdio_gateway.py           # 标准输入输出网关（本地进程）
│   ├── protocol/                       # 通信协议封装
│   │   ├── json_rpc.py                # JSON-RPC 2.0 实现
│   │   ├── message_serializer.py       # 序列化器（支持增量更新）
│   │   └── codec.py                    # 编解码（集成数据优化层 ADOL）
│   ├── telemetry/                       # 可观测性
│   │   ├── otel_collector.py           # OpenTelemetry 集成
│   │   ├── metrics.py                  # 性能指标（p95 延迟、Token 独特性）
│   │   └── tracing.py                  # 分布式追踪
│   └── health_checker.py               # 健康检查（医生自检）
│
├── saferoom/                         # 安全隔离层（安全内生）
│   ├── __init__.py
│   ├── virtual_workbench.py           # 虚拟工位：沙箱隔离（每个 Agent 独立容器/WASM）
│   ├── permission_engine.py           # 权限裁决引擎（基于规则，非 LLM）
│   ├── tool_audit.py                  # 工具调用审计（记录、异常检测）
│   ├── input_sanitizer.py             # 输入净化器（防止提示词注入）
│   └── schemas/                       # 安全数据模型
│       ├── permission.py
│       └── audit_record.py
│
└── utils/                            # 通用工具
    ├── __init__.py
    ├── token_counter.py               # Token 计数与预算管理
    ├── token_uniqueness.py            # Token 独特性预测（缓存决策）
    ├── cost_estimator.py              # 成本预估（基于模型配置）
    ├── latency_monitor.py             # p95 延迟监控
    ├── structured_logger.py           # 结构化日志（支持 TraceID）
    ├── error_types.py                 # 统一错误类型（AgentOSError 等）
    └── file_utils.py                  # 文件操作辅助（安全读写、临时文件）
```
## 三、开放生态 `agentos_open/`

生态部分独立于内核，可独立仓库化，由社区驱动发展。
```
agentos_open/
├── README.md                         # 生态概述：市场使用、贡献指南
│
├── markets/                           # 市场中心
│   ├── agent/                          # Agent 市场
│   │   ├── __init__.py
│   │   ├── registry.py                  # Agent 注册中心（SQLite，存储契约）
│   │   ├── installer.py                 # Agent 安装器（支持 GitHub/本地源）
│   │   ├── publisher.py                 # Agent 发布工具（供社区上传）
│   │   └── contracts/                    # Agent 契约标准（JSON Schema）
│   │       ├── agent_schema.json
│   │       └── validator.py
│   │
│   ├── skill/                          # 技能市场
│   │   ├── __init__.py
│   │   ├── registry.py                  # 技能注册中心
│   │   ├── installer.py                 # 技能安装器
│   │   ├── commands/                     # CLI 命令封装
│   │   │   ├── install.py
│   │   │   ├── list.py
│   │   │   ├── info.py
│   │   │   └── search.py
│   │   └── contracts/                    # 技能契约标准
│   │       ├── skill_schema.json
│   │       └── validator.py
│   │
│   └── contracts/                       # 共享契约规范（被 agent 和 skill 共用）
│       ├── base_schema.json
│       └── common_types.py
│
└── contrib/                            # 社区贡献（实际代码）
    ├── agents/                          # 社区贡献的 Agent
    │   ├── product_manager/              # 示例：产品经理 Agent
    │   │   ├── agent.py
    │   │   ├── contract.json
    │   │   └── prompts/
    │   │       ├── system1.md
    │   │       └── system2.md
    │   ├── architect/
    │   ├── frontend/
    │   ├── backend/
    │   ├── tester/
    │   ├── devops/
    │   └── security/
    └── skills/                          # 社区贡献的技能
        ├── shell_skill/
        ├── filesystem_skill/
        ├── github_skill/
        ├── browser_skill/
        └── database_skill/
```
## 四、配置、文档与测试
```
config/                                # 配置文件（与代码完全分离）
├── settings.yaml                      # 系统级配置（日志、并发、超时）
├── models.yaml                        # 最多 3 个 LLM 配置（成本、上下文窗口）
├── agents/                             # Agent 相关配置
│   ├── registry.yaml                    # 可用 Agent 列表（由市场同步）
│   └── profiles/                        # Agent 默认配置（模型偏好、超时）
├── skills/                             # 技能相关配置
│   └── registry.yaml                    # 可用技能列表
├── security/                           # 安全配置
│   ├── permissions.yaml                 # 默认权限规则
│   └── audit.yaml                       # 审计规则
└── token_strategy.yaml                 # Token 分配策略（动态阈值）

docs/                                   # 文档
├── architecture/                       # 架构设计
│   ├── CoreLoopThree.md                 # 三层架构详解
│   ├── world_model.md                    # 世界模型抽象层
│   ├── consensus.md                      # 共识语义层
│   ├── create_agentos_project.md         #项目目录结构设计
│   └── diagrams/                         # 架构图源文件
├── specifications/                      # 技术规范
│   ├── agent_contract_spec.md           # Agent 契约规范
│   ├── skill_spec.md                    # 技能规范
│   ├── protocol_spec.md                 # 通信协议规范
│   └── security_spec.md                 # 安全规范
├── guides/                              # 使用指南
│   ├── getting_started.md               # 快速开始
│   ├── create_agent.md                  # 创建自定义 Agent
│   ├── create_skill.md                  # 创建自定义 Skill
│   ├── token_optimization.md            # Token 优化指南
│   ├── deployment.md                    # 部署指南
│   └── troubleshooting.md               # 故障排查
└── api/                                 # API 文档（自动生成）
    └── .gitkeep

examples/                               # 示例项目
├── ecommerce_dev/                      # 电商应用开发示例
│   ├── README.md
│   ├── run.sh
│   ├── project_config.yaml
│   └── expected_output/                 # 预期产出占位
│       └── .gitkeep
├── video_editing/                      # 视频剪辑处理示例
│   ├── README.md
│   ├── run.sh
│   ├── project_config.yaml
│   └── expected_output/
│       └── .gitkeep
└── document_generation/                # 文档生成示例
    ├── README.md
    ├── run.sh
    ├── project_config.yaml
    └── expected_output/
        └── .gitkeep

tests/                                  # 测试套件
├── __init__.py
├── unit/                               # 单元测试
│   ├── test_token_counter.py
│   ├── test_router.py
│   └── ...
├── integration/                        # 集成测试
│   ├── test_cognition_execution_flow.py
│   └── ...
├── contract/                           # 契约测试
│   ├── test_agent_contracts.py
│   └── test_skill_contracts.py
├── security/                           # 安全测试
│   ├── test_sandbox.py
│   └── test_permissions.py
└── benchmarks/                         # 性能基准测试
    ├── test_token_efficiency.py
    ├── test_latency.py
    └── test_consensus.py
```
## 五、工具脚本
```
scripts/                                # 安装、维护、诊断脚本
├── install.sh                          # 一键安装（Linux/macOS）
├── install.ps1                         # 一键安装（Windows）
├── init_config.py                      # 初始化配置文件（从 .env.example 生成）
├── doctor.py                           # 医生自检（环境、依赖、配置诊断与修复）
├── validate_contracts.py               # 验证所有 Agent 和 Skill 契约
├── benchmark.py                        # 运行性能基准测试
├── update_registry.py                  # 扫描 contrib/ 更新注册中心
├── generate_docs.py                    # 自动生成 API 文档
└── quickstart.sh                       # 快速启动示例（调用 examples/ 下脚本）
```
## 六、设计原则贯彻说明
```
| 原则 | 体现 |
| :--- | :--- |
| **工程两论反馈闭环** | `coreloopthree` 三层通过 `traceability_tracer`、`committees` 形成实时、轮次内、跨轮次反馈。 |
| **思维双系统** | `dual_model_coordinator` 实现 1+2 冗余，`agent_pool` 中的每个 Agent 采用 1+1 双模型。 |
| **内核纯净** | `agentos_cta` 不含市场代码，所有生态组件置于 `agentos_open`。 |
| **生态开放** | `markets/` 和 `contrib/` 分离，支持独立仓库、第三方源。 |
| **命名美学** | `coreloopthree`（理论映射）、`saferoom`（意象）、`runtime`（标准）、`markets/agent`（层级清晰）。 |
| **可落地** | 每个模块均有占位文件，脚本齐全，文档完整，可直接进入编码阶段。 |
```
此目录结构已整合,是项目开发的蓝图。
