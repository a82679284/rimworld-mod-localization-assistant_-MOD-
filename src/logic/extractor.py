"""
XML 提取器逻辑
"""
from pathlib import Path
from typing import List, Dict
from lxml import etree
from ..models.translation_entry import TranslationEntry
from ..models.mod_info import ModInfo
from ..storage.file_storage import FileStorage
from ..utils.exceptions import ModNotFoundError, ModInvalidStructureError


class Extractor:
    """MOD 内容提取器"""

    def __init__(self):
        self.file_storage = FileStorage()

    def scan_mod(self, mod_path: Path) -> ModInfo:
        """
        扫描 MOD 结构

        Args:
            mod_path: MOD 根目录

        Returns:
            ModInfo: MOD 信息

        Raises:
            ModNotFoundError: MOD 不存在
            ModInvalidStructureError: MOD 结构无效
        """
        if not mod_path.exists():
            raise ModNotFoundError(f"MOD 目录不存在: {mod_path}")

        # 读取 About.xml 获取 MOD 信息
        about_xml = mod_path / "About" / "About.xml"
        mod_name = mod_path.name
        version = None
        author = None

        if about_xml.exists():
            try:
                root = self.file_storage.read_xml(about_xml)
                name_elem = root.find(".//name")
                if name_elem is not None and name_elem.text:
                    mod_name = name_elem.text

                version_elem = root.find(".//packageId")
                if version_elem is not None and version_elem.text:
                    version = version_elem.text

                author_elem = root.find(".//author")
                if author_elem is not None and author_elem.text:
                    author = author_elem.text
            except Exception:
                pass  # 忽略 About.xml 解析错误

        # 检查 Languages 目录
        languages_dir = mod_path / "Languages"
        if not languages_dir.exists():
            raise ModInvalidStructureError(
                f"MOD 缺少 Languages 目录: {mod_path}"
            )

        return ModInfo(
            name=mod_name,
            path=mod_path,
            version=version,
            author=author
        )

    def extract_entries(
        self,
        mod_path: Path,
        source_language: str = "English"
    ) -> List[TranslationEntry]:
        """
        提取可翻译条目

        Args:
            mod_path: MOD 根目录
            source_language: 源语言目录名 (默认 English)

        Returns:
            List[TranslationEntry]: 翻译条目列表
        """
        mod_info = self.scan_mod(mod_path)
        entries = []

        # 扫描源语言目录
        source_dir = mod_path / "Languages" / source_language
        if not source_dir.exists():
            return entries

        # 提取 DefInjected 文件
        def_injected_dir = source_dir / "DefInjected"
        if def_injected_dir.exists():
            entries.extend(
                self._extract_def_injected(def_injected_dir, mod_info.name)
            )

        # 提取 Keyed 文件
        keyed_dir = source_dir / "Keyed"
        if keyed_dir.exists():
            entries.extend(
                self._extract_keyed(keyed_dir, mod_info.name)
            )

        return entries

    def _extract_def_injected(
        self,
        def_injected_dir: Path,
        mod_name: str
    ) -> List[TranslationEntry]:
        """提取 DefInjected 文件"""
        entries = []
        xml_files = self.file_storage.list_files(def_injected_dir, "*.xml")

        for xml_file in xml_files:
            try:
                root = self.file_storage.read_xml(xml_file)

                # 相对路径
                rel_path = xml_file.relative_to(def_injected_dir.parent.parent.parent)

                for elem in root:
                    if elem.tag == etree.Comment:
                        continue

                    xml_path = elem.tag
                    original_text = elem.text or ""

                    # 提取注释 (<!-- EN: ... -->)
                    comment = None
                    prev = elem.getprevious()
                    if prev is not None and isinstance(prev, etree._Comment):
                        comment_text = prev.text.strip()
                        if comment_text.startswith("EN:"):
                            comment = comment_text[3:].strip()

                    entries.append(TranslationEntry(
                        mod_name=mod_name,
                        file_path=str(rel_path),
                        xml_path=xml_path,
                        original_text=original_text,
                        comment=comment
                    ))

            except Exception as e:
                # 跳过解析失败的文件
                print(f"警告: 跳过文件 {xml_file}: {e}")
                continue

        return entries

    def _extract_keyed(
        self,
        keyed_dir: Path,
        mod_name: str
    ) -> List[TranslationEntry]:
        """提取 Keyed 文件"""
        entries = []
        xml_files = self.file_storage.list_files(keyed_dir, "*.xml")

        for xml_file in xml_files:
            try:
                root = self.file_storage.read_xml(xml_file)
                rel_path = xml_file.relative_to(keyed_dir.parent.parent.parent)

                for elem in root:
                    if elem.tag == etree.Comment:
                        continue

                    xml_path = elem.tag
                    original_text = elem.text or ""

                    entries.append(TranslationEntry(
                        mod_name=mod_name,
                        file_path=str(rel_path),
                        xml_path=xml_path,
                        original_text=original_text
                    ))

            except Exception as e:
                print(f"警告: 跳过文件 {xml_file}: {e}")
                continue

        return entries
