# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 共享内存空间：中央看板、项目上下文、Agent注册中心。

from typing import Dict, Any, Optional, List
import asyncio
import time
from agentos_cta.utils.structured_logger import get_logger
from agentos_cta.utils.file_utils import FileUtils

logger = get_logger(__name__)


class SharedMemory:
    """
    共享内存空间。
    提供中央看板（实时状态同步）、项目上下文（全局信息）、Agent注册中心（动态更新）的统一访问接口。
    """

    def __init__(self, workspace_dir: str = "data/workspace"):
        self.workspace_dir = workspace_dir
        self._central_board: Dict[str, Any] = {}
        self._project_context: Dict[str, Any] = {}
        self._agent_registry: Dict[str, Any] = {}
        self._lock = asyncio.Lock()
        self._load_persisted()

    def _load_persisted(self):
        """从文件加载持久化数据。"""
        # 中央看板
        board_file = f"{self.workspace_dir}/central_board.json"
        board = FileUtils.read_json(board_file)
        if board:
            self._central_board = board
        # 项目上下文
        ctx_file = f"{self.workspace_dir}/project_context.json"
        ctx = FileUtils.read_json(ctx_file)
        if ctx:
            self._project_context = ctx
        # Agent注册中心（通常从数据库加载，此处简化）
        registry_file = f"{self.workspace_dir}/agent_registry.json"
        reg = FileUtils.read_json(registry_file)
        if reg:
            self._agent_registry = reg

    def _save_central_board(self):
        """持久化中央看板。"""
        board_file = f"{self.workspace_dir}/central_board.json"
        FileUtils.write_json(board_file, self._central_board)

    def _save_project_context(self):
        """持久化项目上下文。"""
        ctx_file = f"{self.workspace_dir}/project_context.json"
        FileUtils.write_json(ctx_file, self._project_context)

    def _save_agent_registry(self):
        """持久化Agent注册中心（简化）。"""
        registry_file = f"{self.workspace_dir}/agent_registry.json"
        FileUtils.write_json(registry_file, self._agent_registry)

    # === 中央看板接口 ===
    async def update_board(self, key: str, value: Any):
        """更新中央看板的某个字段。"""
        async with self._lock:
            self._central_board[key] = value
            self._central_board["last_updated"] = time.time()
            self._save_central_board()
            logger.debug(f"Central board updated: {key}={value}")

    async def get_board(self, key: str = None) -> Any:
        """获取中央看板的某个字段或全部。"""
        async with self._lock:
            if key is None:
                return self._central_board.copy()
            return self._central_board.get(key)

    # === 项目上下文接口 ===
    async def set_project_context(self, context: Dict[str, Any]):
        """设置整个项目上下文。"""
        async with self._lock:
            self._project_context = context
            self._save_project_context()
            logger.info("Project context updated")

    async def get_project_context(self, key: str = None) -> Any:
        """获取项目上下文的某个字段或全部。"""
        async with self._lock:
            if key is None:
                return self._project_context.copy()
            return self._project_context.get(key)

    async def update_project_context(self, key: str, value: Any):
        """更新项目上下文的某个字段。"""
        async with self._lock:
            self._project_context[key] = value
            self._save_project_context()
            logger.debug(f"Project context updated: {key}={value}")

    # === Agent注册中心接口 ===
    async def register_agent(self, agent_id: str, agent_info: Dict[str, Any]):
        """注册一个Agent。"""
        async with self._lock:
            self._agent_registry[agent_id] = {
                **agent_info,
                "registered_at": time.time(),
                "last_seen": time.time(),
            }
            self._save_agent_registry()
            logger.info(f"Agent {agent_id} registered")

    async def unregister_agent(self, agent_id: str):
        """注销Agent。"""
        async with self._lock:
            if agent_id in self._agent_registry:
                del self._agent_registry[agent_id]
                self._save_agent_registry()
                logger.info(f"Agent {agent_id} unregistered")

    async def get_agent_info(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """获取Agent信息。"""
        async with self._lock:
            return self._agent_registry.get(agent_id)

    async def list_agents(self, role: Optional[str] = None) -> List[Dict[str, Any]]:
        """列出所有Agent，可按角色筛选。"""
        async with self._lock:
            agents = list(self._agent_registry.values())
            if role:
                agents = [a for a in agents if a.get("role") == role]
            return agents

    async def update_agent_heartbeat(self, agent_id: str):
        """更新Agent心跳。"""
        async with self._lock:
            if agent_id in self._agent_registry:
                self._agent_registry[agent_id]["last_seen"] = time.time()
                self._save_agent_registry()