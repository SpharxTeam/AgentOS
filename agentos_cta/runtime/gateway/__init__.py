# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 网关模块，负责不同传输协议的接入。

from abc import ABC, abstractmethod
from .http_gateway import HTTPGateway
from .websocket_gateway import WebSocketGateway
from .stdio_gateway import StdioGateway


class BaseGateway(ABC):
    """网关基类。"""

    @abstractmethod
    async def start(self):
        """启动网关。"""
        pass

    @abstractmethod
    async def stop(self):
        """停止网关。"""
        pass


__all__ = [
    "BaseGateway",
    "HTTPGateway",
    "WebSocketGateway",
    "StdioGateway",
]