"""
术语库条目数据模型
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class GlossaryEntry:
    """术语库条目"""

    id: Optional[int] = None
    term_en: str = ""  # 英文术语
    term_zh: str = ""  # 中文术语
    category: Optional[str] = None  # 分类 (物品/角色/技能等)
    note: Optional[str] = None  # 备注
    priority: int = 0  # 优先级 (用于冲突解决)
    source: str = "user"  # 来源 (user/official)
    created_at: Optional[datetime] = None

    def __post_init__(self):
        """初始化后处理"""
        if self.created_at is None:
            self.created_at = datetime.now()

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "term_en": self.term_en,
            "term_zh": self.term_zh,
            "category": self.category,
            "note": self.note,
            "priority": self.priority,
            "source": self.source,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
