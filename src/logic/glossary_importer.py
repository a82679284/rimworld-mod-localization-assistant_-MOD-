"""
术语库导入器 - 从Rimworld官方文件导入术语
"""
import xml.etree.ElementTree as ET
import tarfile
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Optional
from ..models.glossary_entry import GlossaryEntry
from ..data.glossary_repository import GlossaryRepository


class GlossaryImporter:
    """术语库导入器"""

    def __init__(self, glossary_repo: GlossaryRepository):
        """
        初始化导入器

        Args:
            glossary_repo: 术语库Repository
        """
        self.glossary_repo = glossary_repo

    def import_from_rimworld(
        self,
        game_path: Path,
        categories: Optional[List[str]] = None
    ) -> Dict[str, int]:
        """
        从Rimworld游戏目录导入官方术语

        Args:
            game_path: Rimworld游戏根目录
            categories: 要导入的分类列表(None=全部)

        Returns:
            Dict: 导入结果统计
                {
                    'total': 总导入数,
                    'success': 成功数,
                    'failed': 失败数,
                    'categories': {分类: 数量}
                }
        """
        result = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'categories': {}
        }

        # 自动扫描 Data 目录下的所有子文件夹
        data_path = game_path / "Data"
        if not data_path.exists():
            print(f"Data 目录不存在: {data_path}")
            return result

        # 遍历 Data 目录下的所有子文件夹
        for data_dir in data_path.iterdir():
            if not data_dir.is_dir():
                continue

            # 检查是否包含 Languages 文件夹
            languages_dir = data_dir / "Languages"
            if not languages_dir.exists():
                continue

            print(f"正在扫描: {data_dir.name}")

            # 尝试从目录导入
            dir_result = self._import_from_data_dir(data_dir, categories)
            result['total'] += dir_result['total']
            result['success'] += dir_result['success']
            result['failed'] += dir_result['failed']
            for cat, count in dir_result['categories'].items():
                result['categories'][cat] = result['categories'].get(cat, 0) + count

        return result

    def _import_from_data_dir(
        self,
        data_dir: Path,
        categories: Optional[List[str]] = None
    ) -> Dict[str, int]:
        """从单个Data目录导入术语"""
        result = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'categories': {}
        }

        languages_dir = data_dir / "Languages"
        if not languages_dir.exists():
            return result

        # 优先使用已解压的目录
        english_dir = languages_dir / "English"
        chinese_dir = None

        # 查找中文目录(可能是文件夹或tar文件)
        for item in languages_dir.iterdir():
            if 'ChineseSimplified' in item.name or '简体中文' in item.name:
                if item.is_dir():
                    chinese_dir = item
                    break
                elif item.suffix == '.tar':
                    # 解压tar文件
                    chinese_dir = self._extract_tar(item)
                    break

        if not english_dir.exists():
            # 尝试解压英文tar
            english_tar = languages_dir / "English.tar"
            if english_tar.exists():
                english_dir = self._extract_tar(english_tar)
            else:
                return result

        if not chinese_dir:
            return result

        # 从Keyed文件提取术语
        keyed_result = self._import_from_keyed(english_dir, chinese_dir, categories)
        result['total'] += keyed_result['total']
        result['success'] += keyed_result['success']
        result['failed'] += keyed_result['failed']
        for cat, count in keyed_result['categories'].items():
            result['categories'][cat] = result['categories'].get(cat, 0) + count

        # 从DefInjected文件提取术语
        definjected_result = self._import_from_definjected(english_dir, chinese_dir, categories)
        result['total'] += definjected_result['total']
        result['success'] += definjected_result['success']
        result['failed'] += definjected_result['failed']
        for cat, count in definjected_result['categories'].items():
            result['categories'][cat] = result['categories'].get(cat, 0) + count

        return result

    def _extract_tar(self, tar_path: Path) -> Optional[Path]:
        """
        解压tar文件到临时目录

        Args:
            tar_path: tar文件路径

        Returns:
            Optional[Path]: 解压后的目录路径
        """
        try:
            # 创建临时目录
            temp_dir = Path(tempfile.mkdtemp(prefix='rimworld_'))

            # 解压tar文件
            with tarfile.open(tar_path, 'r') as tar:
                tar.extractall(temp_dir)

            return temp_dir

        except Exception as e:
            print(f"解压tar文件失败: {e}")
            return None

    def _import_from_keyed(
        self,
        english_dir: Path,
        chinese_dir: Path,
        categories: Optional[List[str]]
    ) -> Dict[str, int]:
        """从Keyed文件导入术语"""
        result = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'categories': {}
        }

        english_keyed = english_dir / "Keyed"
        chinese_keyed = chinese_dir / "Keyed"

        if not english_keyed.exists() or not chinese_keyed.exists():
            return result

        # 遍历所有XML文件
        for en_file in english_keyed.glob("*.xml"):
            zh_file = chinese_keyed / en_file.name

            if not zh_file.exists():
                continue

            try:
                # 解析英文和中文XML
                en_tree = ET.parse(en_file)
                zh_tree = ET.parse(zh_file)

                en_root = en_tree.getroot()
                zh_root = zh_tree.getroot()

                # 确定分类
                category = en_file.stem  # 使用文件名作为分类

                if categories and category not in categories:
                    continue

                # 提取术语对
                for en_elem in en_root:
                    key = en_elem.tag
                    en_text = en_elem.text

                    if not en_text or not en_text.strip():
                        continue

                    # 查找对应的中文
                    zh_elem = zh_root.find(key)
                    if zh_elem is not None and zh_elem.text:
                        zh_text = zh_elem.text.strip()

                        # 创建术语条目
                        entry = GlossaryEntry(
                            term_en=en_text.strip(),
                            term_zh=zh_text,
                            category=category,
                            priority=50,  # 官方术语优先级设为50
                            source="official",
                            note=f"来源: Keyed/{en_file.name}"
                        )

                        result['total'] += 1

                        try:
                            self.glossary_repo.save(entry)
                            result['success'] += 1
                            result['categories'][category] = result['categories'].get(category, 0) + 1
                        except Exception:
                            result['failed'] += 1

            except Exception:
                continue

        return result

    def _import_from_definjected(
        self,
        english_dir: Path,
        chinese_dir: Path,
        categories: Optional[List[str]]
    ) -> Dict[str, int]:
        """从DefInjected文件导入术语"""
        result = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'categories': {}
        }

        english_def = english_dir / "DefInjected"
        chinese_def = chinese_dir / "DefInjected"

        if not english_def.exists() or not chinese_def.exists():
            return result

        # 遍历DefInjected子目录
        for en_category_dir in english_def.iterdir():
            if not en_category_dir.is_dir():
                continue

            category = en_category_dir.name
            zh_category_dir = chinese_def / category

            if not zh_category_dir.exists():
                continue

            if categories and category not in categories:
                continue

            # 遍历该分类下的所有XML文件
            for en_file in en_category_dir.glob("*.xml"):
                zh_file = zh_category_dir / en_file.name

                if not zh_file.exists():
                    continue

                try:
                    en_tree = ET.parse(en_file)
                    zh_tree = ET.parse(zh_file)

                    en_root = en_tree.getroot()
                    zh_root = zh_tree.getroot()

                    # 提取名称标签
                    for en_def in en_root:
                        # 查找label或name标签
                        en_label = en_def.find(".//label")
                        if en_label is None:
                            en_label = en_def.find(".//name")

                        if en_label is None or not en_label.text:
                            continue

                        # 查找对应的中文定义
                        def_name = en_def.tag
                        zh_def = zh_root.find(f".//{def_name}")

                        if zh_def is not None:
                            zh_label = zh_def.find(".//label")
                            if zh_label is None:
                                zh_label = zh_def.find(".//name")

                            if zh_label is not None and zh_label.text:
                                # 创建术语条目
                                entry = GlossaryEntry(
                                    term_en=en_label.text.strip(),
                                    term_zh=zh_label.text.strip(),
                                    category=category,
                                    priority=60,  # DefInjected术语优先级更高
                                    source="official",
                                    note=f"来源: DefInjected/{category}/{en_file.name}"
                                )

                                result['total'] += 1

                                try:
                                    self.glossary_repo.save(entry)
                                    result['success'] += 1
                                    result['categories'][category] = result['categories'].get(category, 0) + 1
                                except Exception:
                                    result['failed'] += 1

                except Exception:
                    continue

        return result

    def get_supported_categories(self, game_path: Path) -> List[str]:
        """
        获取支持的术语分类列表

        Args:
            game_path: 游戏根目录

        Returns:
            List[str]: 分类名称列表
        """
        categories = set()

        # 从Keyed文件获取
        keyed_dir = game_path / "Data" / "Core" / "Languages" / "English" / "Keyed"
        if keyed_dir.exists():
            for file in keyed_dir.glob("*.xml"):
                categories.add(file.stem)

        # 从DefInjected文件获取
        def_dir = game_path / "Data" / "Core" / "Languages" / "English" / "DefInjected"
        if def_dir.exists():
            for category_dir in def_dir.iterdir():
                if category_dir.is_dir():
                    categories.add(category_dir.name)

        return sorted(list(categories))
