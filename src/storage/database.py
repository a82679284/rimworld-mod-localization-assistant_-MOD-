"""
数据库连接管理模块
"""
import sqlite3
from pathlib import Path
from typing import Optional
from contextlib import contextmanager
from ..utils.exceptions import DatabaseError


class Database:
    """SQLite 数据库管理"""

    def __init__(self, db_path: str = "data/translations.db"):
        """
        初始化数据库连接

        Args:
            db_path: 数据库文件路径
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._connection: Optional[sqlite3.Connection] = None
        self._initialize_schema()

    def _initialize_schema(self):
        """初始化数据库表结构"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # 翻译条目表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS translations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    mod_name TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    xml_path TEXT NOT NULL,
                    original_text TEXT NOT NULL,
                    translated_text TEXT DEFAULT '',
                    comment TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(mod_name, xml_path)
                )
            """)

            # 翻译记忆表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS translation_memory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_text TEXT NOT NULL,
                    target_text TEXT NOT NULL,
                    source_hash TEXT NOT NULL,
                    context TEXT,
                    use_count INTEGER DEFAULT 1,
                    last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(source_hash)
                )
            """)

            # 术语库表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS glossary (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    term_en TEXT NOT NULL UNIQUE,
                    term_zh TEXT NOT NULL,
                    category TEXT,
                    note TEXT,
                    priority INTEGER DEFAULT 0,
                    source TEXT DEFAULT 'user',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 会话表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS translation_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    mod_name TEXT NOT NULL UNIQUE,
                    mod_path TEXT NOT NULL,
                    total_entries INTEGER DEFAULT 0,
                    translated_entries INTEGER DEFAULT 0,
                    current_page INTEGER DEFAULT 0,
                    last_save TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 创建索引
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_translations_mod_name
                ON translations(mod_name)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_translations_status
                ON translations(status)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_tm_source_hash
                ON translation_memory(source_hash)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_glossary_term_en
                ON glossary(term_en)
            """)

            conn.commit()

    @contextmanager
    def get_connection(self):
        """
        获取数据库连接的上下文管理器

        Yields:
            sqlite3.Connection: 数据库连接
        """
        conn = None
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row  # 返回字典形式的结果
            yield conn
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            raise DatabaseError(f"数据库操作失败: {e}") from e
        finally:
            if conn:
                conn.close()

    def execute_query(self, query: str, params: tuple = ()) -> list:
        """
        执行查询语句

        Args:
            query: SQL 查询语句
            params: 参数元组

        Returns:
            list: 查询结果列表
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()

    def execute_update(self, query: str, params: tuple = ()) -> int:
        """
        执行更新语句

        Args:
            query: SQL 更新语句
            params: 参数元组

        Returns:
            int: 受影响的行数
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.rowcount

    def execute_many(self, query: str, params_list: list) -> int:
        """
        批量执行语句

        Args:
            query: SQL 语句
            params_list: 参数列表

        Returns:
            int: 受影响的行数
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(query, params_list)
            conn.commit()
            return cursor.rowcount

    def backup(self, backup_path: str):
        """
        备份数据库

        Args:
            backup_path: 备份文件路径
        """
        backup_file = Path(backup_path)
        backup_file.parent.mkdir(parents=True, exist_ok=True)

        with self.get_connection() as source_conn:
            backup_conn = sqlite3.connect(str(backup_file))
            source_conn.backup(backup_conn)
            backup_conn.close()

    def close(self):
        """关闭数据库连接"""
        if self._connection:
            self._connection.close()
            self._connection = None
