# CoreLoopThree：三层核心运行时

**版本**: 1.0.0.2  
**路径**: `coreadd/coreloopthree/`

---

## 1. 概述

CoreLoopThree 是 AgentOS 的三层核心运行时，包含认知层（Cognition）、行动层（Execution）和记忆层（Memory）。

这三层通过可插拔的策略接口和标准化的数据流协作，实现智能体的完整生命周期管理。

- **认知层**：负责意图理解、任务规划、模型协同和 Agent 调度。
- **行动层**：负责任务执行、补偿事务、责任链追踪和执行单元管理。
- **记忆层**：封装 MemoryRovol，提供记忆的写入、查询、挂载等高级接口。

## 2. 目录结构
```
coreadd/coreloopthree/
├── CMakeLists.txt # 顶层构建文件
├── README.md # 本文件
├── include/ # 公共头文件
│ ├── cognition.h # 认知层接口
│ ├── execution.h # 行动层接口
│ ├── memory.h # 记忆层接口
│ └── loop.h # 三层闭环主接口
└── src/ # 源文件
├── cognition/ # 认知层实现
│ ├── engine.c
│ ├── planner/ # 规划策略
│ ├── coordinator/ # 协同策略
│ └── dispatcher/ # 调度策略
├── execution/ # 行动层实现
│ ├── engine.c
│ ├── registry.c
│ ├── compensation.c
│ ├── trace.c
│ └── units/ # 执行单元
└── memory/ # 记忆层实现
├── engine.c
├── memory_service.c
└── rov_ffi.h # MemoryRovol 接口
```

## 3. 构建方法

在项目根目录执行：
```bash
mkdir build && cd build
cmake ../coreadd -DCMAKE_BUILD_TYPE=Release
make
```