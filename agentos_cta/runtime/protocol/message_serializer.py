# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 消息序列化器，支持增量更新和压缩。

import json
import zlib
from typing import Any, Dict, Optional


class MessageSerializer:
    """
    消息序列化器。
    支持 JSON 序列化、压缩、以及增量更新（占位）。
    """

    def __init__(self, compress: bool = False, compression_level: int = 6):
        self.compress = compress
        self.compression_level = compression_level

    def serialize(self, obj: Any) -> bytes:
        """将对象序列化为字节。"""
        data = json.dumps(obj, separators=(',', ':')).encode('utf-8')
        if self.compress:
            data = zlib.compress(data, level=self.compression_level)
        return data

    def deserialize(self, data: bytes) -> Any:
        """将字节反序列化为对象。"""
        if self.compress:
            data = zlib.decompress(data)
        return json.loads(data.decode('utf-8'))

    # 增量更新相关（预留）
    def create_diff(self, old: Dict, new: Dict) -> Optional[Dict]:
        """生成增量 diff（简化版，实际可用 jsonpatch 等）。"""
        # 这里简化，仅当新旧不同时返回新对象
        if old == new:
            return None
        return new

    def apply_diff(self, base: Dict, diff: Dict) -> Dict:
        """应用 diff。"""
        # 简单合并
        base.update(diff)
        return base