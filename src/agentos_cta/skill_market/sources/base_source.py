# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 技能源基类。

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pathlib import Path


class SkillSource(ABC):
    """技能源基类，定义从何处获取技能。"""

    @abstractmethod
    async def list_skills(self) -> List[Dict[str, Any]]:
        """列出该源中可用的技能元数据（不含完整代码）。"""
        pass

    @abstractmethod
    async def fetch_skill(self, skill_id: str, version: Optional[str] = None) -> Path:
        """
        获取指定技能，返回技能包所在的本地路径。
        技能包应包含 skill.json 契约和实现代码。
        """
        pass

    @abstractmethod
    async def search(self, query: str) -> List[Dict[str, Any]]:
        """搜索技能。"""
        pass