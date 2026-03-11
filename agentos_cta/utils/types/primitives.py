# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 基础类型别名。

from typing import TypeAlias, Dict, Any, Union
from datetime import timedelta

# ID 类型
TraceID: TypeAlias = str
SessionID: TypeAlias = str
TaskID: TypeAlias = str
AgentID: TypeAlias = str
MemoryID: TypeAlias = str

# JSON 兼容字典
JSONDict: TypeAlias = Dict[str, Any]

# 时间间隔
TimeInterval: TypeAlias = Union[float, timedelta]