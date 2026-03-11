# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 专业 Agent 池管理。

from typing import Dict, Optional, Any
import asyncio
from agentos_cta.utils.observability import get_logger
from agentos_cta.utils.error import AgentOSError

logger = get_logger(__name__)


class AgentPool:
    """
    专业 Agent 池。
    负责加载、缓存、管理 Agent 实例，并提供获取 Agent 的接口。
    每个 Agent 实例采用 1+1 双模型结构。
    """

    def __init__(self, registry_client, config: Dict[str, Any]):
        """
        初始化 Agent 池。

        Args:
            registry_client: Agent 注册中心客户端，用于查询和获取 Agent 信息。
            config: 配置字典。
        """
        self.registry = registry_client
        self.config = config
        self._agents: Dict[str, Any] = {}  # agent_id -> Agent 实例
        self._lock = asyncio.Lock()

    async def get_agent(self, agent_id: str) -> Optional[Any]:
        """
        获取 Agent 实例（如果已加载则返回缓存，否则从注册信息创建）。

        Args:
            agent_id: Agent 的唯一标识。

        Returns:
            Agent 实例，如果失败则返回 None。
        """
        async with self._lock:
            if agent_id in self._agents:
                return self._agents[agent_id]

            # 从注册中心查询 Agent 信息
            agents = await self.registry.query_agents()
            agent_info = next((a for a in agents if a["agent_id"] == agent_id), None)
            if not agent_info:
                logger.error(f"Agent {agent_id} not found in registry")
                return None

            # 动态导入 Agent 类（根据 role 映射）
            role = agent_info.get("role")
            try:
                agent_class = self._import_agent_class(role)
                if agent_class is None:
                    return None
                # 创建实例
                agent_instance = agent_class(
                    agent_id=agent_id,
                    config=agent_info.get("config", {})
                )
                self._agents[agent_id] = agent_instance
                logger.info(f"Agent {agent_id} loaded and cached")
                return agent_instance
            except Exception as e:
                logger.error(f"Failed to create agent {agent_id}: {e}")
                return None

    def _import_agent_class(self, role: str):
        """根据角色导入对应的 Agent 类。"""
        try:
            if role == "product_manager":
                from agentos_open.contrib.agents.product_manager.agent import ProductManagerAgent
                return ProductManagerAgent
            elif role == "architect":
                from agentos_open.contrib.agents.architect.agent import ArchitectAgent
                return ArchitectAgent
            elif role == "frontend":
                from agentos_open.contrib.agents.frontend.agent import FrontendAgent
                return FrontendAgent
            elif role == "backend":
                from agentos_open.contrib.agents.backend.agent import BackendAgent
                return BackendAgent
            elif role == "tester":
                from agentos_open.contrib.agents.tester.agent import TesterAgent
                return TesterAgent
            elif role == "devops":
                from agentos_open.contrib.agents.devops.agent import DevOpsAgent
                return DevOpsAgent
            elif role == "security":
                from agentos_open.contrib.agents.security.agent import SecurityAgent
                return SecurityAgent
            else:
                logger.error(f"Unknown role {role}")
                return None
        except ImportError as e:
            logger.error(f"Failed to import agent class for role {role}: {e}")
            return None

    async def release_agent(self, agent_id: str):
        """释放 Agent 资源（如需清理）。"""
        async with self._lock:
            if agent_id in self._agents:
                # 可调用清理方法
                del self._agents[agent_id]
                logger.info(f"Agent {agent_id} released")