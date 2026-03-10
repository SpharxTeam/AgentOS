# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 技能注册中心。

import sqlite3
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
from agentos_cta.utils.structured_logger import get_logger
from agentos_cta.utils.file_utils import FileUtils
from .version_manager import VersionManager

logger = get_logger(__name__)


class SkillRegistry:
    """
    技能注册中心。
    管理已安装技能的元数据，提供查询和版本管理。
    """

    def __init__(self, db_path: str = "data/registry/skills.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        # 技能表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS skills (
                skill_id TEXT PRIMARY KEY,
                name TEXT,
                version TEXT,
                description TEXT,
                contract TEXT NOT NULL,  -- JSON格式的完整契约
                install_path TEXT,
                installed_at TIMESTAMP,
                is_active INTEGER DEFAULT 1
            )
        """)
        # 版本历史表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS skill_versions (
                skill_id TEXT,
                version TEXT,
                contract TEXT,
                released_at TIMESTAMP,
                PRIMARY KEY (skill_id, version)
            )
        """)
        # 创建索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_skill_name ON skills(name)")
        conn.commit()
        conn.close()

    async def register_skill(self, contract: Dict[str, Any], install_path: str) -> bool:
        """注册一个新安装的技能。"""
        skill_id = contract["skill_id"]
        version = contract["version"]
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO skills
                (skill_id, name, version, description, contract, install_path, installed_at, is_active)
                VALUES (?, ?, ?, ?, ?, ?, datetime('now'), 1)
            """, (
                skill_id,
                contract.get("name", ""),
                version,
                contract.get("description", ""),
                json.dumps(contract),
                install_path
            ))
            # 同时记录版本历史
            cursor.execute("""
                INSERT OR IGNORE INTO skill_versions (skill_id, version, contract, released_at)
                VALUES (?, ?, ?, datetime('now'))
            """, (skill_id, version, json.dumps(contract)))
            conn.commit()
            logger.info(f"Registered skill {skill_id} v{version}")
            return True
        except Exception as e:
            logger.error(f"Failed to register skill {skill_id}: {e}")
            return False
        finally:
            conn.close()

    async def unregister_skill(self, skill_id: str) -> bool:
        """卸载技能（标记为非活跃）。"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE skills SET is_active = 0 WHERE skill_id = ?", (skill_id,))
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to unregister {skill_id}: {e}")
            return False
        finally:
            conn.close()

    async def get_skill(self, skill_id: str) -> Optional[Dict[str, Any]]:
        """获取技能信息（最新版本）。"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM skills WHERE skill_id = ? AND is_active = 1 ORDER BY installed_at DESC LIMIT 1",
            (skill_id,)
        )
        row = cursor.fetchone()
        conn.close()
        if row:
            result = dict(row)
            result["contract"] = json.loads(result["contract"])
            return result
        return None

    async def get_skill_contract(self, skill_id: str, version: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """获取指定版本的契约。"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        if version:
            cursor.execute(
                "SELECT contract FROM skill_versions WHERE skill_id = ? AND version = ?",
                (skill_id, version)
            )
        else:
            cursor.execute(
                "SELECT contract FROM skills WHERE skill_id = ? AND is_active = 1",
                (skill_id,)
            )
        row = cursor.fetchone()
        conn.close()
        if row:
            return json.loads(row["contract"])
        return None

    async def get_versions(self, skill_id: str) -> List[str]:
        """获取技能的所有可用版本。"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute(
            "SELECT version FROM skill_versions WHERE skill_id = ? ORDER BY version",
            (skill_id,)
        )
        rows = cursor.fetchall()
        conn.close()
        return [row[0] for row in rows]

    async def list_skills(self, include_inactive: bool = False) -> List[Dict[str, Any]]:
        """列出所有已安装技能。"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        if include_inactive:
            cursor.execute("SELECT * FROM skills ORDER BY skill_id")
        else:
            cursor.execute("SELECT * FROM skills WHERE is_active = 1 ORDER BY skill_id")
        rows = cursor.fetchall()
        conn.close()
        result = []
        for row in rows:
            item = dict(row)
            item["contract"] = json.loads(item["contract"])
            result.append(item)
        return result

    async def search(self, query: str) -> List[Dict[str, Any]]:
        """搜索已安装技能。"""
        skills = await self.list_skills()
        query_lower = query.lower()
        results = []
        for s in skills:
            if (query_lower in s.get("name", "").lower() or
                query_lower in s.get("description", "").lower() or
                query_lower in s.get("skill_id", "").lower()):
                results.append(s)
        return results