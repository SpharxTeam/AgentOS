# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 会话管理器：管理 Agent 会话生命周期。

import time
import uuid
import asyncio
from enum import Enum
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from agentos_cta.utils.observability import get_logger, set_trace_id

logger = get_logger(__name__)


class SessionStatus(str, Enum):
    """会话状态。"""
    ACTIVE = "active"
    IDLE = "idle"
    CLOSED = "closed"
    EXPIRED = "expired"


@dataclass
class Session:
    """会话实体。"""
    session_id: str
    trace_id: str
    status: SessionStatus = SessionStatus.ACTIVE
    created_at: float = field(default_factory=time.time)
    last_active: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典。"""
        return {
            "session_id": self.session_id,
            "trace_id": self.trace_id,
            "status": self.status.value,
            "created_at": self.created_at,
            "last_active": self.last_active,
            "metadata": self.metadata,
        }

    def touch(self):
        """更新最后活跃时间。"""
        self.last_active = time.time()


class SessionManager:
    """
    会话管理器。
    负责会话的创建、查询、更新和清理。
    借鉴 Agno AgentOS 的会话管理设计 [citation:4]。
    """

    def __init__(self, max_sessions: int = 1000, session_timeout: int = 3600):
        """
        初始化会话管理器。

        Args:
            max_sessions: 最大并发会话数。
            session_timeout: 会话超时时间（秒）。
        """
        self.max_sessions = max_sessions
        self.session_timeout = session_timeout
        self._sessions: Dict[str, Session] = {}
        self._lock = asyncio.Lock()

    async def create_session(self, metadata: Optional[Dict[str, Any]] = None) -> Session:
        """
        创建新会话。

        Args:
            metadata: 会话元数据。

        Returns:
            创建的会话对象。
        """
        async with self._lock:
            if len(self._sessions) >= self.max_sessions:
                # 尝试清理过期会话
                await self._cleanup_expired_locked()
                if len(self._sessions) >= self.max_sessions:
                    raise RuntimeError("Max sessions reached")

            session_id = str(uuid.uuid4())
            trace_id = str(uuid.uuid4())
            set_trace_id(trace_id)

            session = Session(
                session_id=session_id,
                trace_id=trace_id,
                metadata=metadata or {},
            )
            self._sessions[session_id] = session
            logger.info(f"Created session {session_id} with trace {trace_id}")
            return session

    async def get_session(self, session_id: str) -> Optional[Session]:
        """
        获取会话。

        Args:
            session_id: 会话 ID。

        Returns:
            会话对象，不存在则返回 None。
        """
        async with self._lock:
            session = self._sessions.get(session_id)
            if session:
                session.touch()
                set_trace_id(session.trace_id)
            return session

    async def update_session_context(self, session_id: str, context: Dict[str, Any]) -> bool:
        """
        更新会话上下文。

        Args:
            session_id: 会话 ID。
            context: 要更新的上下文。

        Returns:
            是否更新成功。
        """
        async with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                return False
            session.context.update(context)
            session.touch()
            return True

    async def list_sessions(self, status: Optional[SessionStatus] = None) -> List[Session]:
        """
        列出会话。

        Args:
            status: 按状态过滤。

        Returns:
            会话列表。
        """
        async with self._lock:
            sessions = list(self._sessions.values())
            if status:
                sessions = [s for s in sessions if s.status == status]
            return sessions

    async def close_session(self, session_id: str) -> bool:
        """
        关闭会话。

        Args:
            session_id: 会话 ID。

        Returns:
            是否关闭成功。
        """
        async with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                return False
            session.status = SessionStatus.CLOSED
            del self._sessions[session_id]
            logger.info(f"Closed session {session_id}")
            return True

    async def close_all(self):
        """关闭所有会话。"""
        async with self._lock:
            session_ids = list(self._sessions.keys())
            for sid in session_ids:
                await self.close_session(sid)
            logger.info(f"Closed all {len(session_ids)} sessions")

    async def cleanup_expired(self) -> int:
        """清理过期会话。"""
        async with self._lock:
            return await self._cleanup_expired_locked()

    async def _cleanup_expired_locked(self) -> int:
        """内部：清理过期会话（已加锁）。"""
        now = time.time()
        expired = []
        for sid, session in self._sessions.items():
            if now - session.last_active > self.session_timeout:
                expired.append(sid)

        for sid in expired:
            session = self._sessions[sid]
            session.status = SessionStatus.EXPIRED
            del self._sessions[sid]

        if expired:
            logger.info(f"Cleaned up {len(expired)} expired sessions")
        return len(expired)