# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 工具调用执行单元。
# 用于调用外部工具（如 Shell 命令、API 等），实际由工具注册中心转发。

from typing import Dict, Any
from .base_unit import ExecutionUnit
from agentos_cta.utils.error_types import ToolExecutionError
import asyncio
import subprocess


class ToolUnit(ExecutionUnit):
    """工具调用单元，通过工具注册中心调用已注册的工具。"""

    def __init__(self, unit_id: str, config: Dict[str, Any], tool_registry):
        super().__init__(unit_id, config)
        self.tool_registry = tool_registry
        self.tool_name = config.get("tool_name")
        if not self.tool_name:
            raise ValueError("ToolUnit requires 'tool_name' in config")

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        # 从工具注册中心获取工具
        tool = await self.tool_registry.get_tool(self.tool_name)
        if not tool:
            raise ToolExecutionError(f"Tool {self.tool_name} not found")

        # 调用工具（假设工具是异步函数）
        try:
            result = await tool.execute(input_data)
            return result
        except Exception as e:
            raise ToolExecutionError(f"Tool {self.tool_name} execution failed: {e}") from e

    def get_input_schema(self) -> Dict[str, Any]:
        # 应从工具注册中心获取，简化返回通用
        return {"type": "object"}

    def get_output_schema(self) -> Dict[str, Any]:
        return {"type": "object"}

    def is_idempotent(self) -> bool:
        # 根据工具特性，可从注册中心获取，默认 False
        return False