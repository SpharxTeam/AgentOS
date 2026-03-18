# AgentOS 服务层 (Backs)

提供 LLM、工具、市场、调度、监控等核心服务。每个服务独立进程，通过 HTTP/gRPC 与内核及其他服务通信。

## 目录结构
- llm_d/      - 大模型服务
- tool_d/     - 工具服务
- market_d/   - 市场服务
- sched_d/    - 调度服务
- monit_d/    - 监控服务
