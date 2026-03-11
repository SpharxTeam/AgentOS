# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 文件操作执行单元。

import aiofiles
import os
from pathlib import Path
from typing import Dict, Any
from .base_unit import ExecutionUnit
from agentos_cta.utils.error_types import ToolExecutionError, SecurityError
from agentos_cta.utils.file_utils import FileUtils


class FileUnit(ExecutionUnit):
    """文件操作单元，支持读写、复制、移动、删除等。"""

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        operation = input_data.get("operation")
        if not operation:
            raise ToolExecutionError("No operation specified")

        # 安全检查：防止路径遍历
        path = input_data.get("path")
        if path:
            if ".." in path:
                raise SecurityError("Path traversal attempt detected")
            allowed_root = self.config.get("allowed_root", "/tmp/agentos")
            full_path = os.path.abspath(os.path.join(allowed_root, path))
            if not full_path.startswith(os.path.abspath(allowed_root)):
                raise SecurityError(f"Access to {full_path} denied")

        if operation == "read":
            return await self._read(input_data)
        elif operation == "write":
            return await self._write(input_data)
        elif operation == "delete":
            return await self._delete(input_data)
        elif operation == "list":
            return await self._list(input_data)
        else:
            raise ToolExecutionError(f"Unsupported operation: {operation}")

    async def _read(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        path = input_data["path"]
        encoding = input_data.get("encoding", "utf-8")
        try:
            async with aiofiles.open(path, 'r', encoding=encoding) as f:
                content = await f.read()
            return {"content": content}
        except Exception as e:
            raise ToolExecutionError(f"Read failed: {e}") from e

    async def _write(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        path = input_data["path"]
        content = input_data.get("content", "")
        encoding = input_data.get("encoding", "utf-8")
        mode = input_data.get("mode", "w")
        try:
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            async with aiofiles.open(path, mode, encoding=encoding) as f:
                await f.write(content)
            return {"success": True, "path": path}
        except Exception as e:
            raise ToolExecutionError(f"Write failed: {e}") from e

    async def _delete(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        path = input_data["path"]
        try:
            os.remove(path)
            return {"success": True}
        except Exception as e:
            raise ToolExecutionError(f"Delete failed: {e}") from e

    async def _list(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        path = input_data["path"]
        try:
            files = os.listdir(path)
            return {"files": files}
        except Exception as e:
            raise ToolExecutionError(f"List failed: {e}") from e

    def get_input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["read", "write", "delete", "list"]},
                "path": {"type": "string"},
                "content": {"type": "string"},
                "encoding": {"type": "string"},
                "mode": {"type": "string"}
            },
            "required": ["operation", "path"]
        }

    def get_output_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "content": {"type": "string"},
                "success": {"type": "boolean"},
                "path": {"type": "string"},
                "files": {"type": "array", "items": {"type": "string"}}
            }
        }

    def is_idempotent(self) -> bool:
        op = self.config.get("default_operation", "read")
        return op in ["read", "list"]