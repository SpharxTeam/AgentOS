# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 元数据管理。

import time
import uuid
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from agentos_cta.utils.structured_logger import get_logger

logger = get_logger(__name__)


@dataclass
class MemoryMetadata:
    """记忆元数据。"""
    memory_id: str  # 全局唯一 ID
    trace_id: str   # 关联的追踪 ID
    agent_id: str   # 来源 Agent
    task_id: Optional[str] = None
    round_id: Optional[str] = None
    timestamp: float = field(default_factory=time.time)
    access_count: int = 0
    last_access: Optional[float] = None
    size_bytes: int = 0
    format: str = 'json'
    tags: Dict[str, Any] = field(default_factory=dict)


class MetadataManager:
    """
    元数据管理器。
    维护每个记忆的元数据，支持检索和更新。
    实际可基于 SQLite 或 Redis 实现。
    """

    def __init__(self, storage_path: str = "data/workspace/memory/metadata.db"):
        import sqlite3
        self.db_path = storage_path
        self._init_db()

    def _init_db(self):
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memory_metadata (
                memory_id TEXT PRIMARY KEY,
                trace_id TEXT,
                agent_id TEXT,
                task_id TEXT,
                round_id TEXT,
                timestamp REAL,
                access_count INTEGER DEFAULT 0,
                last_access REAL,
                size_bytes INTEGER,
                format TEXT,
                tags TEXT
            )
        """)
        conn.commit()
        conn.close()

    async def create(self, metadata: MemoryMetadata) -> str:
        """创建新元数据记录。"""
        import sqlite3, json
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO memory_metadata
            (memory_id, trace_id, agent_id, task_id, round_id, timestamp, access_count, last_access, size_bytes, format, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            metadata.memory_id, metadata.trace_id, metadata.agent_id,
            metadata.task_id, metadata.round_id, metadata.timestamp,
            metadata.access_count, metadata.last_access,
            metadata.size_bytes, metadata.format,
            json.dumps(metadata.tags)
        ))
        conn.commit()
        conn.close()
        return metadata.memory_id

    async def get(self, memory_id: str) -> Optional[MemoryMetadata]:
        """获取元数据。"""
        import sqlite3, json
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM memory_metadata WHERE memory_id = ?", (memory_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return MemoryMetadata(
                memory_id=row['memory_id'],
                trace_id=row['trace_id'],
                agent_id=row['agent_id'],
                task_id=row['task_id'],
                round_id=row['round_id'],
                timestamp=row['timestamp'],
                access_count=row['access_count'],
                last_access=row['last_access'],
                size_bytes=row['size_bytes'],
                format=row['format'],
                tags=json.loads(row['tags'])
            )
        return None

    async def update_access(self, memory_id: str):
        """更新访问计数。"""
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE memory_metadata
            SET access_count = access_count + 1, last_access = ?
            WHERE memory_id = ?
        """, (time.time(), memory_id))
        conn.commit()
        conn.close()