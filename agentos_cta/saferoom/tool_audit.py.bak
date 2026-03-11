# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 工具调用审计：记录所有工具调用，支持异常检测和追溯。

import asyncio
import time
import uuid
from typing import Dict, Any, Optional, List
from agentos_cta.utils.structured_logger import get_logger
from agentos_cta.utils.error_types import SecurityError
from .schemas import AuditEvent, AuditSeverity

logger = get_logger(__name__)


class ToolAudit:
    """
    工具调用审计器。
    记录每次工具调用的详细信息，支持异常检测和事后追溯。
    """

    def __init__(self, storage_backend=None):
        """
        初始化审计器。

        Args:
            storage_backend: 审计记录存储后端，默认为内存，可替换为数据库。
        """
        self.storage = storage_backend or []
        self._lock = asyncio.Lock()

    async def record(self, event: AuditEvent):
        """记录审计事件。"""
        async with self._lock:
            self.storage.append(event)
        logger.info(f"Audit record: {event.action} on {event.resource} -> {event.decision}")

        # 对于严重事件，立即记录警告
        if event.severity in (AuditSeverity.CRITICAL, AuditSeverity.ERROR):
            logger.error(f"Critical audit event: {event.event_id} - {event.reason}")

    async def create_event(
        self,
        agent_id: str,
        action: str,
        resource: str,
        decision: str,
        severity: AuditSeverity = AuditSeverity.INFO,
        reason: Optional[str] = None,
        input_data: Optional[Dict[str, Any]] = None,
        trace_id: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> AuditEvent:
        """创建并记录审计事件。"""
        # 对输入进行脱敏（仅保留前100字符，防止敏感信息泄露）
        input_preview = None
        if input_data:
            import json
            preview = json.dumps(input_data)[:100]
            if len(preview) == 100:
                preview += "..."
            input_preview = preview

        event = AuditEvent(
            event_id=str(uuid.uuid4()),
            agent_id=agent_id,
            action=action,
            resource=resource,
            decision=decision,
            severity=severity,
            reason=reason,
            input_preview=input_preview,
            trace_id=trace_id,
            metadata=metadata or {},
        )
        await self.record(event)
        return event

    async def query(self, agent_id: Optional[str] = None, limit: int = 100) -> List[AuditEvent]:
        """查询审计记录。"""
        async with self._lock:
            events = list(self.storage)
            if agent_id:
                events = [e for e in events if e.agent_id == agent_id]
            return sorted(events, key=lambda e: e.timestamp, reverse=True)[:limit]

    async def detect_anomalies(self, window_seconds: int = 300) -> List[Dict[str, Any]]:
        """
        检测异常模式。
        例如：短时间内高频失败、敏感操作集中等。
        """
        now = time.time()
        async with self._lock:
            recent = [e for e in self.storage if now - e.timestamp < window_seconds]

        anomalies = []

        # 统计每个 Agent 的失败次数
        failures_by_agent = {}
        for e in recent:
            if e.decision == "deny":
                failures_by_agent[e.agent_id] = failures_by_agent.get(e.agent_id, 0) + 1

        for agent_id, count in failures_by_agent.items():
            if count > 10:  # 阈值可配置
                anomalies.append({
                    "type": "high_failure_rate",
                    "agent_id": agent_id,
                    "count": count,
                    "window": window_seconds,
                })

        # 检测敏感操作（如删除文件）
        sensitive_ops = [e for e in recent if "delete" in e.action.lower()]
        if len(sensitive_ops) > 5:
            anomalies.append({
                "type": "excessive_sensitive_ops",
                "count": len(sensitive_ops),
                "examples": [e.action for e in sensitive_ops[:3]],
            })

        return anomalies