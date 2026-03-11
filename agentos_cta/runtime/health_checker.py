# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 健康检查器。

import time
import psutil
from enum import Enum
from typing import Dict, Any, List
from dataclasses import dataclass, field
from agentos_cta.utils.observability import get_logger

logger = get_logger(__name__)


class HealthStatus(str, Enum):
    """健康状态。"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class HealthCheckResult:
    """健康检查结果。"""
    status: HealthStatus
    timestamp: float = field(default_factory=time.time)
    message: str = ""
    checks: Dict[str, Any] = field(default_factory=dict)


class HealthChecker:
    """
    健康检查器。
    定期检查系统各组件状态，提供统一健康视图。
    """

    def __init__(self, runtime):
        self.runtime = runtime
        self.last_result: Optional[HealthCheckResult] = None

    async def check(self) -> HealthCheckResult:
        """执行健康检查。"""
        checks = {}

        # 检查内存使用
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        checks["memory"] = {
            "status": "healthy" if memory_percent < 80 else "degraded" if memory_percent < 90 else "unhealthy",
            "percent": memory_percent,
            "available_gb": memory.available / (1024 ** 3),
        }

        # 检查 CPU 使用
        cpu_percent = psutil.cpu_percent(interval=0.1)
        checks["cpu"] = {
            "status": "healthy" if cpu_percent < 70 else "degraded" if cpu_percent < 85 else "unhealthy",
            "percent": cpu_percent,
        }

        # 检查会话数
        sessions = await self.runtime.session_manager.list_sessions()
        session_count = len(sessions)
        max_sessions = self.runtime.config.max_sessions
        checks["sessions"] = {
            "status": "healthy" if session_count < max_sessions * 0.8 else "degraded" if session_count < max_sessions else "unhealthy",
            "count": session_count,
            "max": max_sessions,
            "percent": session_count / max_sessions * 100 if max_sessions > 0 else 0,
        }

        # 检查网关状态
        gateway_status = {}
        for gateway in self.runtime.gateways:
            gateway_status[gateway.__class__.__name__] = "running" if gateway.running else "stopped"
        checks["gateways"] = gateway_status

        # 确定整体状态
        overall_status = HealthStatus.HEALTHY
        messages = []

        for name, check in checks.items():
            if isinstance(check, dict) and "status" in check:
                if check["status"] == "unhealthy":
                    overall_status = HealthStatus.UNHEALTHY
                    messages.append(f"{name} is unhealthy")
                elif check["status"] == "degraded" and overall_status == HealthStatus.HEALTHY:
                    overall_status = HealthStatus.DEGRADED
                    messages.append(f"{name} is degraded")

        result = HealthCheckResult(
            status=overall_status,
            message="; ".join(messages) if messages else "All systems healthy",
            checks=checks,
        )
        self.last_result = result
        return result

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典。"""
        if not self.last_result:
            return {"status": "unknown"}
        return {
            "status": self.last_result.status.value,
            "timestamp": self.last_result.timestamp,
            "message": self.last_result.message,
            "checks": self.last_result.checks,
        }