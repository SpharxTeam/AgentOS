# AgentOS 脚本工具集 (Scripts)

**版本**: 1.0.0.3  
**最后更新**: 2026-03-18  

---

## 📋 概述

`scripts/` 目录包含 AgentOS 项目的所有运维和开发辅助脚本，涵盖构建、部署、测试、文档生成等全流程自动化工具。

---

## 📁 脚本分类

```
scripts/
├── README.md                    # 本文件
│
├── build.sh                     # 构建脚本 ⭐
├── install.sh                   # 安装脚本
├── install.ps1                  # Windows 安装脚本
├── quickstart.sh                # 快速启动脚本
│
├── init_config.py               # 配置初始化 ⭐
├── doctor.py                    # 健康检查 ⭐
├── validate_contracts.py        # 合约验证
├── update_registry.py           # 注册表更新
├── generate_docs.py             # 文档生成
├── benchmark.py                 # 性能基准测试 ⭐
│
├── run_example.sh               # 示例运行脚本
│
└── docker/                      # Docker 相关脚本
    ├── Dockerfile.kernel        # 内核镜像
    ├── Dockerfile.service       # 服务镜像
    └── docker-compose.yml       # Docker Compose 配置
```

---

## 🔧 核心脚本详解

### 1. build.sh - 构建脚本 ⭐

**功能**: 自动化编译整个项目

**使用方法**:
```bash
# 默认构建（Release 模式）
./scripts/build.sh

# Debug 模式构建
./scripts/build.sh --debug

# 并行编译（指定核心数）
./scripts/build.sh --jobs 8

# 清理并重新构建
./scripts/build.sh --clean

# 只构建特定模块
./scripts/build.sh --module atoms
./scripts/build.sh --module backs/llm_d
```

**内部流程**:
```bash
#!/bin/bash

# 1. 检查依赖
check_dependencies()

# 2. 创建构建目录
mkdir -p build && cd build

# 3. 配置 CMake
cmake ../atoms \
  -DCMAKE_BUILD_TYPE=${BUILD_TYPE} \
  -DBUILD_TESTS=${BUILD_TESTS} \
  -DENABLE_TRACING=${ENABLE_TRACING}

# 4. 编译
cmake --build . --parallel ${JOBS}

# 5. 运行测试（可选）
ctest --output-on-failure

# 6. 安装（可选）
sudo cmake --install .
```

---

### 2. init_config.py - 配置初始化 ⭐

**功能**: 初始化项目配置，复制环境变量模板，生成必要的配置文件

**使用方法**:
```bash
# 交互式初始化
python scripts/init_config.py

# 非交互式（使用默认值）
python scripts/init_config.py --yes

# 指定配置目录
python scripts/init_config.py --config-dir /path/to/config
```

**初始化流程**:
```python
def main():
    # 1. 复制环境变量
    copy(".env.example", ".env")
    
    # 2. 生成 API 密钥（如果需要）
    if not os.getenv("OPENAI_API_KEY"):
        print("请设置 OPENAI_API_KEY 环境变量")
        
    # 3. 创建必要目录
    os.makedirs("partdata/logs", exist_ok=True)
    os.makedirs("partdata/registry", exist_ok=True)
    
    # 4. 初始化数据库
    init_registry_db()
    
    # 5. 验证配置
    validate_config()
```

**生成的文件**:
- `.env` - 环境变量配置
- `partdata/registry/agents.db` - Agent 注册表
- `partdata/registry/skills.db` - 技能注册表
- `config/services/*/config.yaml` - 服务配置

---

### 3. doctor.py - 健康检查 ⭐

**功能**: 全面检查项目环境和运行状态

**使用方法**:
```bash
# 完整检查
python scripts/doctor.py

# 只检查环境依赖
python scripts/doctor.py --check-env

# 只检查服务状态
python scripts/doctor.py --check-services

# 生成诊断报告
python scripts/doctor.py --report > diagnosis.txt
```

