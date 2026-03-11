# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 虚拟工位：提供隔离的执行环境（沙箱）。

import os
import tempfile
import shutil
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any
import uuid
import asyncio
from agentos_cta.utils.structured_logger import get_logger
from agentos_cta.utils.error_types import SecurityError

logger = get_logger(__name__)


class VirtualWorkbench:
    """
    虚拟工位。
    为每个 Agent 提供独立的沙箱环境，包含临时工作目录和资源限制。
    """

    def __init__(self, base_dir: str = "/tmp/agentos_workbench"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.active_workbenches: Dict[str, Path] = {}

    async def create(self, agent_id: str, resource_limits: Optional[Dict[str, Any]] = None) -> str:
        """
        为指定 Agent 创建一个新的虚拟工位。

        Args:
            agent_id: Agent 标识。
            resource_limits: 资源限制（如内存、CPU、磁盘）。

        Returns:
            工位 ID（可用于后续操作）。
        """
        workbench_id = str(uuid.uuid4())
        workbench_path = self.base_dir / workbench_id
        workbench_path.mkdir(parents=True)

        # 创建子目录
        (workbench_path / "tmp").mkdir()
        (workbench_path / "data").mkdir()
        (workbench_path / "logs").mkdir()

        self.active_workbenches[workbench_id] = workbench_path
        logger.info(f"Created workbench {workbench_id} for agent {agent_id}")
        return workbench_id

    async def destroy(self, workbench_id: str):
        """销毁虚拟工位，清理所有文件。"""
        path = self.active_workbenches.get(workbench_id)
        if path and path.exists():
            shutil.rmtree(path)
            del self.active_workbenches[workbench_id]
            logger.info(f"Destroyed workbench {workbench_id}")

    def get_path(self, workbench_id: str) -> Optional[Path]:
        """获取工位路径。"""
        return self.active_workbenches.get(workbench_id)

    async def execute_in_sandbox(self, workbench_id: str, cmd: list, cwd: Optional[str] = None,
                                 env: Optional[Dict[str, str]] = None,
                                 timeout_sec: int = 30) -> Dict[str, Any]:
        """
        在沙箱中执行命令（用于代码执行隔离）。

        注意：此处为简化实现，实际应使用容器或更严格的隔离。
        """
        workbench_path = self.get_path(workbench_id)
        if not workbench_path:
            raise SecurityError(f"Workbench {workbench_id} not found")

        # 确定工作目录
        if cwd:
            target_cwd = workbench_path / cwd
        else:
            target_cwd = workbench_path

        # 执行命令
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=str(target_cwd),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout_sec)
            return {
                "returncode": proc.returncode,
                "stdout": stdout.decode(errors='replace'),
                "stderr": stderr.decode(errors='replace'),
            }
        except asyncio.TimeoutError:
            proc.terminate()
            await proc.wait()
            raise SecurityError(f"Command execution timed out after {timeout_sec}s")
        except Exception as e:
            raise SecurityError(f"Sandbox execution failed: {e}") from e