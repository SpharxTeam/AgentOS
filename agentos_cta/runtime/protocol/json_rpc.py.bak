# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# JSON-RPC 2.0 协议实现。

import json
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass
from agentos_cta.utils.error_types import AgentOSError


@dataclass
class RpcRequest:
    """JSON-RPC 请求。"""
    jsonrpc: str = "2.0"
    method: str = ""
    params: Optional[Union[Dict[str, Any], list]] = None
    id: Optional[Union[str, int]] = None


@dataclass
class RpcResponse:
    """JSON-RPC 响应。"""
    jsonrpc: str = "2.0"
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None
    id: Optional[Union[str, int]] = None


@dataclass
class RpcError:
    """JSON-RPC 错误。"""
    code: int
    message: str
    data: Optional[Any] = None


class JsonRpcProtocol:
    """
    JSON-RPC 2.0 协议处理器。
    """

    @staticmethod
    def parse_request(data: Union[str, bytes, Dict]) -> RpcRequest:
        """解析请求。"""
        if isinstance(data, (str, bytes)):
            parsed = json.loads(data)
        else:
            parsed = data

        if not isinstance(parsed, dict):
            raise AgentOSError("Invalid request format")

        if parsed.get("jsonrpc") != "2.0":
            raise AgentOSError("Invalid JSON-RPC version")

        return RpcRequest(
            jsonrpc=parsed["jsonrpc"],
            method=parsed.get("method", ""),
            params=parsed.get("params"),
            id=parsed.get("id"),
        )

    @staticmethod
    def create_response(result: Any = None, error: Optional[RpcError] = None,
                        request_id: Optional[Union[str, int]] = None) -> Dict:
        """创建响应。"""
        response = {"jsonrpc": "2.0"}
        if error:
            response["error"] = {
                "code": error.code,
                "message": error.message,
            }
            if error.data:
                response["error"]["data"] = error.data
        else:
            response["result"] = result
        if request_id is not None:
            response["id"] = request_id
        return response

    @staticmethod
    def create_error_response(code: int, message: str, data: Any = None,
                              request_id: Optional[Union[str, int]] = None) -> Dict:
        """创建错误响应。"""
        error = RpcError(code=code, message=message, data=data)
        return JsonRpcProtocol.create_response(error=error, request_id=request_id)

    @staticmethod
    def serialize_response(response: Dict) -> str:
        """序列化响应。"""
        return json.dumps(response)