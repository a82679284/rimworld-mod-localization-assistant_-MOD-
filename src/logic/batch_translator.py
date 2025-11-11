"""
批量翻译业务逻辑层
"""
from typing import List, Optional, Dict
from ..models.translation_entry import TranslationEntry
from ..providers.base import TranslationProvider
from ..providers.deepseek_translator import DeepSeekTranslator
from ..providers.baidu_translator import BaiduTranslator
from ..providers.ollama_translator import OllamaTranslator
from ..logic.translation_memory import TranslationMemoryLogic
from ..utils.config import Config


class BatchTranslatorLogic:
    """批量翻译业务逻辑"""

    def __init__(
        self,
        config: Config,
        translation_memory: Optional[TranslationMemoryLogic] = None
    ):
        """
        初始化批量翻译器

        Args:
            config: 配置对象
            translation_memory: 翻译记忆逻辑(可选)
        """
        self.config = config
        self.translation_memory = translation_memory
        self.providers: Dict[str, TranslationProvider] = {}
        self._initialize_providers()

    def _initialize_providers(self):
        """初始化所有翻译提供商"""
        provider_config = self.config.get_translation_config()

        # 注册所有支持的翻译器
        provider_classes = {
            'deepseek': DeepSeekTranslator,
            'baidu': BaiduTranslator,
            'ollama': OllamaTranslator
        }

        for name, provider_class in provider_classes.items():
            if name in provider_config.get('providers', {}):
                config_dict = provider_config['providers'][name]
                try:
                    provider = provider_class(config_dict)
                    if provider.is_available():
                        self.providers[name] = provider
                        print(f"✓ {name.capitalize()} 翻译器已加载")
                    else:
                        print(f"✗ {name.capitalize()} 翻译器不可用 (请检查配置)")
                except Exception as e:
                    print(f"✗ {name.capitalize()} 翻译器初始化失败: {e}")

    def get_available_providers(self) -> List[str]:
        """获取可用的翻译提供商列表"""
        return list(self.providers.keys())

    def batch_translate(
        self,
        entries: List[TranslationEntry],
        provider_name: Optional[str] = None,
        use_memory: bool = True,
        progress_callback: Optional[callable] = None
    ) -> Dict[str, any]:
        """
        批量翻译条目

        Args:
            entries: 翻译条目列表
            provider_name: 指定的翻译提供商,None 则使用默认
            use_memory: 是否使用翻译记忆
            progress_callback: 进度回调函数 callback(current, total, entry)

        Returns:
            Dict: {
                'success_count': int,
                'failed_count': int,
                'memory_hit_count': int,
                'results': List[TranslationEntry]
            }
        """
        # 选择翻译提供商
        if not provider_name:
            provider_name = self.config.get_translation_config().get('default_provider', 'deepseek')

        provider = self.providers.get(provider_name)
        if not provider:
            print(f"错误: 翻译提供商 '{provider_name}' 不可用")
            return {
                'success_count': 0,
                'failed_count': len(entries),
                'memory_hit_count': 0,
                'results': entries
            }

        success_count = 0
        failed_count = 0
        memory_hit_count = 0

        # 批量处理
        for i, entry in enumerate(entries):
            # 跳过已翻译的条目
            if entry.translated_text and entry.translated_text.strip():
                # 确保状态正确
                if entry.status != 'completed':
                    entry.status = 'completed'
                success_count += 1
                if progress_callback:
                    progress_callback(i + 1, len(entries), entry)
                continue

            # 1. 尝试从翻译记忆获取
            if use_memory and self.translation_memory:
                match = self.translation_memory.find_translation(entry.original_text)
                if match and match['type'] == 'exact':
                    entry.translated_text = match['translation']
                    entry.status = 'completed'  # 设置状态为已完成
                    memory_hit_count += 1
                    success_count += 1
                    if progress_callback:
                        progress_callback(i + 1, len(entries), entry)
                    continue

            # 2. 使用 API 翻译
            try:
                translation = provider.translate(entry.original_text)
                if translation:
                    entry.translated_text = translation
                    entry.status = 'completed'
                    success_count += 1

                    # 保存到翻译记忆
                    if self.translation_memory:
                        self.translation_memory.save_translation(
                            entry.original_text,
                            translation,
                            entry.xml_path
                        )
                else:
                    entry.status = 'failed'
                    failed_count += 1

            except Exception as e:
                print(f"翻译失败: {entry.original_text[:30]}... - {e}")
                entry.status = 'failed'
                failed_count += 1

            # 进度回调
            if progress_callback:
                progress_callback(i + 1, len(entries), entry)

        return {
            'success_count': success_count,
            'failed_count': failed_count,
            'memory_hit_count': memory_hit_count,
            'results': entries
        }

    def translate_single(
        self,
        text: str,
        provider_name: Optional[str] = None,
        use_memory: bool = True
    ) -> Optional[str]:
        """
        翻译单个文本

        Args:
            text: 待翻译文本
            provider_name: 翻译提供商名称
            use_memory: 是否使用翻译记忆

        Returns:
            Optional[str]: 翻译结果
        """
        # 1. 尝试从翻译记忆获取
        if use_memory and self.translation_memory:
            match = self.translation_memory.find_translation(text)
            if match:
                return match['translation']

        # 2. 使用 API 翻译
        if not provider_name:
            provider_name = self.config.get_translation_config().get('default_provider', 'deepseek')

        provider = self.providers.get(provider_name)
        if not provider:
            return None

        try:
            translation = provider.translate(text)
            if translation and self.translation_memory:
                self.translation_memory.save_translation(text, translation)
            return translation
        except Exception as e:
            print(f"翻译失败: {e}")
            return None

    def get_provider_info(self, provider_name: str) -> Optional[Dict[str, any]]:
        """
        获取翻译提供商信息

        Args:
            provider_name: 提供商名称

        Returns:
            Optional[Dict]: 提供商信息
        """
        provider = self.providers.get(provider_name)
        if not provider:
            return None

        return {
            'name': provider.get_provider_name(),
            'available': provider.is_available(),
            'rate_limit': provider.get_rate_limit()
        }
