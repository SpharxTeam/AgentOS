# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 团队委员会：负责个体规则进化，更新Agent契约。

from typing import Dict, Any, List, Optional
import time
from agentos_cta.utils.structured_logger import get_logger
from agentos_open.markets.agent.contracts import validate_contract, ContractValidationError
from agentos_cta.utils.file_utils import FileUtils

logger = get_logger(__name__)


class TeamCommittee:
    """
    团队委员会。
    根据其他委员会的报告，更新各Agent的规则文件（契约），实现个体进化。
    """

    def __init__(self, config: Dict[str, Any], agents_dir: str = "agentos_open/markets/agent/builtin"):
        self.config = config
        self.agents_dir = agents_dir

    async def evolve_rules(self, round_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        根据输入（协调、技术、审计报告）进化个体规则。

        Args:
            round_data: 包含所有委员会报告的数据

        Returns:
            更新的Agent列表及变更详情
        """
        updates = []
        # 获取审计报告中的问题
        audit_report = round_data.get("audit_report", {})
        issues = audit_report.get("issues", [])
        # 按Agent分组
        agent_issues = {}
        for issue in issues:
            agent_id = issue.get("agent_id")
            if agent_id:
                if agent_id not in agent_issues:
                    agent_issues[agent_id] = []
                agent_issues[agent_id].append(issue)

        # 为每个有问题的Agent更新契约
        for agent_id, iss_list in agent_issues.items():
            update = await self._update_agent_contract(agent_id, iss_list)
            if update:
                updates.append(update)

        # 同时根据技术委员会的建议更新规范（可能影响多个Agent）
        tech_report = round_data.get("technical_report", {})
        spec_updates = tech_report.get("spec_updates", [])
        for spec in spec_updates:
            # 规范更新可能涉及多个Agent，此处简化记录
            updates.append({
                "type": "spec_update",
                "spec": spec.get("spec"),
                "reason": spec.get("reason"),
            })

        logger.info(f"Team committee evolved {len(updates)} rules")
        return updates

    async def _update_agent_contract(self, agent_id: str, issues: List[Dict]) -> Optional[Dict]:
        """更新单个Agent的契约文件。"""
        # 找到Agent的契约文件路径
        # 假设 agents_dir 下每个Agent有 contract.json
        import glob
        import json
        pattern = f"{self.agents_dir}/**/contract.json"
        files = glob.glob(pattern, recursive=True)
        contract_file = None
        for f in files:
            # 简单通过目录名匹配 agent_id（简化）
            if agent_id in f:
                contract_file = f
                break
        if not contract_file:
            logger.warning(f"Contract file for agent {agent_id} not found")
            return None

        # 读取现有契约
        contract = FileUtils.read_json(contract_file)
        if not contract:
            return None

        # 根据 issues 修改契约（例如降低信任度、增加限制等）
        changes = []
        for issue in issues:
            if issue.get("severity") == "critical":
                # 降低信任度
                if "trust_metrics" in contract:
                    old = contract["trust_metrics"].get("rating", 5.0)
                    new = max(0, old - 0.5)
                    contract["trust_metrics"]["rating"] = new
                    changes.append(f"decreased rating from {old} to {new}")
                # 增加警告说明
                if "notes" not in contract:
                    contract["notes"] = []
                contract["notes"].append({
                    "timestamp": time.time(),
                    "issue": issue.get("description"),
                })

        # 验证修改后的契约
        try:
            validate_contract(contract)
        except ContractValidationError as e:
            logger.error(f"Updated contract for {agent_id} is invalid: {e}")
            return None

        # 写回文件
        if changes:
            FileUtils.write_json(contract_file, contract)
            return {
                "agent_id": agent_id,
                "changes": changes,
                "contract_file": contract_file,
            }
        return None