**检查项目**:
```python
checks = {
    "环境依赖": [
        "Python 版本 >= 3.9",
        "CMake 版本 >= 3.20",
        "GCC/Clang 编译器",
        "FAISS 库",
        "SQLite3",
        "libcurl"
    ],
    
    "目录结构": [
        "atoms/ 存在",
        "backs/ 存在",
        "config/ 存在",
        "partdata/ 可写"
    ],
    
    "服务状态": [
        "LLM 服务可达 (http://localhost:18791)",
        "Dynamic 服务可达 (http://localhost:18789)",
        "数据库连接正常"
    ],
    
    "配置验证": [
        ".env 文件存在",
        "API 密钥已设置",
        "配置文件语法正确"
    ]
}
```

**输出示例**:
```
✅ Python 3.10.8 detected
✅ CMake 3.24.1 detected
✅ GCC 12.2.0 detected
✅ FAISS found at /usr/lib/libfaiss.so
✅ SQLite3 version 3.39.2
✅ Directory structure OK
✅ LLM service is running (latency: 23ms)
✅ Dynamic service is running (latency: 5ms)
✅ All checks passed!
```

---

### 4. benchmark.py - 性能基准测试 ⭐

**功能**: 测试系统各项性能指标

**使用方法**:
```bash
# 完整基准测试
python scripts/benchmark.py

# 只测试记忆写入
python scripts/benchmark.py --test memory_write

# 只测试向量检索
python scripts/benchmark.py --test vector_search

# 导出结果为 JSON
python scripts/benchmark.py --output results.json
```

**测试项目**:
```python
tests = {
    "memory_write": {
        "description": "记忆写入吞吐测试",
        "method": "异步批量写入 L1 层",
        "expected": "> 10,000 条/秒"
    },
    
    "vector_search": {
        "description": "向量检索延迟测试",
        "method": "FAISS IVF 索引查询",
        "expected": "< 10ms (k=10)"
    },
    
    "task_scheduling": {
        "description": "任务调度延迟测试",
        "method": "加权轮询算法",
        "expected": "< 1ms"
    },
    
    "intent_parsing": {
        "description": "意图解析延迟",
        "method": "简单意图识别",
        "expected": "< 50ms"
    },
    
    "concurrent_connections": {
        "description": "并发连接数测试",
        "method": "Binder IPC 最大连接",
        "expected": ">= 1024"
    }
}
```

**输出示例**:
```
=================================================
AgentOS Benchmark Suite v1.0.0.3
=================================================

[1/5] Memory Write Throughput...
  ✓ Result: 12,345 records/sec (expected: > 10,000)
  ✓ PASS

[2/5] Vector Search Latency...
  ✓ Result: 8.5ms (expected: < 10ms)
  ✓ PASS

[3/5] Task Scheduling Latency...
  ✓ Result: 0.8ms (expected: < 1ms)
  ✓ PASS

[4/5] Intent Parsing Latency...
  ✓ Result: 35ms (expected: < 50ms)
  ✓ PASS

[5/5] Concurrent Connections...
  ✓ Result: 1,024 connections
  ✓ PASS

=================================================
All tests passed! System performance is excellent.
=================================================
```

---

### 5. validate_contracts.py - 合约验证

**功能**: 验证 Agent 和技能的服务合约是否符合规范

**使用方法**:
```bash
# 验证所有合约
python scripts/validate_contracts.py

# 只验证 Agent 合约
python scripts/validate_contracts.py --type agent

# 只验证技能合约
python scripts/validate_contracts.py --type skill

# 详细输出
python scripts/validate_contracts.py --verbose
```

**验证规则**:
```python
validation_rules = {
    "agent_contract": {
        "required_fields": [
            "name",
            "version",
            "capabilities",
            "interface_version"
        ],
        "optional_fields": [
            "description",
            "author",
            "license",
            "prompts"
        ],
        "constraints": {
            "name": "^[a-z][a-z0-9_]*$",
            "version": "^\\d+\\.\\d+\\.\\d+$"
        }
    },
    
    "skill_contract": {
        "required_fields": [
            "name",
            "version",
            "library_path",
            "functions"
        ],
        "constraints": {
            "library_path": "must_exist",
            "functions": "must_be_list"
        }
    }
}
```

---

### 6. generate_docs.py - 文档生成

**功能**: 自动生成 API 文档和技术文档

