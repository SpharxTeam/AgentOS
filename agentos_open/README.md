# AgentOS Open - 开放生态

🔥 **AgentOS Open** 是 AgentOS 的开放生态模块，包含 Agent 市场、技能市场和社区贡献。

## 📁 目录结构

```
agentos_open/
├── markets/                      # 市场模块
│   ├── agent/                    # Agent 市场
│   │   ├── builtin/              # 内置Agent（产品经理、架构师、开发者等）
│   │   ├── registry/             # Agent 注册中心
│   │   ├── installer/            # Agent 安装器
│   │   ├── publisher/            # Agent 发布工具
│   │   └── contracts/            # Agent 契约规范
│   │
│   ├── skill/                    # 技能市场
│   │   ├── commands/             # 命令行工具（install/list/search）
│   │   ├── registry/             # 技能注册中心
│   │   ├── installer/            # 技能安装器
│   │   └── contracts/            # 技能契约规范
│   │
│   └── contracts/                # 市场通用契约规范
│
└── contrib/                      # 社区贡献
    ├── agents/                   # 社区开发的 Agent
    └── skills/                   # 社区开发的技能
```

## 🎯 核心功能

### 1. Agent 市场 (markets/agent)

**内置Agent** (`builtin/`):
- 产品经理 Agent - 需求分析与产品规划
- 架构师 Agent - 系统设计与技术选型
- 前端 Agent - UI/UX 设计与前端开发
- 后端 Agent - API 设计与服务端开发
- 测试 Agent - 自动化测试与质量保障
- DevOps Agent - 部署与运维

**市场功能**:
- `registry/` - Agent 注册与发现
- `installer/` - Agent 安装与依赖管理
- `publisher/` - Agent 发布与版本管理
- `contracts/` - Agent 能力描述契约

### 2. 技能市场 (markets/skill)

**核心模块**:
- `commands/` - 命令行工具
  - `skill install <name>` - 安装技能
  - `skill list` - 列出已安装技能
  - `skill search <query>` - 搜索技能
  
- `registry/` - 技能注册中心
- `installer/` - 技能安装器（支持 GitHub、本地、官方源）
- `contracts/` - 技能契约（依赖、权限、版本）

### 3. 社区贡献 (contrib)

- `agents/` - 社区开发的第三方 Agent
- `skills/` - 社区开发的扩展技能

## 🚀 使用示例

### 安装 Agent

```bash
# 从官方源安装产品经理 Agent
agentos agent install product_manager

# 从 GitHub 安装社区 Agent
agentos agent install github:user/repo
```

### 安装技能

```bash
# 搜索技能
agentos skill search git

# 安装 Git 技能
agentos skill install git-tools

# 列出所有技能
agentos skill list
```

## 🔗 与内核的关系

```
agentos_cta/          # 内核（不可变核心）
├── coreloopthree/    # 认知 - 行动 - 记忆进化
├── runtime/          # 运行时管理
├── saferoom/         # 安全隔离层
└── utils/            # 工具集

agentos_open/         # 开放生态（可扩展）
├── markets/          # 市场模块
└── contrib/          # 社区贡献
```

**设计哲学**:
- ✅ 内核稳定：CoreLoopThree 架构保持不变
- ✅ 生态开放：任何人都可以发布 Agent 和技能
- ✅ 解耦设计：未来可独立为单独仓库

## 📝 下一步

1. **完善市场命令** - 实现 `agentos agent` 和 `agentos skill` CLI
2. **建立审核机制** - 社区贡献需通过审计委员会审查
3. **版本管理** - 实现语义化版本和依赖解析
4. **文档完善** - 为每个 Agent 和技能编写详细文档

---

<p align="center">
  <sub>Built with ❤️ by the AgentOS community</sub>
</p>
