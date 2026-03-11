# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 会话管理器，管理用户会话的生命周期和状态。

import asyncio
import uuid
import time
from typing import Dict, Optional, Any
from dataclasses import dataclass, field
from agentos_cta.utils.structured_logger import get_logger
from agentos_cta.utils.error_types import AgentOSError

logger = get_logger(__name__)


@dataclass
class Session:
    """用户会话。"""
    session_id: str
    created_at: float
    last_active: float
    context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    async def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """处理请求（占位，实际应由上层注入处理器）。"""
        # 这里简化，实际应由 AppServer 设置回调
        return {"status": "ok", "echo": request}


class SessionManager:
    """
    会话管理器。
    负责创建、获取、更新和清理会话。
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.sessions: Dict[str, Session] = {}
        self.timeout_seconds = config.get("timeout_seconds", 3600)  # 默认1小时
        self._cleanup_task = None
        self._lock = asyncio.Lock()

    async def start(self):
        """启动后台清理任务。"""
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def stop(self):
        """停止清理任务。"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

    async def create_session(self, metadata: Optional[Dict[str, Any]] = None) -> Session:
        """创建新会话。"""
        session_id = str(uuid.uuid4())
        now = time.time()
        session = Session(
            session_id=session_id,
            created_at=now,
            last_active=now,
            metadata=metadata or {}
        )
        async with self._lock:
            self.sessions[session_id] = session
        logger.info(f"Session created: {session_id}")
        return session

    async def get_session(self, session_id: str) -> Optional[Session]:
        """获取会话，并更新最后活跃时间。"""
        async with self._lock:
            session = self.sessions.get(session_id)
            if session:
                session.last_active = time.time()
            return session

    async def delete_session(self, session_id: str):
        """删除会话。"""
        async with self._lock:
            if session_id in self.sessions:
                del self.sessions[session_id]
                logger.info(f"Session deleted: {session_id}")

    async def _cleanup_loop(self):
        """定期清理超时会话。"""
        while True:
            await asyncio.sleep(60)  # 每分钟检查一次
            now = time.time()
            expired = []
            async with self._lock:
                for sid, sess in list(self.sessions.items()):
                    if now - sess.last_active > self.timeout_seconds:
                        expired.append(sid)
                        del self.sessions[sid]
            if expired:
                logger.info(f"Cleaned up {len(expired)} expired sessions")