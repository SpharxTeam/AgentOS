# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 技能安装器。

import shutil
from pathlib import Path
from typing import Optional, Dict, Any, List
from agentos_cta.utils.structured_logger import get_logger
from agentos_cta.utils.file_utils import FileUtils
from .contracts import validate_skill_contract
from .sources import GitHubSource, LocalSource, RegistrySource
from .dependency_resolver import DependencyResolver
from .registry import SkillRegistry

logger = get_logger(__name__)


class SkillInstaller:
    """技能安装器，支持从不同源安装技能。"""

    def __init__(self, registry: SkillRegistry, install_dir: str = "data/skills"):
        self.registry = registry
        self.install_dir = Path(install_dir)
        self.install_dir.mkdir(parents=True, exist_ok=True)
        self.resolver = DependencyResolver(registry)

        # 初始化技能源
        self.sources = {
            "github": GitHubSource({}),
            "local": LocalSource("data/skill_sources/local"),
            "registry": RegistrySource(),
        }

    async def install(self, skill_ref: str, source: str = "github", version: Optional[str] = None) -> bool:
        """
        安装技能。

        Args:
            skill_ref: 技能标识（如 "github:owner/repo" 或 skill_id）
            source: 源名称 ("github", "local", "registry")
            version: 指定版本，默认最新

        Returns:
            是否安装成功
        """
        # 解析源
        src = self.sources.get(source)
        if not src:
            logger.error(f"Unknown source: {source}")
            return False

        # 解析依赖
        try:
            # 先获取技能契约（可能需要先解析 skill_ref 为 skill_id）
            # 简化：假设 skill_ref 就是 skill_id
            skill_id = skill_ref
            resolved = await self.resolver.resolve(skill_id, version)
        except Exception as e:
            logger.error(f"Dependency resolution failed: {e}")
            return False

        # 按顺序安装依赖
        for dep in resolved:
            dep_id = dep["skill_id"]
            dep_ver = dep.get("version")
            # 检查是否已安装
            existing = await self.registry.get_skill(dep_id)
            if existing:
                logger.info(f"Skill {dep_id} already installed, skipping")
                continue
            # 获取技能包
            try:
                skill_path = await src.fetch_skill(dep_id, dep_ver)
            except Exception as e:
                logger.error(f"Failed to fetch skill {dep_id}: {e}")
                return False

            # 验证契约
            contract_file = skill_path / "skill.json"
            if not contract_file.exists():
                logger.error(f"No skill.json found in {skill_path}")
                return False
            contract = FileUtils.read_json(contract_file)
            if not contract:
                logger.error("Invalid skill.json")
                return False
            try:
                validate_skill_contract(contract)
            except Exception as e:
                logger.error(f"Contract validation failed: {e}")
                return False

            # 复制到安装目录
            target_dir = self.install_dir / f"{dep_id}-{contract['version']}"
            if target_dir.exists():
                shutil.rmtree(target_dir)
            shutil.copytree(skill_path, target_dir)

            # 注册
            await self.registry.register_skill(contract, str(target_dir))

            logger.info(f"Installed skill {dep_id} v{contract['version']}")

        return True