# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# Agent 基类。
# 所有专业 Agent 必须继承此类，并实现核心方法。
# 每个 Agent 采用 1+1 双模型结构（System 1 快速响应，System 2 深度思考）。

import asyncio
import json
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple, List
from agentos_cta.utils.structured_logger import get_logger
from agentos_cta.utils.error_types import AgentOSError, ModelUnavailableError

logger = get_logger(__name__)


class BaseAgent(ABC):
    """
    Agent 基类。
    封装了双模型调用逻辑，子类只需实现具体的 prompt 构建和结果解析。
    """

    def __init__(self, agent_id: str, config: Dict[str, Any]):
        """
        初始化 Agent。

        Args:
            agent_id: Agent 唯一标识。
            config: 配置字典，需包含 model_system1, model_system2 等。
        """
        self.agent_id = agent_id
        self.config = config
        self.model_system1 = config.get("model_system1", "gpt-3.5-turbo")
        self.model_system2 = config.get("model_system2", "gpt-4")
        self.timeout_ms = config.get("timeout_ms", 30000)
        self.max_retries = config.get("max_retries", 3)

    async def _call_model(self, model_name: str, prompt: str, system_prompt: Optional[str] = None) -> Tuple[str, float]:
        """
        调用指定模型（模拟实现，实际应调用 LLM API）。
        返回 (输出文本, 延迟秒数)。
        """
        # 模拟调用，子类可重写
        await asyncio.sleep(0.5)
        if "error" in prompt.lower():
            raise ModelUnavailableError(f"Model {model_name} simulated failure")
        return f"[{model_name}] Processed: {prompt[:50]}...", 0.5

    async def execute(self, task_input: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行任务的入口方法。
        子类应实现 _build_prompts 和 _parse_output，但也可重写此方法。
        """
        # 构建 System 1 和 System 2 的提示词
        prompts = self._build_prompts(task_input, context)
        system_prompt = prompts.get("system", "")
        user_prompt = prompts.get("user", "")

        # 第一步：System 1 快速响应
        s1_output, s1_latency = await self._call_model(self.model_system1, user_prompt, system_prompt)

        # 判断是否需要 System 2 深入处理（可根据复杂度或结果置信度）
        need_deep = self._need_deep_processing(task_input, s1_output)
        if need_deep:
            s2_output, s2_latency = await self._call_model(self.model_system2, user_prompt, system_prompt)
            final_output = self._merge_outputs(s1_output, s2_output)
            logger.info(f"Agent {self.agent_id} used both systems (S2 latency {s2_latency:.2f}s)")
        else:
            final_output = s1_output
            logger.info(f"Agent {self.agent_id} used only System 1")

        # 解析输出
        result = self._parse_output(final_output)
        return result

    @abstractmethod
    def _build_prompts(self, task_input: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, str]:
        """
        构建提示词，应返回包含 'system' 和 'user' 的字典。
        """
        pass

    @abstractmethod
    def _parse_output(self, raw_output: str) -> Dict[str, Any]:
        """
        解析模型输出，返回结构化结果。
        """
        pass

    def _need_deep_processing(self, task_input: Dict[str, Any], s1_output: str) -> bool:
        """
        判断是否需要 System 2 深入处理。
        默认根据任务输入中的复杂度标志或输出长度等判断，子类可覆盖。
        """
        # 简单规则：如果输入包含 'complex' 或输出较短（可能不完整），则启用 S2
        if task_input.get("complex", False):
            return True
        if len(s1_output) < 100:
            return True
        return False

    def _merge_outputs(self, s1: str, s2: str) -> str:
        """
        合并 System 1 和 System 2 的输出，默认取较长的（假设更详细）。
        """
        return s2 if len(s2) > len(s1) else s1

    def get_contract(self) -> Dict[str, Any]:
        """
        返回该 Agent 的契约描述。
        子类应重写，或从配置文件加载。
        """
        # 默认实现，返回空契约；实际应由子类提供
        return {
            "agent_id": self.agent_id,
            "role": "unknown",
            "capabilities": [],
            "input_schema": {},
            "output_schema": {},
        }