# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 路由模块：意图理解、复杂度评估、资源匹配。

from typing import Optional, Dict, Any
import re
from agentos_cta.utils.observability import get_logger
from agentos_cta.utils.error import ConfigurationError
from .schemas import Intent, ComplexityLevel, ResourceMatch

logger = get_logger(__name__)


class Router:
    """
    路由层核心类。
    负责将原始用户输入转化为结构化 Intent，并匹配合适的模型资源。
    """

    def __init__(self, config: Dict[str, Any]):
        """
        初始化路由器。

        Args:
            config: 配置字典，需包含 models.yaml 中定义的模型列表。
        """
        self.config = config
        self.models = config.get('models', [])
        if not self.models:
            raise ConfigurationError("No models configured in Router")

    def parse_intent(self, raw_text: str, context: Optional[Dict[str, Any]] = None) -> Intent:
        """
        解析用户原始输入，生成结构化 Intent。
        当前实现简单基于规则，后续可替换为 NLU 模型。
        """
        text_lower = raw_text.lower()
        simple_keywords = ['hello', 'hi', 'help', 'status']
        complex_keywords = ['develop', 'create', 'build', 'design', 'analyze', 'multiple', 'steps']

        if any(kw in text_lower for kw in simple_keywords) and len(raw_text) < 100:
            complexity = ComplexityLevel.SIMPLE
        elif any(kw in text_lower for kw in complex_keywords) or len(raw_text) > 500:
            complexity = ComplexityLevel.COMPLEX
        else:
            complexity = ComplexityLevel.COMPLEX  # 默认复杂

        # 提取目标（简单提取第一句话）
        goal = re.split(r'[.。!！?？]', raw_text)[0].strip()
        if not goal:
            goal = raw_text[:100]

        intent = Intent(
            raw_text=raw_text,
            normalized_text=raw_text.strip(),
            goal=goal,
            constraints={},
            context=context or {},
            complexity=complexity
        )
        logger.info(f"Parsed intent: goal='{goal}', complexity={complexity}")
        return intent

    def match_resource(self, intent: Intent) -> ResourceMatch:
        """
        根据意图复杂度匹配合适的模型资源。
        返回 ResourceMatch 包含模型名称和 Token 预算。
        """
        complexity = intent.complexity
        selected_model = None

        if complexity == ComplexityLevel.SIMPLE:
            # 选取轻量模型（如 gpt-3.5-turbo）
            for m in self.models:
                if 'gpt-3.5' in m.get('name', ''):
                    selected_model = m
                    break
            if not selected_model and self.models:
                selected_model = self.models[0]
        else:  # COMPLEX or CRITICAL
            # 选取最强模型（如 gpt-4 或 claude-3-opus）
            for m in self.models:
                if 'gpt-4' in m.get('name', '') or 'opus' in m.get('name', ''):
                    selected_model = m
                    break
            if not selected_model and self.models:
                selected_model = self.models[-1]

        if not selected_model:
            raise ConfigurationError(f"No suitable model found for complexity {complexity}")

        model_name = selected_model['name']
        # 预估 token（简单估算，实际应调用 token_counter）
        estimated_input = 500 if complexity == ComplexityLevel.SIMPLE else 2000
        estimated_output = 200 if complexity == ComplexityLevel.SIMPLE else 1000
        budget = selected_model.get('context_window', 16000)

        resource = ResourceMatch(
            model_name=model_name,
            estimated_input_tokens=estimated_input,
            estimated_output_tokens=estimated_output,
            max_budget_tokens=budget,
            reason=f"Matched based on complexity {complexity}"
        )
        logger.info(f"Resource matched: {model_name}, budget={budget}")
        return resource