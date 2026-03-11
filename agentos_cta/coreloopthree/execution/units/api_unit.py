# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# API 调用执行单元。

import aiohttp
import asyncio
from typing import Dict, Any
from .base_unit import ExecutionUnit
from agentos_cta.utils.error_types import ToolExecutionError


class APIUnit(ExecutionUnit):
    """API 调用单元，支持 HTTP 请求。"""

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        method = input_data.get("method", "GET").upper()
        url = input_data.get("url")
        headers = input_data.get("headers", {})
        params = input_data.get("params", {})
        body = input_data.get("body")
        timeout = input_data.get("timeout", self.timeout_ms / 1000.0)

        if not url:
            raise ToolExecutionError("URL is required")

        async with aiohttp.ClientSession() as session:
            try:
                async with session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    json=body if isinstance(body, dict) else None,
                    data=body if not isinstance(body, dict) else None,
                    timeout=aiohttp.ClientTimeout(total=timeout)
                ) as resp:
                    response_body = await resp.text()
                    return {
                        "status_code": resp.status,
                        "headers": dict(resp.headers),
                        "body": response_body
                    }
            except aiohttp.ClientError as e:
                raise ToolExecutionError(f"API request failed: {e}") from e
            except asyncio.TimeoutError:
                raise ToolExecutionError("API request timed out")

    def get_input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "method": {"type": "string", "enum": ["GET", "POST", "PUT", "DELETE", "PATCH"]},
                "url": {"type": "string"},
                "headers": {"type": "object"},
                "params": {"type": "object"},
                "body": {"type": ["object", "string", "null"]},
                "timeout": {"type": "number"}
            },
            "required": ["url"]
        }

    def get_output_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "status_code": {"type": "integer"},
                "headers": {"type": "object"},
                "body": {"type": "string"}
            }
        }

    def is_idempotent(self) -> bool:
        method = self.config.get("default_method", "GET").upper()
        return method in ["GET", "HEAD", "OPTIONS"]