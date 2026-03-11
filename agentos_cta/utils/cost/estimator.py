# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 成本预估器。

import yaml
from typing import Dict, Optional
from pathlib import Path
from agentos_cta.utils.error import ConfigurationError


class ModelPricing:
    """模型定价信息。"""

    def __init__(self, input_cost: float, output_cost: float, currency: str = "USD"):
        self.input_cost = input_cost  # 每千 token 成本
        self.output_cost = output_cost
        self.currency = currency

    def estimate(self, input_tokens: int, output_tokens: int) -> float:
        """预估成本。"""
        return (input_tokens / 1000 * self.input_cost) + (output_tokens / 1000 * self.output_cost)


class CostEstimator:
    """
    成本预估器。
    基于模型配置和 Token 用量计算 API 调用成本。
    """

    DEFAULT_PRICING = {
        "gpt-4": ModelPricing(0.03, 0.06),
        "gpt-4-turbo": ModelPricing(0.01, 0.03),
        "gpt-3.5-turbo": ModelPricing(0.0015, 0.002),
        "claude-3-opus": ModelPricing(0.015, 0.075),
        "claude-3-sonnet": ModelPricing(0.003, 0.015),
        "claude-3-haiku": ModelPricing(0.00025, 0.00125),
    }

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化成本预估器。

        Args:
            config_path: 模型配置文件路径（YAML）。若未提供，使用默认定价。
        """
        self.pricing = self.DEFAULT_PRICING.copy()
        if config_path and Path(config_path).exists():
            self._load_config(config_path)

    def _load_config(self, config_path: str):
        """加载配置文件。"""
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        models = config.get('models', [])
        for model in models:
            name = model['name']
            self.pricing[name] = ModelPricing(
                input_cost=model.get('input_cost_per_1k', 0),
                output_cost=model.get('output_cost_per_1k', 0),
            )

    def estimate(self, model_name: str, input_tokens: int, output_tokens: int) -> float:
        """
        估算一次调用的成本。

        Args:
            model_name: 模型名称。
            input_tokens: 输入 token 数。
            output_tokens: 输出 token 数。

        Returns:
            成本（美元）。
        """
        pricing = self.pricing.get(model_name)
        if not pricing:
            raise ConfigurationError(f"No pricing found for model {model_name}")
        return pricing.estimate(input_tokens, output_tokens)

    def get_pricing(self, model_name: str) -> Optional[ModelPricing]:
        """获取模型定价。"""
        return self.pricing.get(model_name)