**使用方法**:
```bash
# 生成所有文档
python scripts/generate_docs.py

# 只生成 Python SDK 文档
python scripts/generate_docs.py --target python-sdk

# 只生成架构图
python scripts/generate_docs.py --target diagrams

# 预览文档（启动本地服务器）
python scripts/generate_docs.py --serve
```

**支持的文档类型**:
```python
doc_targets = {
    "python-sdk": "tools/python 的 API 文档",
    "go-sdk": "tools/go 的 API 文档",
    "rust-sdk": "tools/rust 的 API 文档",
    "typescript-sdk": "tools/typescript 的 API 文档",
    "diagrams": "Mermaid 架构图转换为 PNG",
    "examples": "示例代码提取和格式化"
}
```

---

## 🐳 Docker 脚本

### docker-compose.yml

**功能**: 使用 Docker Compose 部署完整环境

**使用方法**:
```bash
# 启动所有服务
cd scripts/docker
docker-compose up -d

# 查看日志
docker-compose logs -f

# 重启某个服务
docker-compose restart llm_d

# 停止所有服务
docker-compose down

# 清理数据卷
docker-compose down -v
```

**服务列表**:
```yaml
version: '3.8'
services:
  dynamic:
    build:
      context: ..
      dockerfile: scripts/docker/Dockerfile.service
    ports:
      - "18789:18789"
    environment:
      - LOG_LEVEL=INFO
    depends_on:
      - llm_d
      
  llm_d:
    build:
      context: ..
      dockerfile: scripts/docker/Dockerfile.service
    ports:
      - "18791:18791"
    volumes:
      - ../config:/etc/agentos
      - ../partdata/logs:/var/log/agentos
      
  kernel:
    build:
      context: ..
      dockerfile: scripts/docker/Dockerfile.kernel
    volumes:
      - ../partdata:/var/agentos/data
```

---

## 🛠️ 脚本开发指南

### 编写新脚本

1. **命名规范**:
   - Shell 脚本：`.sh` 后缀，小写字母 + 下划线
   - Python 脚本：`.py` 后缀，小写字母 + 下划线
   - PowerShell 脚本：`.ps1` 后缀

2. **添加帮助信息**:
```bash
#!/bin/bash

show_help() {
    cat << EOF
Usage: $0 [OPTIONS]

Options:
  -h, --help          Show this help message
  -d, --debug         Enable debug mode
  -j, --jobs NUM      Number of parallel jobs
  -c, --clean         Clean before build
  
Examples:
  $0 --debug --jobs 8
  $0 --clean
EOF
}

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help) show_help; exit 0 ;;
        -d|--debug) DEBUG=1; shift ;;
        # ... 处理其他参数
    esac
done
```

3. **错误处理**:
```python
#!/usr/bin/env python3

import sys

def main():
    try:
        # 主要逻辑
        pass
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
```

---

## 📊 脚本统计

| 类别 | 脚本数量 | 总行数 |
|------|----------|--------|
| **构建部署** | 4 个 | ~800 行 |
| **配置管理** | 3 个 | ~600 行 |
| **测试验证** | 3 个 | ~1000 行 |
| **文档工具** | 2 个 | ~400 行 |
| **Docker** | 3 个文件 | ~200 行 |
| **总计** | 15+ 个 | ~3000 行 |

---

## 🤝 最佳实践

### 1. 跨平台兼容

```bash
#!/bin/bash
# 检测操作系统
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    CORES=$(sysctl -n hw.ncpu)
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    CORES=$(nproc)
else
    echo "Unsupported OS: $OSTYPE"
    exit 1
fi
```

### 2. 日志输出

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s.%(msecs)03d [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)
logger.info("Starting process...")
```

### 3. 配置外部化

```bash
#!/bin/bash

# 加载用户配置
if [ -f ".build_config" ]; then
    source .build_config
fi

# 使用环境变量或默认值
BUILD_TYPE="${BUILD_TYPE:-Release}"
JOBS="${JOBS:-$(nproc)}"
```

---

## 📚 相关文档

- [快速入门](../partdocs/guides/getting_started.md) - 使用脚本快速开始
- [部署指南](../partdocs/guides/deployment.md) - 生产环境部署
- [故障排查](../partdocs/guides/troubleshooting.md) - 使用 doctor.py 诊断问题

---

**Apache License 2.0 © 2026 SPHARX**
