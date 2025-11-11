"""
翻译提供商基类
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional


class TranslationProvider(ABC):
    """翻译提供商抽象基类"""

    def __init__(self, config: Dict[str, any]):
        """
        初始化翻译提供商

        Args:
            config: 配置字典
        """
        self.config = config
        self.enabled = config.get('enabled', False)

    @abstractmethod
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
            Optional[str]: 翻译结果,失败返回 None
        """
        pass

    @abstractmethod
    def batch_translate(
        self,
        texts: List[str],
        source_lang: str = 'en',
        target_lang: str = 'zh'
    ) -> List[Optional[str]]:
        """
        批量翻译文本

        Args:
            texts: 待翻译文本列表
            source_lang: 源语言代码
            target_lang: 目标语言代码

        Returns:
            List[Optional[str]]: 翻译结果列表,失败的位置为 None
        """
        pass

    def is_available(self) -> bool:
        """
        检查翻译服务是否可用

        Returns:
            bool: 是否可用
        """
        return self.enabled

    def get_provider_name(self) -> str:
        """
        获取提供商名称

        Returns:
            str: 提供商名称
        """
        return self.__class__.__name__.replace('Translator', '')

    def validate_config(self) -> bool:
        """
        验证配置是否有效

        Returns:
            bool: 配置是否有效
        """
        return self.enabled

    @abstractmethod
    def get_rate_limit(self) -> Dict[str, int]:
        """
        获取速率限制信息

        Returns:
            Dict[str, int]: {'qps': 每秒查询数, 'daily': 每日查询数}
        """
        pass

    def handle_error(self, error: Exception) -> str:
        """
        处理翻译错误

        Args:
            error: 异常对象

        Returns:
            str: 错误信息
        """
        return f"{self.get_provider_name()} 翻译失败: {str(error)}"
