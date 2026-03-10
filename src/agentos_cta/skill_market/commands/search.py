# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# skill search 命令实现。

import argparse
import asyncio
from agentos_cta.skill_market import SkillRegistry
from agentos_cta.skill_market.sources import GitHubSource, RegistrySource


async def search_cmd(args: argparse.Namespace):
    """搜索可用技能。"""
    registry = SkillRegistry()
    # 先搜索已安装
    installed = await registry.search(args.query)
    if installed:
        print("Installed skills:")
        for s in installed:
            print(f"  {s['skill_id']} v{s['version']} - {s.get('name', '')}")
        print()

    # 搜索远程源
    sources = []
    if args.source == "github" or args.source == "all":
        sources.append(GitHubSource({}))
    if args.source == "registry" or args.source == "all":
        sources.append(RegistrySource())

    for src in sources:
        print(f"Searching {args.source}...")
        results = await src.search(args.query)
        if results:
            for r in results:
                print(f"  {r.get('skill_id')} - {r.get('name')} v{r.get('latest_version', '?')}")
        else:
            print("  No results.")


def register_search_subcommand(subparsers):
    parser = subparsers.add_parser("search", help="Search for skills")
    parser.add_argument("query", help="Search query")
    parser.add_argument("--source", default="all", choices=["github", "registry", "all"],
                        help="Source to search")
    parser.set_defaults(func=search_cmd)