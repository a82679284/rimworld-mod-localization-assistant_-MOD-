"""
翻译条目数据模型
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class TranslationEntry:
    """翻译条目"""

    id: Optional[int] = None
    mod_name: str = ""
    file_path: str = ""  # 相对于 MOD 根目录的路径
    xml_path: str = ""  # XML 节点路径 (例: Beer.label)
    original_text: str = ""
    translated_text: str = ""
    comment: Optional[str] = None  # XML 注释 (<!-- EN: ... -->)
    status: str = "pending"  # pending|completed|skipped|in_progress
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """初始化后处理"""
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "mod_name": self.mod_name,
            "file_path": self.file_path,
            "xml_path": self.xml_path,
            "original_text": self.original_text,
            "translated_text": self.translated_text,
            "comment": self.comment,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TranslationEntry":
        """从字典创建"""
        return cls(
            id=data.get("id"),
            mod_name=data.get("mod_name", ""),
            file_path=data.get("file_path", ""),
            xml_path=data.get("xml_path", ""),
            original_text=data.get("original_text", ""),
            translated_text=data.get("translated_text", ""),
            comment=data.get("comment"),
            status=data.get("status", "pending"),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None,
        )
