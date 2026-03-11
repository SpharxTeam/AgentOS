# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# HTTP 网关：基于 FastAPI 实现。

import asyncio
import json
from typing import Dict, Any
import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
import httpx
from .base import Gateway, GatewayConfig
from agentos_cta.utils.observability import get_logger

logger = get_logger(__name__)


class HttpGateway(Gateway):
    """
    HTTP 网关。
    基于 FastAPI 实现，提供 RESTful 接口。
    借鉴 Agno AgentOS 的 FastAPI 集成设计 [citation:4]。
    """

    def __init__(self, config: GatewayConfig, runtime):
        super().__init__(config, runtime)
        self.app = FastAPI(title="AgentOS Runtime API")
        self.server = None
        self._setup_routes()
        self._setup_middleware()

    def _setup_middleware(self):
        """设置中间件。"""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def _setup_routes(self):
        """设置路由。"""

        @self.app.get("/health")
        async def health():
            result = await self.runtime.health_checker.check()
            return result.to_dict()

        @self.app.post("/api/v1/rpc")
        async def rpc_endpoint(request: Request):
            body = await request.body()
            try:
                data = json.loads(body) if body else {}
                response = await self.runtime.handle_request(data, "http")
                return Response(
                    content=json.dumps(response),
                    media_type="application/json",
                )
            except Exception as e:
                logger.error(f"HTTP request failed: {e}")
                return Response(
                    content=json.dumps({
                        "jsonrpc": "2.0",
                        "error": {
                            "code": -32603,
                            "message": str(e),
                        },
                        "id": data.get("id") if 'data' in locals() else None,
                    }),
                    media_type="application/json",
                    status_code=500,
                )

        @self.app.get("/api/v1/sessions")
        async def list_sessions():
            sessions = await self.runtime.session_manager.list_sessions()
            return {"sessions": [s.to_dict() for s in sessions]}

        @self.app.get("/api/v1/sessions/{session_id}")
        async def get_session(session_id: str):
            session = await self.runtime.session_manager.get_session(session_id)
            if not session:
                return Response(
                    content=json.dumps({"error": "Session not found"}),
                    status_code=404,
                )
            return session.to_dict()

        @self.app.delete("/api/v1/sessions/{session_id}")
        async def close_session(session_id: str):
            success = await self.runtime.session_manager.close_session(session_id)
            if not success:
                return Response(
                    content=json.dumps({"error": "Session not found"}),
                    status_code=404,
                )
            return {"success": True}

    async def start(self):
        """启动 HTTP 服务器。"""
        self.running = True
        config = uvicorn.Config(
            self.app,
            host=self.config.host,
            port=self.config.port,
            log_level="info",
        )
        self.server = uvicorn.Server(config)
        logger.info(f"HTTP gateway listening on {self.config.host}:{self.config.port}")
        await self.server.serve()

    async def stop(self):
        """停止 HTTP 服务器。"""
        self.running = False
        if self.server:
            self.server.should_exit = True
            await self.server.shutdown()
            logger.info("HTTP gateway stopped")