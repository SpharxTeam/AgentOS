# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 统一错误类型定义。

from typing import Optional, Dict, Any


class AgentOSError(Exception):
    """AgentOS 基础异常类。"""

    def __init__(self, message: str, code: int = 500, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(message)


class ConfigurationError(AgentOSError):
    """配置错误：如缺少必要配置、配置格式错误等。"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code=400, details=details)


class ResourceLimitError(AgentOSError):
    """资源限制错误：如超出 Token 预算、并发限制等。"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code=429, details=details)


class ConsensusError(AgentOSError):
    """共识错误：多智能体协作无法达成一致。"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code=409, details=details)


class SecurityError(AgentOSError):
    """安全错误：权限不足、非法操作、注入攻击等。"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code=403, details=details)


class ToolExecutionError(AgentOSError):
    """工具执行错误：执行单元调用失败。"""

    def __init__(self, message: str, tool_name: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        details = details or {}
        if tool_name:
            details['tool_name'] = tool_name
        super().__init__(message, code=500, details=details)


class ModelUnavailableError(AgentOSError):
    """模型不可用错误：LLM 服务暂时不可用。"""

    def __init__(self, message: str, model_name: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        details = details or {}
        if model_name:
            details['model_name'] = model_name
        super().__init__(message, code=503, details=details)


class ContractValidationError(ConfigurationError):
    """契约验证失败异常。"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details=details)