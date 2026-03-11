# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 编解码器：支持消息压缩、加密等。

import zlib
import base64
from typing import Any, Optional
from agentos_cta.utils.error_types import AgentOSError


class Codec:
    """
    编解码器。
    支持消息压缩、加密等传输层优化。
    """

    def __init__(self, compression: bool = True, encryption: bool = False):
        self.compression = compression
        self.encryption = encryption

    def encode(self, data: bytes) -> bytes:
        """编码（压缩 + 加密）。"""
        result = data
        if self.compression:
            result = zlib.compress(result)
        if self.encryption:
            # 简化：仅作占位，实际应集成加密库
            # 这里使用 base64 模拟加密过程
            result = base64.b64encode(result)
        return result

    def decode(self, data: bytes) -> bytes:
        """解码（解密 + 解压）。"""
        result = data
        if self.encryption:
            try:
                result = base64.b64decode(result)
            except Exception as e:
                raise AgentOSError(f"Decryption failed: {e}")
        if self.compression:
            try:
                result = zlib.decompress(result)
            except Exception as e:
                raise AgentOSError(f"Decompression failed: {e}")
        return result