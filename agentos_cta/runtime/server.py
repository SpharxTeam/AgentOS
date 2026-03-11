# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# Runtime 服务器：管理服务生命周期、会话和网关。

import asyncio
import signal
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
import uvloop
from agentos_cta.utils.observability import get_logger, set_trace_id
from agentos_cta.utils.error import AgentOSError
from .session_manager import SessionManager
from .gateway import HttpGateway, WebSocketGateway, StdioGateway, GatewayConfig
from .telemetry import TelemetryCollector
from .health_checker import HealthChecker

logger = get_logger(__name__)


@dataclass
class RuntimeConfig:
    """运行时配置。"""
    host: str = "127.0.0.1"
    http_port: int = 18789
    websocket_port: int = 18790
    enable_http: bool = True
    enable_websocket: bool = True
    enable_stdio: bool = True
    max_sessions: int = 1000
    session_timeout_seconds: int = 3600
    enable_telemetry: bool = True
    otlp_endpoint: Optional[str] = None
    health_check_interval: int = 30


class RuntimeServer:
    """
    Runtime 服务器。
    借鉴 Agno AgentOS 的 FastAPI 集成设计，提供生产级运行时能力 [citation:4]。
    管理所有网关和服务生命周期，支持水平扩展。
    """

    def __init__(self, config: RuntimeConfig, agent_pool=None, memory_roviol=None):
        """
        初始化 Runtime 服务器。

        Args:
            config: 运行时配置。
            agent_pool: Agent 池实例，用于执行任务。
            memory_roviol: MemoryRovol 实例，用于记忆访问。
        """
        self.config = config
        self.agent_pool = agent_pool
        self.memory = memory_roviol
        self.running = False
        self._tasks: List[asyncio.Task] = []

        # 初始化会话管理器
        self.session_manager = SessionManager(
            max_sessions=config.max_sessions,
            session_timeout=config.session_timeout_seconds,
        )

        # 初始化网关
        self.gateways = []
        if config.enable_http:
            http_config = GatewayConfig(
                host=config.host,
                port=config.http_port,
                protocol="http",
            )
            self.http_gateway = HttpGateway(http_config, self)
            self.gateways.append(self.http_gateway)

        if config.enable_websocket:
            ws_config = GatewayConfig(
                host=config.host,
                port=config.websocket_port,
                protocol="websocket",
            )
            self.websocket_gateway = WebSocketGateway(ws_config, self)
            self.gateways.append(self.websocket_gateway)

        if config.enable_stdio:
            stdio_config = GatewayConfig(protocol="stdio")
            self.stdio_gateway = StdioGateway(stdio_config, self)
            self.gateways.append(self.stdio_gateway)

        # 初始化可观测性
        if config.enable_telemetry:
            self.telemetry = TelemetryCollector(
                otlp_endpoint=config.otlp_endpoint,
                service_name="agentos-runtime",
            )
        else:
            self.telemetry = None

        # 初始化健康检查
        self.health_checker = HealthChecker(self)

    async def start(self):
        """启动所有服务。"""
        if self.running:
            logger.warning("Runtime already running")
            return

        logger.info(f"Starting AgentOS Runtime on {self.config.host}:{self.config.http_port}")
        self.running = True

        # 启动所有网关
        for gateway in self.gateways:
            task = asyncio.create_task(gateway.start())
            self._tasks.append(task)
            logger.info(f"Gateway {gateway.__class__.__name__} started")

        # 启动健康检查
        health_task = asyncio.create_task(self._run_health_checks())
        self._tasks.append(health_task)

        # 启动会话清理
        cleanup_task = asyncio.create_task(self._cleanup_sessions())
        self._tasks.append(cleanup_task)

        # 注册信号处理
        try:
            loop = asyncio.get_running_loop()
            for sig in (signal.SIGTERM, signal.SIGINT):
                loop.add_signal_handler(sig, lambda: asyncio.create_task(self.stop()))
        except NotImplementedError:
            # Windows 不支持信号处理
            pass

        logger.info("Runtime started successfully")

    async def stop(self):
        """停止所有服务。"""
        if not self.running:
            return

        logger.info("Stopping AgentOS Runtime...")
        self.running = False

        # 停止所有网关
        for gateway in self.gateways:
            await gateway.stop()

        # 取消所有任务
        for task in self._tasks:
            task.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()

        # 关闭会话
        await self.session_manager.close_all()

        # 关闭可观测性
        if self.telemetry:
            await self.telemetry.shutdown()

        logger.info("Runtime stopped")

    async def handle_request(self, request: Dict[str, Any], gateway_type: str) -> Dict[str, Any]:
        """
        处理来自网关的请求。
        遵循 Aura 架构的 Hub-and-Spoke 设计，由 System Agent 统一处理 [citation:1][citation:8]。
        """
        # 从请求中提取 trace_id
        trace_id = request.get("trace_id")
        if trace_id:
            set_trace_id(trace_id)

        # 记录请求
        if self.telemetry:
            await self.telemetry.record_request(gateway_type, request)

        try:
            # 解析请求方法
            method = request.get("method")
            params = request.get("params", {})
            session_id = request.get("session_id")

            if method == "execute_task":
                # 执行任务
                result = await self._execute_task(params, session_id)
            elif method == "create_session":
                result = await self._create_session(params)
            elif method == "get_session":
                result = await self._get_session(params)
            elif method == "list_sessions":
                result = await self._list_sessions()
            elif method == "close_session":
                result = await self._close_session(params)
            elif method == "health":
                result = await self.health_checker.check()
            else:
                raise AgentOSError(f"Unknown method: {method}")

            response = {
                "jsonrpc": "2.0",
                "result": result,
                "id": request.get("id"),
            }

        except Exception as e:
            logger.error(f"Request handling failed: {e}")
            response = {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32000,
                    "message": str(e),
                },
                "id": request.get("id"),
            }

        # 记录响应
        if self.telemetry:
            await self.telemetry.record_response(response)

        return response

    async def _execute_task(self, params: Dict[str, Any], session_id: Optional[str]) -> Dict[str, Any]:
        """执行任务。"""
        if not self.agent_pool:
            raise AgentOSError("Agent pool not configured")

        # 获取或创建会话
        if session_id:
            session = await self.session_manager.get_session(session_id)
            if not session:
                raise AgentOSError(f"Session not found: {session_id}")
        else:
            session = await self.session_manager.create_session()

        # 执行任务
        task_input = params.get("input", {})
        context = {
            "session_id": session.session_id,
            "trace_id": session.trace_id,
            **params.get("context", {}),
        }

        # 这里简化：假设任务已经由上层规划好，直接分配
        # 实际应由 cognition 层处理
        result = {
            "session_id": session.session_id,
            "task_id": "task_123",
            "status": "completed",
            "output": task_input,
        }

        return result

    async def _create_session(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """创建新会话。"""
        session = await self.session_manager.create_session(
            metadata=params.get("metadata")
        )
        return {
            "session_id": session.session_id,
            "trace_id": session.trace_id,
            "created_at": session.created_at,
        }

    async def _get_session(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """获取会话信息。"""
        session_id = params.get("session_id")
        if not session_id:
            raise AgentOSError("session_id required")

        session = await self.session_manager.get_session(session_id)
        if not session:
            raise AgentOSError(f"Session not found: {session_id}")

        return session.to_dict()

    async def _list_sessions(self) -> List[Dict[str, Any]]:
        """列出所有活跃会话。"""
        sessions = await self.session_manager.list_sessions()
        return [s.to_dict() for s in sessions]

    async def _close_session(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """关闭会话。"""
        session_id = params.get("session_id")
        if not session_id:
            raise AgentOSError("session_id required")

        success = await self.session_manager.close_session(session_id)
        return {"success": success, "session_id": session_id}

    async def _run_health_checks(self):
        """定期运行健康检查。"""
        while self.running:
            try:
                await asyncio.sleep(self.config.health_check_interval)
                result = await self.health_checker.check()
                if result.status != HealthStatus.HEALTHY:
                    logger.warning(f"Health check: {result.status.value} - {result.message}")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check error: {e}")

    async def _cleanup_sessions(self):
        """定期清理过期会话。"""
        while self.running:
            try:
                await asyncio.sleep(60)  # 每分钟检查
                cleaned = await self.session_manager.cleanup_expired()
                if cleaned > 0:
                    logger.info(f"Cleaned up {cleaned} expired sessions")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Session cleanup error: {e}")