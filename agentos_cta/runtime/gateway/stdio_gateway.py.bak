# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# stdio 网关：支持本地进程通信。

import asyncio
import json
import sys
from typing import Optional
from .base import Gateway, GatewayConfig
from agentos_cta.utils.structured_logger import get_logger

logger = get_logger(__name__)


class StdioGateway(Gateway):
    """
    stdio 网关。
    通过标准输入输出进行通信，适用于本地进程调用。
    借鉴 MCP 协议的 stdio 传输设计。
    """

    def __init__(self, config: GatewayConfig, runtime):
        super().__init__(config, runtime)
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None
        self._task: Optional[asyncio.Task] = None

    async def start(self):
        """启动 stdio 网关。"""
        self.running = True
        loop = asyncio.get_running_loop()
        self.reader = asyncio.StreamReader()
        reader_protocol = asyncio.StreamReaderProtocol(self.reader)
        await loop.connect_read_pipe(lambda: reader_protocol, sys.stdin)

        self.writer = await self._create_stdout_writer()

        logger.info("Stdio gateway started")
        self._task = asyncio.create_task(self._read_loop())

    async def _create_stdout_writer(self):
        """创建标准输出写入器。"""
        loop = asyncio.get_running_loop()
        transport, protocol = await loop.connect_write_pipe(
            asyncio.streams.FlowControlMixin,
            sys.stdout
        )
        writer = asyncio.StreamWriter(transport, protocol, None, loop)
        return writer

    async def _read_loop(self):
        """读取循环。"""
        while self.running:
            try:
                line = await self.reader.readline()
                if not line:
                    break

                data = json.loads(line.decode())
                response = await self.runtime.handle_request(data, "stdio")

                # 写入响应
                response_line = (json.dumps(response) + "\n").encode()
                self.writer.write(response_line)
                await self.writer.drain()

            except json.JSONDecodeError:
                logger.error("Invalid JSON from stdin")
                error_response = {
                    "jsonrpc": "2.0",
                    "error": {"code": -32700, "message": "Parse error"},
                }
                self.writer.write((json.dumps(error_response) + "\n").encode())
                await self.writer.drain()
            except Exception as e:
                logger.error(f"Stdio error: {e}")
                error_response = {
                    "jsonrpc": "2.0",
                    "error": {"code": -32000, "message": str(e)},
                }
                self.writer.write((json.dumps(error_response) + "\n").encode())
                await self.writer.drain()

        logger.info("Stdio gateway read loop ended")

    async def stop(self):
        """停止 stdio 网关。"""
        self.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()
        logger.info("Stdio gateway stopped")