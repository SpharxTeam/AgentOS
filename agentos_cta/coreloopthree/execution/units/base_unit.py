# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 执行单元基类。

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import asyncio
from agentos_cta.utils.observability import get_logger
from agentos_cta.utils.error import ToolExecutionError

logger = get_logger(__name__)


class ExecutionUnit(ABC):
    """
    执行单元基类。
    所有具体执行单元必须继承此类，并实现 execute 方法。
    每个单元应具备幂等性标识，支持契约测试。
    """

    def __init__(self, unit_id: str, config: Dict[str, Any]):
        self.unit_id = unit_id
        self.config = config
        self.timeout_ms = config.get("timeout_ms", 10000)
        self.retry_count = 0
        self.max_retries = config.get("max_retries", 2)

    @abstractmethod
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行单元的核心逻辑。

        Args:
            input_data: 符合输入 Schema 的数据。

        Returns:
            执行结果，必须符合输出 Schema。

        Raises:
            ToolExecutionError: 执行失败时抛出。
        """
        pass

    @abstractmethod
    def get_input_schema(self) -> Dict[str, Any]:
        """返回该单元的输入 JSON Schema。"""
        pass

    @abstractmethod
    def get_output_schema(self) -> Dict[str, Any]:
        """返回该单元的输出 JSON Schema。"""
        pass

    def is_idempotent(self) -> bool:
        """返回该单元是否幂等（可重复执行而不产生副作用）。"""
        return False

    async def execute_with_retry(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """带重试的执行包装。"""
        for attempt in range(self.max_retries + 1):
            try:
                result = await asyncio.wait_for(
                    self.execute(input_data),
                    timeout=self.timeout_ms / 1000.0
                )
                return result
            except asyncio.TimeoutError:
                logger.warning(f"Unit {self.unit_id} timeout (attempt {attempt+1}/{self.max_retries+1})")
                if attempt == self.max_retries:
                    raise ToolExecutionError(f"Unit {self.unit_id} timeout after {self.max_retries} retries")
            except Exception as e:
                logger.error(f"Unit {self.unit_id} failed: {e}")
                if attempt == self.max_retries:
                    raise ToolExecutionError(f"Unit {self.unit_id} failed: {e}") from e