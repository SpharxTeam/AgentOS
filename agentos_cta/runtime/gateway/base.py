# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 网关基类。

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass
from agentos_cta.utils.observability import get_logger

logger = get_logger(__name__)


@dataclass
class GatewayConfig:
    """网关配置。"""
    protocol: str  # "http", "websocket", "stdio"
    host: str = "127.0.0.1"
    port: int = 0
    max_connections: int = 100
    timeout_seconds: int = 30


class Gateway(ABC):
    """网关基类。"""

    def __init__(self, config: GatewayConfig, runtime):
        self.config = config
        self.runtime = runtime
        self.running = False

    @abstractmethod
    async def start(self):
        """启动网关。"""
        pass

    @abstractmethod
    async def stop(self):
        """停止网关。"""
        pass