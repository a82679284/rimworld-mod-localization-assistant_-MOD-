"""
MOD 信息数据模型
"""
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class ModInfo:
    """MOD 信息"""

    name: str
    path: Path
    version: Optional[str] = None
    author: Optional[str] = None
    total_entries: int = 0
    translated_entries: int = 0
    pending_entries: int = 0

    @property
    def progress(self) -> float:
        """翻译进度百分比"""
        if self.total_entries == 0:
            return 0.0
        return (self.translated_entries / self.total_entries) * 100

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "name": self.name,
            "path": str(self.path),
            "version": self.version,
            "author": self.author,
            "total_entries": self.total_entries,
            "translated_entries": self.translated_entries,
            "pending_entries": self.pending_entries,
            "progress": self.progress,
        }
