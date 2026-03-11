# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 团队委员会：负责个体规则进化、Agent契约更新。

from typing import Dict, Any, List, Optional
import asyncio
import time
import json
from pathlib import Path
from dataclasses import dataclass, field
from agentos_cta.utils.observability import get_logger
from agentos_cta.utils.error import AgentOSError
from agentos_cta.utils.io.file_utils import FileUtils

logger = get_logger(__name__)


@dataclass
class RuleUpdate:
    """个体规则更新项。"""
    agent_role: str
    rule_file: str  # 规则文件路径
    old_version: str
    new_version: str
    changes: List[str]
    reason: str
    updated_content: str  # 新规则内容


class TeamCommittee:
    """
    团队委员会。
    负责根据协调、技术、审计委员会的建议，更新个体 Agent 的规则文件。
    更新 Agent 契约（contract.json）和提示词模板。
    """

    def __init__(self, memory_roviol, config: Dict[str, Any]):
        self.memory = memory_roviol
        self.config = config
        self.rule_updates: List[RuleUpdate] = []
        self._lock = asyncio.Lock()
        self.agents_dir = Path(config.get("agents_dir", "agentos_open/contrib/agents"))

    async def integrate_committee_inputs(self,
                                         coordination_proposals: List,
                                         technical_updates: List,
                                         audit_findings: List) -> List[RuleUpdate]:
        """
        整合其他委员会的输出，生成规则更新列表。
        """
        updates = []
        # 根据审计发现更新 Agent 规则
        for finding in audit_findings:
            if finding.severity == "critical":
                for agent in finding.affected_agents:
                    # 为受影响的 Agent 生成规则更新
                    update = await self._generate_rule_update(agent, finding)
                    if update:
                        updates.append(update)
        # 根据技术规范更新更新 Agent 契约
        for spec_update in technical_updates:
            # 查找依赖该规范的 Agent
            # 简化：假设所有 Agent 都需要更新
            update = RuleUpdate(
                agent_role="all",
                rule_file="contract.json",
                old_version="1.0.0",
                new_version="1.1.0",
                changes=["Update API schema"],
                reason=spec_update.reason,
                updated_content=json.dumps({"version": "1.1.0", "apis": [...]})
            )
            updates.append(update)
        return updates

    async def _generate_rule_update(self, agent_id: str, finding) -> Optional[RuleUpdate]:
        """根据审计发现为特定 Agent 生成规则更新。"""
        # 定位 Agent 的规则文件
        agent_path = self.agents_dir / agent_id / "contract.json"
        if not agent_path.exists():
            logger.error(f"Agent contract not found: {agent_path}")
            return None
        # 读取现有契约
        contract = FileUtils.read_json(agent_path)
        if not contract:
            return None
        old_version = contract.get("version", "0.0.0")
        # 计算新版本（语义化版本递增）
        parts = old_version.split(".")
        new_version = f"{parts[0]}.{parts[1]}.{int(parts[2])+1}"
        # 修改内容（示例：增加一条规则）
        if "rules" not in contract:
            contract["rules"] = []
        contract["rules"].append({
            "type": "audit_fix",
            "description": finding.description,
            "added_at": time.time()
        })
        contract["version"] = new_version

        update = RuleUpdate(
            agent_role=agent_id,
            rule_file=str(agent_path),
            old_version=old_version,
            new_version=new_version,
            changes=[f"Add rule to address: {finding.title}"],
            reason=finding.description,
            updated_content=json.dumps(contract, indent=2)
        )
        return update

    async def apply_rule_update(self, update: RuleUpdate) -> bool:
        """
        应用规则更新：将新内容写入文件。
        """
        try:
            FileUtils.safe_write(update.rule_file, update.updated_content)
            logger.info(f"Rule update applied: {update.agent_role} -> {update.new_version}")
            return True
        except Exception as e:
            logger.error(f"Failed to apply rule update: {e}")
            return False

    async def propose_rule_updates(self, updates: List[RuleUpdate]) -> List[str]:
        """
        向 CTO 提议规则更新。
        返回提议 ID 列表。
        """
        async with self._lock:
            for u in updates:
                self.rule_updates.append(u)
        return [f"{u.agent_role}_{u.new_version}" for u in updates]

    async def get_pending_updates(self) -> List[RuleUpdate]:
        """获取待审批的规则更新。"""
        # 假设所有更新都待审批，这里简化
        return self.rule_updates