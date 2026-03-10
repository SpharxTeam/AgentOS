# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 技能契约验证器。

import json
import jsonschema
from pathlib import Path
from typing import Dict, Any, Union
from agentos_cta.utils.error_types import ConfigurationError


class SkillContractValidationError(ConfigurationError):
    """技能契约验证失败异常。"""
    pass


def load_schema() -> Dict[str, Any]:
    """加载技能契约 JSON Schema。"""
    schema_path = Path(__file__).parent / "skill_schema.json"
    with open(schema_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def validate_skill_contract(contract: Dict[str, Any]) -> bool:
    """
    验证技能契约是否符合规范。

    Args:
        contract: 待验证的契约字典。

    Returns:
        True 表示验证通过。

    Raises:
        SkillContractValidationError: 如果验证失败。
    """
    schema = load_schema()
    try:
        jsonschema.validate(contract, schema)
    except jsonschema.ValidationError as e:
        raise SkillContractValidationError(f"Skill contract validation failed: {e.message}") from e
    return True


def validate_skill_contract_file(file_path: Union[str, Path]) -> bool:
    """从文件加载并验证技能契约。"""
    with open(file_path, 'r', encoding='utf-8') as f:
        contract = json.load(f)
    return validate_skill_contract(contract)