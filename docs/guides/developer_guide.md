# AgentOS CoreLoopThree 开发者指南

**版本**: v1.0.0  
**最后更新**: 2026-03-11  
**目标读者**: 开发者和系统管理员

---

## 📋 目录

1. [开发环境搭建](#1-开发环境搭建)
2. [代码规范](#2-代码规范)
3. [测试指南](#3-测试指南)
4. [调试技巧](#4-调试技巧)
5. [性能调优](#5-性能调优)
6. [故障排查](#6-故障排查)
7. [部署指南](#7-部署指南)
8. [监控与运维](#8-监控与运维)

---

## 1. 开发环境搭建

### 1.1 系统要求

| 组件 | 最低要求 | 推荐配置 |
|------|----------|----------|
| **操作系统** | Linux/macOS/Windows | Linux (Ubuntu 22.04+) |
| **CPU** | 4 核 | 8 核 + |
| **内存** | 8GB | 16GB+ |
| **存储** | 10GB | 50GB SSD |
| **Python** | 3.10+ | 3.11+ |

### 1.2 安装步骤

#### 步骤 1: 克隆代码库

```bash
git clone https://github.com/spharx/spharxworks.git
cd spharxworks/AgentOS
```

#### 步骤 2: 创建虚拟环境

```bash
# Python 3.10+
python -m venv .venv

# 激活虚拟环境
# Linux/macOS:
source .venv/bin/activate

# Windows:
.venv\Scripts\activate
```

#### 步骤 3: 安装依赖

```bash
# 安装基础依赖
pip install -r requirements.txt

# 安装开发依赖
pip install -r requirements-dev.txt

# 安装可选依赖（根据需要）
pip install -r requirements-optional.txt
```

#### 步骤 4: 环境变量配置

创建 `.env` 文件：

```bash
# API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# 数据库配置
DATABASE_URL=postgresql://user:pass@localhost:5432/agentos

# Redis 配置
REDIS_URL=redis://localhost:6379/0

# 日志配置
LOG_LEVEL=INFO
LOG_FORMAT=json

# OpenTelemetry 配置
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
```

#### 步骤 5: 初始化数据库

```bash
# 运行数据库迁移
alembic upgrade head

# 插入初始数据
python scripts/init_db.py
```

#### 步骤 6: 验证安装

```bash
# 运行单元测试
pytest tests/unit -v

# 运行健康检查
python scripts/health_check.py
```

### 1.3 IDE 配置

#### VS Code 配置

创建 `.vscode/settings.json`:

```json
{
    "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.formatting.provider": "black",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.organizeImports": true
    },
    "[python]": {
        "editor.defaultFormatter": "ms-python.black-formatter",
        "editor.tabSize": 4
    }
}
```

创建 `.vscode/launch.json`:

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: Current File",
            "type": "python",
            "request": "launch",
            "program": "${file}",
            "console": "integratedTerminal",
            "justMyCode": false,
            "env": {
                "PYTHONPATH": "${workspaceFolder}"
            }
        },
        {
            "name": "Python: FastAPI",
            "type": "python",
            "request": "launch",
            "module": "uvicorn",
            "args": [
                "agentos_cta.runtime.server:app",
                "--reload",
                "--host", "0.0.0.0",
                "--port", "8000"
            ],
            "env": {
                "PYTHONPATH": "${workspaceFolder}"
            }
        }
    ]
}
```

---

## 2. 代码规范

### 2.1 Python 编码规范

遵循 [PEP 8](https://pep8.org/) 标准，使用 Black 格式化代码。

```python
# ✅ 好的示例
from typing import Optional, List
import asyncio

class UserService:
    """用户服务类"""
    
    def __init__(self, config: dict):
        self.config = config
        self._cache = {}
    
    async def get_user(self, user_id: str) -> Optional[dict]:
        """获取用户信息"""
        if user_id in self._cache:
            return self._cache[user_id]
        
        user = await self._fetch_from_db(user_id)
        self._cache[user_id] = user
        return user


# ❌ 坏的示例
class userService:  # 类名应该大驼峰
    def __init__(s,c):  # 参数命名不规范
        s.c=c  # 缺少空格和类型注解
        pass
```

### 2.2 类型注解

所有公共 API 必须包含类型注解：

```python
from typing import Dict, List, Optional, Union, Callable
from dataclasses import dataclass
from enum import Enum

class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILURE = "failure"


@dataclass
class TaskResult:
    task_id: str
    status: TaskStatus
    output: Optional[Dict[str, any]]
    error: Optional[str]
    duration_ms: int


async def process_task(
    task_id: str,
    callback: Callable[[TaskResult], None],
    timeout: int = 300
) -> TaskResult:
    """处理任务"""
    pass
```

### 2.3 文档字符串

使用 Google 风格的 docstring：

```python
def calculate_score(
    accuracy: float,
    completion_rate: float,
    weights: Optional[Dict[str, float]] = None
) -> float:
    """
    计算综合评分
    
    Args:
        accuracy: 准确率 (0-1)
        completion_rate: 完成率 (0-1)
        weights: 权重配置，默认 {'accuracy': 0.6, 'completion': 0.4}
    
    Returns:
        float: 综合评分 (0-100)
    
    Raises:
        ValueError: 当参数超出有效范围时
    
    Example:
        >>> score = calculate_score(0.95, 0.80)
        >>> print(f"{score:.2f}")
        89.00
    """
    if not 0 <= accuracy <= 1:
        raise ValueError("accuracy must be between 0 and 1")
    
    default_weights = {'accuracy': 0.6, 'completion': 0.4}
    final_weights = weights or default_weights
    
    score = (
        accuracy * final_weights['accuracy'] +
        completion_rate * final_weights['completion']
    ) * 100
    
    return score
```

### 2.4 错误处理

```python
from agentos_cta.utils.error_types import AgentOSError, ConfigurationError

async def load_config(config_path: str) -> dict:
    """
    加载配置文件
    
    Raises:
        ConfigurationError: 当配置文件不存在或格式错误时
    """
    import os
    import json
    
    if not os.path.exists(config_path):
        raise ConfigurationError(
            f"Config file not found: {config_path}",
            details={"path": config_path}
        )
    
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ConfigurationError(
            f"Invalid JSON format: {e}",
            details={"line": e.lineno, "column": e.colno}
        )
```

### 2.5 日志规范

```python
from agentos_cta.utils import get_logger

logger = get_logger(__name__)

async def process_data(data_id: str):
    """处理数据"""
    
    # 使用结构化日志
    logger.info(
        "开始处理数据",
        extra={
            "data_id": data_id,
            "operation": "process_data",
            "stage": "start"
        }
    )
    
    try:
        result = await _do_process(data_id)
        
        logger.info(
            "数据处理完成",
            extra={
                "data_id": data_id,
                "result_size": len(result),
                "duration_ms": 1234
            }
        )
        
        return result
        
    except Exception as e:
        logger.error(
            "数据处理失败",
            extra={
                "data_id": data_id,
                "error": str(e),
                "error_type": type(e).__name__
            },
            exc_info=True  # 包含堆栈跟踪
        )
        raise
```

---

## 3. 测试指南

### 3.1 测试框架

项目使用 pytest 作为测试框架：

```bash
# 安装测试依赖
pip install pytest pytest-asyncio pytest-cov pytest-mock

# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/unit/test_router.py

# 运行特定测试函数
pytest tests/unit/test_router.py::test_parse_intent

# 生成覆盖率报告
pytest --cov=agentos_cta --cov-report=html

# 并行执行测试
pytest -n auto
```

### 3.2 单元测试示例

```python
# tests/unit/test_router.py
import pytest
from unittest.mock import Mock, AsyncMock
from agentos_cta.coreloopthree.cognition.router import Router
from agentos_cta.coreloopthree.cognition.schemas import ComplexityLevel


@pytest.fixture
def router_config():
    return {
        "complexity_thresholds": {
            "simple": 1000,
            "complex": 5000,
            "critical": 5000
        },
        "models": [
            {"name": "gpt-3.5-turbo", "context_window": 4096},
            {"name": "gpt-4", "context_window": 8192}
        ]
    }


@pytest.fixture
def router(router_config):
    return Router(router_config)


@pytest.mark.asyncio
async def test_parse_intent_simple(router):
    """测试简单意图解析"""
    intent = await router.parse_intent("你好")
    
    assert intent is not None
    assert intent.complexity == ComplexityLevel.SIMPLE
    assert intent.estimated_tokens < 1000


@pytest.mark.asyncio
async def test_parse_intent_complex(router):
    """测试复杂意图解析"""
    long_text = "帮我开发一个完整的电商网站，包括..." * 100
    intent = await router.parse_intent(long_text)
    
    assert intent.complexity in [ComplexityLevel.COMPLEX, ComplexityLevel.CRITICAL]


@pytest.mark.asyncio
async def test_match_resource(router):
    """测试资源匹配"""
    from agentos_cta.coreloopthree.cognition.schemas import Intent, ComplexityLevel
    
    intent = Intent(
        raw_text="测试",
        goal="测试目标",
        constraints=[],
        context={},
        complexity=ComplexityLevel.COMPLEX,
        estimated_tokens=3000
    )
    
    resource = router.match_resource(intent)
    
    assert resource is not None
    assert resource.model_name in ["gpt-4", "gpt-3.5-turbo"]
    assert resource.token_budget >= 3000
```

### 3.3 集成测试示例

```python
# tests/integration/test_full_flow.py
import pytest
import asyncio
from agentos_cta import (
    Router,
    DualModelCoordinator,
    Dispatcher,
    TraceabilityTracer
)


@pytest.mark.asyncio
async def test_full_execution_flow(test_config):
    """测试完整执行流程"""
    
    # 初始化组件
    router = Router(test_config)
    coordinator = DualModelCoordinator(
        primary_model="gpt-3.5-turbo",  # 测试使用便宜模型
        secondary_models=[],
        config=test_config
    )
    tracer = TraceabilityTracer({"log_dir": "test_logs"})
    
    # 执行流程
    intent = await router.parse_intent("写一个 Hello World 函数")
    plan = await coordinator.generate_plan(intent, context={})
    
    # 验证计划
    assert plan is not None
    assert len(plan.tasks) > 0
    assert plan.plan_id.startswith("plan_")
    
    # 清理
    tracer.dump_to_file(f"trace_{plan.plan_id}")
```

### 3.4 Mock 和 Fixture

```python
# tests/conftest.py
import pytest
import os
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture(scope="session")
def test_config():
    """测试配置"""
    return {
        "models": [{"name": "gpt-3.5-turbo", "context_window": 4096}],
        "session": {"timeout_seconds": 300},
        "logging": {"level": "DEBUG"}
    }


@pytest.fixture
def mock_registry_client():
    """模拟注册中心客户端"""
    client = AsyncMock()
    client.get_agents = AsyncMock(return_value=[
        {
            "agent_id": "agent_test_001",
            "role": "developer",
            "status": "available"
        }
    ])
    return client


@pytest.fixture
def mock_agent():
    """模拟 Agent"""
    agent = AsyncMock()
    agent.agent_id = "agent_test_001"
    agent.execute = AsyncMock(return_value={
        "status": "success",
        "output": {"code": "print('Hello')"}
    })
    return agent
```

---

## 4. 调试技巧

### 4.1 启用调试模式

```python
# 方法 1: 环境变量
export LOG_LEVEL=DEBUG
export AGENTOS_DEBUG=1

# 方法 2: 代码中设置
import logging
logging.basicConfig(level=logging.DEBUG)

# 方法 3: 配置文件
config = {
    "logging": {
        "level": "DEBUG",
        "format": "detailed"
    }
}
```

### 4.2 使用断点调试

```python
# 使用 pdb
import pdb; pdb.set_trace()

# Python 3.7+ 使用 breakpoint()
breakpoint()

# 在异步代码中
import asyncio
asyncio.create_task(asyncio.sleep(0))  # 让出控制权
breakpoint()
```

### 4.3 追踪执行流程

```python
from agentos_cta import TraceabilityTracer

tracer = TraceabilityTracer({"log_dir": "debug_logs"})

# 开始追踪
span_id = tracer.start_span(
    task_id="debug_task",
    agent_id="debug_agent",
    input_summary="调试输入"
)

try:
    # 执行业务逻辑
    result = await some_function()
    
    # 结束追踪
    tracer.end_span(
        span_id=span_id,
        status="success",
        output_summary=str(result)
    )
    
except Exception as e:
    tracer.end_span(
        span_id=span_id,
        status="failure",
        error=str(e)
    )
    raise

# 查看追踪树
trace_tree = tracer.get_trace_tree(tracer.get_current_trace_id())
for span in trace_tree:
    print(f"{span.span_id}: {span.status} - {span.duration_ms}ms")
```

### 4.4 内存分析

```bash
# 使用 memory_profiler
pip install memory_profiler

# 在代码中添加装饰器
from memory_profiler import profile

@profile
def my_function():
    # 内存密集型操作
    pass

# 运行分析
python -m memory_profiler script.py
```

### 4.5 性能分析

```bash
# 使用 cProfile
python -m cProfile -o output.prof script.py

# 可视化分析结果
pip install snakeviz
snakeviz output.prof

# 使用 py-spy（无需修改代码）
pip install py-spy
py-spy top -- python script.py
py-spy record -o profile.svg -- python script.py
```

---

## 5. 性能调优

### 5.1 数据库优化

```python
# 使用连接池
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True  # 自动检测失效连接
)

# 批量操作
async def batch_insert(items: List[dict]):
    """批量插入数据"""
    chunk_size = 1000
    for i in range(0, len(items), chunk_size):
        chunk = items[i:i + chunk_size]
        await db.execute(insert_query, chunk)

# 使用索引
# CREATE INDEX idx_task_status ON tasks(status);
# CREATE INDEX idx_created_at ON tasks(created_at);
```

### 5.2 缓存策略

```python
from functools import lru_cache
import asyncio

# LRU 缓存
@lru_cache(maxsize=1000)
def get_agent_info(agent_id: str) -> dict:
    # 从缓存获取
    pass

# Redis 缓存
import redis.asyncio as redis

class CacheManager:
    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url)
    
    async def get_or_set(
        self,
        key: str,
        factory: Callable,
        ttl: int = 300
    ):
        """获取或设置缓存"""
        cached = await self.redis.get(key)
        if cached:
            return cached
        
        value = await factory()
        await self.redis.setex(key, ttl, value)
        return value

# 使用示例
cache = CacheManager("redis://localhost:6379")
result = await cache.get_or_set(
    f"agent:{agent_id}",
    lambda: fetch_agent_info(agent_id),
    ttl=600
)
```

### 5.3 并发控制

```python
import asyncio

# 信号量控制并发数
semaphore = asyncio.Semaphore(10)

async def limited_task(task_id: str):
    async with semaphore:
        return await process_task(task_id)

# 批量执行
tasks = [limited_task(f"task_{i}") for i in range(100)]
results = await asyncio.gather(*tasks, return_exceptions=True)

# 超时控制
async def with_timeout(coro, timeout_seconds: float):
    try:
        return await asyncio.wait_for(coro, timeout=timeout_seconds)
    except asyncio.TimeoutError:
        raise TimeoutError(f"Operation timed out after {timeout_seconds}s")
```

### 5.4 异步优化

```python
# ❌ 避免顺序执行异步操作
async def slow_version():
    result1 = await fetch_data("url1")  # 耗时 1s
    result2 = await fetch_data("url2")  # 耗时 1s
    result3 = await fetch_data("url3")  # 耗时 1s
    # 总耗时：3s
    return [result1, result2, result3]

# ✅ 使用 gather 并发执行
async def fast_version():
    results = await asyncio.gather(
        fetch_data("url1"),
        fetch_data("url2"),
        fetch_data("url3")
    )
    # 总耗时：~1s
    return results

# ✅ 使用 wait 控制完成条件
done, pending = await asyncio.wait(
    [task1, task2, task3],
    return_when=asyncio.FIRST_COMPLETED
)
```

---

## 6. 故障排查

### 6.1 常见问题诊断表

| 问题现象 | 可能原因 | 解决方案 |
|---------|---------|---------|
| 启动失败 | 端口被占用 | `lsof -i :8000` 查找并终止进程 |
| 内存泄漏 | 缓存未清理 | 检查 LRU 缓存大小限制 |
| 请求超时 | 模型 API 慢 | 增加 timeout 或降级到轻量模型 |
| 数据库连接失败 | 连接池耗尽 | 增加 pool_size 或检查慢查询 |
| TraceID 丢失 | 上下文未传递 | 使用 set_trace_id() 确保传递 |

### 6.2 日志分析

```bash
# 查看最近的错误日志
tail -f logs/app.log | grep ERROR

# 统计错误类型
grep "ERROR" logs/app.log | cut -d':' -f3 | sort | uniq -c | sort -rn

# 查看特定 TraceID 的完整日志
grep "trace_abc123" logs/*.log | jq .

# 分析慢请求
grep "duration_ms.*[0-9]{4,}" logs/app.log | jq '. | select(.duration_ms > 1000)'
```

### 6.3 性能问题排查

```python
# 启用慢查询日志
import logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

# 监控任务队列
from prometheus_client import Gauge
queue_size = Gauge('task_queue_size', 'Current queue size')

# 定期检查
async def monitor_queue():
    while True:
        queue_size.set(len(task_queue))
        await asyncio.sleep(5)
```

### 6.4 内存泄漏排查

```python
# 使用 tracemalloc
import tracemalloc

tracemalloc.start()

# ... 执行代码 ...

current, peak = tracemalloc.get_traced_memory()
print(f"当前内存：{current / 1024 / 1024:.2f} MB")
print(f"峰值内存：{peak / 1024 / 1024:.2f} MB")

tracemalloc.stop()

# 查看内存分配详情
snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics('lineno')

for stat in top_stats[:10]:
    print(stat)
```

---

## 7. 部署指南

### 7.1 Docker 部署

#### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY . .

# 创建非 root 用户
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 启动命令
CMD ["uvicorn", "agentos_cta.runtime.server:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### docker-compose.yml

```yaml
version: '3.8'

services:
  agentos:
    build: .
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - DATABASE_URL=postgresql://postgres:pass@db:5432/agentos
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped

  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=agentos
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

### 7.2 Kubernetes 部署

#### deployment.yaml

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: agentos
spec:
  replicas: 3
  selector:
    matchLabels:
      app: agentos
  template:
    metadata:
      labels:
        app: agentos
    spec:
      containers:
      - name: agentos
        image: spharx/agentos-cta:v1.0.0
        ports:
        - containerPort: 8000
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: agentos-secrets
              key: openai-api-key
        - name: DATABASE_URL
          valueFrom:
            configMapKeyRef:
              name: agentos-config
              key: database-url
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

### 7.3 生产环境配置

```python
# config.production.py
production_config = {
    "models": [
        {
            "name": "gpt-4-turbo",
            "api_key_env": "OPENAI_API_KEY",
            "context_window": 128000,
            "rate_limit": 100  # 每分钟请求数
        }
    ],
    "database": {
        "pool_size": 50,
        "max_overflow": 20,
        "pool_timeout": 30,
        "pool_recycle": 1800
    },
    "redis": {
        "max_connections": 100,
        "socket_timeout": 5,
        "socket_connect_timeout": 5
    },
    "logging": {
        "level": "INFO",
        "format": "json",
        "output": "stdout"
    },
    "server": {
        "workers": 4,  # CPU 核数 * 2 + 1
        "worker_class": "uvicorn.workers.UvicornWorker",
        "keep_alive": 5,
        "limit_concurrency": 1000
    }
}
```

---

## 8. 监控与运维

### 8.1 Prometheus 指标

```python
from prometheus_client import Counter, Histogram, Gauge, start_http_server

# 定义指标
REQUEST_COUNT = Counter(
    'agentos_requests_total',
    'Total requests',
    ['method', 'status']
)

REQUEST_DURATION = Histogram(
    'agentos_request_duration_seconds',
    'Request duration',
    ['method'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 5.0, 10.0]
)

ACTIVE_SESSIONS = Gauge(
    'agentos_active_sessions',
    'Active sessions'
)

TOKEN_USAGE = Counter(
    'agentos_token_usage_total',
    'Token usage',
    ['model', 'type']
)

# 启动指标服务器
start_http_server(9090)
```

### 8.2 Grafana 仪表板

导入以下仪表板 ID：
- **应用监控**: 10000+
- **Prometheus 指标**: 9000+

关键面板：
1. 请求速率和延迟
2. 错误率趋势
3. Token 使用量
4. 活跃会话数
5. 数据库连接池状态

### 8.3 告警规则

```yaml
# prometheus_alerts.yml
groups:
- name: agentos_alerts
  rules:
  - alert: HighErrorRate
    expr: sum(rate(agentos_requests_total{status="error"}[5m])) / sum(rate(agentos_requests_total[5m])) > 0.05
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "高错误率"
      description: "错误率超过 5%"
  
  - alert: HighLatency
    expr: histogram_quantile(0.95, rate(agentos_request_duration_seconds_bucket[5m])) > 5
    for: 10m
    labels:
      severity: warning
    annotations:
      summary: "高延迟"
      description: "P95 延迟超过 5 秒"
  
  - alert: LowSessionCount
    expr: agentos_active_sessions < 10
    for: 1h
    labels:
      severity: info
    annotations:
      summary: "会话数过低"
      description: "活跃会话数低于 10，持续 1 小时"
```

### 8.4 日志收集

```yaml
# fluentd 配置
<match agentos.**>
  @type elasticsearch
  host elasticsearch.logging.svc
  port 9200
  logstash_format true
  logstash_prefix agentos-logs
  flush_interval 5s
</match>
```

### 8.5 备份策略

```bash
#!/bin/bash
# backup.sh - 数据库备份脚本

BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="agentos"

# 备份数据库
pg_dump $DATABASE_URL > $BACKUP_DIR/db_$DATE.sql

# 压缩备份
gzip $BACKUP_DIR/db_$DATE.sql

# 删除 7 天前的备份
find $BACKUP_DIR -name "db_*.sql.gz" -mtime +7 -delete

# 上传到对象存储（可选）
aws s3 cp $BACKUP_DIR/db_$DATE.sql.gz s3://backets/backups/
```

---

## 附录

### A. 快捷键参考

| 操作 | 快捷键 | 说明 |
|------|--------|------|
| 运行测试 | `pytest` | 运行所有测试 |
| 格式化代码 | `black .` | 格式化所有 Python 文件 |
| 检查类型 | `mypy .` | 类型检查 |
| 查看日志 | `tail -f logs/app.log` | 实时查看日志 |

### B. 常用命令

```bash
# 开发环境
pip install -e .                    # 可编辑安装
black .                             # 格式化代码
mypy .                              # 类型检查
pytest --cov                        # 运行测试并生成覆盖率

# 生产环境
docker-compose up -d                # 后台启动
docker-compose logs -f              # 查看日志
kubectl apply -f deployment.yaml    # K8s 部署
```

### C. 参考资料

- [官方文档](https://github.com/spharx/spharxworks)
- [Python 异步编程](https://docs.python.org/3/library/asyncio.html)
- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [Prometheus 最佳实践](https://prometheus.io/docs/practices/)

---

**文档维护**: SpharxWorks Team  
**联系方式**: lidecheng@spharx.cn, wangliren@spharx.cn
