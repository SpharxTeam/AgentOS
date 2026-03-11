# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# JSON-RPC 2.0 协议实现。

import json
import uuid
from typing import Dict, Any, Optional, Union


class JsonRpcProtocol:
    """JSON-RPC 2.0 协议封装。"""

    @staticmethod
    def create_request(method: str, params: Any = None, request_id: Optional[str] = None) -> Dict[str, Any]:
        """创建请求对象。"""
        req = {
            "jsonrpc": "2.0",
            "method": method,
            "id": request_id or str(uuid.uuid4())
        }
        if params is not None:
            req["params"] = params
        return req

    @staticmethod
    def create_response(result: Any, request_id: Union[str, int]) -> Dict[str, Any]:
        """创建成功响应。"""
        return {
            "jsonrpc": "2.0",
            "result": result,
            "id": request_id
        }

    @staticmethod
    def create_error(code: int, message: str, data: Any = None, request_id: Union[str, int, None] = None) -> Dict[str, Any]:
        """创建错误响应。"""
        error = {
            "code": code,
            "message": message
        }
        if data is not None:
            error["data"] = data
        return {
            "jsonrpc": "2.0",
            "error": error,
            "id": request_id
        }

    @staticmethod
    def parse_message(data: Union[str, bytes, Dict]) -> Dict[str, Any]:
        """解析传入消息，返回字典。"""
        if isinstance(data, (str, bytes)):
            return json.loads(data)
        return data

    @staticmethod
    def is_request(msg: Dict) -> bool:
        """判断是否为请求（包含 method）。"""
        return "method" in msg

    @staticmethod
    def is_response(msg: Dict) -> bool:
        """判断是否为响应（包含 result 或 error）。"""
        return "result" in msg or "error" in msg