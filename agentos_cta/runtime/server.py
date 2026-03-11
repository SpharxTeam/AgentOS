# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 应用服务器，管理会话生命周期和并发控制。

import asyncio
from typing import Dict, Any, Optional, Callable, Awaitable
from agentos_cta.utils.structured_logger import get_logger
from agentos_cta.utils.error_types import AgentOSError
from .session_manager import SessionManager
from .gateway import BaseGateway
from .health_checker import HealthChecker

logger = get_logger(__name__)


class AppServer:
    """
    应用服务器。
    负责启动网关、管理会话、处理请求分发。
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.session_manager = SessionManager(config.get("session", {}))
        self.health_checker = HealthChecker(config.get("health", {}))
        self.gateways: Dict[str, BaseGateway] = {}
        self._running = False
        self._tasks = []

    def register_gateway(self, name: str, gateway: BaseGateway):
        """注册网关。"""
        self.gateways[name] = gateway
        logger.info(f"Gateway {name} registered")

    async def start(self):
        """启动所有网关和后台任务。"""
        self._running = True
        for name, gateway in self.gateways.items():
            task = asyncio.create_task(gateway.start(), name=f"gateway-{name}")
            self._tasks.append(task)
            logger.info(f"Gateway {name} started")

        # 启动健康检查后台任务
        health_task = asyncio.create_task(self._health_check_loop(), name="health-checker")
        self._tasks.append(health_task)

        logger.info("AppServer started")

    async def stop(self):
        """优雅停止。"""
        self._running = False
        for name, gateway in self.gateways.items():
            await gateway.stop()
        for task in self._tasks:
            task.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
        logger.info("AppServer stopped")

    async def _health_check_loop(self):
        """定期健康检查。"""
        interval = self.config.get("health_interval_seconds", 30)
        while self._running:
            await asyncio.sleep(interval)
            status = self.health_checker.check()
            if status["status"] != "healthy":
                logger.warning(f"Health check degraded: {status}")
            # 可上报到外部监控

    async def handle_request(self, gateway_name: str, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理外部请求（由网关调用）。
        根据请求内容创建或恢复会话，并调用相应的处理器。
        """
        # 提取会话 ID
        session_id = request.get("session_id")
        if not session_id:
            # 新会话
            session = await self.session_manager.create_session()
            session_id = session.session_id
        else:
            session = await self.session_manager.get_session(session_id)
            if not session:
                raise AgentOSError(f"Session {session_id} not found", code=404)

        # 将请求交给会话处理
        response = await session.process(request)
        response["session_id"] = session_id
        return response