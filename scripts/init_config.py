#!/usr/bin/env python
# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 初始化配置文件（从模板生成实际配置）

import os
import shutil
from pathlib import Path

def main():
    root = Path(__file__).parent.parent
    env_example = root / ".env.example"
    env_file = root / ".env"

    if not env_file.exists():
        shutil.copy(env_example, env_file)
        print(f"Created {env_file} from template.")
    else:
        print(f"{env_file} already exists, skipping.")

    # 创建数据目录
    data_dirs = [
        "data/workspace/projects",
        "data/workspace/memory/buffer",
        "data/workspace/memory/summary",
        "data/workspace/memory/vector",
        "data/workspace/memory/patterns",
        "data/workspace/sessions",
        "data/registry",
        "data/security/audit_logs",
        "data/logs",
    ]
    for d in data_dirs:
        (root / d).mkdir(parents=True, exist_ok=True)
        print(f"Ensured directory: {d}")

if __name__ == "__main__":
    main()