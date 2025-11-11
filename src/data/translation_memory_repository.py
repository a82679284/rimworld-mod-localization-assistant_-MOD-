"""
翻译记忆数据访问层
"""
import hashlib
from datetime import datetime
from typing import List, Optional, Tuple
from ..storage.database import Database
from ..models.translation_entry import TranslationEntry
from ..utils.exceptions import DatabaseError


class TranslationMemoryRepository:
    """翻译记忆数据访问"""

    def __init__(self, db: Database):
        """
        初始化翻译记忆Repository

        Args:
            db: 数据库实例
        """
        self.db = db

    def _calculate_hash(self, text: str) -> str:
        """
        计算文本的MD5哈希值

        Args:
            text: 源文本

        Returns:
            str: MD5哈希值
        """
        return hashlib.md5(text.encode('utf-8')).hexdigest()

    def save_translation(
        self,
        source_text: str,
        target_text: str,
        context: str = None
    ) -> int:
        """
        保存翻译到记忆库

        Args:
            source_text: 源文本
            target_text: 目标翻译
            context: 上下文信息

        Returns:
            int: 保存的记录ID
        """
        source_hash = self._calculate_hash(source_text)

        # 使用 UPSERT 语法(INSERT OR REPLACE)
        query = """
            INSERT INTO translation_memory
            (source_text, target_text, source_hash, context, use_count, last_used)
            VALUES (?, ?, ?, ?, 1, CURRENT_TIMESTAMP)
            ON CONFLICT(source_hash) DO UPDATE SET
                target_text = excluded.target_text,
                use_count = use_count + 1,
                last_used = CURRENT_TIMESTAMP
        """

        try:
            self.db.execute_update(query, (source_text, target_text, source_hash, context))

            # 获取插入或更新的记录ID
            result = self.db.execute_query(
                "SELECT id FROM translation_memory WHERE source_hash = ?",
                (source_hash,)
            )
            return result[0]['id'] if result else 0
        except Exception as e:
            raise DatabaseError(f"保存翻译记忆失败: {e}") from e

    def find_exact_match(self, source_text: str) -> Optional[str]:
        """
        查找精确匹配的翻译

        Args:
            source_text: 源文本

        Returns:
            Optional[str]: 匹配的翻译,如果没有则返回 None
        """
        source_hash = self._calculate_hash(source_text)

        query = """
            SELECT target_text FROM translation_memory
            WHERE source_hash = ?
        """

        try:
            result = self.db.execute_query(query, (source_hash,))
            if result:
                # 更新使用次数和时间
                self._update_usage(source_hash)
                return result[0]['target_text']
            return None
        except Exception as e:
            raise DatabaseError(f"查询翻译记忆失败: {e}") from e

    def find_similar_matches(
        self,
        source_text: str,
        limit: int = 5
    ) -> List[Tuple[str, str, float]]:
        """
        查找相似的翻译(模糊匹配)

        Args:
            source_text: 源文本
            limit: 返回结果数量限制

        Returns:
            List[Tuple[str, str, float]]: (源文本, 目标翻译, 相似度)列表
        """
        # 使用简单的子串匹配策略
        # 如果需要更精确的相似度计算,可以集成 FuzzyWuzzy 库
        query = """
            SELECT source_text, target_text
            FROM translation_memory
            WHERE source_text LIKE ?
            ORDER BY use_count DESC, last_used DESC
            LIMIT ?
        """

        try:
            # 使用模糊查询
            pattern = f"%{source_text[:20]}%"  # 使用前20个字符进行模糊匹配
            results = self.db.execute_query(query, (pattern, limit))

            # 计算简单的相似度(基于长度比)
            matches = []
            for row in results:
                src = row['source_text']
                tgt = row['target_text']

                # 简单的相似度计算:共同字符数 / 最大长度
                common_len = len(set(source_text) & set(src))
                max_len = max(len(source_text), len(src))
                similarity = common_len / max_len if max_len > 0 else 0

                matches.append((src, tgt, similarity))

            # 按相似度排序
            matches.sort(key=lambda x: x[2], reverse=True)
            return matches
        except Exception as e:
            raise DatabaseError(f"查询相似翻译失败: {e}") from e

    def _update_usage(self, source_hash: str):
        """
        更新翻译记忆的使用统计

        Args:
            source_hash: 源文本哈希值
        """
        query = """
            UPDATE translation_memory
            SET use_count = use_count + 1,
                last_used = CURRENT_TIMESTAMP
            WHERE source_hash = ?
        """
        try:
            self.db.execute_update(query, (source_hash,))
        except Exception:
            # 更新失败不影响主流程
            pass

    def get_memory_stats(self) -> dict:
        """
        获取翻译记忆统计信息

        Returns:
            dict: 统计信息
        """
        query = """
            SELECT
                COUNT(*) as total_entries,
                SUM(use_count) as total_uses,
                AVG(use_count) as avg_uses
            FROM translation_memory
        """

        try:
            result = self.db.execute_query(query)
            if result:
                return {
                    'total_entries': result[0]['total_entries'] or 0,
                    'total_uses': result[0]['total_uses'] or 0,
                    'avg_uses': round(result[0]['avg_uses'] or 0, 2)
                }
            return {'total_entries': 0, 'total_uses': 0, 'avg_uses': 0}
        except Exception as e:
            raise DatabaseError(f"获取统计信息失败: {e}") from e

    def clear_old_entries(self, days: int = 365):
        """
        清理超过指定天数未使用的记忆条目

        Args:
            days: 保留天数
        """
        query = """
            DELETE FROM translation_memory
            WHERE julianday('now') - julianday(last_used) > ?
        """

        try:
            deleted = self.db.execute_update(query, (days,))
            return deleted
        except Exception as e:
            raise DatabaseError(f"清理旧记录失败: {e}") from e
