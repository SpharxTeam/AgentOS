# AgentOS CoreLoopThree 使用示例

**版本**: v1.0.0  
**最后更新**: 2026-03-11  

---

## 📋 目录

1. [快速开始](#1-快速开始)
2. [基础示例](#2-基础示例)
   - [简单任务处理](#21-简单任务处理)
   - [多轮对话](#22-多轮对话)
   - [文件操作](#23-文件操作)
3. [高级示例](#3-高级示例)
   - [完整应用开发流程](#31-完整应用开发流程)
   - [并行任务执行](#32-并行任务执行)
   - [错误处理与补偿](#33-错误处理与补偿)
4. [集成示例](#4-集成示例)
   - [HTTP API 集成](#41-http-api 集成)
   - [WebSocket 实时通信](#42-websocket 实时通信)
   - [CLI 工具集成](#43-cli 工具集成)
5. [最佳实践](#5-最佳实践)

---

## 1. 快速开始

### 安装依赖

```bash
pip install agentos-cta
```

### 最小化示例

```python
import asyncio
from agentos_cta import AppServer, Router, DualModelCoordinator

async def main():
    # 1. 初始化配置
    config = {
        "models": [
            {"name": "gpt-3.5-turbo", "context_window": 4096},
            {"name": "gpt-4", "context_window": 8192}
        ],
        "session": {"timeout_seconds": 3600}
    }
    
    # 2. 启动服务器
    server = AppServer(config)
    await server.start()
    
    # 3. 处理请求
    router = Router(config)
    coordinator = DualModelCoordinator(
        primary_model="gpt-4",
        secondary_models=["gpt-3.5-turbo"],
        config=config
    )
    
    # 4. 用户输入
    user_input = "帮我写一个 Python 函数，计算斐波那契数列"
    
    # 5. 解析意图
    intent = await router.parse_intent(user_input)
    
    # 6. 生成计划
    plan = await coordinator.generate_plan(intent, context={})
    
    print(f"计划 ID: {plan.plan_id}")
    print(f"任务数量：{len(plan.tasks)}")
    
    # 7. 停止服务器
    await server.stop()

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 2. 基础示例

### 2.1 简单任务处理

#### 示例 1: 代码生成

```python
import asyncio
from agentos_cta import (
    Router,
    DualModelCoordinator,
    Dispatcher,
    AgentPool,
    TraceabilityTracer
)

async def generate_code():
    """代码生成示例"""
    
    # 初始化组件
    config = {
        "models": [
            {"name": "gpt-4", "context_window": 8192}
        ]
    }
    
    router = Router(config)
    coordinator = DualModelCoordinator(
        primary_model="gpt-4",
        secondary_models=["gpt-3.5-turbo"],
        config=config
    )
    dispatcher = Dispatcher(registry_client=None, config=config)
    tracer = TraceabilityTracer({"log_dir": "logs"})
    
    # 用户需求
    user_input = """
    创建一个 Python 类，实现以下功能：
    1. 连接 MySQL 数据库
    2. 执行 CRUD 操作
    3. 支持事务处理
    4. 包含错误处理和日志记录
    """
    
    # 意图解析
    intent = await router.parse_intent(user_input)
    print(f"意图：{intent.goal}")
    print(f"复杂度：{intent.complexity}")
    
    # 生成计划
    plan = await coordinator.generate_plan(intent, context={})
    print(f"\n生成计划：{plan.plan_id}")
    
    # 开始追踪
    trace_id = f"trace_{plan.plan_id}"
    span_id = tracer.start_span(
        task_id=plan.plan_id,
        input_summary="数据库操作类生成"
    )
    
    try:
        # 执行计划
        result = await dispatcher.dispatch_plan(plan, context={})
        
        # 结束追踪
        tracer.end_span(
            span_id=span_id,
            status="success",
            output_summary=f"完成 {len(result.task_results)} 个任务"
        )
        
        # 输出结果
        print("\n=== 执行结果 ===")
        for task_id, task_result in result.task_results.items():
            print(f"\n任务 {task_id}: {task_result.status}")
            if task_result.output:
                print(f"输出：{str(task_result.output)[:200]}...")
        
        tracer.dump_to_file(trace_id)
        
    except Exception as e:
        tracer.end_span(span_id, status="failure", error=str(e))
        raise

if __name__ == "__main__":
    asyncio.run(generate_code())
```

#### 示例 2: 数据分析

```python
async def analyze_data():
    """数据分析示例"""
    
    config = {
        "models": [{"name": "gpt-4", "context_window": 8192}],
        "execution": {"sandbox_enabled": True}
    }
    
    router = Router(config)
    coordinator = DualModelCoordinator("gpt-4", ["gpt-3.5-turbo"], config)
    dispatcher = Dispatcher(None, config)
    
    user_input = """
    分析以下销售数据：
    1. 计算月度总销售额
    2. 找出最畅销的产品
    3. 生成可视化图表
    4. 提供改进建议
    
    数据格式：CSV，包含字段：日期、产品名、销量、单价
    """
    
    intent = await router.parse_intent(user_input)
    plan = await coordinator.generate_plan(intent, context={})
    
    # 添加数据文件路径到上下文
    context = {
        "data_file": "data/sales_2024.csv",
        "output_dir": "output/analysis"
    }
    
    result = await dispatcher.dispatch_plan(plan, context)
    
    print(f"\n分析完成！")
    print(f"报告路径：{result.output.get('report_path')}")
    print(f"图表路径：{result.output.get('chart_paths')}")

# asyncio.run(analyze_data())
```

---

### 2.2 多轮对话

```python
import asyncio
from agentos_cta import SessionManager, Router, DualModelCoordinator

class MultiTurnConversation:
    """多轮对话管理器"""
    
    def __init__(self, config: dict):
        self.config = config
        self.session_manager = SessionManager(config)
        self.router = Router(config)
        self.coordinator = DualModelCoordinator(
            primary_model="gpt-4",
            secondary_models=["gpt-3.5-turbo"],
            config=config
        )
        self.context = {}
    
    async def chat(self, user_input: str) -> str:
        """
        发送消息并获取回复
        
        Args:
            user_input: 用户输入
        
        Returns:
            str: AI 回复
        """
        # 创建或获取会话
        if not hasattr(self, 'session'):
            self.session = await self.session_manager.create_session({
                "user_id": "user_123"
            })
        
        # 更新上下文
        self.context["history"] = self.context.get("history", [])
        self.context["history"].append({
            "role": "user",
            "content": user_input
        })
        
        # 解析意图
        intent = await self.router.parse_intent(
            user_input,
            context=self.context
        )
        
        # 生成回复
        plan = await self.coordinator.generate_plan(intent, self.context)
        
        # 简化处理：直接返回第一个任务的结果
        response = plan.metadata.get("response", "抱歉，我无法回答")
        
        # 更新历史记录
        self.context["history"].append({
            "role": "assistant",
            "content": response
        })
        
        return response


async def demo_conversation():
    """演示多轮对话"""
    
    config = {
        "models": [{"name": "gpt-4", "context_window": 8192}],
        "session": {"timeout_seconds": 1800}
    }
    
    conversation = MultiTurnConversation(config)
    
    # 第一轮：需求咨询
    print("用户：我想开发一个电商网站")
    response = await conversation.chat("我想开发一个电商网站")
    print(f"AI: {response}\n")
    
    # 第二轮：技术选型
    print("用户：应该用什么技术栈？")
    response = await conversation.chat("应该用什么技术栈？")
    print(f"AI: {response}\n")
    
    # 第三轮：详细设计
    print("用户：数据库怎么设计？")
    response = await conversation.chat("数据库怎么设计？")
    print(f"AI: {response}\n")

# asyncio.run(demo_conversation())
```

---

### 2.3 文件操作

```python
import asyncio
from agentos_cta import (
    Router,
    DualModelCoordinator,
    Dispatcher,
    AgentPool,
    VirtualWorkbench,
    PermissionEngine
)

async def file_operations_demo():
    """文件操作示例"""
    
    config = {
        "models": [{"name": "gpt-4", "context_window": 8192}],
        "workbench": {
            "resource_limits": {
                "cpu_cores": 2,
                "memory_mb": 1024,
                "disk_mb": 512
            }
        }
    }
    
    # 初始化沙箱
    workbench = VirtualWorkbench(config["workbench"])
    workbench_id = await workbench.create("agent_dev_001")
    
    try:
        # 初始化核心组件
        router = Router(config)
        coordinator = DualModelCoordinator("gpt-4", ["gpt-3.5-turbo"], config)
        dispatcher = Dispatcher(None, config)
        
        user_input = """
        在项目目录下创建一个 Python 项目结构：
        1. 创建 src/ 目录和 __init__.py
        2. 创建 main.py 文件，包含 Hello World 代码
        3. 创建 requirements.txt
        4. 创建 README.md 说明文档
        """
        
        intent = await router.parse_intent(user_input)
        plan = await coordinator.generate_plan(intent, context={})
        
        # 添加工作目录到上下文
        context = {
            "workbench_id": workbench_id,
            "project_root": f"/tmp/agentos_workbench/{workbench_id}/data"
        }
        
        result = await dispatcher.dispatch_plan(plan, context)
        
        print("项目创建完成！")
        print(f"任务执行数：{len(result.task_results)}")
        
    finally:
        # 清理沙箱
        await workbench.destroy(workbench_id)

# asyncio.run(file_operations_demo())
```

---

## 3. 高级示例

### 3.1 完整应用开发流程

```python
import asyncio
from agentos_cta import (
    Router,
    DualModelCoordinator,
    IncrementalPlanner,
    Dispatcher,
    AgentPool,
    CompensationManager,
    TraceabilityTracer
)

async def full_app_development():
    """完整应用开发流程示例"""
    
    config = {
        "models": [
            {"name": "gpt-4", "context_window": 8192},
            {"name": "gpt-3.5-turbo", "context_window": 4096}
        ],
        "agents": {
            "roles": ["product_manager", "architect", "frontend", "backend", "qa"]
        },
        "compensation": {
            "retry_policy": {"max_retries": 3},
            "human_intervention": {"enabled": True}
        }
    }
    
    # 初始化所有组件
    router = Router(config)
    coordinator = DualModelCoordinator("gpt-4", ["gpt-3.5-turbo", "claude-3-sonnet"], config)
    planner = IncrementalPlanner(config)
    dispatcher = Dispatcher(None, config)
    agent_pool = AgentPool(None, config)
    comp_mgr = CompensationManager(config["compensation"])
    tracer = TraceabilityTracer({"log_dir": "logs/traces"})
    
    # 用户需求
    user_input = """
    开发一个完整的待办事项（Todo）应用，要求：
    
    前端：
    - React + TypeScript
    - 响应式设计
    - 支持拖拽排序
    
    后端：
    - FastAPI
    - PostgreSQL 数据库
    - JWT 认证
    
    功能：
    - 用户注册登录
    - 创建/编辑/删除任务
    - 任务分类和标签
    - 截止日期提醒
    """
    
    # 阶段 1: 需求分析
    print("=" * 60)
    print("阶段 1: 需求分析")
    print("=" * 60)
    
    intent = await router.parse_intent(user_input)
    initial_plan = await coordinator.generate_plan(intent, context={})
    
    trace_id = f"trace_{initial_plan.plan_id}"
    span_id = tracer.start_span(
        task_id=initial_plan.plan_id,
        input_summary="Todo 应用开发"
    )
    
    # 阶段 2: 架构设计
    print("\n" + "=" * 60)
    print("阶段 2: 架构设计")
    print("=" * 60)
    
    arch_context = {
        "requirements": initial_plan.metadata.get("requirements"),
        "tech_stack": {
            "frontend": "React + TypeScript",
            "backend": "FastAPI + PostgreSQL",
            "auth": "JWT"
        }
    }
    
    arch_plan = planner.create_initial_plan(
        goal="设计系统架构",
        context=arch_context
    )
    
    arch_result = await dispatcher.dispatch_plan(arch_plan, arch_context)
    
    # 阶段 3: 增量开发
    print("\n" + "=" * 60)
    print("阶段 3: 增量开发")
    print("=" * 60)
    
    dev_plan = planner.extend_plan(
        current_plan=arch_plan,
        completed_tasks=list(arch_result.task_results.values()),
        feedback={"architecture_approved": True}
    )
    
    # 预热 Agent
    await agent_pool.warmup_agents(["frontend", "backend", "qa"])
    
    # 并行执行开发任务
    dev_result = await dispatcher.dispatch_plan(
        dev_plan,
        context={**arch_context, "parallel_limit": 3}
    )
    
    # 阶段 4: 测试与修复
    print("\n" + "=" * 60)
    print("阶段 4: 测试与修复")
    print("=" * 60)
    
    test_plan = planner.create_initial_plan(
        goal="执行测试并修复 bug",
        context={
            "codebase": dev_result.output,
            "test_types": ["unit", "integration", "e2e"]
        }
    )
    
    test_result = await dispatcher.dispatch_plan(test_plan, test_plan.metadata)
    
    # 处理失败的任务（如果有）
    failed_tasks = [
        (task_id, result) 
        for task_id, result in test_result.task_results.items()
        if result.status == "failure"
    ]
    
    if failed_tasks:
        print(f"\n发现 {len(failed_tasks)} 个失败任务，开始补偿...")
        
        # 执行补偿
        action_ids = []
        for task_id, result in failed_tasks:
            action_id = f"act_{task_id}"
            action_ids.append(action_id)
            
            await comp_mgr.register_action(
                action_id=action_id,
                task_id=task_id,
                unit_id=result.agent_id,
                input_data={},
                result=result.output,
                compensator_id="rollback_changes"
            )
        
        # 逆序补偿
        comp_report = await comp_mgr.compensate_sequence(action_ids)
        print(f"补偿完成：成功 {len(comp_report.successful)}, 失败 {len(comp_report.failed)}")
    
    # 结束追踪
    tracer.end_span(
        span_id=span_id,
        status="completed",
        output_summary="Todo 应用开发完成"
    )
    tracer.dump_to_file(trace_id)
    
    # 输出最终报告
    print("\n" + "=" * 60)
    print("项目完成报告")
    print("=" * 60)
    print(f"总任务数：{len(test_result.task_results)}")
    print(f"成功：{sum(1 for r in test_result.task_results.values() if r.status == 'success')}")
    print(f"失败：{len(failed_tasks)}")
    print(f"总耗时：{test_result.total_duration_ms / 1000:.2f}秒")
    print(f"TraceID: {trace_id}")
    
    return test_result

# asyncio.run(full_app_development())
```

---

### 3.2 并行任务执行

```python
import asyncio
from agentos_cta import Dispatcher, IncrementalPlanner

async def parallel_execution_demo():
    """并行任务执行示例"""
    
    config = {
        "models": [{"name": "gpt-4", "context_window": 8192}],
        "dispatcher": {
            "weights": {'cost': 0.2, 'performance': 0.5, 'trust': 0.3},
            "parallel_limit": 5
        }
    }
    
    planner = IncrementalPlanner(config)
    dispatcher = Dispatcher(None, config)
    
    # 创建包含并行任务的计划
    plan = planner.create_initial_plan(
        goal="生成多个微服务代码",
        context={"project_type": "microservices"}
    )
    
    # 手动添加可并行的任务
    services = ["user-service", "order-service", "payment-service", "notification-service"]
    
    for service in services:
        task = planner.create_task(
            name=f"开发{service}",
            role="backend",
            dependencies=[],  # 无依赖，可并行
            metadata={"service_name": service}
        )
        plan.dag.add_node(task)
    
    print(f"计划包含 {len(plan.dag.nodes)} 个任务")
    print(f"可并行组：{planner.get_parallel_groups(plan)}")
    
    # 执行并行任务
    start_time = asyncio.get_event_loop().time()
    result = await dispatcher.dispatch_plan(plan, context={}, parallel_limit=5)
    end_time = asyncio.get_event_loop().time()
    
    print(f"\n执行完成！")
    print(f"实际耗时：{end_time - start_time:.2f}秒")
    print(f"任务状态统计:")
    
    status_count = {}
    for task_result in result.task_results.values():
        status = task_result.status
        status_count[status] = status_count.get(status, 0) + 1
    
    for status, count in status_count.items():
        print(f"  {status}: {count}")

# asyncio.run(parallel_execution_demo())
```

---

### 3.3 错误处理与补偿

```python
import asyncio
from agentos_cta import (
    CompensationManager,
    TraceabilityTracer,
    ExecutionUnit
)
from agentos_cta.utils.error_types import (
    ToolExecutionError,
    ResourceLimitError,
    CompensationError
)

class FileCreateUnit(ExecutionUnit):
    """文件创建单元（支持补偿）"""
    
    async def execute(self, input_data: dict) -> dict:
        path = input_data.get("path")
        content = input_data.get("content")
        
        # 模拟文件创建
        print(f"创建文件：{path}")
        # 实际实现：with open(path, 'w') as f: f.write(content)
        
        return {"success": True, "path": path}
    
    def compensate(self, input_data: dict, result: dict) -> dict:
        """补偿操作：删除已创建的文件"""
        path = input_data.get("path")
        print(f"补偿操作：删除文件 {path}")
        # 实际实现：os.remove(path)
        return {"deleted": path}


async def error_handling_demo():
    """错误处理与补偿示例"""
    
    config = {
        "compensation": {
            "retry_policy": {
                "max_retries": 3,
                "backoff_multiplier": 2,
                "initial_delay_ms": 1000
            },
            "human_intervention": {
                "enabled": True,
                "queue_name": "manual_queue"
            }
        }
    }
    
    comp_mgr = CompensationManager(config["compensation"])
    tracer = TraceabilityTracer({"log_dir": "logs"})
    file_unit = FileCreateUnit({})
    
    # 开始追踪
    trace_id = "trace_error_demo"
    span_id = tracer.start_span(task_id="task_error_demo")
    
    executed_actions = []
    
    try:
        # 任务 1: 创建配置文件（成功）
        result1 = await file_unit.execute({
            "path": "/tmp/config.json",
            "content": '{"debug": true}'
        })
        
        await comp_mgr.register_action(
            action_id="act_config",
            task_id="task_1",
            unit_id="file_unit",
            input_data={"path": "/tmp/config.json"},
            result=result1,
            compensator_id="file_delete"
        )
        executed_actions.append("act_config")
        
        # 任务 2: 创建数据文件（成功）
        result2 = await file_unit.execute({
            "path": "/tmp/data.db",
            "content": "binary_data"
        })
        
        await comp_mgr.register_action(
            action_id="act_data",
            task_id="task_2",
            unit_id="file_unit",
            input_data={"path": "/tmp/data.db"},
            result=result2,
            compensator_id="file_delete"
        )
        executed_actions.append("act_data")
        
        # 任务 3: 创建日志文件（失败）
        raise ToolExecutionError("磁盘空间不足")
        
    except Exception as e:
        print(f"\n❌ 发生错误：{e}")
        
        tracer.end_span(span_id, status="failure", error=str(e))
        
        # 执行补偿
        print("\n开始补偿操作...")
        comp_report = await comp_mgr.compensate_sequence(executed_actions)
        
        print(f"\n补偿报告:")
        print(f"  成功：{comp_report.successful}")
        print(f"  失败：{comp_report.failed}")
        print(f"  需要人工介入：{comp_report.human_intervention}")
        
        # 对于需要人工介入的操作
        for action_id in comp_report.human_intervention:
            await comp_mgr.add_to_human_queue(
                action_id=action_id,
                reason="自动补偿失败，需要人工确认",
                priority=1
            )
    
    tracer.dump_to_file(trace_id)

# asyncio.run(error_handling_demo())
```

---

## 4. 集成示例

### 4.1 HTTP API 集成

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from agentos_cta import AppServer, Router, DualModelCoordinator
import asyncio

app = FastAPI(title="AgentOS API", version="1.0.0")

# 全局变量存储服务器实例
server_instance = None
router_instance = None
coordinator_instance = None


class ProcessRequest(BaseModel):
    input: str
    context: dict = {}


class ProcessResponse(BaseModel):
    session_id: str
    output: str
    trace_id: str


@app.on_event("startup")
async def startup_event():
    """启动时初始化 AgentOS 服务器"""
    global server_instance, router_instance, coordinator_instance
    
    config = {
        "models": [{"name": "gpt-4", "context_window": 8192}],
        "http": {"port": 8000},
        "session": {"timeout_seconds": 3600}
    }
    
    server_instance = AppServer(config)
    router_instance = Router(config)
    coordinator_instance = DualModelCoordinator(
        primary_model="gpt-4",
        secondary_models=["gpt-3.5-turbo"],
        config=config
    )
    
    await server_instance.start()


@app.on_event("shutdown")
async def shutdown_event():
    """关闭时清理资源"""
    if server_instance:
        await server_instance.stop()


@app.post("/api/v1/process", response_model=ProcessResponse)
async def process_request(request: ProcessRequest):
    """处理用户请求"""
    try:
        # 解析意图
        intent = await router_instance.parse_intent(
            request.input,
            context=request.context
        )
        
        # 生成计划
        plan = await coordinator_instance.generate_plan(
            intent,
            context=request.context
        )
        
        # 返回结果
        return ProcessResponse(
            session_id=plan.plan_id,
            output=plan.metadata.get("response", ""),
            trace_id=f"trace_{plan.plan_id}"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "version": "1.0.0"}


# 运行服务器
# uvicorn main:app --host 0.0.0.0 --port 8000
```

---

### 4.2 WebSocket 实时通信

```python
import asyncio
import json
from websockets import serve, WebSocketServerProtocol
from agentos_cta import (
    SessionManager,
    Router,
    DualModelCoordinator,
    TraceabilityTracer
)

class WebSocketHandler:
    """WebSocket 处理器"""
    
    def __init__(self, config: dict):
        self.config = config
        self.session_manager = SessionManager(config)
        self.router = Router(config)
        self.coordinator = DualModelCoordinator(
            primary_model="gpt-4",
            secondary_models=["gpt-3.5-turbo"],
            config=config
        )
        self.tracer = TraceabilityTracer({"log_dir": "logs"})
        self.sessions = {}  # websocket -> session_id
    
    async def handle_connection(self, websocket: WebSocketServerProtocol):
        """处理 WebSocket 连接"""
        session = await self.session_manager.create_session({
            "client_type": "websocket",
            "remote_address": websocket.remote_address
        })
        
        self.sessions[websocket] = session.session_id
        
        print(f"新连接：{session.session_id}")
        
        # 发送欢迎消息
        await websocket.send(json.dumps({
            "type": "welcome",
            "session_id": session.session_id
        }))
        
        try:
            async for message in websocket:
                await self.handle_message(websocket, message)
        except Exception as e:
            print(f"连接错误：{e}")
        finally:
            # 清理会话
            if websocket in self.sessions:
                await self.session_manager.delete_session(self.sessions[websocket])
                del self.sessions[websocket]
    
    async def handle_message(self, websocket: WebSocketServerProtocol, message: str):
        """处理单条消息"""
        try:
            data = json.loads(message)
            
            if data.get("type") == "request":
                # 发送处理中通知
                await websocket.send(json.dumps({
                    "type": "progress",
                    "status": "processing",
                    "message": "正在处理您的请求..."
                }))
                
                # 解析意图
                intent = await self.router.parse_intent(
                    data.get("input", ""),
                    context={"session_id": self.sessions[websocket]}
                )
                
                # 生成计划
                plan = await self.coordinator.generate_plan(
                    intent,
                    context={"session_id": self.sessions[websocket]}
                )
                
                # 流式输出（模拟）
                response_text = plan.metadata.get("response", "")
                for i in range(0, len(response_text), 50):
                    chunk = response_text[i:i+50]
                    await websocket.send(json.dumps({
                        "type": "stream_chunk",
                        "chunk": chunk
                    }))
                    await asyncio.sleep(0.1)  # 模拟打字延迟
                
                # 发送完成通知
                await websocket.send(json.dumps({
                    "type": "complete",
                    "trace_id": f"trace_{plan.plan_id}"
                }))
            
        except json.JSONDecodeError:
            await websocket.send(json.dumps({
                "type": "error",
                "message": "无效的 JSON 格式"
            }))
        except Exception as e:
            await websocket.send(json.dumps({
                "type": "error",
                "message": str(e)
            }))


async def websocket_server():
    """启动 WebSocket 服务器"""
    config = {
        "models": [{"name": "gpt-4", "context_window": 8192}],
        "session": {"timeout_seconds": 1800}
    }
    
    handler = WebSocketHandler(config)
    
    async with serve(
        handler.handle_connection,
        "localhost",
        8765
    ) as server:
        print("WebSocket 服务器已启动：ws://localhost:8765")
        await server.serve_forever()

# asyncio.run(websocket_server())
```

---

### 4.3 CLI 工具集成

```python
#!/usr/bin/env python3
"""
AgentOS CLI 工具
使用方法:
    python cli_tool.py "帮我写一个 Python 脚本"
"""

import sys
import json
import asyncio
import aiohttp
from typing import Optional

class AgentOSCLI:
    """AgentOS 命令行工具"""
    
    def __init__(self, api_url: str = "http://localhost:8000"):
        self.api_url = api_url
        self.session_id: Optional[str] = None
    
    async def process(self, user_input: str, verbose: bool = False):
        """处理用户输入"""
        
        url = f"{self.api_url}/api/v1/process"
        payload = {
            "input": user_input,
            "context": {"cli": True}
        }
        
        if verbose:
            print(f"发送请求到：{url}")
            print(f"输入：{user_input}\n")
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    if verbose:
                        print(f"会话 ID: {result['session_id']}")
                        print(f"Trace ID: {result['trace_id']}\n")
                        print("=" * 60)
                    
                    print(result['output'])
                    
                    if verbose:
                        print("=" * 60)
                    
                    self.session_id = result['session_id']
                    
                else:
                    error = await response.json()
                    print(f"错误：{error.get('detail', '未知错误')}", file=sys.stderr)
                    sys.exit(1)
    
    async def get_status(self):
        """获取会话状态"""
        if not self.session_id:
            print("没有活跃的会话")
            return
        
        url = f"{self.api_url}/api/v1/session/{self.session_id}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    status = await response.json()
                    print(json.dumps(status, indent=2))
                else:
                    print("无法获取会话状态")


async def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="AgentOS CLI 工具")
    parser.add_argument("input", nargs="?", help="用户输入")
    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="API 服务器地址"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="详细输出"
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="获取会话状态"
    )
    
    args = parser.parse_args()
    
    cli = AgentOSCLI(api_url=args.url)
    
    if args.status:
        await cli.get_status()
    elif args.input:
        await cli.process(args.input, verbose=args.verbose)
    else:
        # 交互模式
        print("AgentOS CLI - 交互模式")
        print("输入 'quit' 或 'exit' 退出\n")
        
        while True:
            try:
                user_input = input("> ").strip()
                
                if user_input.lower() in ['quit', 'exit']:
                    break
                
                if user_input:
                    await cli.process(user_input, verbose=args.verbose)
                    
            except KeyboardInterrupt:
                print("\n再见！")
                break
            except EOFError:
                break


if __name__ == "__main__":
    asyncio.run(main())
```

---

## 5. 最佳实践

### 5.1 配置管理

```python
# 推荐：使用环境变量管理敏感配置
import os
from dotenv import load_dotenv

load_dotenv()  # 加载 .env 文件

config = {
    "models": [
        {
            "name": "gpt-4",
            "api_key": os.getenv("OPENAI_API_KEY"),
            "context_window": 8192
        }
    ],
    "database": {
        "url": os.getenv("DATABASE_URL"),
        "pool_size": int(os.getenv("DB_POOL_SIZE", "10"))
    }
}
```

### 5.2 错误处理

```python
from agentos_cta.utils.error_types import (
    AgentOSError,
    ModelUnavailableError,
    ResourceLimitError
)

async def safe_execute():
    """安全的错误处理示例"""
    
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            # 执行任务
            result = await some_operation()
            return result
            
        except ModelUnavailableError as e:
            retry_count += 1
            if retry_count >= max_retries:
                # 降级到备用模型
                result = await fallback_operation()
                return result
            
        except ResourceLimitError as e:
            # 资源超限，等待后重试
            await asyncio.sleep(2 ** retry_count)
            retry_count += 1
            
        except AgentOSError as e:
            # 其他 AgentOS 错误
            print(f"错误 [{e.code}]: {e}")
            raise
            
        except Exception as e:
            # 未知错误
            print(f"未知错误：{e}")
            raise
```

### 5.3 性能优化

```python
# 1. 使用连接池
config = {
    "database": {
        "pool_size": 20,
        "max_overflow": 10
    }
}

# 2. 批量处理任务
tasks = [task1, task2, task3, ...]
results = await asyncio.gather(*tasks, return_exceptions=True)

# 3. 缓存热点数据
from functools import lru_cache

@lru_cache(maxsize=100)
def get_agent_info(agent_id: str):
    # 从缓存获取 Agent 信息
    pass

# 4. 异步并发
async def process_multiple_inputs(inputs):
    semaphore = asyncio.Semaphore(5)  # 限制并发数为 5
    
    async def process_with_semaphore(input_text):
        async with semaphore:
            return await process_single(input_text)
    
    tasks = [process_with_semaphore(inp) for inp in inputs]
    return await asyncio.gather(*tasks)
```

### 5.4 日志与监控

```python
from agentos_cta.utils import get_logger, set_trace_id

logger = get_logger(__name__)

async def monitored_operation():
    """带日志和监控的操作"""
    
    trace_id = "trace_abc123"
    set_trace_id(trace_id)
    
    logger.info("开始处理", extra={
        "operation": "data_processing",
        "input_size": 1000
    })
    
    try:
        result = await process_data()
        
        logger.info("处理完成", extra={
            "operation": "data_processing",
            "output_size": len(result),
            "duration_ms": 1234
        })
        
        return result
        
    except Exception as e:
        logger.error("处理失败", extra={
            "operation": "data_processing",
            "error": str(e)
        })
        raise
```

---

**文档维护**: SpharxWorks Team  
**联系方式**: lidecheng@spharx.cn, wangliren@spharx.cn
