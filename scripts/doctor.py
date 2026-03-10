#!/usr/bin/env python
# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 医生自检脚本（诊断环境、配置问题，自动修复）

import os
import sys
import importlib
from pathlib import Path

GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"

def check_python_version():
    required = (3, 9)
    current = sys.version_info[:2]
    if current >= required:
        print(f"{GREEN}✓ Python {current[0]}.{current[1]} (OK){RESET}")
        return True
    else:
        print(f"{RED}✗ Python {current[0]}.{current[1]} < {required[0]}.{required[1]}{RESET}")
        return False

def check_dependencies():
    required_packages = [
        "aiohttp",
        "aiofiles",
        "jsonschema",
        "tiktoken",
        "chromadb",
        "pyyaml",
    ]
    missing = []
    for pkg in required_packages:
        try:
            importlib.import_module(pkg)
            print(f"{GREEN}✓ {pkg}{RESET}")
        except ImportError:
            missing.append(pkg)
            print(f"{RED}✗ {pkg} (missing){RESET}")
    return missing

def check_env_file():
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        print(f"{GREEN}✓ .env file exists{RESET}")
        # 简单检查是否包含必要变量
        with open(env_path) as f:
            content = f.read()
        if "OPENAI_API_KEY" in content or "ANTHROPIC_API_KEY" in content:
            print(f"{GREEN}  - API keys found{RESET}")
        else:
            print(f"{YELLOW}  ⚠ No API keys found in .env{RESET}")
        return True
    else:
        print(f"{RED}✗ .env file missing (run scripts/init_config.py){RESET}")
        return False

def check_data_dirs():
    root = Path(__file__).parent.parent
    required_dirs = [
        "data/workspace/projects",
        "data/workspace/memory/buffer",
        "data/registry",
        "data/logs",
    ]
    all_ok = True
    for d in required_dirs:
        if (root / d).exists():
            print(f"{GREEN}✓ {d}{RESET}")
        else:
            print(f"{YELLOW}⚠ {d} missing (will be created on demand){RESET}")
            all_ok = False
    return all_ok

def main():
    print("AgentOS Doctor - System Health Check")
    print("=" * 40)

    python_ok = check_python_version()
    missing = check_dependencies()
    env_ok = check_env_file()
    data_ok = check_data_dirs()

    print("\n" + "=" * 40)
    if python_ok and not missing and env_ok and data_ok:
        print(f"{GREEN}All checks passed! System is healthy.{RESET}")
    else:
        if missing:
            print(f"{YELLOW}Missing dependencies: {', '.join(missing)}. Run 'pip install -r requirements.txt'{RESET}")
        if not env_ok:
            print(f"{YELLOW}Please run 'python scripts/init_config.py' to create .env{RESET}")
        if not data_ok:
            print(f"{YELLOW}Missing data directories will be auto-created when needed.{RESET}")
        print(f"{YELLOW}Some checks failed. Please address the issues above.{RESET}")

if __name__ == "__main__":
    main()