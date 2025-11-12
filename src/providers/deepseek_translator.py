"""
DeepSeek 翻译器
使用 DeepSeek API 进行翻译(OpenAI 兼容格式)
"""
import requests
import time
from typing import List, Dict, Optional
from .base import TranslationProvider


class DeepSeekTranslator(TranslationProvider):
    """DeepSeek AI 翻译器"""

    def __init__(self, config: Dict[str, any], glossary_repo=None):
        """
        初始化 DeepSeek 翻译器

        Args:
            config: 配置字典,包含 api_key, base_url, model
            glossary_repo: 术语库仓库(可选),用于提供术语参考
        """
        super().__init__(config)
        self.api_key = config.get('api_key', '')
        self.base_url = config.get('base_url', 'https://api.deepseek.com/v1')
        self.model = config.get('model', 'deepseek-chat')
        self.timeout = config.get('timeout', 30)
        self.glossary_repo = glossary_repo

    def translate(
        self,
        text: str,
        source_lang: str = 'en',
        target_lang: str = 'zh'
    ) -> Optional[str]:
        """
        翻译单个文本

        Args:
            text: 待翻译文本
            source_lang: 源语言代码
            target_lang: 目标语言代码

        Returns:
            Optional[str]: 翻译结果
        """
        if not self.is_available():
            return None

        try:
            # 构建翻译 prompt
            prompt = self._build_translation_prompt(text, source_lang, target_lang)

            # 调用 DeepSeek API
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }

            payload = {
                'model': self.model,
                'messages': [
                    {
                        'role': 'system',
                        'content': '你是一个专业的游戏本地化翻译专家,擅长将英文游戏内容翻译成简洁准确的中文。'
                    },
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                'temperature': 0.3,  # 降低温度以获得更稳定的翻译
                'max_tokens': 1000
            }

            response = requests.post(
                f'{self.base_url}/chat/completions',
                headers=headers,
                json=payload,
                timeout=self.timeout
            )

            if response.status_code == 200:
                result = response.json()
                translation = result['choices'][0]['message']['content'].strip()
                return self._extract_translation(translation)
            else:
                print(f"DeepSeek API 错误: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            print(self.handle_error(e))
            return None

    def batch_translate(
        self,
        texts: List[str],
        source_lang: str = 'en',
        target_lang: str = 'zh',
        batch_size: int = 10,
        delay: float = 0.5
    ) -> List[Optional[str]]:
        """
        批量翻译文本

        Args:
            texts: 待翻译文本列表
            source_lang: 源语言代码
            target_lang: 目标语言代码
            batch_size: 每批处理的数量
            delay: 批次间延迟(秒)

        Returns:
            List[Optional[str]]: 翻译结果列表
        """
        results = []

        # 分批处理
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]

            # 批量翻译
            batch_prompt = self._build_batch_translation_prompt(
                batch,
                source_lang,
                target_lang
            )

            try:
                translation = self.translate(batch_prompt, source_lang, target_lang)
                if translation:
                    # 解析批量翻译结果
                    batch_results = self._parse_batch_translation(translation, len(batch))
                    results.extend(batch_results)
                else:
                    # 翻译失败,逐个重试
                    for text in batch:
                        result = self.translate(text, source_lang, target_lang)
                        results.append(result)
                        time.sleep(0.2)  # 短暂延迟

            except Exception as e:
                print(f"批量翻译失败: {e}")
                # 逐个重试
                for text in batch:
                    result = self.translate(text, source_lang, target_lang)
                    results.append(result)
                    time.sleep(0.2)

            # 批次间延迟
            if i + batch_size < len(texts):
                time.sleep(delay)

        return results

    def _build_translation_prompt(
        self,
        text: str,
        source_lang: str,
        target_lang: str
    ) -> str:
        """构建翻译 prompt,包含术语库参考"""
        lang_names = {
            'en': '英文',
            'zh': '简体中文'
        }

        # 查询相关术语
        glossary_hint = ""
        if self.glossary_repo:
            try:
                words = text.split()
                terms = []
                seen_terms = set()

                for word in words:
                    # 跳过太短的词
                    if len(word) < 3:
                        continue

                    # 移除标点符号
                    clean_word = word.strip('.,!?;:()"\'')
                    if not clean_word:
                        continue

                    # 查询术语库
                    matches = self.glossary_repo.search_terms(clean_word)
                    if matches:
                        for match in matches[:2]:  # 每个词最多2个匹配
                            term_key = (match.term_en, match.term_zh)
                            if term_key not in seen_terms:
                                seen_terms.add(term_key)
                                terms.append(f"  - {match.term_en} → {match.term_zh}")

                            # 限制总数
                            if len(terms) >= 5:
                                break

                    if len(terms) >= 5:
                        break

                if terms:
                    glossary_hint = "\n\n术语参考(优先使用):\n" + "\n".join(terms)

            except Exception as e:
                # 术语库查询失败不影响翻译
                print(f"术语库查询失败: {e}")

        return f"""请将以下{lang_names.get(source_lang, source_lang)}游戏文本翻译成{lang_names.get(target_lang, target_lang)}:

原文: {text}{glossary_hint}

翻译要求:
1. **优先使用上述术语参考中的翻译**
2. 保持游戏术语的准确性和一致性
3. 语言简洁流畅,符合中文表达习惯
4. 保留原文中的格式标记(如括号、引号等)
5. 只返回翻译结果,不要添加解释

翻译:"""

    def _build_batch_translation_prompt(
        self,
        texts: List[str],
        source_lang: str,
        target_lang: str
    ) -> str:
        """构建批量翻译 prompt"""
        lang_names = {
            'en': '英文',
            'zh': '简体中文'
        }

        texts_str = '\n'.join([f"{i+1}. {text}" for i, text in enumerate(texts)])

        return f"""请将以下{lang_names.get(source_lang, source_lang)}游戏文本批量翻译成{lang_names.get(target_lang, target_lang)}:

{texts_str}

翻译要求:
1. 保持游戏术语的准确性和一致性
2. 语言简洁流畅,符合中文表达习惯
3. 保留原文中的格式标记
4. 按原序号输出翻译结果,每行一个

翻译:"""

    def _extract_translation(self, response: str) -> str:
        """从 API 响应中提取翻译结果"""
        # 移除可能的标签和说明
        lines = response.split('\n')
        for line in lines:
            line = line.strip()
            if line and not line.startswith(('翻译:', 'Translation:', '原文:')):
                return line
        return response.strip()

    def _parse_batch_translation(
        self,
        translation: str,
        expected_count: int
    ) -> List[str]:
        """解析批量翻译结果"""
        results = []
        lines = translation.split('\n')

        for line in lines:
            line = line.strip()
            if line:
                # 移除序号
                if line[0].isdigit() and '.' in line[:5]:
                    line = line.split('.', 1)[1].strip()
                results.append(line)

        # 确保结果数量正确
        while len(results) < expected_count:
            results.append(None)

        return results[:expected_count]

    def validate_config(self) -> bool:
        """验证配置"""
        return (
            self.enabled and
            bool(self.api_key) and
            self.api_key not in ('YOUR_API_KEY', 'YOUR_DEEPSEEK_API_KEY_HERE') and
            len(self.api_key) > 10
        )

    def get_rate_limit(self) -> Dict[str, int]:
        """获取速率限制"""
        return {
            'qps': 10,  # 每秒10个请求
            'daily': 100000  # 每日限制(根据实际套餐)
        }

    def is_available(self) -> bool:
        """检查服务是否可用"""
        return self.validate_config()
