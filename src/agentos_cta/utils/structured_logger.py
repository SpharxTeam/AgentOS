# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 结构化日志模块。
# 提供支持 TraceID 的结构化日志记录，便于责任链追溯和分析。

import logging
import json
import time
import uuid
from typing import Optional, Dict, Any
from contextvars import ContextVar

# 上下文变量，用于传递当前 TraceID
_trace_id_var: ContextVar[Optional[str]] = ContextVar('trace_id', default=None)


def set_trace_id(trace_id: Optional[str] = None):
    """设置当前上下文的 TraceID，若未提供则自动生成。"""
    if trace_id is None:
        trace_id = str(uuid.uuid4())
    _trace_id_var.set(trace_id)


def get_trace_id() -> Optional[str]:
    """获取当前上下文的 TraceID。"""
    return _trace_id_var.get()


class StructuredLogger:
    """
    结构化日志记录器。
    包装标准 logging，自动添加 trace_id 和其他字段。
    """

    def __init__(self, name: str, level: int = logging.INFO):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)

    def _log(self, level: int, msg: str, **kwargs):
        """核心日志方法，添加结构化字段。"""
        record = {
            "timestamp": time.time(),
            "level": logging.getLevelName(level).lower(),
            "logger": self.logger.name,
            "trace_id": get_trace_id(),
            "message": msg,
            **kwargs,
        }
        # 输出 JSON 格式
        self.logger.log(level, json.dumps(record))

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
    """获取指定名称的结构化日志记录器（单例）。"""
    if name not in _loggers:
        _loggers[name] = StructuredLogger(name)
    return _loggers[name]