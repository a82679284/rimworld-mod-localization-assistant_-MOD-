"""
配置管理模块
"""
import json
from pathlib import Path
from typing import Dict, Any, Optional
from ..utils.exceptions import ConfigurationError


class Config:
    """配置管理器"""

    def __init__(self, config_path: str = "config/translation_api.json"):
        """
        初始化配置管理器

        Args:
            config_path: 配置文件路径
        """
        self.config_path = Path(config_path)
        self._config: Dict[str, Any] = {}
        self._load_config()

    def _load_config(self):
        """加载配置文件"""
        if not self.config_path.exists():
            # 如果配置文件不存在,尝试从模板复制
            template_path = self.config_path.with_suffix('.json.template')
            if template_path.exists():
                import shutil
                shutil.copy(str(template_path), str(self.config_path))
            else:
                raise ConfigurationError(f"配置文件不存在: {self.config_path}")

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self._config = json.load(f)
        except json.JSONDecodeError as e:
            raise ConfigurationError(f"配置文件格式错误: {e}") from e

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置项

        Args:
            key: 配置键 (支持点号分隔的嵌套键,如 "providers.baidu.api_key")
            default: 默认值

        Returns:
            Any: 配置值
        """
        keys = key.split('.')
        value = self._config

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default

        return value if value is not None else default

    def set(self, key: str, value: Any):
        """
        设置配置项

        Args:
            key: 配置键 (支持点号分隔的嵌套键)
            value: 配置值
        """
        keys = key.split('.')
        config = self._config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value

    def save(self):
        """保存配置到文件"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
        except IOError as e:
            raise ConfigurationError(f"配置文件保存失败: {e}") from e

    def get_provider_config(self, provider: str) -> Optional[Dict[str, Any]]:
        """
        获取翻译提供商配置

        Args:
            provider: 提供商名称 (baidu, youdao, google, deepl, ollama)

        Returns:
            Optional[Dict[str, Any]]: 提供商配置
        """
        return self.get(f"providers.{provider}")

    def is_provider_enabled(self, provider: str) -> bool:
        """
        检查翻译提供商是否启用

        Args:
            provider: 提供商名称

        Returns:
            bool: 是否启用
        """
        config = self.get_provider_config(provider)
        return config.get('enabled', False) if config else False

    def get_rimworld_path(self) -> Optional[str]:
        """
        获取 Rimworld 游戏路径

        Returns:
            Optional[str]: 游戏路径
        """
        return self.get('rimworld_path')

    def set_rimworld_path(self, path: str):
        """
        设置 Rimworld 游戏路径

        Args:
            path: 游戏路径
        """
        self.set('rimworld_path', path)
        self.save()

    def get_auto_save_interval(self) -> int:
        """
        获取自动保存间隔(秒)

        Returns:
            int: 自动保存间隔
        """
        return self.get('auto_save_interval', 30)

    def get_page_size(self) -> int:
        """
        获取每页显示条目数

        Returns:
            int: 每页条目数
        """
        return self.get('page_size', 100)

    def get_translation_config(self) -> Dict[str, Any]:
        """
        获取完整的翻译配置

        Returns:
            Dict[str, Any]: 翻译配置字典
        """
        return self._config

    def get_default_provider(self) -> str:
        """
        获取默认翻译提供商

        Returns:
            str: 默认提供商名称
        """
        return self.get('default_provider', 'deepseek')

    def save_translation_config(self, config_data: Dict[str, Any]):
        """
        保存完整的翻译配置

        Args:
            config_data: 完整的配置字典
        """
        self._config = config_data
        self.save()

    def get_available_providers(self) -> list:
        """
        获取所有已启用的翻译提供商列表

        Returns:
            list: 提供商名称列表
        """
        providers = []
        providers_config = self.get('providers', {})

        for provider, config in providers_config.items():
            if config.get('enabled', False):
                providers.append(provider)

        return providers
