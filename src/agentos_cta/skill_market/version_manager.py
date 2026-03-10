# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 技能版本管理器。

from typing import List, Dict, Any, Optional
from packaging import version as version_parser
from packaging.version import Version
from packaging.specifiers import SpecifierSet


class VersionManager:
    """技能版本管理，处理语义版本和约束。"""

    @staticmethod
    def parse_version(version_str: str) -> Version:
        """解析版本字符串为可比较对象。"""
        return version_parser.parse(version_str)

    @staticmethod
    def meets_constraint(version_str: str, constraint: str) -> bool:
        """
        检查版本是否满足约束（如 ">=1.0.0,<2.0.0"）。
        """
        try:
            version = VersionManager.parse_version(version_str)
            spec = SpecifierSet(constraint)
            return version in spec
        except Exception:
            return False

    @staticmethod
    def sort_versions(versions: List[str], reverse: bool = False) -> List[str]:
        """按语义版本排序。"""
        parsed = [(VersionManager.parse_version(v), v) for v in versions]
        parsed.sort(key=lambda x: x[0], reverse=reverse)
        return [v for _, v in parsed]

    @staticmethod
    def latest_version(versions: List[str]) -> Optional[str]:
        """获取最新版本。"""
        if not versions:
            return None
        sorted_versions = VersionManager.sort_versions(versions, reverse=True)
        return sorted_versions[0]

    @staticmethod
    def get_matching_versions(versions: List[str], constraint: str) -> List[str]:
        """返回满足约束的所有版本。"""
        result = []
        for v in versions:
            if VersionManager.meets_constraint(v, constraint):
                result.append(v)
        return VersionManager.sort_versions(result)