# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 共享内存空间：中央看板、Agent注册中心、项目上下文。

from typing import Dict, Any, Optional
import asyncio
from agentos_cta.utils.structured_logger import get_logger

logger = get_logger(__name__)


class SharedMemory:
    """
    共享内存空间。
    提供跨Agent的实时状态同步、上下文共享和注册中心访问。
    """

    def __init__(self, config: Dict[str, Any], agent_registry=None):
        self.config = config
        self.agent_registry = agent_registry  # 注入的注册中心客户端
        self._central_board: Dict[str, Any] = {}
        self._project_context: Dict[str, Any] = {}
        self._lock = asyncio.Lock()

    async def update_board(self, key: str, value: Any) -> None:
        """更新中央看板。"""
        async with self._lock:
            self._central_board[key] = value
            logger.debug(f"Central board updated: {key} = {value}")

    async def get_board(self, key: str) -> Optional[Any]:
        """读取中央看板。"""
        async with self._lock:
            return self._central_board.get(key)

    async def get_all_board(self) -> Dict[str, Any]:
        """获取整个看板快照。"""
        async with self._lock:
            return self._central_board.copy()

    async def set_project_context(self, context: Dict[str, Any]) -> None:
        """设置项目上下文。"""
        async with self._lock:
            self._project_context = context
            logger.info("Project context updated")

    async def get_project_context(self) -> Dict[str, Any]:
        """获取项目上下文。"""
        async with self._lock:
            return self._project_context.copy()

    async def query_agents(self, role: Optional[str] = None, **kwargs) -> list:
        """通过注册中心查询Agent。"""
        if self.agent_registry:
            return await self.agent_registry.query_agents(role=role, **kwargs)
        else:
            logger.warning("Agent registry not available")
            return []