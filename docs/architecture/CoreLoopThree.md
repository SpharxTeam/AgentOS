# CoreLoopThree 架构

**版本**: 3.0.0

## 概述

CoreLoopThree 是 AgentOS 的基础架构，由三层构成：认知层（Cognition）、行动层（Execution）、记忆与进化层（Memory & Evolution）。三层通过实时反馈、规划调整和跨轮次规则进化形成闭环。

## 三层架构

### 认知层
负责意图理解、任务规划、Agent调度。包含：
- Router：路由层，意图识别、复杂度评估、资源匹配
- DualModelCoordinator：双模型协同协调器（1大+2小冗余）
- IncrementalPlanner：增量规划器
- Dispatcher：调度官，动态组建团队

### 行动层
负责任务执行，包含专业Agent池和执行单元。支持补偿事务和责任链追踪。

### 记忆与进化层
提供深层记忆（L1-L4）、世界模型抽象、共识语义层和进化委员会。实现系统自我进化。

## 反馈闭环
- 执行反馈（实时）
- 规划调整（轮次内）
- 规则进化（跨轮次）