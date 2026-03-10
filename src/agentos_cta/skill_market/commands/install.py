# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# skill install 命令实现。

import argparse
import asyncio
from agentos_cta.skill_market import SkillInstaller, SkillRegistry


async def install_cmd(args: argparse.Namespace):
    """执行技能安装。"""
    registry = SkillRegistry()
    installer = SkillInstaller(registry)
    success = await installer.install(args.skill_ref, source=args.source, version=args.version)
    if success:
        print(f"✅ Skill {args.skill_ref} installed successfully.")
    else:
        print(f"❌ Failed to install {args.skill_ref}.")


def register_install_subcommand(subparsers):
    parser = subparsers.add_parser("install", help="Install a skill")
    parser.add_argument("skill_ref", help="Skill reference (e.g., github:owner/repo or skill_id)")
    parser.add_argument("--source", default="github", choices=["github", "local", "registry"],
                        help="Source to install from")
    parser.add_argument("--version", help="Specific version to install")
    parser.set_defaults(func=install_cmd)