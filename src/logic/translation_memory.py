"""
翻译记忆业务逻辑层
"""
from typing import List, Optional, Dict
from ..data.translation_memory_repository import TranslationMemoryRepository
from ..data.glossary_repository import GlossaryRepository
from ..models.translation_entry import TranslationEntry


class TranslationMemoryLogic:
    """翻译记忆业务逻辑"""

    def __init__(
        self,
        memory_repo: TranslationMemoryRepository,
        glossary_repo: GlossaryRepository
    ):
        """
        初始化翻译记忆逻辑

        Args:
            memory_repo: 翻译记忆Repository
            glossary_repo: 术语库Repository
        """
        self.memory_repo = memory_repo
        self.glossary_repo = glossary_repo

    def find_translation(
        self,
        source_text: str,
        use_fuzzy: bool = True
    ) -> Optional[Dict[str, any]]:
        """
        查找翻译(先精确匹配,再模糊匹配)

        Args:
            source_text: 源文本
            use_fuzzy: 是否使用模糊匹配

        Returns:
            Optional[Dict]: 匹配结果
                {
                    'type': 'exact'|'fuzzy',
                    'translation': str,
                    'similarity': float (仅模糊匹配时有效)
                }
        """
        # 1. 精确匹配
        exact_match = self.memory_repo.find_exact_match(source_text)
        if exact_match:
            return {
                'type': 'exact',
                'translation': exact_match,
                'similarity': 1.0
            }

        # 2. 模糊匹配
        if use_fuzzy:
            similar_matches = self.memory_repo.find_similar_matches(source_text, limit=1)
            if similar_matches and similar_matches[0][2] >= 0.7:  # 相似度阈值 70%
                return {
                    'type': 'fuzzy',
                    'translation': similar_matches[0][1],
                    'similarity': similar_matches[0][2],
                    'source': similar_matches[0][0]
                }

        return None

    def save_translation(
        self,
        source_text: str,
        translated_text: str,
        context: str = None
    ) -> bool:
        """
        保存翻译到记忆库

        Args:
            source_text: 源文本
            translated_text: 翻译文本
            context: 上下文

        Returns:
            bool: 是否保存成功
        """
        try:
            self.memory_repo.save_translation(source_text, translated_text, context)
            return True
        except Exception:
            return False

    def batch_save_translations(
        self,
        entries: List[TranslationEntry]
    ) -> int:
        """
        批量保存翻译到记忆库

        Args:
            entries: 翻译条目列表

        Returns:
            int: 成功保存的数量
        """
        saved_count = 0
        for entry in entries:
            if entry.translated_text and entry.translated_text.strip():
                if self.save_translation(
                    entry.original_text,
                    entry.translated_text,
                    entry.xml_path
                ):
                    saved_count += 1

        return saved_count

    def get_suggestions(
        self,
        source_text: str,
        count: int = 5
    ) -> List[Dict[str, any]]:
        """
        获取翻译建议列表

        Args:
            source_text: 源文本
            count: 建议数量

        Returns:
            List[Dict]: 建议列表
                [{
                    'source': str,
                    'translation': str,
                    'similarity': float,
                    'source_type': 'memory'|'glossary'
                }]
        """
        suggestions = []

        # 1. 从翻译记忆获取
        similar_matches = self.memory_repo.find_similar_matches(source_text, limit=count)
        for src, tgt, sim in similar_matches:
            if sim >= 0.5:  # 相似度阈值 50%
                suggestions.append({
                    'source': src,
                    'translation': tgt,
                    'similarity': sim,
                    'source_type': 'memory'
                })

        # 2. 从术语库获取(如果源文本包含术语)
        try:
            glossary_terms = self.glossary_repo.get_all_terms()
            for term in glossary_terms:
                if term['term_en'].lower() in source_text.lower():
                    suggestions.append({
                        'source': term['term_en'],
                        'translation': term['term_zh'],
                        'similarity': 1.0,
                        'source_type': 'glossary'
                    })
        except Exception:
            pass

        # 按相似度排序
        suggestions.sort(key=lambda x: x['similarity'], reverse=True)
        return suggestions[:count]

    def apply_glossary_terms(
        self,
        text: str,
        auto_replace: bool = False
    ) -> Dict[str, any]:
        """
        应用术语库到文本

        Args:
            text: 待处理文本
            auto_replace: 是否自动替换

        Returns:
            Dict: {
                'text': str (替换后的文本,如果auto_replace=True),
                'terms_found': List[Dict] (找到的术语列表)
            }
        """
        result = {
            'text': text,
            'terms_found': []
        }

        try:
            # 获取所有术语,按优先级排序
            glossary_terms = self.glossary_repo.get_all_terms()
            glossary_terms.sort(key=lambda x: x.get('priority', 0), reverse=True)

            for term in glossary_terms:
                term_en = term['term_en']
                term_zh = term['term_zh']

                # 检查术语是否在文本中(忽略大小写)
                if term_en.lower() in text.lower():
                    result['terms_found'].append({
                        'en': term_en,
                        'zh': term_zh,
                        'category': term.get('category', ''),
                        'note': term.get('note', '')
                    })

                    # 自动替换
                    if auto_replace:
                        # 保持大小写匹配
                        import re
                        pattern = re.compile(re.escape(term_en), re.IGNORECASE)
                        result['text'] = pattern.sub(term_zh, result['text'])

        except Exception:
            pass

        return result

    def get_statistics(self) -> Dict[str, any]:
        """
        获取翻译记忆统计信息

        Returns:
            Dict: 统计信息
        """
        return self.memory_repo.get_memory_stats()

    def cleanup_old_entries(self, days: int = 365) -> int:
        """
        清理旧的翻译记忆条目

        Args:
            days: 保留天数

        Returns:
            int: 清理的条目数
        """
        return self.memory_repo.clear_old_entries(days)
