"""
翻译器逻辑
"""
from pathlib import Path
from typing import List, Dict
from lxml import etree
from ..models.translation_entry import TranslationEntry
from ..storage.file_storage import FileStorage


class Translator:
    """翻译器"""

    def __init__(self):
        self.file_storage = FileStorage()

    def generate_chinese_xml(
        self,
        entries: List[TranslationEntry],
        mod_path: Path,
        target_language: str = "ChineseSimplified"
    ):
        """
        生成中文 XML 文件

        Args:
            entries: 翻译条目列表
            mod_path: MOD 根目录
            target_language: 目标语言目录名
        """
        # 按文件路径分组
        files_dict: Dict[str, List[TranslationEntry]] = {}

        for entry in entries:
            if entry.status == "completed" and entry.translated_text:
                if entry.file_path not in files_dict:
                    files_dict[entry.file_path] = []
                files_dict[entry.file_path].append(entry)

        # 生成每个文件
        for file_path, file_entries in files_dict.items():
            self._generate_file(file_path, file_entries, mod_path, target_language)

    def _generate_file(
        self,
        rel_path: str,
        entries: List[TranslationEntry],
        mod_path: Path,
        target_language: str
    ):
        """生成单个 XML 文件"""
        # 创建 XML 结构
        root = etree.Element("LanguageData")

        for entry in entries:
            elem = etree.SubElement(root, entry.xml_path)
            elem.text = entry.translated_text

            # 添加注释 (如果有)
            if entry.comment:
                comment = etree.Comment(f" EN: {entry.comment} ")
                root.insert(root.index(elem), comment)

        # 构建目标路径
        # rel_path 格式: Languages/English/DefInjected/ThingDef/Items.xml
        # 需要替换为: Languages/ChineseSimplified/DefInjected/ThingDef/Items.xml
        path_parts = Path(rel_path).parts
        if path_parts[0] == "Languages" and len(path_parts) > 2:
            target_path = Path(path_parts[0]) / target_language / Path(*path_parts[2:])
        else:
            target_path = Path(rel_path)

        output_file = mod_path / target_path

        # 写入文件
        self.file_storage.write_xml(output_file, root)

    def group_by_file(self, entries: List[TranslationEntry]) -> Dict[str, List[TranslationEntry]]:
        """
        按文件路径分组翻译条目

        Args:
            entries: 翻译条目列表

        Returns:
            Dict: 文件路径 -> 条目列表
        """
        files_dict: Dict[str, List[TranslationEntry]] = {}

        for entry in entries:
            if entry.status == "completed" and entry.translated_text:
                if entry.file_path not in files_dict:
                    files_dict[entry.file_path] = []
                files_dict[entry.file_path].append(entry)

        return files_dict

    def build_xml(self, entries: List[TranslationEntry]):
        """
        构建 XML 根元素

        Args:
            entries: 翻译条目列表

        Returns:
            etree.Element: XML 根元素
        """
        root = etree.Element("LanguageData")

        for entry in entries:
            elem = etree.SubElement(root, entry.xml_path)
            elem.text = entry.translated_text

            # 添加注释 (如果有)
            if entry.comment:
                comment = etree.Comment(f" EN: {entry.comment} ")
                root.insert(root.index(elem), comment)

        return root

    def validate_translation(self, text: str) -> bool:
        """
        验证翻译文本

        Args:
            text: 待验证的文本

        Returns:
            bool: 是否有效
        """
        if not text or not text.strip():
            return False

        # 检查 XML 特殊字符是否正确转义
        # (这里简化处理,实际应更严格)
        return True
