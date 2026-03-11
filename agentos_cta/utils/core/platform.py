# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 平台检测与系统资源。

import os
import sys
import multiprocessing


def is_windows() -> bool:
    """是否为 Windows 系统。"""
    return sys.platform == "win32" or sys.platform == "cygwin"


def is_linux() -> bool:
    """是否为 Linux 系统。"""
    return sys.platform.startswith("linux")


def is_macos() -> bool:
    """是否为 macOS 系统。"""
    return sys.platform == "darwin"


def get_platform() -> str:
    """获取平台名称。"""
    if is_windows():
        return "windows"
    elif is_linux():
        return "linux"
    elif is_macos():
        return "macos"
    else:
        return sys.platform


def get_cpu_count() -> int:
    """获取 CPU 核心数。"""
    return multiprocessing.cpu_count()


def get_memory_info() -> dict:
    """获取内存信息（单位：字节）。"""
    try:
        import psutil
        mem = psutil.virtual_memory()
        return {
            "total": mem.total,
            "available": mem.available,
            "percent": mem.percent,
            "used": mem.used,
            "free": mem.free,
        }
    except ImportError:
        # 降级返回空信息
        return {
            "total": 0,
            "available": 0,
            "percent": 0,
            "used": 0,
            "free": 0,
        }