# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 代码执行单元。
# 在沙箱中执行用户提供的代码片段。

import subprocess
import tempfile
import os
from typing import Dict, Any
from .base_unit import ExecutionUnit
from agentos_cta.utils.error_types import ToolExecutionError


class CodeUnit(ExecutionUnit):
    """代码执行单元，支持 Python、JavaScript 等。"""

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        code = input_data.get("code")
        language = input_data.get("language", "python")
        if not code:
            raise ToolExecutionError("No code provided")

        # 根据语言选择执行方式
        if language == "python":
            return await self._run_python(code)
        elif language == "javascript":
            return await self._run_javascript(code)
        else:
            raise ToolExecutionError(f"Unsupported language: {language}")

    async def _run_python(self, code: str) -> Dict[str, Any]:
        # 使用 subprocess 在隔离环境中运行
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            try:
                # 超时控制
                result = subprocess.run(
                    ["python", f.name],
                    capture_output=True,
                    text=True,
                    timeout=self.timeout_ms / 1000.0
                )
                if result.returncode == 0:
                    return {"stdout": result.stdout, "stderr": result.stderr}
                else:
                    raise ToolExecutionError(f"Code execution failed: {result.stderr}")
            except subprocess.TimeoutExpired:
                raise ToolExecutionError("Code execution timed out")
            finally:
                os.unlink(f.name)

    async def _run_javascript(self, code: str) -> Dict[str, Any]:
        # 类似使用 node
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
            f.write(code)
            f.flush()
            try:
                result = subprocess.run(
                    ["node", f.name],
                    capture_output=True,
                    text=True,
                    timeout=self.timeout_ms / 1000.0
                )
                if result.returncode == 0:
                    return {"stdout": result.stdout, "stderr": result.stderr}
                else:
                    raise ToolExecutionError(f"Code execution failed: {result.stderr}")
            except subprocess.TimeoutExpired:
                raise ToolExecutionError("Code execution timed out")
            finally:
                os.unlink(f.name)

    def get_input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "code": {"type": "string"},
                "language": {"type": "string", "enum": ["python", "javascript"]}
            },
            "required": ["code"]
        }

    def get_output_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "stdout": {"type": "string"},
                "stderr": {"type": "string"}
            }
        }

    def is_idempotent(self) -> bool:
        # 代码执行通常不是幂等的
        return False