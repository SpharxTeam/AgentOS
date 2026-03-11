# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 成本预估模块。
# 根据模型配置、token 用量估算 API 调用成本。

from typing import Dict, Optional
import yaml
import os


class CostEstimator:
    """成本预估器，基于模型定价计算费用。"""

    DEFAULT_MODEL_CONFIG = {
        "gpt-4": {"input_cost_per_token": 0.00003, "output_cost_per_token": 0.00006},
        "gpt-3.5-turbo": {"input_cost_per_token": 0.0000015, "output_cost_per_token": 0.000002},
        "claude-3-opus": {"input_cost_per_token": 0.000015, "output_cost_per_token": 0.000075},
        "claude-3-sonnet": {"input_cost_per_token": 0.000003, "output_cost_per_token": 0.000015},
        "default": {"input_cost_per_token": 0.00001, "output_cost_per_token": 0.00003},
    }

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化成本预估器。

        Args:
            config_path: 模型配置文件路径（YAML）。若未提供，使用默认定价。
        """
        self.model_config = self.DEFAULT_MODEL_CONFIG.copy()
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                user_config = yaml.safe_load(f)
                if user_config and 'models' in user_config:
                    for model in user_config['models']:
                        name = model['name']
                        self.model_config[name] = {
                            'input_cost_per_token': model.get('input_cost_per_token', 0),
                            'output_cost_per_token': model.get('output_cost_per_token', 0),
                        }

    def estimate_cost(self, model_name: str, input_tokens: int, output_tokens: int) -> float:
        """
        估算一次调用的成本。

        Args:
            model_name: 模型名称。
            input_tokens: 输入 token 数。
            output_tokens: 输出 token 数。

        Returns:
            成本（美元）。
        """
        cfg = self.model_config.get(model_name, self.model_config['default'])
        input_cost = cfg['input_cost_per_token'] * input_tokens
        output_cost = cfg['output_cost_per_token'] * output_tokens
        return input_cost + output_cost

    def estimate_task_cost(self, model_name: str, total_input_tokens: int, total_output_tokens: int) -> float:
        """同 estimate_cost，保留别名。"""
        return self.estimate_cost(model_name, total_input_tokens, total_output_tokens)