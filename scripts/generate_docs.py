#!/usr/bin/env python
# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 自动生成 API 文档

import pkgutil
import inspect
from pathlib import Path

def generate_api_docs():
    docs_dir = Path(__file__).parent.parent / "docs/api"
    docs_dir.mkdir(parents=True, exist_ok=True)

    # 导入主包
    import agentos_cta

    modules = []
    for importer, modname, ispkg in pkgutil.walk_packages(agentos_cta.__path__, agentos_cta.__name__ + "."):
        modules.append(modname)

    with open(docs_dir / "index.md", "w") as f:
        f.write("# AgentOS API Reference\n\n")
        for modname in modules:
            f.write(f"- [{modname}]({modname}.md)\n")

    for modname in modules:
        try:
            module = __import__(modname, fromlist=["dummy"])
            with open(docs_dir / f"{modname}.md", "w") as f:
                f.write(f"# {modname}\n\n")
                for name, obj in inspect.getmembers(module):
                    if inspect.isclass(obj):
                        f.write(f"## class {name}\n\n")
                        doc = inspect.getdoc(obj)
                        if doc:
                            f.write(f"{doc}\n\n")
                        # 方法
                        for method_name, method in inspect.getmembers(obj, inspect.isfunction):
                            if not method_name.startswith("_"):
                                f.write(f"### {method_name}\n\n")
                                doc = inspect.getdoc(method)
                                if doc:
                                    f.write(f"{doc}\n\n")
                print(f"Generated docs for {modname}")
        except Exception as e:
            print(f"Failed to generate docs for {modname}: {e}")

if __name__ == "__main__":
    generate_api_docs()