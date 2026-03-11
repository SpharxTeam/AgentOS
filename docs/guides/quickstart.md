# AgentOS CoreLoopThree 快速入门指南

**版本**: v1.0.0  
**最后更新**: 2026-03-11  
**预计阅读时间**: 15 分钟

---

## 🎯 本指南将帮助您

- ✅ 在 5 分钟内完成安装
- ✅ 在 10 分钟内运行第一个示例
- ✅ 理解核心概念和基本用法
- ✅ 快速开始开发自己的应用

---

## 📋 目录

1. [快速安装](#1-快速安装)
2. [Hello World](#2-hello-world)
3. [核心概念](#3-核心概念)
4. [第一个完整示例](#4-第一个完整示例)
5. [下一步学习](#5-下一步学习)

---

## 1. 快速安装

### 1.1 环境要求

- Python 3.10 或更高版本
- pip 包管理器
- 稳定的网络连接（用于下载依赖和访问 AI 模型 API）

### 1.2 安装步骤

#### 步骤 1: 创建项目目录

```bash
mkdir my-agentos-app
cd my-agentos-app
```

#### 步骤 2: 创建虚拟环境

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

#### 步骤 3: 安装 AgentOS

```bash
pip install agentos-cta
```

#### 步骤 4: 配置环境变量

创建 `.env` 文件：

```bash
# .env 文件
OPENAI_API_KEY=sk-your-api-key-here
```

或者在代码中设置：

```python
import os
os.environ["OPENAI_API_KEY"] = "sk-your-api-key-here"
```

#### 步骤 5: 验证安装

```python
python -c "import agentos_cta; print(f'AgentOS version: {agentos_cta.__version__}')"
```

如果看到版本号输出，说明安装成功！

---

## 2. Hello World

### 2.1 最简单的示例

创建 `hello.py` 文件：

```python
import asyncio
from agentos_cta import Router, DualModelCoordinator

async def main():
    # 1. 初始化配置
    config = {
        "models": [
            {"name": "gpt-3.5-turbo", "context_window": 4096}
        ]
    }
    
    # 2. 创建组件
    router = Router(config)
    coordinator = DualModelCoordinator(
        primary_model="gpt-3.5-turbo",
        secondary_models=[],
        config=config
    )
    
    # 3. 用户输入
    user_input = "用 Python 写一个 Hello World 函数"
    
    # 4. 解析意图
    intent = await router.parse_intent(user_input)
    print(f"✅ 意图解析完成：{intent.goal}")
    
    # 5. 生成计划
    plan = await coordinator.generate_plan(intent, context={})
    print(f"✅ 计划生成完成：{plan.plan_id}")
    print(f"   任务数量：{len(plan.tasks)}")
    
    # 6. 显示结果
    print("\n📝 生成的代码:")
    print(plan.metadata.get("code", "无代码输出"))

if __name__ == "__main__":
    asyncio.run(main())
```

运行：

```bash
python hello.py
```

### 2.2 预期输出

```
✅ 意图解析完成：用 Python 写一个 Hello World 函数
✅ 计划生成完成：plan_abc123def456
   任务数量：1

📝 生成的代码:
def hello_world():
    print("Hello, World!")

if __name__ == "__main__":
    hello_world()
```

---

## 3. 核心概念

### 3.1 三层架构

AgentOS 采用 **认知 - 行动 - 记忆进化** 三层循环架构：

```
┌─────────────────────────────────────┐
│  🔵 认知层                          │
│  - 理解用户意图                     │
│  - 生成任务计划                     │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  🟢 行动层                          │
│  - 执行具体任务                     │
│  - 调用工具/API                     │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  🟣 记忆与进化层                    │
│  - 存储经验                         │
│  - 持续优化                         │
└─────────────────────────────────────┘
```

### 3.2 核心组件

| 组件 | 作用 | 类比 |
|------|------|------|
| **Router** | 解析用户意图 | 翻译官 |
| **DualModelCoordinator** | 多模型协同规划 | 军师团 |
| **Dispatcher** | 分配任务给 Agent | 调度员 |
| **AgentPool** | 管理 Agent 实例 | 人才库 |
| **ExecutionUnit** | 执行具体操作 | 工具集 |

### 3.3 数据流

```
用户输入 → Router 解析 → Coordinator 规划 → Dispatcher 分发 → Agent 执行 → 返回结果
```

---

## 4. 第一个完整示例

### 4.1 开发待办事项应用

让我们创建一个完整的示例：开发一个简单的待办事项应用。

创建 `todo_app.py`:

```python
import asyncio
from agentos_cta import (
    Router,
    DualModelCoordinator,
    IncrementalPlanner,
    Dispatcher,
    TraceabilityTracer
)

async def develop_todo_app():
    """开发待办事项应用"""
    
    # 1. 初始化配置
    config = {
        "models": [
            {"name": "gpt-3.5-turbo", "context_window": 4096},
            {"name": "gpt-4", "context_window": 8192}
        ],
        "logging": {"level": "INFO"}
    }
    
    # 2. 创建核心组件
    router = Router(config)
    coordinator = DualModelCoordinator(
        primary_model="gpt-3.5-turbo",
        secondary_models=["gpt-4"],
        config=config
    )
    planner = IncrementalPlanner(config)
    dispatcher = Dispatcher(registry_client=None, config=config)
    tracer = TraceabilityTracer({"log_dir": "logs"})
    
    # 3. 定义用户需求
    user_input = """
    开发一个命令行待办事项应用，要求：
    1. 可以添加任务
    2. 可以查看任务列表
    3. 可以标记任务为完成
    4. 数据保存到 JSON 文件
    
    使用 Python 实现
    """
    
    print("=" * 60)
    print("🚀 开始开发待办事项应用")
    print("=" * 60)
    
    # 4. 意图解析
    print("\n📌 步骤 1: 解析需求")
    intent = await router.parse_intent(user_input)
    print(f"   目标：{intent.goal}")
    print(f"   复杂度：{intent.complexity}")
    
    # 5. 生成计划
    print("\n📌 步骤 2: 生成开发计划")
    plan = await coordinator.generate_plan(intent, context={})
    print(f"   计划 ID: {plan.plan_id}")
    print(f"   任务数：{len(plan.tasks)}")
    
    for i, task in enumerate(plan.tasks.values(), 1):
        print(f"   {i}. {task.name} ({task.role})")
    
    # 6. 开始追踪
    trace_id = f"trace_{plan.plan_id}"
    span_id = tracer.start_span(
        task_id=plan.plan_id,
        input_summary="Todo 应用开发"
    )
    
    try:
        # 7. 执行计划
        print("\n📌 步骤 3: 执行开发任务")
        result = await dispatcher.dispatch_plan(plan, context={})
        
        # 8. 结束追踪
        tracer.end_span(
            span_id=span_id,
            status="success",
            output_summary="开发完成"
        )
        
        # 9. 显示结果
        print("\n" + "=" * 60)
        print("✅ 开发完成！")
        print("=" * 60)
        
        print("\n📊 执行统计:")
        print(f"   总任务数：{len(result.task_results)}")
        print(f"   总耗时：{result.total_duration_ms / 1000:.2f}秒")
        
        success_count = sum(
            1 for r in result.task_results.values() 
            if r.status == "success"
        )
        print(f"   成功：{success_count}")
        
        print("\n📁 生成的文件:")
        for task_id, task_result in result.task_results.items():
            if task_result.output and 'file' in task_result.output:
                print(f"   - {task_result.output['file']}")
        
        print("\n💡 下一步:")
        print("   1. 查看生成的代码文件")
        print("   2. 运行：python todo.py --help")
        print("   3. 尝试添加任务：python todo.py add '买牛奶'")
        
    except Exception as e:
        tracer.end_span(span_id, status="failure", error=str(e))
        print(f"\n❌ 开发失败：{e}")
        raise
    
    finally:
        # 10. 保存追踪日志
        tracer.dump_to_file(trace_id)
        print(f"\n📝 追踪日志已保存到：logs/{trace_id}.json")

if __name__ == "__main__":
    asyncio.run(develop_todo_app())
```

### 4.2 运行示例

```bash
python todo_app.py
```

### 4.3 预期输出

```
============================================================
🚀 开始开发待办事项应用
============================================================

📌 步骤 1: 解析需求
   目标：开发一个命令行待办事项应用
   复杂度：complex

📌 步骤 2: 生成开发计划
   计划 ID: plan_todo_123
   任务数：4
   1. 设计数据结构 (product_manager)
   2. 实现添加任务功能 (backend)
   3. 实现查看任务功能 (backend)
   4. 实现完成任务功能 (backend)

📌 步骤 3: 执行开发任务
...

============================================================
✅ 开发完成！
============================================================

📊 执行统计:
   总任务数：4
   总耗时：8.52 秒
   成功：4

📁 生成的文件:
   - todo.py
   - data.json
   - README.md

💡 下一步:
   1. 查看生成的代码文件
   2. 运行：python todo.py --help
   3. 尝试添加任务：python todo.py add '买牛奶'

📝 追踪日志已保存到：logs/trace_plan_todo_123.json
```

---

## 5. 下一步学习

### 5.1 推荐学习路径

```
快速入门 → 使用示例 → API 文档 → 架构设计 → 开发者指南
```

### 5.2 更多资源

#### 📚 文档
- [使用示例文档](examples/usage_examples.md) - 丰富的代码示例
- [API 文档](api/core_components.md) - 详细的 API 参考
- [架构设计](architecture/agentos_cta_design.md) - 深入理解系统架构
- [开发者指南](guides/developer_guide.md) - 开发和调试技巧

#### 💻 示例代码
- [简单任务处理](examples/usage_examples.md#21-简单任务处理)
- [多轮对话](examples/usage_examples.md#22-多轮对话)
- [文件操作](examples/usage_examples.md#23-文件操作)
- [完整应用开发](examples/usage_examples.md#31-完整应用开发流程)

#### 🔧 工具
- CLI 工具 - 命令行交互
- WebSocket 客户端 - 实时通信
- HTTP API 集成 - Web 服务集成

### 5.3 实践建议

1. **从简单开始**: 先运行 Hello World 示例，熟悉基本流程
2. **逐步深入**: 尝试修改示例代码，观察输出变化
3. **实际项目**: 选择一个小型项目，应用所学知识
4. **参与社区**: 加入讨论，分享经验和问题

### 5.4 常见问题

#### Q: 如何更换 AI 模型？

A: 修改配置中的模型名称：

```python
config = {
    "models": [
        {"name": "claude-3-sonnet", "context_window": 200000}
    ]
}
```

#### Q: 如何处理长文本？

A: 使用 Router 的自动截断功能：

```python
intent = await router.parse_intent(long_text)
truncated = router.adaptive_truncate(long_text, max_tokens=4000)
```

#### Q: 如何保存生成的代码？

A: 从计划结果中提取：

```python
for task_result in result.task_results.values():
    if task_result.output and 'code' in task_result.output:
        with open('output.py', 'w') as f:
            f.write(task_result.output['code'])
```

#### Q: 遇到问题怎么办？

A: 
1. 查看日志文件：`logs/*.json`
2. 启用调试模式：`export LOG_LEVEL=DEBUG`
3. 查阅文档：[开发者指南](guides/developer_guide.md#6-故障排查)
4. 提交 Issue: GitHub Issues

---

## 🎉 恭喜您完成快速入门！

现在您已经：
- ✅ 成功安装了 AgentOS
- ✅ 运行了第一个示例
- ✅ 理解了核心概念
- ✅ 完成了完整的应用开发示例

接下来，您可以：
- 📖 阅读 [使用示例文档](examples/usage_examples.md) 学习更多场景
- 🔍 研究 [API 文档](api/core_components.md) 了解详细接口
- 🏗️ 查看 [架构设计](architecture/agentos_cta_design.md) 深入理解系统
- 👨‍💻 参考 [开发者指南](guides/developer_guide.md) 开始实际开发

祝您开发愉快！🚀

---

**文档维护**: SpharxWorks Team  
**联系方式**: lidecheng@spharx.cn, wangliren@spharx.cn  
**项目地址**: https://github.com/spharx/spharxworks
