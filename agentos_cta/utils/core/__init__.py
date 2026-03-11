# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 核心基础工具 - 无外部依赖。

from .version import VERSION, get_agentos_version
from .platform import (
    is_windows,
    is_linux,
    is_macos,
    get_platform,
    get_cpu_count,
    get_memory_info,
)

__all__ = [
    "VERSION",
    "get_agentos_version",
    "is_windows",
    "is_linux",
    "is_macos",
    "get_platform",
    "get_cpu_count",
    "get_memory_info",
]