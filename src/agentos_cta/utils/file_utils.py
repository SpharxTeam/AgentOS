# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 文件操作工具模块。
# 提供安全的文件读写、路径处理、临时文件管理等功能。

import os
import shutil
import tempfile
from pathlib import Path
from typing import Optional, Union, List
import json
import yaml


class FileUtils:
    """文件操作工具类（静态方法）。"""

    @staticmethod
    def safe_read(file_path: Union[str, Path], encoding: str = 'utf-8') -> str:
        """
        安全读取文件内容，如果文件不存在返回空字符串。

        Args:
            file_path: 文件路径。
            encoding: 编码。

        Returns:
            文件内容字符串。
        """
        path = Path(file_path)
        if not path.exists():
            return ""
        with open(path, 'r', encoding=encoding) as f:
            return f.read()

    @staticmethod
    def safe_write(file_path: Union[str, Path], content: str, encoding: str = 'utf-8') -> bool:
        """
        安全写入文件（自动创建父目录）。

        Args:
            file_path: 文件路径。
            content: 写入内容。
            encoding: 编码。

        Returns:
            是否成功写入。
        """
        try:
            path = Path(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, 'w', encoding=encoding) as f:
                f.write(content)
            return True
        except Exception:
            return False

    @staticmethod
    def read_json(file_path: Union[str, Path]) -> Optional[dict]:
        """读取 JSON 文件，失败返回 None。"""
        content = FileUtils.safe_read(file_path)
        if not content:
            return None
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return None

    @staticmethod
    def write_json(file_path: Union[str, Path], data: dict, indent=2) -> bool:
        """写入 JSON 文件。"""
        try:
            content = json.dumps(data, indent=indent, ensure_ascii=False)
            return FileUtils.safe_write(file_path, content)
        except Exception:
            return False

    @staticmethod
    def read_yaml(file_path: Union[str, Path]) -> Optional[dict]:
        """读取 YAML 文件，失败返回 None。"""
        content = FileUtils.safe_read(file_path)
        if not content:
            return None
        try:
            return yaml.safe_load(content)
        except yaml.YAMLError:
            return None

    @staticmethod
    def write_yaml(file_path: Union[str, Path], data: dict) -> bool:
        """写入 YAML 文件。"""
        try:
            content = yaml.dump(data, allow_unicode=True, default_flow_style=False)
            return FileUtils.safe_write(file_path, content)
        except Exception:
            return False

    @staticmethod
    def ensure_dir(path: Union[str, Path]) -> Path:
        """确保目录存在，若不存在则创建。"""
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @staticmethod
    def list_files(directory: Union[str, Path], pattern: str = "*") -> List[Path]:
        """列出目录下匹配模式的文件。"""
        path = Path(directory)
        if not path.exists():
            return []
        return list(path.glob(pattern))

    @staticmethod
    def create_temp_file(suffix: str = ".tmp", prefix: str = "agentos_") -> str:
        """创建临时文件，返回文件路径。"""
        fd, path = tempfile.mkstemp(suffix=suffix, prefix=prefix)
        os.close(fd)
        return path

    @staticmethod
    def create_temp_dir(prefix: str = "agentos_") -> str:
        """创建临时目录，返回目录路径。"""
        return tempfile.mkdtemp(prefix=prefix)

    @staticmethod
    def safe_delete(path: Union[str, Path]) -> bool:
        """安全删除文件或目录（如果存在）。"""
        try:
            path = Path(path)
            if path.is_file():
                path.unlink()
            elif path.is_dir():
                shutil.rmtree(path)
            else:
                return False
            return True
        except Exception:
            return False