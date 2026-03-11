# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# WebSocket 网关：支持双向实时通信。

import asyncio
import json
from typing import Set, Dict, Any
import websockets
from websockets.server import WebSocketServerProtocol
from .base import Gateway, GatewayConfig
from agentos_cta.utils.observability import get_logger

logger = get_logger(__name__)


class WebSocketGateway(Gateway):
    """
    WebSocket 网关。
    支持双向实时通信，适用于流式响应和多轮对话。
    """

    def __init__(self, config: GatewayConfig, runtime):
        super().__init__(config, runtime)
        self.server = None
        self.connections: Set[WebSocketServerProtocol] = set()
        self.session_map: Dict[str, WebSocketServerProtocol] = {}

    async def start(self):
        """启动 WebSocket 服务器。"""
        self.running = True
        self.server = await websockets.serve(
            self._handle_connection,
            self.config.host,
            self.config.port,
            max_size=10 * 1024 * 1024,  # 10MB
        )
        logger.info(f"WebSocket gateway listening on ws://{self.config.host}:{self.config.port}")
        await self.server.wait_closed()

    async def stop(self):
        """停止 WebSocket 服务器。"""
        self.running = False
        # 关闭所有连接
        for conn in list(self.connections):
            await conn.close()
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        logger.info("WebSocket gateway stopped")

    async def _handle_connection(self, websocket: WebSocketServerProtocol):
        """处理新连接。"""
        self.connections.add(websocket)
        client_id = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
        logger.info(f"WebSocket client connected: {client_id}")

        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    response = await self.runtime.handle_request(data, "websocket")

                    # 如果是响应式请求，通过 WebSocket 返回
                    await websocket.send(json.dumps(response))

                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON from {client_id}")
                    await websocket.send(json.dumps({
                        "jsonrpc": "2.0",
                        "error": {"code": -32700, "message": "Parse error"},
                    }))
                except Exception as e:
                    logger.error(f"WebSocket error: {e}")
                    await websocket.send(json.dumps({
                        "jsonrpc": "2.0",
                        "error": {"code": -32000, "message": str(e)},
                    }))

        except websockets.exceptions.ConnectionClosed:
            logger.info(f"WebSocket client disconnected: {client_id}")
        finally:
            self.connections.remove(websocket)