"""
MOD 列表数据访问层
"""
from datetime import datetime
from typing import List, Optional, Dict
from ..storage.database import Database


class ModListRepository:
    """MOD 列表数据库操作"""

    def __init__(self, database: Database):
        """
        初始化 Repository

        Args:
            database: 数据库实例
        """
        self.db = database

    def add_mod(self, mod_name: str, mod_path: str, root_path: Optional[str] = None) -> int:
        """
        添加 MOD 到列表

        Args:
            mod_name: MOD 名称
            mod_path: MOD 路径
            root_path: MOD 管理根目录路径

        Returns:
            int: MOD ID
        """
        query = """
            INSERT OR REPLACE INTO mod_list (mod_name, mod_path, root_path, added_at, last_accessed)
            VALUES (?, ?, ?, ?, ?)
        """
        params = (
            mod_name,
            mod_path,
            root_path,
            datetime.now().isoformat(),
            datetime.now().isoformat()
        )

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.lastrowid

    def get_all_mods(self) -> List[Dict]:
        """
        获取所有 MOD

        Returns:
            List[Dict]: MOD 列表
        """
        query = """
            SELECT id, mod_name, mod_path, root_path, added_at, last_accessed
            FROM mod_list
            ORDER BY last_accessed DESC
        """

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()

            return [
                {
                    'id': row['id'],
                    'mod_name': row['mod_name'],
                    'mod_path': row['mod_path'],
                    'root_path': row['root_path'],
                    'added_at': row['added_at'],
                    'last_accessed': row['last_accessed']
                }
                for row in rows
            ]

    def get_mod_by_name(self, mod_name: str) -> Optional[Dict]:
        """
        根据名称获取 MOD

        Args:
            mod_name: MOD 名称

        Returns:
            Optional[Dict]: MOD 信息
        """
        query = """
            SELECT id, mod_name, mod_path, root_path, added_at, last_accessed
            FROM mod_list
            WHERE mod_name = ?
        """

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (mod_name,))
            row = cursor.fetchone()

            if row:
                return {
                    'id': row['id'],
                    'mod_name': row['mod_name'],
                    'mod_path': row['mod_path'],
                    'root_path': row['root_path'],
                    'added_at': row['added_at'],
                    'last_accessed': row['last_accessed']
                }
            return None

    def update_last_accessed(self, mod_name: str):
        """
        更新 MOD 最后访问时间

        Args:
            mod_name: MOD 名称
        """
        query = """
            UPDATE mod_list
            SET last_accessed = ?
            WHERE mod_name = ?
        """
        params = (datetime.now().isoformat(), mod_name)

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()

    def remove_mod(self, mod_name: str) -> bool:
        """
        从列表中移除 MOD

        Args:
            mod_name: MOD 名称

        Returns:
            bool: 是否成功移除
        """
        query = "DELETE FROM mod_list WHERE mod_name = ?"

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (mod_name,))
            conn.commit()
            return cursor.rowcount > 0

    def clear_all(self):
        """清空所有 MOD 列表"""
        query = "DELETE FROM mod_list"

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            conn.commit()

    def count_all(self) -> int:
        """
        获取 MOD 总数

        Returns:
            int: MOD 总数
        """
        query = "SELECT COUNT(*) as count FROM mod_list"

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            row = cursor.fetchone()
            return row['count'] if row else 0
