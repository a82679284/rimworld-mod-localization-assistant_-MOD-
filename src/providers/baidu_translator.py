"""
百度翻译器
"""
import requests
import hashlib
import random
import time
from typing import List, Dict, Optional
from .base import TranslationProvider


class BaiduTranslator(TranslationProvider):
    """百度翻译 API"""

    def __init__(self, config: Dict[str, any]):
        super().__init__(config)
        self.api_key = config.get('api_key', '')
        self.secret_key = config.get('secret_key', '')
        self.qps_limit = config.get('qps_limit', 10)
        self.api_url = 'https://fanyi-api.baidu.com/api/trans/vip/translate'

    def translate(
        self,
        text: str,
        source_lang: str = 'en',
        target_lang: str = 'zh'
    ) -> Optional[str]:
        if not self.is_available():
            return None

        try:
            # 百度API参数
            salt = str(random.randint(32768, 65536))
            sign = self._generate_sign(text, salt)

            params = {
                'q': text,
                'from': 'en',
                'to': 'zh',
                'appid': self.api_key,
                'salt': salt,
                'sign': sign
            }

            response = requests.get(self.api_url, params=params, timeout=10)

            if response.status_code == 200:
                result = response.json()
                if 'trans_result' in result:
                    return result['trans_result'][0]['dst']
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
            time.sleep(1.0 / self.qps_limit)  # QPS 限流
        return results

    def _generate_sign(self, query: str, salt: str) -> str:
        """生成百度API签名"""
        sign_str = f"{self.api_key}{query}{salt}{self.secret_key}"
        return hashlib.md5(sign_str.encode('utf-8')).hexdigest()

    def validate_config(self) -> bool:
        return (
            self.enabled and
            bool(self.api_key) and
            bool(self.secret_key) and
            self.api_key != 'YOUR_API_KEY'
        )

    def get_rate_limit(self) -> Dict[str, int]:
        return {'qps': self.qps_limit, 'daily': 2000000}  # 标准版每月200万字符

    def is_available(self) -> bool:
        return self.validate_config()
