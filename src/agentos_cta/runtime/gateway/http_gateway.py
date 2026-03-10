# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# HTTP 网关，提供 RESTful API 和 SSE 支持。

from typing import Dict, Any, Optional
import asyncio
from aiohttp import web
from agentos_cta.utils.structured_logger import get_logger
from . import BaseGateway

logger = get_logger(__name__)


class HTTPGateway(BaseGateway):
    """HTTP 网关，基于 aiohttp。"""

    def __init__(self, config: Dict[str, Any], request_handler):
        """
        Args:
            config: 配置，如 host, port
            request_handler: 异步函数，接收 (gateway_name, request_dict) 返回响应字典
        """
        self.config = config
        self.handler = request_handler
        self.host = config.get("host", "127.0.0.1")
        self.port = config.get("port", 8080)
        self.app = web.Application()
        self.runner = None
        self.site = None

        # 注册路由
        self.app.router.add_post("/api/v1/process", self._handle_post)
        self.app.router.add_get("/health", self._handle_health)

    async def _handle_post(self, request: web.Request) -> web.Response:
        """处理 POST /api/v1/process"""
        try:
            body = await request.json()
            logger.debug(f"HTTP request: {body}")
            response = await self.handler("http", body)
            return web.json_response(response)
        except Exception as e:
            logger.error(f"HTTP error: {e}")
            return web.json_response({"error": str(e)}, status=500)

    async def _handle_health(self, request: web.Request) -> web.Response:
        return web.json_response({"status": "ok"})

    async def start(self):
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, self.host, self.port)
        await self.site.start()
        logger.info(f"HTTP gateway started at http://{self.host}:{self.port}")

    async def stop(self):
        if self.runner:
            await self.runner.cleanup()
            logger.info("HTTP gateway stopped")