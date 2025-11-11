"""
Ollama 本地翻译器
"""
import requests
from typing import List, Dict, Optional
from .base import TranslationProvider


class OllamaTranslator(TranslationProvider):
    """Ollama 本地 AI 翻译器"""

    def __init__(self, config: Dict[str, any]):
        super().__init__(config)
        self.base_url = config.get('base_url', 'http://localhost:11434')
        self.model = config.get('model', 'qwen2.5:7b')
        self.timeout = config.get('timeout', 60)

    def translate(
        self,
        text: str,
        source_lang: str = 'en',
        target_lang: str = 'zh'
    ) -> Optional[str]:
        if not self.is_available():
            return None

        try:
            prompt = f"""请将以下英文游戏文本翻译成简体中文,只返回翻译结果:

原文: {text}

翻译:"""

            payload = {
                'model': self.model,
                'prompt': prompt,
                'stream': False
            }

            response = requests.post(
                f'{self.base_url}/api/generate',
                json=payload,
                timeout=self.timeout
            )

            if response.status_code == 200:
                result = response.json()
                return result['response'].strip()
            return None

        except Exception as e:
            print(self.handle_error(e))
            return None

    def batch_translate(
        self,
        texts: List[str],
        source_lang: str = 'en',
        target_lang: str = 'zh'
    ) -> List[Optional[str]]:
        results = []
        for text in texts:
            result = self.translate(text, source_lang, target_lang)
            results.append(result)
        return results

    def validate_config(self) -> bool:
        """验证 Ollama 服务是否可用"""
        try:
            response = requests.get(f'{self.base_url}/api/tags', timeout=5)
            return response.status_code == 200
        except:
            return False

    def get_rate_limit(self) -> Dict[str, int]:
        return {'qps': 999, 'daily': 999999}  # 本地无限制

    def is_available(self) -> bool:
        return self.enabled and self.validate_config()
