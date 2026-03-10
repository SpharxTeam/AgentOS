import os
import sys
from pathlib import Path

# ===================== 配置项（可根据需要修改） =====================
# 项目根目录（你指定的路径）
PROJECT_ROOT = r"D:\Spharx\SpharxWorks\AgentOS"
# 是否为所有空目录自动创建.gitkeep（True=是，False=否）
CREATE_GITKEEP = True
# ==================================================================

# 定义所有需要创建的目录列表（按层级排序）
DIRECTORIES = [
    # 核心代码目录
    "src/agentos_cta/core/cognition/schemas",
    "src/agentos_cta/core/execution/units",
    "src/agentos_cta/core/execution/schemas",
    "src/agentos_cta/core/memory_evolution/deep_memory",
    "src/agentos_cta/core/memory_evolution/world_model",
    "src/agentos_cta/core/memory_evolution/consensus",
    "src/agentos_cta/core/memory_evolution/committees",
    "src/agentos_cta/core/memory_evolution/schemas",
    # 代理模块目录
    "src/agentos_cta/agents/builtin/product_manager/prompts",
    "src/agentos_cta/agents/builtin/architect",
    "src/agentos_cta/agents/builtin/frontend",
    "src/agentos_cta/agents/builtin/backend",
    "src/agentos_cta/agents/builtin/tester",
    "src/agentos_cta/agents/builtin/devops",
    "src/agentos_cta/agents/builtin/security",
    "src/agentos_cta/agents/community",
    # 技能市场目录
    "src/agentos_cta/skill_market/contracts",
    "src/agentos_cta/skill_market/sources",
    "src/agentos_cta/skill_market/commands",
    # 安全模块目录
    "src/agentos_cta/security/schemas",
    # 运行时模块目录
    "src/agentos_cta/runtime/gateway",
    "src/agentos_cta/runtime/protocol",
    "src/agentos_cta/runtime/telemetry",
    "src/agentos_cta/utils",
    # 配置目录
    "config/agents/profiles",
    "config/skills",
    "config/security",
    # 数据目录
    "data/workspace/projects/{project_id}/artifacts",
    "data/workspace/projects/{project_id}/logs",
    "data/workspace/memory/buffer",
    "data/workspace/memory/summary",
    "data/workspace/memory/vector",
    "data/workspace/memory/patterns",
    "data/workspace/sessions",
    "data/registry",
    "data/security/audit_logs",
    "data/logs",
    # 脚本目录
    "scripts",
    # 测试目录
    "tests/unit",
    "tests/integration",
    "tests/contract",
    "tests/security",
    "tests/benchmarks",
    # 文档目录
    "docs/architecture/diagrams",
    "docs/specifications",
    "docs/guides",
    "docs/api",
    # 示例目录
    "examples/ecommerce_dev/expected_output",
    "examples/video_editing",
    "examples/document_generation"
]

