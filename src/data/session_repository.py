"""
会话数据访问层
"""
from datetime import datetime
from typing import List, Optional, Dict
from ..storage.database import Database
from ..utils.exceptions import DatabaseError


class SessionRepository:
    """会话数据访问"""

    def __init__(self, db: Database):
        """
        初始化会话Repository

        Args:
            db: 数据库实例
        """
        self.db = db

    def create_or_update_session(
        self,
        mod_name: str,
        mod_path: str,
        total_entries: int = 0,
        translated_entries: int = 0,
        current_page: int = 0
    ) -> int:
        """
        创建或更新会话

        Args:
            mod_name: MOD名称
            mod_path: MOD路径
            total_entries: 总条目数
            translated_entries: 已翻译条目数
            current_page: 当前页码

        Returns:
            int: 会话ID
        """
        query = """
            INSERT INTO translation_sessions
            (mod_name, mod_path, total_entries, translated_entries, current_page, last_save)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(mod_name) DO UPDATE SET
                mod_path = excluded.mod_path,
                total_entries = excluded.total_entries,
                translated_entries = excluded.translated_entries,
                current_page = excluded.current_page,
                last_save = CURRENT_TIMESTAMP
        """

        try:
            self.db.execute_update(
                query,
                (mod_name, mod_path, total_entries, translated_entries, current_page)
            )

            # 获取会话ID
            result = self.db.execute_query(
                "SELECT id FROM translation_sessions WHERE mod_name = ?",
                (mod_name,)
            )
            return result[0]['id'] if result else 0
        except Exception as e:
            raise DatabaseError(f"保存会话失败: {e}") from e

    def get_session(self, mod_name: str) -> Optional[Dict]:
        """
        获取会话信息

        Args:
            mod_name: MOD名称

        Returns:
            Optional[Dict]: 会话信息
        """
        query = """
            SELECT * FROM translation_sessions WHERE mod_name = ?
        """

        try:
            result = self.db.execute_query(query, (mod_name,))
            if result:
                row = result[0]
                return {
                    'id': row['id'],
                    'mod_name': row['mod_name'],
                    'mod_path': row['mod_path'],
                    'total_entries': row['total_entries'],
                    'translated_entries': row['translated_entries'],
                    'current_page': row['current_page'],
                    'last_save': row['last_save'],
                    'created_at': row['created_at']
                }
            return None
        except Exception as e:
            raise DatabaseError(f"获取会话失败: {e}") from e

    def get_all_sessions(self) -> List[Dict]:
        """
        获取所有会话

        Returns:
            List[Dict]: 会话列表
        """
        query = """
            SELECT * FROM translation_sessions
            ORDER BY last_save DESC
        """

        try:
            results = self.db.execute_query(query)
            sessions = []
            for row in results:
                sessions.append({
                    'id': row['id'],
                    'mod_name': row['mod_name'],
                    'mod_path': row['mod_path'],
                    'total_entries': row['total_entries'],
                    'translated_entries': row['translated_entries'],
                    'current_page': row['current_page'],
                    'last_save': row['last_save'],
                    'progress_percent': round(
                        (row['translated_entries'] / row['total_entries'] * 100)
                        if row['total_entries'] > 0 else 0,
                        2
                    )
                })
            return sessions
        except Exception as e:
            raise DatabaseError(f"获取会话列表失败: {e}") from e

    def delete_session(self, mod_name: str) -> bool:
        """
        删除会话

        Args:
            mod_name: MOD名称

        Returns:
            bool: 是否删除成功
        """
        query = "DELETE FROM translation_sessions WHERE mod_name = ?"

        try:
            deleted = self.db.execute_update(query, (mod_name,))
            return deleted > 0
        except Exception as e:
            raise DatabaseError(f"删除会话失败: {e}") from e

    def has_active_session(self) -> bool:
        """检查是否有活动会话"""
        try:
            result = self.db.execute_query(
                "SELECT COUNT(*) as count FROM translation_sessions"
            )
            return result[0]['count'] > 0 if result else False
        except:
            return False

    def get_all_active(self) -> List[Dict]:
        """
        获取所有活动会话(与get_all_sessions相同)

        Returns:
            List[Dict]: 会话列表
        """
        return self.get_all_sessions()

    def update_or_create(
        self,
        mod_name: str,
        mod_path: str,
        total_entries: int = 0,
        translated_entries: int = 0,
        current_page: int = 0
    ) -> int:
        """
        更新或创建会话(与create_or_update_session相同,兼容旧代码)

        Args:
            mod_name: MOD名称
            mod_path: MOD路径
            total_entries: 总条目数
            translated_entries: 已翻译条目数
            current_page: 当前页码

        Returns:
            int: 会话ID
        """
        return self.create_or_update_session(
            mod_name, mod_path, total_entries, translated_entries, current_page
        )
