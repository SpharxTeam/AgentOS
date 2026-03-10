# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 专业 Agent 池管理。

from typing import Dict, Optional, Any
import asyncio
from agentos_cta.utils.structured_logger import get_logger
from agentos_cta.agents.base_agent import BaseAgent
from agentos_cta.agents.registry_client import AgentRegistryClient

logger = get_logger(__name__)


class AgentPool:
    """
    专业 Agent 池。
    负责加载、缓存、管理 Agent 实例，并提供获取 Agent 的接口。
    """

    def __init__(self, registry_client: AgentRegistryClient, config: Dict[str, Any]):
        self.registry = registry_client
        self.config = config
        self._agents: Dict[str, BaseAgent] = {}  # agent_id -> instance
        self._lock = asyncio.Lock()

    async def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """获取 Agent 实例（如果已加载则返回缓存，否则从注册信息创建）。"""
        async with self._lock:
            if agent_id in self._agents:
                return self._agents[agent_id]

            # 从注册中心获取契约
            agents = await self.registry.query_agents()
            agent_info = next((a for a in agents if a["agent_id"] == agent_id), None)
            if not agent_info:
                logger.error(f"Agent {agent_id} not found in registry")
                return None

            # 根据 role 动态导入对应的 Agent 类（简化：假设所有 Agent 类在 builtin 下）
            # 实际应使用插件机制，这里做简单映射
            role = agent_info["role"]
            try:
                if role == "product_manager":
                    from agentos_cta.agents.builtin.product_manager.agent import ProductManagerAgent
                    agent_class = ProductManagerAgent
                elif role == "architect":
                    from agentos_cta.agents.builtin.architect.agent import ArchitectAgent
                    agent_class = ArchitectAgent
                elif role == "frontend":
                    from agentos_cta.agents.builtin.frontend.agent import FrontendAgent
                    agent_class = FrontendAgent
                elif role == "backend":
                    from agentos_cta.agents.builtin.backend.agent import BackendAgent
                    agent_class = BackendAgent
                # ... 其他角色
                else:
                    logger.error(f"Unknown role {role}")
                    return None
            except ImportError as e:
                logger.error(f"Failed to import agent class for role {role}: {e}")
                return None

            # 创建实例
            agent_instance = agent_class(agent_id=agent_id, config=agent_info.get("config", {}))
            self._agents[agent_id] = agent_instance
            return agent_instance

    async def release_agent(self, agent_id: str):
        """释放 Agent 资源（如需清理）。"""
        async with self._lock:
            if agent_id in self._agents:
                # 可调用清理方法
                del self._agents[agent_id]
                logger.info(f"Agent {agent_id} released")