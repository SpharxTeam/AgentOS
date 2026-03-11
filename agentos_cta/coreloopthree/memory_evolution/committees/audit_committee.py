# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 审计委员会：负责交叉验证输出质量，识别共识妥协。

from typing import Dict, Any, List, Optional
import time
from agentos_cta.utils.structured_logger import get_logger
from agentos_cta.utils.error_types import ConsensusError

logger = get_logger(__name__)


class AuditCommittee:
    """
    审计委员会。
    不参与生产，只做离线审计，交叉检查各Agent输出质量，识别共识妥协。
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.audit_records: List[Dict] = []

    async def audit_round(self, round_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        审计一个轮次的所有输出。

        Args:
            round_data: 包含所有Agent输出、任务结果等

        Returns:
            审计报告
        """
        issues = []
        # 检查各任务输出
        tasks = round_data.get("tasks", [])
        for task in tasks:
            task_issues = self._audit_task(task)
            issues.extend(task_issues)

        # 检查共识妥协
        consensus_issues = self._detect_consensus_compromises(round_data)
        issues.extend(consensus_issues)

        report = {
            "round_id": round_data.get("round_id"),
            "timestamp": time.time(),
            "issues": issues,
            "summary": {
                "total_issues": len(issues),
                "critical_issues": len([i for i in issues if i.get("severity") == "critical"]),
            }
        }
        self.audit_records.append(report)
        logger.info(f"Audit completed for round {round_data.get('round_id')} with {len(issues)} issues")
        return report

    def _audit_task(self, task: Dict) -> List[Dict]:
        """审计单个任务输出。"""
        issues = []
        # 检查是否有输出
        if not task.get("result"):
            issues.append({
                "type": "missing_output",
                "task_id": task.get("task_id"),
                "severity": "warning",
                "description": "Task produced no output",
            })
        # 检查输出格式是否符合预期（简化）
        expected_schema = task.get("output_schema")
        if expected_schema and task.get("result"):
            # 简单检查类型
            if not isinstance(task["result"], dict):
                issues.append({
                    "type": "schema_mismatch",
                    "task_id": task.get("task_id"),
                    "severity": "error",
                    "description": "Output type mismatch",
                })
        return issues

    def _detect_consensus_compromises(self, round_data: Dict) -> List[Dict]:
        """检测是否存在共识妥协（多个Agent对同一问题给出不同答案且最终选择并非最优）。"""
        issues = []
        # 假设 round_data 中包含多个Agent对同一决策的投票
        votes = round_data.get("consensus_votes", [])
        for vote in votes:
            options = vote.get("options", {})
            if len(options) < 2:
                continue
            # 找出最优选项（假设有 ground_truth 或通过交叉验证）
            ground_truth = vote.get("ground_truth")
            chosen = vote.get("chosen")
            if ground_truth and chosen != ground_truth:
                issues.append({
                    "type": "consensus_compromise",
                    "topic": vote.get("topic"),
                    "chosen": chosen,
                    "ground_truth": ground_truth,
                    "severity": "critical",
                    "description": "Consensus chose suboptimal option",
                })
        return issues