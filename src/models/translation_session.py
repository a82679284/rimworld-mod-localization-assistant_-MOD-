"""
翻译会话数据模型
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class TranslationSession:
    """翻译会话"""

    id: Optional[int] = None
    mod_name: str = ""
    mod_path: str = ""
    total_entries: int = 0
    translated_entries: int = 0
    current_page: int = 0  # 当前页码
    last_save: Optional[datetime] = None
    created_at: Optional[datetime] = None

    def __post_init__(self):
        """初始化后处理"""
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.last_save is None:
            self.last_save = datetime.now()

    @property
    def progress(self) -> float:
        """进度百分比"""
        if self.total_entries == 0:
            return 0.0
        return (self.translated_entries / self.total_entries) * 100

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "mod_name": self.mod_name,
            "mod_path": self.mod_path,
            "total_entries": self.total_entries,
            "translated_entries": self.translated_entries,
            "current_page": self.current_page,
            "progress": self.progress,
            "last_save": self.last_save.isoformat() if self.last_save else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
