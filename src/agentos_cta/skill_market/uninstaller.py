# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 技能卸载器。

import shutil
from pathlib import Path
from agentos_cta.utils.structured_logger import get_logger
from .registry import SkillRegistry

logger = get_logger(__name__)


class SkillUninstaller:
    """技能卸载器。"""

    def __init__(self, registry: SkillRegistry):
        self.registry = registry

    async def uninstall(self, skill_id: str, remove_files: bool = True) -> bool:
        """卸载指定技能。"""
        skill = await self.registry.get_skill(skill_id)
        if not skill:
            logger.warning(f"Skill {skill_id} not found")
            return False

        # 检查是否有其他技能依赖它（可选）
        # 简单实现：直接卸载

        # 从注册中心移除
        await self.registry.unregister_skill(skill_id)

        # 删除文件
        if remove_files and skill.get("install_path"):
            install_path = Path(skill["install_path"])
            if install_path.exists():
                shutil.rmtree(install_path)
                logger.info(f"Removed files at {install_path}")

        logger.info(f"Uninstalled skill {skill_id}")
        return True