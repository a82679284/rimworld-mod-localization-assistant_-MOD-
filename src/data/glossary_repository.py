"""
术语库数据访问层
"""
from typing import List, Optional
import csv
from pathlib import Path
from ..storage.database import Database
from ..models.glossary_entry import GlossaryEntry


class GlossaryRepository:
    """术语库仓库"""

    def __init__(self, database: Database):
        self.db = database

    def save(self, entry: GlossaryEntry) -> int:
        """保存术语"""
        query = """
            INSERT OR REPLACE INTO glossary
            (term_en, term_zh, category, note, priority, source)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (
                entry.term_en, entry.term_zh, entry.category,
                entry.note, entry.priority, entry.source
            ))
            conn.commit()
            return cursor.lastrowid

    def find_all(self, category: Optional[str] = None) -> List[GlossaryEntry]:
        """查找所有术语"""
        query = "SELECT * FROM glossary"
        params = []

        if category:
            query += " WHERE category = ?"
            params.append(category)

        query += " ORDER BY priority DESC, term_en"
        results = self.db.execute_query(query, tuple(params))

        return [self._row_to_entry(row) for row in results]

    def find_by_term(self, term_en: str) -> Optional[GlossaryEntry]:
        """根据英文术语查找"""
        query = "SELECT * FROM glossary WHERE term_en = ?"
        results = self.db.execute_query(query, (term_en,))
        return self._row_to_entry(results[0]) if results else None

    def find_by_id(self, term_id: int) -> Optional[GlossaryEntry]:
        """
        根据ID查找术语

        Args:
            term_id: 术语ID

        Returns:
            Optional[GlossaryEntry]: 术语条目
        """
        query = "SELECT * FROM glossary WHERE id = ?"
        results = self.db.execute_query(query, (term_id,))
        return self._row_to_entry(results[0]) if results else None

    def import_from_csv(self, csv_path: Path) -> int:
        """从 CSV 导入术语库"""
        count = 0
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                entry = GlossaryEntry(
                    term_en=row['term_en'],
                    term_zh=row['term_zh'],
                    category=row.get('category'),
                    priority=int(row.get('priority', 0)),
                    note=row.get('note'),
                    source=row.get('source', 'user')
                )
                self.save(entry)
                count += 1
        return count

    def count_all(self) -> int:
        """统计所有术语数量"""
        query = "SELECT COUNT(*) as count FROM glossary"
        results = self.db.execute_query(query)
        return results[0]['count'] if results else 0

    def get_categories(self) -> List[str]:
        """获取所有分类列表"""
        query = "SELECT DISTINCT category FROM glossary WHERE category IS NOT NULL ORDER BY category"
        results = self.db.execute_query(query)
        return [row['category'] for row in results]

    def count_by_category(self, category: str) -> int:
        """统计指定分类的术语数量"""
        query = "SELECT COUNT(*) as count FROM glossary WHERE category = ?"
        results = self.db.execute_query(query, (category,))
        return results[0]['count'] if results else 0

    def get_all_terms(self) -> List[dict]:
        """
        获取所有术语的字典列表

        Returns:
            List[dict]: 术语字典列表
        """
        query = "SELECT * FROM glossary ORDER BY priority DESC, term_en"
        results = self.db.execute_query(query)
        return [
            {
                'id': row['id'],
                'term_en': row['term_en'],
                'term_zh': row['term_zh'],
                'category': row['category'],
                'priority': row['priority'],
                'note': row['note'],
                'source': row['source']
            }
            for row in results
        ]

    def delete_by_id(self, term_id: int) -> bool:
        """
        删除指定ID的术语

        Args:
            term_id: 术语ID

        Returns:
            bool: 是否删除成功
        """
        query = "DELETE FROM glossary WHERE id = ?"
        try:
            deleted = self.db.execute_update(query, (term_id,))
            return deleted > 0
        except Exception:
            return False

    def search_terms(self, keyword: str) -> List[GlossaryEntry]:
        """
        搜索术语(英文或中文)

        Args:
            keyword: 搜索关键词

        Returns:
            List[GlossaryEntry]: 匹配的术语列表
        """
        query = """
            SELECT * FROM glossary
            WHERE term_en LIKE ? OR term_zh LIKE ?
            ORDER BY priority DESC, term_en
        """
        pattern = f"%{keyword}%"
        results = self.db.execute_query(query, (pattern, pattern))
        return [self._row_to_entry(row) for row in results]

    def _row_to_entry(self, row: dict) -> GlossaryEntry:
        """转换数据库行"""
        return GlossaryEntry(
            id=row['id'],
            term_en=row['term_en'],
            term_zh=row['term_zh'],
            category=row['category'],
            note=row['note'],
            priority=row['priority'],
            source=row['source']
        )
