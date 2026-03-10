# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 技能更新器。

from typing import Optional
from agentos_cta.utils.structured_logger import get_logger
from .installer import SkillInstaller
from .uninstaller import SkillUninstaller
from .registry import SkillRegistry
from .version_manager import VersionManager

logger = get_logger(__name__)


class SkillUpdater:
    """技能更新器，检查并更新到最新版本。"""

    def __init__(self, registry: SkillRegistry, installer: SkillInstaller, uninstaller: SkillUninstaller):
        self.registry = registry
        self.installer = installer
        self.uninstaller = uninstaller

    async def check_updates(self, skill_id: Optional[str] = None) -> dict:
        """检查技能是否有更新。返回需要更新的技能列表。"""
        updates = {}
        if skill_id:
            skills = [await self.registry.get_skill(skill_id)]
        else:
            skills = await self.registry.list_skills()

        for skill in skills:
            if not skill:
                continue
            current_version = skill["version"]
            # 从源获取最新版本（需要源信息，简化：从注册中心获取所有版本）
            versions = await self.registry.get_versions(skill["skill_id"])
            latest = VersionManager.latest_version(versions)
            if latest and latest != current_version:
                updates[skill["skill_id"]] = {
                    "current": current_version,
                    "latest": latest
                }
        return updates

    async def update(self, skill_id: str) -> bool:
        """更新指定技能到最新版本。"""
        updates = await self.check_updates(skill_id)
        if skill_id not in updates:
            logger.info(f"Skill {skill_id} is already up to date")
            return True

        latest = updates[skill_id]["latest"]
        # 先卸载旧版本
        await self.uninstaller.uninstall(skill_id, remove_files=True)
        # 安装新版本
        # 需要知道源，这里假设源为 registry，实际应记录源信息
        success = await self.installer.install(skill_id, source="registry", version=latest)
        if success:
            logger.info(f"Updated {skill_id} to {latest}")
        return success