# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# OTLP 导出器。

import json
from typing import Dict, Any, Optional
import aiohttp
from agentos_cta.utils.observability import get_logger

logger = get_logger(__name__)


class OtlpExporter:
    """
    OTLP 导出器。
    将指标和追踪导出到兼容 OpenTelemetry 的后端。
    """

    def __init__(self, endpoint: str, headers: Optional[Dict[str, str]] = None):
        self.endpoint = endpoint.rstrip("/")
        self.headers = headers or {}
        self.session: Optional[aiohttp.ClientSession] = None

    async def _ensure_session(self):
        """确保 HTTP 会话存在。"""
        if self.session is None:
            self.session = aiohttp.ClientSession()

    async def export(self, metrics: Dict[str, Any], traces: List[Dict[str, Any]]):
        """导出数据。"""
        await self._ensure_session()

        # 导出指标
        if metrics:
            try:
                async with self.session.post(
                    f"{self.endpoint}/v1/metrics",
                    json=metrics,
                    headers=self.headers,
                ) as resp:
                    if resp.status != 200:
                        logger.error(f"Failed to export metrics: {resp.status}")
            except Exception as e:
                logger.error(f"Metrics export error: {e}")

        # 导出追踪
        if traces:
            try:
                async with self.session.post(
                    f"{self.endpoint}/v1/traces",
                    json={"spans": traces},
                    headers=self.headers,
                ) as resp:
                    if resp.status != 200:
                        logger.error(f"Failed to export traces: {resp.status}")
            except Exception as e:
                logger.error(f"Traces export error: {e}")

    async def shutdown(self):
        """关闭导出器。"""
        if self.session:
            await self.session.close()
            self.session = None