"""
翻译条目数据访问层
"""
from typing import List, Optional
from datetime import datetime
from ..storage.database import Database
from ..models.translation_entry import TranslationEntry
from ..utils.exceptions import DatabaseError


class TranslationRepository:
    """翻译条目仓库"""

    def __init__(self, database: Database):
        """
        初始化仓库

        Args:
            database: 数据库实例
        """
        self.db = database

    def save(self, entry: TranslationEntry) -> int:
        """
        保存翻译条目

        Args:
            entry: 翻译条目

        Returns:
            int: 条目 ID
        """
        query = """
            INSERT OR REPLACE INTO translations
            (mod_name, file_path, xml_path, original_text, translated_text,
             comment, status, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            entry.mod_name,
            entry.file_path,
            entry.xml_path,
            entry.original_text,
            entry.translated_text,
            entry.comment,
            entry.status,
            datetime.now().isoformat()
        )

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.lastrowid

    def save_batch(self, entries: List[TranslationEntry]) -> int:
        """
        批量保存翻译条目

        Args:
            entries: 翻译条目列表

        Returns:
            int: 保存的条目数
        """
        query = """
            INSERT OR REPLACE INTO translations
            (mod_name, file_path, xml_path, original_text, translated_text,
             comment, status, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        params_list = [
            (
                e.mod_name, e.file_path, e.xml_path, e.original_text,
                e.translated_text, e.comment, e.status,
                datetime.now().isoformat()
            )
            for e in entries
        ]

        return self.db.execute_many(query, params_list)

    def find_by_id(self, entry_id: int) -> Optional[TranslationEntry]:
        """
        根据 ID 查找条目

        Args:
            entry_id: 条目 ID

        Returns:
            Optional[TranslationEntry]: 翻译条目
        """
        query = "SELECT * FROM translations WHERE id = ?"
        results = self.db.execute_query(query, (entry_id,))

        if results:
            return self._row_to_entry(results[0])
        return None

    def find_by_mod(
        self,
        mod_name: str,
        status: Optional[str] = None,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[TranslationEntry]:
        """
        根据 MOD 名称查找条目

        Args:
            mod_name: MOD 名称
            status: 状态过滤 (可选)
            limit: 限制数量
            offset: 偏移量

        Returns:
            List[TranslationEntry]: 翻译条目列表
        """
        query = "SELECT * FROM translations WHERE mod_name = ?"
        params = [mod_name]

        if status:
            query += " AND status = ?"
            params.append(status)

        query += " ORDER BY id"

        if limit:
            query += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])

        results = self.db.execute_query(query, tuple(params))
        return [self._row_to_entry(row) for row in results]

    def find_by_status(
        self,
        mod_name: str,
        status: str,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[TranslationEntry]:
        """
        根据MOD名称和状态查找条目

        Args:
            mod_name: MOD名称
            status: 状态
            limit: 限制数量
            offset: 偏移量

        Returns:
            List[TranslationEntry]: 翻译条目列表
        """
        return self.find_by_mod(mod_name, status, limit, offset)

    def count_by_mod(self, mod_name: str, status: Optional[str] = None) -> int:
        """
        统计 MOD 的条目数

        Args:
            mod_name: MOD 名称
            status: 状态过滤 (可选)

        Returns:
            int: 条目数量
        """
        query = "SELECT COUNT(*) as count FROM translations WHERE mod_name = ?"
        params = [mod_name]

        if status:
            query += " AND status = ?"
            params.append(status)

        results = self.db.execute_query(query, tuple(params))
        return results[0]['count'] if results else 0

    def update_status(self, entry_id: int, status: str) -> bool:
        """
        更新条目状态

        Args:
            entry_id: 条目 ID
            status: 新状态

        Returns:
            bool: 是否成功
        """
        query = """
            UPDATE translations
            SET status = ?, updated_at = ?
            WHERE id = ?
        """
        rows = self.db.execute_update(
            query,
            (status, datetime.now().isoformat(), entry_id)
        )
        return rows > 0

    def update_translation(
        self,
        entry_id: int,
        translated_text: str,
        status: str = "completed"
    ) -> bool:
        """
        更新翻译文本

        Args:
            entry_id: 条目 ID
            translated_text: 译文
            status: 状态

        Returns:
            bool: 是否成功
        """
        query = """
            UPDATE translations
            SET translated_text = ?, status = ?, updated_at = ?
            WHERE id = ?
        """
        rows = self.db.execute_update(
            query,
            (translated_text, status, datetime.now().isoformat(), entry_id)
        )
        return rows > 0

    def delete_by_mod(self, mod_name: str) -> int:
        """
        删除 MOD 的所有条目

        Args:
            mod_name: MOD 名称

        Returns:
            int: 删除的条目数
        """
        query = "DELETE FROM translations WHERE mod_name = ?"
        return self.db.execute_update(query, (mod_name,))

    def get_all_mod_names(self) -> List[str]:
        """
        获取所有 MOD 名称列表

        Returns:
            List[str]: MOD 名称列表
        """
        query = "SELECT DISTINCT mod_name FROM translations ORDER BY mod_name"
        results = self.db.execute_query(query)
        return [row['mod_name'] for row in results]

    def get_statistics(self, mod_name: str) -> dict:
        """
        获取MOD翻译统计信息

        Args:
            mod_name: MOD名称

        Returns:
            dict: 统计信息
                - total: 总条目数
                - completed: 已完成数
                - pending: 待翻译数
                - skipped: 跳过数
        """
        query = """
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
                SUM(CASE WHEN status = 'skipped' THEN 1 ELSE 0 END) as skipped
            FROM translations
            WHERE mod_name = ?
        """
        results = self.db.execute_query(query, (mod_name,))

        if results:
            row = results[0]
            return {
                'total': row['total'] or 0,
                'completed': row['completed'] or 0,
                'pending': row['pending'] or 0,
                'skipped': row['skipped'] or 0
            }

        return {
            'total': 0,
            'completed': 0,
            'pending': 0,
            'skipped': 0
        }

    def _row_to_entry(self, row: dict) -> TranslationEntry:
        """
        将数据库行转换为 TranslationEntry

        Args:
            row: 数据库行

        Returns:
            TranslationEntry: 翻译条目
        """
        return TranslationEntry(
            id=row['id'],
            mod_name=row['mod_name'],
            file_path=row['file_path'],
            xml_path=row['xml_path'],
            original_text=row['original_text'],
            translated_text=row['translated_text'] or '',
            comment=row['comment'],
            status=row['status'],
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
            updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None
        )
