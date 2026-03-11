# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 消息序列化器。

import json
import pickle
from typing import Any, Optional
from agentos_cta.utils.error import AgentOSError


class MessageSerializer:
    """
    消息序列化器。
    支持 JSON、Pickle 等格式。
    """

    SUPPORTED_FORMATS = ["json", "pickle"]

    def __init__(self, format: str = "json"):
        if format not in self.SUPPORTED_FORMATS:
            raise AgentOSError(f"Unsupported format: {format}")
        self.format = format

    def serialize(self, obj: Any) -> bytes:
        """序列化对象。"""
        if self.format == "json":
            return json.dumps(obj, ensure_ascii=False).encode("utf-8")
        elif self.format == "pickle":
            return pickle.dumps(obj)
        else:
            raise AgentOSError(f"Format {self.format} not implemented")

    def deserialize(self, data: bytes) -> Any:
        """反序列化对象。"""
        if self.format == "json":
            return json.loads(data.decode("utf-8"))
        elif self.format == "pickle":
            return pickle.loads(data)
        else:
            raise AgentOSError(f"Format {self.format} not implemented")