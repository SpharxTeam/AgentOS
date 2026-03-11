# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 原始记忆存储：仅追加写入，分布式存储支持。

import os
import time
import shutil
from pathlib import Path
from typing import BinaryIO, Optional, Dict, Any
from agentos_cta.utils.structured_logger import get_logger
from agentos_cta.utils.file_utils import FileUtils

logger = get_logger(__name__)


class RawStorage:
    """
    原始卷 L1 存储管理器。
    将原始记忆以文件形式存储，支持按时间分片、仅追加写入。
    可扩展为分布式对象存储。
    """

    def __init__(self, base_dir: str = "data/workspace/memory/raw", max_file_size_mb: int = 100):
        """
        初始化原始存储。

        Args:
            base_dir: 存储根目录。
            max_file_size_mb: 单个文件最大大小（MB），超过则自动分片。
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.max_file_size_bytes = max_file_size_mb * 1024 * 1024
        self.current_file = None
        self.current_file_size = 0
        self._lock = asyncio.Lock()
        self._ensure_current_file()

    def _ensure_current_file(self):
        """确保当前写入文件存在且未超过大小限制。"""
        if self.current_file is None or self.current_file_size >= self.max_file_size_bytes:
            # 生成新的分片文件名：raw_YYYYMMDD_HHMMSS.bin
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = self.base_dir / f"raw_{timestamp}.bin"
            self.current_file = filename
            self.current_file_size = filename.stat().st_size if filename.exists() else 0
            logger.info(f"New raw storage file: {self.current_file}")

    async def append(self, data: bytes, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        追加写入原始数据。

        Args:
            data: 原始字节数据。
            metadata: 附加元数据（如时间戳、来源等）。

        Returns:
            写入位置标识（可用于检索）。
        """
        async with self._lock:
            self._ensure_current_file()
            # 写入前记录位置
            pos = self.current_file_size
            # 实际写入
            mode = 'ab' if self.current_file.exists() else 'wb'
            async with aiofiles.open(self.current_file, mode) as f:
                await f.write(data)
                if metadata:
                    # 可以将元数据单独存储或嵌入数据前，这里简化：另存为同名的 .meta.json
                    meta_path = self.current_file.with_suffix('.meta.json')
                    existing = []
                    if meta_path.exists():
                        content = await FileUtils.safe_read(meta_path)
                        if content:
                            existing = json.loads(content)
                    existing.append({
                        "offset": pos,
                        "length": len(data),
                        "timestamp": time.time(),
                        **metadata
                    })
                    await FileUtils.safe_write(meta_path, json.dumps(existing, indent=2))
            self.current_file_size = self.current_file.stat().st_size
            # 返回标识符：文件名:offset
            location = f"{self.current_file.name}:{pos}"
            logger.debug(f"Appended {len(data)} bytes at {location}")
            return location

    async def read(self, location: str) -> Optional[bytes]:
        """
        根据位置标识读取原始数据。

        Args:
            location: 格式为 "filename:offset"

        Returns:
            原始数据字节，若不存在则返回 None。
        """
        try:
            filename, offset_str = location.split(':')
            offset = int(offset_str)
            filepath = self.base_dir / filename
            if not filepath.exists():
                logger.error(f"Raw storage file not found: {filepath}")
                return None
            async with aiofiles.open(filepath, 'rb') as f:
                await f.seek(offset)
                # 需要知道长度，但仅靠 offset 无法得知长度，这里需要元数据辅助
                # 实际应使用元数据管理，此处简化：读取到文件末尾（但不可行）
                # 因此我们需要从元数据获取长度
                meta_path = filepath.with_suffix('.meta.json')
                if meta_path.exists():
                    meta_content = await FileUtils.safe_read(meta_path)
                    if meta_content:
                        metas = json.loads(meta_content)
                        for m in metas:
                            if m['offset'] == offset:
                                data = await f.read(m['length'])
                                return data
                logger.warning(f"No metadata found for offset {offset}, reading to end")
                data = await f.read()
                return data
        except Exception as e:
            logger.error(f"Failed to read raw memory at {location}: {e}")
            return None