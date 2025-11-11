"""
官方翻译加载器
从Rimworld游戏目录加载官方翻译作为参考
"""
from pathlib import Path
from typing import Dict, List, Optional
from lxml import etree
from ..utils.exceptions import FileAccessError


class OfficialTranslationLoader:
    """官方翻译加载器"""

    def __init__(self, rimworld_path: Optional[str] = None):
        """
        初始化官方翻译加载器

        Args:
            rimworld_path: Rimworld游戏安装路径
        """
        self.rimworld_path = Path(rimworld_path) if rimworld_path else None
        self.official_translations: Dict[str, str] = {}

    def set_rimworld_path(self, path: str):
        """
        设置Rimworld路径

        Args:
            path: 游戏安装路径
        """
        self.rimworld_path = Path(path)

    def load_official_translations(
        self,
        include_dlc: bool = True
    ) -> Dict[str, str]:
        """
        加载官方翻译

        Args:
            include_dlc: 是否包含DLC翻译

        Returns:
            Dict[str, str]: xml_path -> 中文翻译 的映射字典
        """
        if not self.rimworld_path or not self.rimworld_path.exists():
            print("错误: Rimworld路径未设置或不存在")
            return {}

        self.official_translations = {}

        # 加载核心翻译
        core_path = self.rimworld_path / 'Data' / 'Core' / 'Languages'
        self._load_from_directory(core_path)

        # 加载 DLC 翻译
        if include_dlc:
            dlc_names = ['Royalty', 'Ideology', 'Biotech', 'Anomaly', 'Odyssey']
            for dlc in dlc_names:
                dlc_path = self.rimworld_path / 'Data' / dlc / 'Languages'
                if dlc_path.exists():
                    self._load_from_directory(dlc_path)

        print(f"✓ 加载了 {len(self.official_translations)} 条官方翻译")
        return self.official_translations

    def _load_from_directory(self, languages_dir: Path):
        """
        从Languages目录加载翻译

        Args:
            languages_dir: Languages目录路径
        """
        if not languages_dir.exists():
            return

        english_dir = languages_dir / 'English'
        chinese_dir = languages_dir / 'ChineseSimplified'

        if not english_dir.exists() or not chinese_dir.exists():
            return

        # 扫描English目录获取文件结构
        for category in ['DefInjected', 'Keyed', 'Strings']:
            en_category_dir = english_dir / category
            zh_category_dir = chinese_dir / category

            if not en_category_dir.exists() or not zh_category_dir.exists():
                continue

            # 遍历所有XML文件
            for en_file in en_category_dir.rglob('*.xml'):
                # 计算相对路径
                rel_path = en_file.relative_to(en_category_dir)
                zh_file = zh_category_dir / rel_path

                if zh_file.exists():
                    self._parse_translation_pair(en_file, zh_file)

    def _parse_translation_pair(self, en_file: Path, zh_file: Path):
        """
        解析英文和中文翻译文件对

        Args:
            en_file: 英文文件路径
            zh_file: 中文文件路径
        """
        try:
            # 解析英文文件
            en_tree = etree.parse(str(en_file))
            en_root = en_tree.getroot()

            # 解析中文文件
            zh_tree = etree.parse(str(zh_file))
            zh_root = zh_tree.getroot()

            # 建立映射
            zh_dict = {}
            for zh_elem in zh_root:
                zh_dict[zh_elem.tag] = zh_elem.text or ''

            # 匹配英文和中文
            for en_elem in en_root:
                key = en_elem.tag
                if key in zh_dict:
                    self.official_translations[key] = zh_dict[key]

        except Exception as e:
            # 解析失败不影响其他文件
            pass

    def get_suggestion(self, xml_path: str) -> Optional[str]:
        """
        根据XML路径获取官方翻译建议

        Args:
            xml_path: XML节点路径,如 "Beer.label"

        Returns:
            Optional[str]: 官方翻译,没有则返回None
        """
        return self.official_translations.get(xml_path)

    def get_all_suggestions(
        self,
        xml_paths: List[str]
    ) -> Dict[str, str]:
        """
        批量获取翻译建议

        Args:
            xml_paths: XML路径列表

        Returns:
            Dict[str, str]: 找到的翻译映射
        """
        suggestions = {}
        for path in xml_paths:
            if path in self.official_translations:
                suggestions[path] = self.official_translations[path]
        return suggestions

    def is_loaded(self) -> bool:
        """检查是否已加载官方翻译"""
        return len(self.official_translations) > 0

    def get_stats(self) -> Dict[str, int]:
        """获取统计信息"""
        return {
            'total_translations': len(self.official_translations)
        }
