# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# skill info 命令实现。

import argparse
import asyncio
import json
from agentos_cta.skill_market import SkillRegistry


async def info_cmd(args: argparse.Namespace):
    """显示技能详细信息。"""
    registry = SkillRegistry()
    skill = await registry.get_skill(args.skill_id)
    if not skill:
        print(f"Skill {args.skill_id} not found.")
        return
    print(f"Skill ID: {skill['skill_id']}")
    print(f"Name: {skill.get('name', '')}")
    print(f"Version: {skill['version']}")
    print(f"Description: {skill.get('description', '')}")
    print(f"Install Path: {skill.get('install_path', '')}")
    print(f"Installed At: {skill.get('installed_at', '')}")
    print("\nContract:")
    print(json.dumps(skill['contract'], indent=2))


def register_info_subcommand(subparsers):
    parser = subparsers.add_parser("info", help="Show detailed info about a skill")
    parser.add_argument("skill_id", help="Skill ID")
    parser.set_defaults(func=info_cmd)