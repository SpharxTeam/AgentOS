# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# L1 Buffer：实时日志存储，按日期分片。

import os
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, List
from agentos_cta.utils.structured_logger import get_logger
from agentos_cta.utils.file_utils import FileUtils

logger = get_logger(__name__)


class Buffer:
    """
    L1 Buffer：实时日志存储。
    按日期分片保存原始日志，每条日志包含时间戳、角色、内容等。
    """

    def __init__(self, base_dir: str = "data/workspace/memory/buffer"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.current_date = datetime.now().strftime("%Y-%m-%d")
        self.current_file = self.base_dir / f"{self.current_date}.log"

    def _rotate_if_needed(self):
        """检查日期是否变化，若变化则切换文件。"""
        today = datetime.now().strftime("%Y-%m-%d")
        if today != self.current_date:
            self.current_date = today
            self.current_file = self.base_dir / f"{today}.log"
            logger.info(f"Buffer rotated to {self.current_file}")

    async def append(self, record: dict):
        """追加一条日志记录。"""
        self._rotate_if_needed()
        # 添加时间戳
        record["timestamp"] = time.time()
        line = f"{record}\n"  # 简单序列化，实际可考虑 JSON Lines
        FileUtils.safe_write(self.current_file, line, mode="a")  # 追加模式

    async def read_today(self) -> List[dict]:
        """读取今天的全部日志。"""
        self._rotate_if_needed()
        content = FileUtils.safe_read(self.current_file)
        if not content:
            return []
        # 每行一个 dict，需 eval 或 json.loads，这里简化按行处理
        records = []
        for line in content.strip().split("\n"):
            if line:
                try:
                    records.append(eval(line))  # 不安全，仅演示；实际应用应使用 json
                except:
                    pass
        return records

    async def read_range(self, start_date: str, end_date: str) -> List[dict]:
        """读取指定日期范围内的日志。"""
        records = []
        current = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        while current <= end:
            date_str = current.strftime("%Y-%m-%d")
            file_path = self.base_dir / f"{date_str}.log"
            if file_path.exists():
                content = FileUtils.safe_read(file_path)
                for line in content.strip().split("\n"):
                    if line:
                        try:
                            records.append(eval(line))
                        except:
                            pass
            current += timedelta(days=1)
        return records