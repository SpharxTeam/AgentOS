# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 全局异常处理器。

import sys
import traceback
from typing import Optional, Dict, Any
from agentos_cta.utils.observability import get_logger
from .types import AgentOSError

logger = get_logger("error.handler")


def handle_exception(
    exc: Exception,
    context: Optional[Dict[str, Any]] = None,
    fatal: bool = False
) -> Dict[str, Any]:
    """
    统一异常处理函数。

    Args:
        exc: 捕获的异常。
        context: 附加上下文。
        fatal: 是否致命错误。

    Returns:
        结构化错误响应。
    """
    if isinstance(exc, AgentOSError):
        # 已知业务错误
        error_response = {
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            }
        }
        log_level = "error" if exc.code >= 500 else "warning"
        getattr(logger, log_level)(
            f"AgentOS error: {exc.message}",
            code=exc.code,
            details=exc.details,
            context=context,
        )
    else:
        # 未预期异常
        error_response = {
            "error": {
                "code": 500,
                "message": f"Internal error: {str(exc)}",
                "details": {
                    "type": exc.__class__.__name__,
                }
            }
        }
        logger.error(
            f"Unexpected error: {exc}",
            exc_info=True,
            context=context,
        )

    if fatal:
        logger.critical("Fatal error, exiting", error=error_response)
        sys.exit(1)

    return error_response