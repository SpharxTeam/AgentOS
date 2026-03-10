# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 编解码器，集成 ADOL 优化（如 Schema 去重、可选字段控制）。

from typing import Dict, Any, Optional
import json
import copy


class Codec:
    """
    编解码器，负责在传输层进行优化。
    目前主要实现可选字段过滤和 Schema 去重（预留）。
    """

    def __init__(self, schema_registry: Optional[Dict] = None):
        self.schema_registry = schema_registry or {}

    def encode(self, obj: Dict[str, Any], schema_name: Optional[str] = None) -> Dict[str, Any]:
        """
        编码：根据 schema 过滤可选字段、替换引用等。
        目前简单返回原对象，预留扩展。
        """
        # 如果提供了 schema 名称，可进行字段裁剪
        if schema_name and schema_name in self.schema_registry:
            schema = self.schema_registry[schema_name]
            # 示例：仅保留 schema 中定义的字段
            if "properties" in schema:
                allowed = set(schema["properties"].keys())
                encoded = {k: v for k, v in obj.items() if k in allowed}
                return encoded
        return copy.deepcopy(obj)

    def decode(self, obj: Dict[str, Any], schema_name: Optional[str] = None) -> Dict[str, Any]:
        """解码（目前无操作）。"""
        return copy.deepcopy(obj)

    def register_schema(self, name: str, schema: Dict):
        """注册 schema 供编码使用。"""
        self.schema_registry[name] = schema