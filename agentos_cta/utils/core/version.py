# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 版本管理。

VERSION = "3.0.0"
__version__ = VERSION


def get_agentos_version() -> str:
    """获取 AgentOS 内核版本。"""
    return VERSION


def check_version_compatibility(required_version: str) -> bool:
    """
    检查版本兼容性（语义化版本）。
    示例：required_version = ">=3.0.0,<4.0.0"
    """
    from packaging.specifiers import SpecifierSet
    from packaging.version import Version

    spec = SpecifierSet(required_version)
    return Version(VERSION) in spec