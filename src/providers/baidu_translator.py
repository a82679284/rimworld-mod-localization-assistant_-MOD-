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

        if not text or not text.strip():
            return None

        try:
            # 百度API参数
            salt = str(random.randint(32768, 65536))
            sign = self._generate_sign(text, salt)

            # 转换语言代码格式
            from_lang = self._convert_lang_code(source_lang)
            to_lang = self._convert_lang_code(target_lang)

            params = {
                'q': text,
                'from': from_lang,
                'to': to_lang,
                'appid': self.api_key,
                'salt': salt,
                'sign': sign
            }

            response = requests.get(self.api_url, params=params, timeout=10)

            if response.status_code == 200:
                result = response.json()

                # 检查错误码
                if 'error_code' in result:
                    error_code = result['error_code']
                    error_msg = result.get('error_msg', '未知错误')
                    print(f"百度翻译API错误 [{error_code}]: {error_msg}")
                    return None

                # 返回翻译结果
                if 'trans_result' in result and len(result['trans_result']) > 0:
                    return result['trans_result'][0]['dst']

            else:
                print(f"百度翻译HTTP错误: {response.status_code}")

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
        """
        生成百度API签名

        签名生成规则: MD5(appid+q+salt+密钥)
        注意: q需要是UTF-8编码
        """
        sign_str = f"{self.api_key}{query}{salt}{self.secret_key}"
        return hashlib.md5(sign_str.encode('utf-8')).hexdigest()

    def _convert_lang_code(self, lang_code: str) -> str:
        """
        转换语言代码为百度翻译API格式

        Args:
            lang_code: 通用语言代码

        Returns:
            str: 百度翻译API语言代码
        """
        # 语言代码映射表
        lang_map = {
            'en': 'en',      # 英语
            'zh': 'zh',      # 中文
            'auto': 'auto',  # 自动检测
            'jp': 'jp',      # 日语
            'kor': 'kor',    # 韩语
            'fra': 'fra',    # 法语
            'spa': 'spa',    # 西班牙语
            'de': 'de',      # 德语
            'ru': 'ru',      # 俄语
        }

        return lang_map.get(lang_code.lower(), lang_code)

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
