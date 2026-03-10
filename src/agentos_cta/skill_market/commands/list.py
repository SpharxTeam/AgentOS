# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# skill list 命令实现。

import argparse
import asyncio
from agentos_cta.skill_market import SkillRegistry


async def list_cmd(args: argparse.Namespace):
    """列出已安装技能。"""
    registry = SkillRegistry()
    skills = await registry.list_skills(include_inactive=args.all)
    if not skills:
        print("No skills installed.")
        return
    for s in skills:
        status = "[active]" if s.get("is_active") else "[inactive]"
        print(f"{status} {s['skill_id']} v{s['version']} - {s.get('name', '')}")
        print(f"    {s.get('description', '')}\n")


def register_list_subcommand(subparsers):
    parser = subparsers.add_parser("list", help="List installed skills")
    parser.add_argument("--all", action="store_true", help="Include inactive skills")
    parser.set_defaults(func=list_cmd)