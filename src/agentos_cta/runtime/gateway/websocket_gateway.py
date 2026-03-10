# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# WebSocket 网关，支持双向实时通信。

import asyncio
import json
from typing import Dict, Any
import aiohttp
from aiohttp import web
from agentos_cta.utils.structured_logger import get_logger
from . import BaseGateway

logger = get_logger(__name__)


class WebSocketGateway(BaseGateway):
    """WebSocket 网关。"""

    def __init__(self, config: Dict[str, Any], request_handler):
        self.config = config
        self.handler = request_handler
        self.host = config.get("host", "127.0.0.1")
        self.port = config.get("port", 8081)
        self.app = web.Application()
        self.runner = None
        self.site = None
        self.connections = set()

        self.app.router.add_get("/ws", self._handle_websocket)

    async def _handle_websocket(self, request: web.Request):
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        self.connections.add(ws)
        logger.info("WebSocket connection opened")

        try:
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    data = json.loads(msg.data)
                    logger.debug(f"WebSocket received: {data}")
                    # 处理请求
                    response = await self.handler("websocket", data)
                    await ws.send_json(response)
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    logger.error(f"WebSocket error: {ws.exception()}")
        finally:
            self.connections.remove(ws)
            logger.info("WebSocket connection closed")
        return ws

    async def start(self):
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, self.host, self.port)
        await self.site.start()
        logger.info(f"WebSocket gateway started at ws://{self.host}:{self.port}")

    async def stop(self):
        # 关闭所有连接
        for ws in self.connections.copy():
            await ws.close()
        if self.runner:
            await self.runner.cleanup()
            logger.info("WebSocket gateway stopped")