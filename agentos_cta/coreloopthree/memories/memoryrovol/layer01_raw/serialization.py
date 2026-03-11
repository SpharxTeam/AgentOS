# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 记忆序列化：支持多种格式。

import json
import pickle
from typing import Any, Optional
from agentos_cta.utils.error_types import AgentOSError


class Serializer:
    """
    记忆序列化器。
    支持 JSON、Pickle、Protobuf 等格式。
    """

    SUPPORTED_FORMATS = ['json', 'pickle']

    def __init__(self, format: str = 'json'):
        if format not in self.SUPPORTED_FORMATS:
            raise AgentOSError(f"Unsupported serialization format: {format}")
        self.format = format

    def serialize(self, obj: Any) -> bytes:
        """将对象序列化为字节。"""
        if self.format == 'json':
            return json.dumps(obj, ensure_ascii=False).encode('utf-8')
        elif self.format == 'pickle':
            return pickle.dumps(obj)
        else:
            raise AgentOSError(f"Format {self.format} not implemented")

    def deserialize(self, data: bytes) -> Any:
        """将字节反序列化为对象。"""
        if self.format == 'json':
            return json.loads(data.decode('utf-8'))
        elif self.format == 'pickle':
            return pickle.loads(data)
        else:
            raise AgentOSError(f"Format {self.format} not implemented")