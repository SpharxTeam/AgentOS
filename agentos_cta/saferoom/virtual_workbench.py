# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 虚拟工位：为每个 Agent 提供独立的沙箱环境。
# 基于容器或 WASM 实现隔离。

import asyncio
import uuid
import tempfile
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from agentos_cta.utils.structured_logger import get_logger
from agentos_cta.utils.error_types import SecurityError

logger = get_logger(__name__)

# 尝试导入容器库，若无则使用模拟
try:
    import docker
    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False
    logger.warning("Docker not available, using simulated workbench")


@dataclass
class WorkbenchConfig:
    """虚拟工位配置。"""
    isolation_type: str = "docker"  # docker, wasm, process
    memory_limit_mb: int = 512
    cpu_limit: float = 1.0
    network_enabled: bool = False
    allowed_mounts: List[str] = field(default_factory=list)
    read_only_root: bool = True


@dataclass
class WorkbenchSession:
    """工位会话。"""
    session_id: str
    agent_id: str
    container_id: Optional[str] = None
    work_dir: Optional[str] = None
    created_at: float = field(default_factory=asyncio.get_event_loop().time)
    is_active: bool = True


class VirtualWorkbench:
    """
    虚拟工位管理器。
    为每个 Agent 提供独立的沙箱环境，实现资源隔离和权限控制。
    """

    def __init__(self, config: WorkbenchConfig):
        self.config = config
        self.sessions: Dict[str, WorkbenchSession] = {}
        self._lock = asyncio.Lock()
        self._docker_client = None
        if config.isolation_type == "docker" and DOCKER_AVAILABLE:
            self._docker_client = docker.from_env()

    async def create_workbench(self, agent_id: str) -> WorkbenchSession:
        """
        为 Agent 创建新的虚拟工位。
        """
        session_id = str(uuid.uuid4())
        session = WorkbenchSession(
            session_id=session_id,
            agent_id=agent_id,
        )

        if self.config.isolation_type == "docker" and self._docker_client:
            # 创建 Docker 容器
            work_dir = tempfile.mkdtemp(prefix=f"agent_{agent_id}_")
            mounts = []
            for src in self.config.allowed_mounts:
                mounts.append(f"{src}:{src}:ro" if self.config.read_only_root else f"{src}:{src}")

            container = await asyncio.to_thread(
                self._docker_client.containers.create,
                "agentos-sandbox:latest",  # 假设存在基础镜像
                command="/bin/sleep infinity",
                detach=True,
                mem_limit=f"{self.config.memory_limit_mb}m",
                nano_cpus=int(self.config.cpu_limit * 1e9),
                network_disabled=not self.config.network_enabled,
                volumes=mounts,
                working_dir="/workspace",
                environment={"AGENT_ID": agent_id, "SESSION_ID": session_id},
            )
            await asyncio.to_thread(container.start)
            session.container_id = container.id
            session.work_dir = work_dir
            logger.info(f"Created Docker workbench for agent {agent_id} with container {container.id}")

        else:
            # 模拟沙箱：仅创建临时目录
            work_dir = tempfile.mkdtemp(prefix=f"agent_{agent_id}_")
            session.work_dir = work_dir
            logger.info(f"Created simulated workbench for agent {agent_id} at {work_dir}")

        async with self._lock:
            self.sessions[session_id] = session
        return session

    async def get_workbench(self, session_id: str) -> Optional[WorkbenchSession]:
        """获取工位会话。"""
        async with self._lock:
            return self.sessions.get(session_id)

    async def execute_in_workbench(self, session_id: str, cmd: List[str], timeout: int = 30) -> Dict[str, Any]:
        """
        在指定工位中执行命令。
        """
        session = await self.get_workbench(session_id)
        if not session:
            raise SecurityError(f"Workbench session {session_id} not found")

        if not session.is_active:
            raise SecurityError(f"Workbench session {session_id} is inactive")

        if self.config.isolation_type == "docker" and session.container_id:
            # 在容器中执行
            container = self._docker_client.containers.get(session.container_id)
            try:
                exec_result = await asyncio.to_thread(
                    container.exec_run,
                    cmd,
                    demux=True,
                    timeout=timeout,
                )
                return {
                    "exit_code": exec_result.exit_code,
                    "output": exec_result.output.decode() if exec_result.output else "",
                }
            except Exception as e:
                logger.error(f"Command execution in workbench failed: {e}")
                raise SecurityError(f"Command execution failed: {e}")

        else:
            # 模拟执行（实际应使用 subprocess 但限制权限）
            import shlex
            import subprocess
            full_cmd = " ".join(shlex.quote(c) for c in cmd)
            try:
                proc = await asyncio.create_subprocess_shell(
                    full_cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=session.work_dir,
                    env={},
                    limit=1024 * 1024,
                )
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout)
                return {
                    "exit_code": proc.returncode,
                    "stdout": stdout.decode(),
                    "stderr": stderr.decode(),
                }
            except asyncio.TimeoutError:
                proc.terminate()
                raise SecurityError("Command execution timed out")
            except Exception as e:
                raise SecurityError(f"Command execution failed: {e}")

    async def destroy_workbench(self, session_id: str):
        """销毁工位会话。"""
        session = await self.get_workbench(session_id)
        if not session:
            return

        if self.config.isolation_type == "docker" and session.container_id:
            try:
                container = self._docker_client.containers.get(session.container_id)
                await asyncio.to_thread(container.stop)
                await asyncio.to_thread(container.remove)
            except Exception as e:
                logger.error(f"Failed to destroy container {session.container_id}: {e}")

        # 清理临时目录
        if session.work_dir and os.path.exists(session.work_dir):
            import shutil
            shutil.rmtree(session.work_dir, ignore_errors=True)

        async with self._lock:
            session.is_active = False
            del self.sessions[session_id]
        logger.info(f"Destroyed workbench session {session_id}")