"""
文件存储模块
"""
from pathlib import Path
from typing import Optional, List
from lxml import etree
from ..utils.exceptions import FilePermissionError, XMLParseError


class FileStorage:
    """文件系统存储管理"""

    @staticmethod
    def read_xml(file_path: Path) -> etree._Element:
        """
        读取 XML 文件

        Args:
            file_path: XML 文件路径

        Returns:
            etree._Element: XML 根元素

        Raises:
            FilePermissionError: 文件权限不足
            XMLParseError: XML 解析失败
        """
        try:
            if not file_path.exists():
                raise FileNotFoundError(f"文件不存在: {file_path}")

            # 让 lxml 自动检测编码(支持 UTF-8 BOM、其他编码)
            parser = etree.XMLParser(remove_blank_text=False)
            tree = etree.parse(str(file_path), parser)
            return tree.getroot()

        except PermissionError as e:
            raise FilePermissionError(f"文件权限不足: {file_path}") from e
        except etree.XMLSyntaxError as e:
            raise XMLParseError(f"XML 解析失败: {file_path}, 错误: {e}") from e

    @staticmethod
    def write_xml(
        file_path: Path,
        root: etree._Element,
        encoding: str = "utf-8",
        pretty_print: bool = True
    ):
        """
        写入 XML 文件

        Args:
            file_path: 目标文件路径
            root: XML 根元素
            encoding: 文件编码
            pretty_print: 是否格式化输出

        Raises:
            FilePermissionError: 文件权限不足
        """
        try:
            # 确保目录存在
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # 创建临时文件 (原子操作)
            temp_file = file_path.with_suffix('.tmp')

            # 写入临时文件
            tree = etree.ElementTree(root)
            tree.write(
                str(temp_file),
                encoding=encoding,
                xml_declaration=True,
                pretty_print=pretty_print
            )

            # 重命名为目标文件
            if file_path.exists():
                file_path.unlink()
            temp_file.rename(file_path)

        except PermissionError as e:
            raise FilePermissionError(f"文件写入权限不足: {file_path}") from e

    @staticmethod
    def ensure_directory(dir_path: Path):
        """
        确保目录存在

        Args:
            dir_path: 目录路径
        """
        dir_path.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def list_files(
        directory: Path,
        pattern: str = "*.xml",
        recursive: bool = True
    ) -> List[Path]:
        """
        列举目录中的文件

        Args:
            directory: 目录路径
            pattern: 文件匹配模式
            recursive: 是否递归搜索

        Returns:
            List[Path]: 文件路径列表
        """
        if not directory.exists():
            return []

        if recursive:
            return list(directory.rglob(pattern))
        else:
            return list(directory.glob(pattern))

    @staticmethod
    def get_file_size(file_path: Path) -> int:
        """
        获取文件大小

        Args:
            file_path: 文件路径

        Returns:
            int: 文件大小(字节)
        """
        if file_path.exists():
            return file_path.stat().st_size
        return 0

    @staticmethod
    def copy_file(source: Path, destination: Path):
        """
        复制文件

        Args:
            source: 源文件路径
            destination: 目标文件路径
        """
        import shutil

        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(source), str(destination))
