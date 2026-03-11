# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 文件操作工具模块。

import os
import shutil
import tempfile
import json
import yaml
from pathlib import Path
from typing import Optional, Union, List, Any


class FileUtils:
    """文件操作工具类（静态方法）。"""

    @staticmethod
    def safe_read(file_path: Union[str, Path], encoding: str = 'utf-8') -> str:
        path = Path(file_path)
        if not path.exists():
            return ""
        with open(path, 'r', encoding=encoding) as f:
            return f.read()

    @staticmethod
    def safe_write(file_path: Union[str, Path], content: str, mode: str = 'w', encoding: str = 'utf-8') -> bool:
        try:
            path = Path(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, mode, encoding=encoding) as f:
                f.write(content)
            return True
        except Exception:
            return False

    @staticmethod
    def read_json(file_path: Union[str, Path]) -> Optional[dict]:
        content = FileUtils.safe_read(file_path)
        if not content:
            return None
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return None

    @staticmethod
    def write_json(file_path: Union[str, Path], data: dict, indent=2) -> bool:
        try:
            content = json.dumps(data, indent=indent, ensure_ascii=False)
            return FileUtils.safe_write(file_path, content)
        except Exception:
            return False

    @staticmethod
    def read_yaml(file_path: Union[str, Path]) -> Optional[dict]:
        content = FileUtils.safe_read(file_path)
        if not content:
            return None
        try:
            return yaml.safe_load(content)
        except yaml.YAMLError:
            return None

    @staticmethod
    def write_yaml(file_path: Union[str, Path], data: dict) -> bool:
        try:
            content = yaml.dump(data, allow_unicode=True, default_flow_style=False)
            return FileUtils.safe_write(file_path, content)
        except Exception:
            return False

    @staticmethod
    def ensure_dir(path: Union[str, Path]) -> Path:
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @staticmethod
    def list_files(directory: Union[str, Path], pattern: str = "*") -> List[Path]:
        path = Path(directory)
        if not path.exists():
            return []
        return list(path.glob(pattern))

    @staticmethod
    def create_temp_file(suffix: str = ".tmp", prefix: str = "agentos_") -> str:
        fd, path = tempfile.mkstemp(suffix=suffix, prefix=prefix)
        os.close(fd)
        return path

    @staticmethod
    def create_temp_dir(prefix: str = "agentos_") -> str:
        return tempfile.mkdtemp(prefix=prefix)

    @staticmethod
    def safe_delete(path: Union[str, Path]) -> bool:
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