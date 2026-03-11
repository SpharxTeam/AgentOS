# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 工具调用审计模块。

import json
import sqlite3
from pathlib import Path
from typing import Dict, Any, Optional, List
import uuid
import time
from agentos_cta.utils.structured_logger import get_logger
from .schemas import AuditRecord

logger = get_logger(__name__)


class ToolAudit:
    """
    工具调用审计。
    记录所有工具调用，支持异常检测与追溯。
    """

    def __init__(self, db_path: str = "data/security/audit.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """初始化 SQLite 表。"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                record_id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                tool_name TEXT NOT NULL,
                input_data TEXT,
                result TEXT,
                success INTEGER,
                error TEXT,
                timestamp REAL,
                trace_id TEXT,
                permission_granted INTEGER,
                permission_check_id TEXT
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_agent ON audit_log(agent_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON audit_log(timestamp)")
        conn.commit()
        conn.close()

    async def record(self, record: AuditRecord) -> str:
        """记录一条审计记录。"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO audit_log
                (record_id, agent_id, tool_name, input_data, result, success, error,
                 timestamp, trace_id, permission_granted, permission_check_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record.record_id,
                record.agent_id,
                record.tool_name,
                json.dumps(record.input_data),
                json.dumps(record.result) if record.result else None,
                1 if record.success else 0,
                record.error,
                record.timestamp,
                record.trace_id,
                1 if record.permission_granted else 0,
                record.permission_check_id
            ))
            conn.commit()
            return record.record_id
        finally:
            conn.close()

    async def query(self, agent_id: Optional[str] = None,
                    start_time: Optional[float] = None,
                    end_time: Optional[float] = None,
                    limit: int = 100) -> List[Dict]:
        """查询审计记录。"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        sql = "SELECT * FROM audit_log WHERE 1=1"
        params = []
        if agent_id:
            sql += " AND agent_id = ?"
            params.append(agent_id)
        if start_time:
            sql += " AND timestamp >= ?"
            params.append(start_time)
        if end_time:
            sql += " AND timestamp <= ?"
            params.append(end_time)
        sql += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        cursor.execute(sql, params)
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    async def detect_anomalies(self, window_seconds: int = 3600, threshold: int = 100) -> List[Dict]:
        """
        简单异常检测：统计每个 Agent 在时间窗口内的调用频率。
        超过 threshold 则标记为异常。
        """
        now = time.time()
        start = now - window_seconds
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("""
            SELECT agent_id, COUNT(*) as cnt
            FROM audit_log
            WHERE timestamp >= ?
            GROUP BY agent_id
            HAVING cnt > ?
        """, (start, threshold))
        rows = cursor.fetchall()
        conn.close()
        return [{"agent_id": row[0], "count": row[1]} for row in rows]