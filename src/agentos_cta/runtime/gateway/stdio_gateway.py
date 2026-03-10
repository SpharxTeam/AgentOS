# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 标准输入输出网关，用于本地进程通信。

import asyncio
import sys
import json
from typing import Dict, Any
from agentos_cta.utils.structured_logger import get_logger
from . import BaseGateway

logger = get_logger(__name__)


class StdioGateway(BaseGateway):
    """标准输入输出网关，适合命令行调用。"""

    def __init__(self, config: Dict[str, Any], request_handler):
        self.config = config
        self.handler = request_handler
        self._reader = None
        self._writer = None
        self._task = None

    async def start(self):
        loop = asyncio.get_event_loop()
        self._reader = asyncio.StreamReader(loop=loop)
        reader_protocol = asyncio.StreamReaderProtocol(self._reader)
        await loop.connect_read_pipe(lambda: reader_protocol, sys.stdin)

        # 标准输出不需要特别处理，直接用 sys.stdout.write
        self._task = asyncio.create_task(self._read_loop())
        logger.info("Stdio gateway started")

    async def stop(self):
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Stdio gateway stopped")

    async def _read_loop(self):
        """循环读取 stdin 并处理。"""
        while True:
            try:
                line = await self._reader.readline()
                if not line:
                    break  # EOF
                line = line.decode('utf-8').strip()
                if not line:
                    continue
                request = json.loads(line)
                logger.debug(f"Stdio request: {request}")
                response = await self.handler("stdio", request)
                # 输出响应，每个一行
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Stdio error: {e}")
                # 错误响应
                sys.stdout.write(json.dumps({"error": str(e)}) + "\n")
                sys.stdout.flush()