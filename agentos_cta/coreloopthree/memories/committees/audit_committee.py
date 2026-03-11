# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 审计委员会：负责交叉验证输出质量、识别共识妥协。

from typing import Dict, Any, List, Optional
import asyncio
import time
from dataclasses import dataclass, field
from agentos_cta.utils.observability import get_logger
from agentos_cta.utils.error import AgentOSError

logger = get_logger(__name__)


@dataclass
class AuditFinding:
    """审计发现项。"""
    finding_id: str
    title: str
    description: str
    severity: str  # info, warning, critical
    affected_agents: List[str]
    evidence: Dict[str, Any]
    created_at: float
    resolved_at: Optional[float] = None


@dataclass
class ConsensusIssue:
    """共识问题：多智能体对同一事实理解不一致。"""
    issue_id: str
    fact_key: str
    agents_values: Dict[str, Any]  # agent_id -> value
    drift_magnitude: float
    detected_at: float
    resolved: bool = False


class AuditCommittee:
    """
    审计委员会。
    负责交叉验证不同 Agent 的输出质量，识别共识妥协和潜在错误。
    利用 MemoryRovol 中的记忆数据进行验证。
    """

    def __init__(self, memory_roviol, config: Dict[str, Any]):
        self.memory = memory_roviol
        self.config = config
        self.findings: List[AuditFinding] = []
        self.consensus_issues: List[ConsensusIssue] = []
        self._lock = asyncio.Lock()

    async def cross_validate(self, round_id: str) -> List[AuditFinding]:
        """
        对指定轮次进行交叉验证，比较不同 Agent 的输出。
        从记忆系统中检索所有 Agent 的输出记录。
        """
        logger.info(f"Cross-validating round {round_id}...")
        await asyncio.sleep(0.8)

        # 模拟发现
        findings = [
            AuditFinding(
                finding_id=f"audit_{int(time.time())}_1",
                title="Inconsistent product requirements",
                description="Product Manager and Architect have conflicting interpretations of user story #42",
                severity="warning",
                affected_agents=["product_manager_v1", "architect_v1"],
                evidence={"story_id": "42", "pm_output": "...", "arch_output": "..."},
                created_at=time.time()
            )
        ]
        return findings

    async def detect_consensus_drift(self, fact_key: str) -> Optional[ConsensusIssue]:
        """
        检测对特定事实的共识漂移。
        从记忆系统中获取所有 Agent 对该事实的最新断言。
        """
        # 模拟：从 memory 获取事实断言
        # 假设 memory 有方法 get_assertions(fact_key)
        # 简化处理
        await asyncio.sleep(0.2)
        # 模拟两个 Agent 的断言
        agents_values = {
            "product_manager_v1": "high",
            "architect_v1": "medium",
            "backend_v1": "high"
        }
        # 计算漂移幅度（简化）
        values = list(agents_values.values())
        if len(set(values)) > 1:
            drift = 0.5  # 模拟
            issue = ConsensusIssue(
                issue_id=f"consensus_{int(time.time())}",
                fact_key=fact_key,
                agents_values=agents_values,
                drift_magnitude=drift,
                detected_at=time.time()
            )
            return issue
        return None

    async def submit_finding(self, finding: AuditFinding):
        """提交审计发现。"""
        async with self._lock:
            self.findings.append(finding)
        logger.warning(f"Audit finding submitted: {finding.finding_id} - {finding.title}")

    async def submit_consensus_issue(self, issue: ConsensusIssue):
        """提交共识问题。"""
        async with self._lock:
            self.consensus_issues.append(issue)
        logger.warning(f"Consensus issue detected: {issue.issue_id} on {issue.fact_key}")

    async def get_critical_findings(self) -> List[AuditFinding]:
        """获取严重级别的审计发现。"""
        return [f for f in self.findings if f.severity == "critical" and f.resolved_at is None]

    async def resolve_finding(self, finding_id: str):
        """标记审计发现已解决。"""
        async with self._lock:
            for f in self.findings:
                if f.finding_id == finding_id:
                    f.resolved_at = time.time()
                    logger.info(f"Audit finding {finding_id} resolved")
                    break