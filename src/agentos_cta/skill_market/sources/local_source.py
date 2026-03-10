# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 本地文件技能源。

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import shutil
from agentos_cta.utils.structured_logger import get_logger
from agentos_cta.utils.file_utils import FileUtils
from .base_source import SkillSource

logger = get_logger(__name__)


class LocalSource(SkillSource):
    """从本地目录加载技能。"""

    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    async def list_skills(self) -> List[Dict[str, Any]]:
        """扫描本地目录下的所有技能。"""
        skills = []
        for item in self.base_dir.iterdir():
            if item.is_dir():
                contract_file = item / "skill.json"
                if contract_file.exists():
                    try:
                        contract = json.loads(FileUtils.safe_read(contract_file))
                        skills.append(contract)
                    except Exception as e:
                        logger.warning(f"Failed to load skill from {item}: {e}")
        return skills

    async def fetch_skill(self, skill_id: str, version: Optional[str] = None) -> Path:
        """从本地目录复制技能。"""
        # 查找匹配的目录
        for item in self.base_dir.iterdir():
            if item.is_dir():
                contract_file = item / "skill.json"
                if contract_file.exists():
                    contract = json.loads(FileUtils.safe_read(contract_file))
                    if contract.get("skill_id") == skill_id:
                        # 如果指定了版本，检查版本
                        if version and contract.get("version") != version:
                            continue
                        # 复制到临时目录（或直接返回路径，但为了统一，复制）
                        temp_dir = Path("/tmp") / f"skill_{skill_id}_{version or 'latest'}"
                        if temp_dir.exists():
                            shutil.rmtree(temp_dir)
                        shutil.copytree(item, temp_dir)
                        return temp_dir
        raise ValueError(f"Skill {skill_id} not found locally")

    async def search(self, query: str) -> List[Dict[str, Any]]:
        """搜索本地技能。"""
        skills = await self.list_skills()
        query_lower = query.lower()
        results = []
        for s in skills:
            if (query_lower in s.get("name", "").lower() or
                query_lower in s.get("description", "").lower()):
                results.append(s)
        return results