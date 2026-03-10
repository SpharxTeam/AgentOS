#!/usr/bin/env python
# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 更新注册中心（扫描 agents/ 和 skills/ 目录）

import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from agentos_cta.agents.contracts import validate_contract_file

def scan_agents():
    root = Path(__file__).parent.parent
    agents_dir = root / "src/agentos_cta/agents/builtin"
    agents = []
    for agent_dir in agents_dir.iterdir():
        if not agent_dir.is_dir():
            continue
        contract_path = agent_dir / "contract.json"
        if not contract_path.exists():
            continue
        try:
            validate_contract_file(str(contract_path))
            with open(contract_path) as f:
                contract = json.load(f)
            agents.append({
                "agent_id": contract.get("agent_id", agent_dir.name),
                "role": contract.get("role", "unknown"),
                "version": contract.get("version", "1.0.0"),
                "source": "builtin",
                "active": True,
                "trust_score": contract.get("trust_metrics", {}).get("rating", 0.5),
            })
        except Exception as e:
            print(f"Error processing {agent_dir.name}: {e}")
    return agents

def update_agent_db(agents):
    db_path = Path(__file__).parent.parent / "data/registry/agents.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agents (
            agent_id TEXT PRIMARY KEY,
            role TEXT,
            version TEXT,
            source TEXT,
            active INTEGER,
            trust_score REAL,
            contract TEXT
        )
    """)
    for agent in agents:
        cursor.execute("""
            INSERT OR REPLACE INTO agents (agent_id, role, version, source, active, trust_score)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (agent["agent_id"], agent["role"], agent["version"], agent["source"], 1, agent["trust_score"]))
    conn.commit()
    conn.close()
    print(f"Updated {len(agents)} agents in registry.")

def main():
    print("Scanning builtin agents...")
    agents = scan_agents()
    update_agent_db(agents)
    print("Registry update complete.")

if __name__ == "__main__":
    main()