# 定义所有需要创建的空文件列表
FILES = [
    # 根目录文件
    "README.md",
    "LICENSE",
    "CONTRIBUTING.md",
    "CHANGELOG.md",
    "pyproject.toml",
    ".env.example",
    ".gitignore",
    "Makefile",
    "quickstart.sh",
    "validate.sh",
    # 核心代码文件
    "src/agentos_cta/__init__.py",
    "src/agentos_cta/core/__init__.py",
    "src/agentos_cta/core/cognition/__init__.py",
    "src/agentos_cta/core/cognition/router.py",
    "src/agentos_cta/core/cognition/dual_model_coordinator.py",
    "src/agentos_cta/core/cognition/incremental_planner.py",
    "src/agentos_cta/core/cognition/dispatcher.py",
    "src/agentos_cta/core/cognition/schemas/__init__.py",
    "src/agentos_cta/core/cognition/schemas/intent.py",
    "src/agentos_cta/core/cognition/schemas/plan.py",
    "src/agentos_cta/core/cognition/schemas/task_graph.py",
    "src/agentos_cta/core/execution/__init__.py",
    "src/agentos_cta/core/execution/agent_pool.py",
    "src/agentos_cta/core/execution/units/__init__.py",
    "src/agentos_cta/core/execution/units/base_unit.py",
    "src/agentos_cta/core/execution/units/tool_unit.py",
    "src/agentos_cta/core/execution/units/code_unit.py",
    "src/agentos_cta/core/execution/units/api_unit.py",
    "src/agentos_cta/core/execution/units/file_unit.py",
    "src/agentos_cta/core/execution/units/browser_unit.py",
    "src/agentos_cta/core/execution/units/db_unit.py",
    "src/agentos_cta/core/execution/compensation_manager.py",
    "src/agentos_cta/core/execution/traceability_tracer.py",
    "src/agentos_cta/core/execution/schemas/__init__.py",
    "src/agentos_cta/core/execution/schemas/task.py",
    "src/agentos_cta/core/execution/schemas/result.py",
    "src/agentos_cta/core/memory_evolution/__init__.py",
    "src/agentos_cta/core/memory_evolution/deep_memory/__init__.py",
    "src/agentos_cta/core/memory_evolution/deep_memory/buffer.py",
    "src/agentos_cta/core/memory_evolution/deep_memory/summarizer.py",
    "src/agentos_cta/core/memory_evolution/deep_memory/vector_store.py",
    "src/agentos_cta/core/memory_evolution/deep_memory/pattern_miner.py",
    "src/agentos_cta/core/memory_evolution/world_model/__init__.py",
    "src/agentos_cta/core/memory_evolution/world_model/semantic_slicer.py",
    "src/agentos_cta/core/memory_evolution/world_model/temporal_aligner.py",
    "src/agentos_cta/core/memory_evolution/world_model/drift_detector.py",
    "src/agentos_cta/core/memory_evolution/consensus/__init__.py",
    "src/agentos_cta/core/memory_evolution/consensus/quorum_fast.py",
    "src/agentos_cta/core/memory_evolution/consensus/stability_window.py",
    "src/agentos_cta/core/memory_evolution/consensus/streaming_consensus.py",
    "src/agentos_cta/core/memory_evolution/shared_memory.py",
    "src/agentos_cta/core/memory_evolution/committees/__init__.py",
    "src/agentos_cta/core/memory_evolution/committees/coordination_committee.py",
    "src/agentos_cta/core/memory_evolution/committees/technical_committee.py",
    "src/agentos_cta/core/memory_evolution/committees/audit_committee.py",
    "src/agentos_cta/core/memory_evolution/committees/team_committee.py",
    "src/agentos_cta/core/memory_evolution/schemas/__init__.py",
    "src/agentos_cta/core/memory_evolution/schemas/memory_record.py",
    "src/agentos_cta/core/memory_evolution/schemas/evolution_report.py",
    # 代理模块文件
    "src/agentos_cta/agents/__init__.py",
    "src/agentos_cta/agents/base_agent.py",
    "src/agentos_cta/agents/registry_client.py",
    "src/agentos_cta/agents/contracts/__init__.py",
    "src/agentos_cta/agents/contracts/contract_schema.json",
    "src/agentos_cta/agents/contracts/contract_validator.py",
    "src/agentos_cta/agents/builtin/__init__.py",
    "src/agentos_cta/agents/builtin/product_manager/__init__.py",
    "src/agentos_cta/agents/builtin/product_manager/agent.py",
    "src/agentos_cta/agents/builtin/product_manager/contract.json",
    "src/agentos_cta/agents/builtin/product_manager/prompts/__init__.py",
    "src/agentos_cta/agents/builtin/product_manager/prompts/system1.md",
    "src/agentos_cta/agents/builtin/product_manager/prompts/system2.md",
    "src/agentos_cta/agents/builtin/architect/__init__.py",
    "src/agentos_cta/agents/builtin/frontend/__init__.py",
    "src/agentos_cta/agents/builtin/backend/__init__.py",
    "src/agentos_cta/agents/builtin/tester/__init__.py",
    "src/agentos_cta/agents/builtin/devops/__init__.py",
    "src/agentos_cta/agents/builtin/security/__init__.py",
    "src/agentos_cta/agents/community/README.md",
    # 技能市场文件
    "src/agentos_cta/skill_market/__init__.py",
    "src/agentos_cta/skill_market/registry.py",
    "src/agentos_cta/skill_market/installer.py",
    "src/agentos_cta/skill_market/uninstaller.py",
    "src/agentos_cta/skill_market/updater.py",
    "src/agentos_cta/skill_market/dependency_resolver.py",
    "src/agentos_cta/skill_market/version_manager.py",
    "src/agentos_cta/skill_market/contracts/__init__.py",
    "src/agentos_cta/skill_market/contracts/skill_schema.json",
    "src/agentos_cta/skill_market/contracts/validator.py",
    "src/agentos_cta/skill_market/sources/__init__.py",
    "src/agentos_cta/skill_market/sources/github_source.py",
    "src/agentos_cta/skill_market/sources/local_source.py",
    "src/agentos_cta/skill_market/sources/registry_source.py",
    "src/agentos_cta/skill_market/commands/__init__.py",
    "src/agentos_cta/skill_market/commands/install.py",
    "src/agentos_cta/skill_market/commands/list.py",
    "src/agentos_cta/skill_market/commands/info.py",
    "src/agentos_cta/skill_market/commands/search.py",
    # 安全模块文件
    "src/agentos_cta/security/__init__.py",
    "src/agentos_cta/security/virtual_workbench.py",
    "src/agentos_cta/security/permission_engine.py",
    "src/agentos_cta/security/tool_audit.py",
    "src/agentos_cta/security/input_sanitizer.py",
    "src/agentos_cta/security/schemas/__init__.py",
    "src/agentos_cta/security/schemas/permission.py",
    "src/agentos_cta/security/schemas/audit_record.py",
    # 运行时模块文件
    "src/agentos_cta/runtime/__init__.py",
    "src/agentos_cta/runtime/server.py",
    "src/agentos_cta/runtime/session_manager.py",
    "src/agentos_cta/runtime/gateway/__init__.py",
    "src/agentos_cta/runtime/gateway/http_gateway.py",
    "src/agentos_cta/runtime/gateway/websocket_gateway.py",
    "src/agentos_cta/runtime/gateway/stdio_gateway.py",
    "src/agentos_cta/runtime/protocol/__init__.py",
    "src/agentos_cta/runtime/protocol/json_rpc.py",
    "src/agentos_cta/runtime/protocol/message_serializer.py",
    "src/agentos_cta/runtime/protocol/codec.py",
    "src/agentos_cta/runtime/telemetry/__init__.py",
    "src/agentos_cta/runtime/telemetry/otel_collector.py",
    "src/agentos_cta/runtime/telemetry/metrics.py",
    "src/agentos_cta/runtime/telemetry/tracing.py",
    "src/agentos_cta/runtime/health_checker.py",
    # 工具模块文件
    "src/agentos_cta/utils/__init__.py",
    "src/agentos_cta/utils/token_counter.py",
    "src/agentos_cta/utils/token_uniqueness.py",
    "src/agentos_cta/utils/cost_estimator.py",
    "src/agentos_cta/utils/latency_monitor.py",
    "src/agentos_cta/utils/structured_logger.py",
    "src/agentos_cta/utils/error_types.py",
    "src/agentos_cta/utils/file_utils.py",
    # 配置文件
    "config/__init__.py",
    "config/settings.yaml",
    "config/models.yaml",
    "config/agents/__init__.py",
    "config/agents/registry.yaml",
    "config/agents/profiles/__init__.py",
    "config/skills/registry.yaml",
    "config/security/permissions.yaml",
    "config/security/audit.yaml",
    "config/token_strategy.yaml",
    # 数据目录文件
    "data/workspace/projects/{project_id}/context.json",
    # 脚本文件
    "scripts/install.sh",
    "scripts/install.ps1",
    "scripts/init_config.py",
    "scripts/doctor.py",
    "scripts/validate_contracts.py",
    "scripts/benchmark.py",
    "scripts/update_registry.py",
    "scripts/generate_docs.py",
    "scripts/quickstart.sh",
    # 测试文件
    "tests/unit/__init__.py",
    "tests/integration/__init__.py",
    "tests/contract/test_agent_contracts.py",
    "tests/contract/test_skill_contracts.py",
    "tests/security/test_sandbox.py",
    "tests/security/test_permissions.py",
    "tests/benchmarks/test_token_efficiency.py",
    "tests/benchmarks/test_latency.py",
    "tests/benchmarks/test_consensus.py",
    # 文档文件
    "docs/architecture/CoreLoopThree.md",
    "docs/architecture/world_model.md",
    "docs/architecture/consensus.md",
    "docs/specifications/agent_contract_spec.md",
    "docs/specifications/skill_spec.md",
    "docs/specifications/protocol_spec.md",
    "docs/specifications/security_spec.md",
    "docs/guides/getting_started.md",
    "docs/guides/create_agent.md",
    "docs/guides/create_skill.md",
    "docs/guides/token_optimization.md",
    "docs/guides/deployment.md",
    "docs/guides/troubleshooting.md",
    # 示例文件
    "examples/ecommerce_dev/README.md",
    "examples/ecommerce_dev/run.sh",
    "examples/ecommerce_dev/project_config.yaml"
]

