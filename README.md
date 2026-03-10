# AgentOS
这是SPHARX开发的智能体操作系统

## CoreLoopThree Architecture
CoreLoopThree Architecture（简称 CTA），是融合现代系统工程、自动控制理论与前沿多智能体工程实践，面向复杂工业场景原创的三层一体化智能体操作系统架构。

### 核心设计
CTA 架构以「思考 - 决策 - 行动 - 进化」全链路闭环为核心驱动，由三个强耦合、权责边界清晰的核心层级构成，实现全局可控、精确执行、自主进化的核心目标：

- **认知层**（Cognition Layer）：系统的全局决策与管控中枢。具备类人元认知能力，可将用户模糊的定性需求转化为结构化定量目标，拆解生成 DAG 有向无环任务图，匹配并调度专业 Agent；同时通过「模拟执行 - 反思评估 - 规划调整」的微循环实现事前 / 事后自我纠错，维护 Agent 心智模型库，实现全局最优的团队管理与任务管控。
- **行动层**（Execution Layer）：系统的精准执行与状态反馈中枢。将所有原子操作封装为标准化「执行单元」，通过契约测试保障执行可靠性，通过 Saga 补偿事务实现操作可回滚、可审计；精确执行认知层下发的任务指令，实时采集并反馈执行状态、预期与实际结果的差异数据，为闭环调节提供数据支撑。
- **记忆与进化层**（Memory & Evolution Layer）：系统的经验沉淀与自主进化中枢。借鉴卷积神经网络（CNN）「多层卷积 - 池化」的核心思想，设计「记忆卷载」机制，将原始执行事件逐层抽象为事件摘要、语义向量、通用模式规则，实现信息压缩、模式发现与知识泛化；通过多维度进化委员会自动挖掘可复用的经验规则，驱动系统全链路能力的自主迭代进化。

## CoreLoopThree Architecture (English Version)

**CoreLoopThree Architecture** (hereinafter referred to as **CTA Architecture**) is an original three-tier integrated multi-agent operating system architecture designed for complex industrial scenarios. Built upon modern systems engineering, automatic control theory, and cutting-edge multi-agent engineering practices (circa 2026), it aims to bridge the gap between theoretical autonomy and industrial reliability.

### Core Design
Centered on the full closed loop of **"Thinking-Decision-Action-Evolution"**, the CTA Architecture consists of three tightly coupled core layers with clear responsibility boundaries. This design achieves the core goals of globally controllable management, precise execution, and autonomous evolution:

- **Cognition Layer**: The global decision-making and management center of the system. Equipped with human-like metacognitive abilities, it converts users' vague qualitative requirements into structured quantitative objectives. It decomposes tasks into a Directed Acyclic Graph (DAG) to match and schedule professional agents. Furthermore, it realizes pre-event and post-event self-correction through the micro-cycle of *"Simulation Execution → Reflection Evaluation → Plan Adjustment"*, while maintaining a **Theory of Mind (ToM)** model library for agents to achieve globally optimal team management and task control.
  
- **Execution Layer**: The precise execution and status feedback center of the system. It encapsulates all atomic operations into standardized **"Execution Units"**, ensuring execution reliability through contract testing. By leveraging the **Saga compensation transaction mechanism**, it guarantees that operations are rollbackable and auditable. This layer accurately executes task instructions issued by the Cognition Layer, collecting and feeding back execution status and the delta between expected and actual results in real time to support closed-loop regulation.

- **Memory & Evolution Layer**: The experience accumulation and autonomous evolution engine of the system. Drawing on the core idea of *"multi-layer convolution-pooling"* from Convolutional Neural Networks (CNN), it designs the **"Memory Convolution"** mechanism. This mechanism gradually abstracts original execution events into event summaries, semantic vectors, and general pattern rules, realizing information compression, pattern discovery, and knowledge generalization. Through a **multi-dimensional evolution committee**, the system automatically mines reusable experience rules, driving the autonomous iterative evolution of its full-link capabilities.