#!/usr/bin/env python
# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 验证所有 Agent 契约是否符合规范

import json
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from agentos_open.markets.agent.builtin.contracts import validate_contract_file, ContractValidationError

def main():
    root = Path(__file__).parent.parent
    builtin_agents_dir = root / "agentos_open/markets/agent/builtin"

    if not builtin_agents_dir.exists():
        print(f"Builtin agents directory not found: {builtin_agents_dir}")
        return

    all_passed = True
    for agent_dir in builtin_agents_dir.iterdir():
        if not agent_dir.is_dir():
            continue
        contract_path = agent_dir / "contract.json"
        if not contract_path.exists():
            print(f"⚠ No contract.json in {agent_dir.name}")
            continue

        try:
            validate_contract_file(str(contract_path))
            print(f"✓ {agent_dir.name} contract is valid")
        except ContractValidationError as e:
            print(f"✗ {agent_dir.name} contract invalid: {e}")
            all_passed = False
        except json.JSONDecodeError as e:
            print(f"✗ {agent_dir.name} contract is not valid JSON: {e}")
            all_passed = False

    if all_passed:
        print("\nAll contracts are valid.")
        sys.exit(0)
    else:
        print("\nSome contracts have issues.")
        sys.exit(1)

if __name__ == "__main__":
    main()