def is_dir_empty(dir_path: Path) -> bool:
    """检查目录是否为空"""
    try:
        return not any(dir_path.iterdir())
    except Exception:
        return True  # 目录不存在/无权限时默认视为空

def create_gitkeep(dir_path: Path) -> None:
    """为目录创建.gitkeep文件"""
    gitkeep_path = dir_path / ".gitkeep"
    if not gitkeep_path.exists():
        gitkeep_path.touch()
        print(f"  📄 为空目录添加.gitkeep: {gitkeep_path}")

def main():
    """主函数：创建项目结构"""
    # 转换为Path对象（更易用）
    root = Path(PROJECT_ROOT).resolve()
    
    # 第一步：创建所有目录
    print("=== 第一步：创建项目目录 ===")
    for dir_rel in DIRECTORIES:
        dir_abs = root / dir_rel
        try:
            # 创建目录（递归创建父目录，已存在则忽略）
            dir_abs.mkdir(parents=True, exist_ok=True)
            print(f"✅ 创建目录成功: {dir_abs}")
            
            # 如果需要，为空空目录添加.gitkeep
            if CREATE_GITKEEP and is_dir_empty(dir_abs):
                create_gitkeep(dir_abs)
                
        except Exception as e:
            print(f"❌ 创建目录失败: {dir_abs} | 错误: {str(e)}")
    
    # 第二步：创建所有空文件
    print("\n=== 第二步：创建项目文件 ===")
    for file_rel in FILES:
        file_abs = root / file_rel
        try:
            # 确保父目录存在
            file_abs.parent.mkdir(parents=True, exist_ok=True)
            # 创建空文件（已存在则忽略）
            file_abs.touch(exist_ok=True)
            print(f"✅ 创建文件成功: {file_abs}")
            
            # 创建文件后，检查父目录是否为空（避免.gitkeep被误删）
            if CREATE_GITKEEP and is_dir_empty(file_abs.parent):
                create_gitkeep(file_abs.parent)
                
        except Exception as e:
            print(f"❌ 创建文件失败: {file_abs} | 错误: {str(e)}")
    
    # 第三步：检查根目录下的空目录（兜底）
    if CREATE_GITKEEP:
        print("\n=== 第三步：兜底检查空目录 ===")
        for dir_path in root.rglob("*"):
            if dir_path.is_dir() and is_dir_empty(dir_path):
                create_gitkeep(dir_path)
    
    # 完成提示
    print(f"\n🎉 项目结构创建完成！")
    print(f"📌 项目根目录: {root}")
    print(f"🔍 共创建目录: {len(DIRECTORIES)} 个")
    print(f"📄 共创建文件: {len(FILES)} 个")
    if CREATE_GITKEEP:
        print(f"📌 已为所有空目录添加.gitkeep文件")

if __name__ == "__main__":
    # 检查Python版本（确保兼容）
    if sys.version_info < (3, 6):
        print("❌ 错误：需要Python 3.6及以上版本！")
        sys.exit(1)
    
    # 执行主函数
    main()