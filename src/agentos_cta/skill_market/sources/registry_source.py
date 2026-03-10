# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 官方注册源。

import aiohttp
from typing import List, Dict, Any, Optional
from pathlib import Path
import tempfile
import zipfile
from agentos_cta.utils.structured_logger import get_logger
from .base_source import SkillSource

logger = get_logger(__name__)


class RegistrySource(SkillSource):
    """从官方注册中心获取技能。"""

    def __init__(self, registry_url: str = "https://registry.agentos.org/api/v1"):
        self.registry_url = registry_url.rstrip('/')

    async def list_skills(self) -> List[Dict[str, Any]]:
        """调用注册中心 API 获取技能列表。"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.registry_url}/skills") as resp:
                if resp.status != 200:
                    logger.error(f"Failed to fetch registry skills: {resp.status}")
                    return []
                data = await resp.json()
                return data.get("skills", [])

    async def fetch_skill(self, skill_id: str, version: Optional[str] = None) -> Path:
        """下载技能包。"""
        params = {"skill_id": skill_id}
        if version:
            params["version"] = version
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.registry_url}/download", params=params) as resp:
                if resp.status != 200:
                    raise RuntimeError(f"Failed to download skill: {resp.status}")
                # 保存到临时文件
                with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp:
                    tmp.write(await resp.read())
                    tmp_path = tmp.name

        # 解压到临时目录
        extract_dir = Path(tempfile.mkdtemp(prefix=f"skill_{skill_id}_"))
        with zipfile.ZipFile(tmp_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        Path(tmp_path).unlink()  # 删除临时zip
        return extract_dir

    async def search(self, query: str) -> List[Dict[str, Any]]:
        """调用 API 搜索。"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.registry_url}/search", params={"q": query}) as resp:
                if resp.status != 200:
                    return []
                data = await resp.json()
                return data.get("results", [])