# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# GitHub 技能源。

import os
import tempfile
import zipfile
import aiohttp
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse
from agentos_cta.utils.structured_logger import get_logger
from agentos_cta.utils.file_utils import FileUtils
from .base_source import SkillSource

logger = get_logger(__name__)


class GitHubSource(SkillSource):
    """从 GitHub 仓库获取技能。"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.cache_dir = Path(config.get("cache_dir", "data/skill_cache/github"))
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    async def list_skills(self) -> List[Dict[str, Any]]:
        """从 GitHub 索引文件获取可用技能列表。"""
        index_url = self.config.get("index_url", "https://raw.githubusercontent.com/agentos/skills/main/index.json")
        async with aiohttp.ClientSession() as session:
            async with session.get(index_url) as resp:
                if resp.status != 200:
                    logger.error(f"Failed to fetch index: {resp.status}")
                    return []
                data = await resp.json()
                return data.get("skills", [])

    async def fetch_skill(self, skill_id: str, version: Optional[str] = None) -> Path:
        """
        从 GitHub 下载技能。
        格式：https://github.com/{owner}/{repo}/releases/download/{tag}/skill.zip
        """
        # 查找技能元数据
        skills = await self.list_skills()
        skill_info = next((s for s in skills if s["skill_id"] == skill_id), None)
        if not skill_info:
            raise ValueError(f"Skill {skill_id} not found in index")

        # 确定版本
        if version is None:
            version = skill_info.get("latest_version")
        if not version:
            raise ValueError(f"No version specified for skill {skill_id}")

        # 构造下载 URL
        download_url = skill_info.get("download_url")
        if not download_url:
            # 默认构造 pattern
            owner_repo = skill_info.get("repository", "").replace("https://github.com/", "")
            download_url = f"https://github.com/{owner_repo}/releases/download/{version}/skill.zip"

        # 下载到缓存
        cache_file = self.cache_dir / f"{skill_id}-{version}.zip"
        if not cache_file.exists():
            async with aiohttp.ClientSession() as session:
                async with session.get(download_url) as resp:
                    if resp.status != 200:
                        raise RuntimeError(f"Failed to download {download_url}")
                    with open(cache_file, 'wb') as f:
                        f.write(await resp.read())

        # 解压到临时目录
        extract_dir = self.cache_dir / f"{skill_id}-{version}"
        if not extract_dir.exists():
            with zipfile.ZipFile(cache_file, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)

        return extract_dir

    async def search(self, query: str) -> List[Dict[str, Any]]:
        """简单搜索（过滤名称和描述）。"""
        skills = await self.list_skills()
        query_lower = query.lower()
        results = []
        for s in skills:
            if (query_lower in s.get("name", "").lower() or
                query_lower in s.get("description", "").lower()):
                results.append(s)
        return results