# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 结构化日志模块 - 内核日志记录。
# 日志存储位置: data/logs/kernel/YYYY-MM-DD.log

import json
import logging
import time
import uuid
from pathlib import Path
from typing import Optional, Dict, Any
from contextvars import ContextVar
from logging.handlers import RotatingFileHandler

# 上下文变量，用于传递当前 TraceID
_trace_id_var: ContextVar[Optional[str]] = ContextVar('trace_id', default=None)
_session_id_var: ContextVar[Optional[str]] = ContextVar('session_id', default=None)


def set_trace_id(trace_id: Optional[str] = None) -> str:
    """设置当前上下文的 TraceID，若未提供则自动生成。"""
    if trace_id is None:
        trace_id = str(uuid.uuid4())
    _trace_id_var.set(trace_id)
    return trace_id


def get_trace_id() -> Optional[str]:
    """获取当前上下文的 TraceID。"""
    return _trace_id_var.get()


def set_session_id(session_id: Optional[str] = None) -> Optional[str]:
    """设置当前上下文的 SessionID。"""
    _session_id_var.set(session_id)
    return session_id


def get_session_id() -> Optional[str]:
    """获取当前上下文的 SessionID。"""
    return _session_id_var.get()


class StructuredLogger:
    """
    结构化日志记录器。
    输出 JSON 格式的日志，包含 trace_id、session_id、时间戳等字段。
    日志自动按日期分片，存储在 data/logs/kernel/ 目录。
    """

    def __init__(self, name: str, level: int = logging.INFO, log_dir: str = "data/logs/kernel"):
        self.name = name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # 创建标准 logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self.logger.propagate = False

        # 移除已有 handler
        self.logger.handlers.clear()

        # 添加按日期轮转的 handler
        log_file = self.log_dir / f"{time.strftime('%Y-%m-%d')}.log"
        handler = RotatingFileHandler(
            log_file,
            maxBytes=100 * 1024 * 1024,  # 100MB
            backupCount=30,  # 保留30天
            encoding='utf-8'
        )
        handler.setFormatter(logging.Formatter('%(message)s'))
        self.logger.addHandler(handler)

        # 添加控制台 handler（可选）
        console = logging.StreamHandler()
        console.setLevel(logging.WARNING)
        console.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
        self.logger.addHandler(console)

    def _log(self, level: int, msg: str, **kwargs):
        """核心日志方法，添加结构化字段。"""
        record = {
            "timestamp": time.time(),
            "level": logging.getLevelName(level).lower(),
            "logger": self.name,
            "trace_id": get_trace_id(),
            "session_id": get_session_id(),
            "message": msg,
            **kwargs,
        }
        # 输出 JSON 格式
        self.logger.log(level, json.dumps(record, ensure_ascii=False))

    def debug(self, msg: str, **kwargs):
        self._log(logging.DEBUG, msg, **kwargs)

    def info(self, msg: str, **kwargs):
        self._log(logging.INFO, msg, **kwargs)

    def warning(self, msg: str, **kwargs):
        self._log(logging.WARNING, msg, **kwargs)

    def error(self, msg: str, **kwargs):
        self._log(logging.ERROR, msg, **kwargs)

    def critical(self, msg: str, **kwargs):
        self._log(logging.CRITICAL, msg, **kwargs)


# 便捷函数：获取或创建结构化日志记录器
_loggers: Dict[str, StructuredLogger] = {}


def get_logger(name: str) -> StructuredLogger:
    """获取指定名称的结构化日志记录器。"""
    if name not in _loggers:
        _loggers[name] = StructuredLogger(name)
    return _loggers[name]