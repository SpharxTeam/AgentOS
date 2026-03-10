# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# Agent 注册中心客户端。
# 用于查询可用 Agent、注册新 Agent、更新信任指标等。

import sqlite3
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
from agentos_cta.utils.structured_logger import get_logger
from agentos_cta.utils.error_types import ConfigurationError

logger = get_logger(__name__)


class AgentRegistryClient:
    """
    Agent 注册中心客户端。
    使用 SQLite 作为后端存储，提供 Agent 元数据的持久化。
    """

    def __init__(self, db_path: str):
        """
        初始化客户端，连接数据库并确保表存在。

        Args:
            db_path: SQLite 数据库文件路径。
        """
        self.db_path = Path(db_path)
        self._init_db()

    def _init_db(self):
        """初始化数据库表。"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agents (
                agent_id TEXT PRIMARY KEY,
                role TEXT NOT NULL,
                contract TEXT NOT NULL,        -- JSON 格式的契约
                cost_estimate REAL,
                success_rate REAL,
                trust_score REAL,
                last_seen TIMESTAMP,
                is_active INTEGER DEFAULT 1
            )
        """)
        # 创建角色索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_role ON agents(role)")
        conn.commit()
        conn.close()

    async def query_agents(self, role: Optional[str] = None, task_schema: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """
        查询符合条件的 Agent。

        Args:
            role: 角色名称（如 "product_manager"），若为 None 则返回所有角色。
            task_schema: 任务输入 Schema，用于进一步匹配（目前仅作占位）。

        Returns:
            Agent 信息列表。
        """
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if role:
            cursor.execute("SELECT * FROM agents WHERE role = ? AND is_active = 1", (role,))
        else:
            cursor.execute("SELECT * FROM agents WHERE is_active = 1")

        rows = cursor.fetchall()
        conn.close()

        agents = []
        for row in rows:
            agent = dict(row)
            agent['contract'] = json.loads(agent['contract'])  # 解析 JSON
            agents.append(agent)
        return agents

    async def register_agent(self, agent_id: str, role: str, contract: Dict[str, Any],
                             cost_estimate: float, success_rate: float, trust_score: float) -> bool:
        """
        注册或更新 Agent。

        Returns:
            True 表示成功。
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO agents
                (agent_id, role, contract, cost_estimate, success_rate, trust_score, last_seen, is_active)
                VALUES (?, ?, ?, ?, ?, ?, datetime('now'), 1)
            """, (agent_id, role, json.dumps(contract), cost_estimate, success_rate, trust_score))
            conn.commit()
            logger.info(f"Agent {agent_id} registered successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to register agent {agent_id}: {e}")
            return False
        finally:
            conn.close()

    async def update_trust_score(self, agent_id: str, delta: float) -> bool:
        """更新 Agent 信任度（增加或减少）。"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE agents SET trust_score = trust_score + ?, last_seen = datetime('now') WHERE agent_id = ?",
                           (delta, agent_id))
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to update trust for {agent_id}: {e}")
            return False
        finally:
            conn.close()

    async def deactivate_agent(self, agent_id: str) -> bool:
        """停用 Agent（标记为非活跃）。"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE agents SET is_active = 0 WHERE agent_id = ?", (agent_id,))
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to deactivate {agent_id}: {e}")
            return False
        finally:
            conn.close()