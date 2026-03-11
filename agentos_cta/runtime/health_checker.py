# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 健康检查器，用于诊断系统状态。

import psutil
import time
from typing import Dict, Any, List
from agentos_cta.utils.structured_logger import get_logger

logger = get_logger(__name__)


class HealthChecker:
    """
    健康检查器。
    检查系统资源、各组件状态，返回健康报告。
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.thresholds = {
            "cpu_percent": config.get("cpu_threshold", 90),
            "memory_percent": config.get("memory_threshold", 90),
            "disk_percent": config.get("disk_threshold", 90),
        }
        self.checks: List[Dict] = []  # 注册自定义检查

    def register_check(self, name: str, check_func):
        """注册自定义检查函数。"""
        self.checks.append({"name": name, "func": check_func})

    def check(self) -> Dict[str, Any]:
        """
        执行所有检查，返回状态报告。
        返回格式: {"status": "healthy"/"degraded"/"unhealthy", "checks": {...}}
        """
        result = {
            "timestamp": time.time(),
            "status": "healthy",
            "checks": {}
        }

        # 基础系统检查
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        result["checks"]["cpu"] = {
            "value": cpu_percent,
            "threshold": self.thresholds["cpu_percent"],
            "status": "ok" if cpu_percent < self.thresholds["cpu_percent"] else "warning"
        }
        if cpu_percent >= self.thresholds["cpu_percent"]:
            result["status"] = "degraded"

        result["checks"]["memory"] = {
            "value": memory.percent,
            "threshold": self.thresholds["memory_percent"],
            "status": "ok" if memory.percent < self.thresholds["memory_percent"] else "warning"
        }
        if memory.percent >= self.thresholds["memory_percent"]:
            result["status"] = "degraded"

        result["checks"]["disk"] = {
            "value": disk.percent,
            "threshold": self.thresholds["disk_percent"],
            "status": "ok" if disk.percent < self.thresholds["disk_percent"] else "warning"
        }
        if disk.percent >= self.thresholds["disk_percent"]:
            result["status"] = "degraded"

        # 自定义检查
        for chk in self.checks:
            try:
                check_result = chk["func"]()
                result["checks"][chk["name"]] = check_result
                if check_result.get("status") == "error":
                    result["status"] = "unhealthy"
                elif check_result.get("status") == "warning" and result["status"] == "healthy":
                    result["status"] = "degraded"
            except Exception as e:
                result["checks"][chk["name"]] = {"status": "error", "error": str(e)}
                result["status"] = "unhealthy"

        return result