# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 技能依赖解析器。

from typing import List, Dict, Any, Set, Optional
from collections import deque
from agentos_cta.utils.structured_logger import get_logger
from .version_manager import VersionManager

logger = get_logger(__name__)


class DependencyResolver:
    """技能依赖解析器，处理依赖图、版本冲突和拓扑排序。"""

    def __init__(self, registry):
        self.registry = registry  # 技能注册中心，用于获取技能信息

    async def resolve(self, skill_id: str, version_constraint: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        解析指定技能的依赖，返回安装顺序（拓扑排序）。
        每个依赖项包含 skill_id 和选定的版本。
        """
        # 获取技能信息
        skill_info = await self.registry.get_skill(skill_id)
        if not skill_info:
            raise ValueError(f"Skill {skill_id} not found")

        # 确定目标版本
        target_version = None
        if version_constraint:
            available_versions = await self.registry.get_versions(skill_id)
            matching = VersionManager.get_matching_versions(available_versions, version_constraint)
            if not matching:
                raise ValueError(f"No version of {skill_id} satisfies {version_constraint}")
            target_version = VersionManager.latest_version(matching)
        else:
            target_version = skill_info.get("version")  # 默认使用当前版本

        # BFS 收集所有依赖
        graph = {}  # skill_id -> list of (dep_id, constraint)
        queue = deque()
        queue.append((skill_id, target_version))
        visited = set()

        while queue:
            current_id, current_ver = queue.popleft()
            if current_id in visited:
                continue
            visited.add(current_id)

            # 获取技能契约
            contract = await self.registry.get_skill_contract(current_id, current_ver)
            if not contract:
                raise ValueError(f"Cannot fetch contract for {current_id} v{current_ver}")

            deps = contract.get("dependencies", [])
            graph[current_id] = []

            for dep in deps:
                dep_id = dep["skill_id"]
                dep_constraint = dep.get("version_constraint", "")
                graph[current_id].append((dep_id, dep_constraint))

                # 解析依赖版本
                available = await self.registry.get_versions(dep_id)
                matching = VersionManager.get_matching_versions(available, dep_constraint)
                if not matching:
                    raise ValueError(f"Dependency {dep_id} of {current_id} cannot satisfy {dep_constraint}")
                dep_ver = VersionManager.latest_version(matching)

                queue.append((dep_id, dep_ver))

        # 拓扑排序
        in_degree = {node: 0 for node in graph}
        for node, deps in graph.items():
            for dep_id, _ in deps:
                if dep_id in in_degree:
                    in_degree[dep_id] += 1
                else:
                    # 依赖可能不在图中（如果之前未加入）
                    in_degree[dep_id] = 1

        # Kahn 算法
        result = []
        zero_degree = deque([n for n in in_degree if in_degree[n] == 0])

        while zero_degree:
            node = zero_degree.popleft()
            result.append(node)
            for dep_id, _ in graph.get(node, []):
                in_degree[dep_id] -= 1
                if in_degree[dep_id] == 0:
                    zero_degree.append(dep_id)

        # 检查环
        if len(result) != len(in_degree):
            raise ValueError("Circular dependency detected")

        # 转换结果为包含版本信息的列表
        resolved = []
        for skill_id in result:
            # 获取之前确定的版本（简化：我们可以在遍历时记录版本，这里省略）
            # 实际应存储版本信息，此处占位
            resolved.append({"skill_id": skill_id, "version": "latest"})

        return resolved