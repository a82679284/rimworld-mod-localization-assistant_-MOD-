"""
翻译服务 - 协调各模块的业务流程
"""
from pathlib import Path
from typing import List, Optional, Dict
from ..storage.database import Database
from ..storage.file_storage import FileStorage
from ..data.translation_repository import TranslationRepository
from ..data.glossary_repository import GlossaryRepository
from ..logic.extractor import Extractor
from ..logic.translator import Translator
from ..models.translation_entry import TranslationEntry
from ..models.mod_info import ModInfo
from ..models.glossary_entry import GlossaryEntry
from ..utils.exceptions import RimworldTranslatorError


class TranslationService:
    """翻译服务 - 统一协调业务流程"""

    def __init__(self, database: Optional[Database] = None):
        """
        初始化翻译服务

        Args:
            database: 数据库实例,如果不提供则自动创建
        """
        self.db = database or Database()
        self.file_storage = FileStorage()
        self.translation_repo = TranslationRepository(self.db)
        self.glossary_repo = GlossaryRepository(self.db)
        self.extractor = Extractor()
        self.translator = Translator()

    def extract_mod(
        self,
        mod_path: str,
        source_language: str = "English"
    ) -> Dict[str, any]:
        """
        提取 MOD 可翻译内容

        Args:
            mod_path: MOD 根目录路径
            source_language: 源语言 (默认 English)

        Returns:
            Dict: 包含提取结果的字典
                - mod_info: ModInfo 对象
                - total_entries: 总条目数
                - new_entries: 新增条目数
                - updated_entries: 更新条目数

        Raises:
            RimworldTranslatorError: 提取失败
        """
        try:
            path = Path(mod_path)

            # 1. 扫描 MOD 结构
            mod_info = self.extractor.scan_mod(path)

            # 2. 提取翻译条目
            entries = self.extractor.extract_entries(path, source_language)

            if not entries:
                return {
                    "mod_info": mod_info,
                    "total_entries": 0,
                    "new_entries": 0,
                    "updated_entries": 0
                }

            # 3. 批量保存到数据库
            saved_count = self.translation_repo.save_batch(entries)

            return {
                "mod_info": mod_info,
                "total_entries": len(entries),
                "new_entries": saved_count,
                "updated_entries": 0  # save_batch使用INSERT OR REPLACE,无法区分新增和更新
            }

        except Exception as e:
            raise RimworldTranslatorError(f"提取 MOD 失败: {e}") from e

    def get_translation_progress(self, mod_name: str) -> Dict[str, int]:
        """
        获取翻译进度

        Args:
            mod_name: MOD 名称

        Returns:
            Dict: 进度信息
                - total: 总条目数
                - completed: 已完成数
                - pending: 待翻译数
                - skipped: 跳过数
        """
        try:
            stats = self.translation_repo.get_statistics(mod_name)
            return stats
        except Exception as e:
            raise RimworldTranslatorError(f"获取进度失败: {e}") from e

    def export_translations(
        self,
        mod_name: str,
        mod_path: str,
        target_language: str = "ChineseSimplified"
    ) -> Dict[str, any]:
        """
        导出已翻译内容

        Args:
            mod_name: MOD 名称
            mod_path: MOD 根目录路径
            target_language: 目标语言目录名

        Returns:
            Dict: 导出结果
                - total_files: 生成文件数
                - target_path: 目标路径
                - exported_entries: 导出条目数

        Raises:
            RimworldTranslatorError: 导出失败
        """
        try:
            path = Path(mod_path)

            # 1. 获取已完成翻译的条目
            entries = self.translation_repo.find_by_status(mod_name, "completed")

            if not entries:
                raise RimworldTranslatorError(
                    f"MOD '{mod_name}' 没有已完成的翻译条目"
                )

            # 2. 按文件路径分组
            grouped = self.translator.group_by_file(entries)

            # 3. 生成目标 XML 文件
            target_base = path / "Languages" / target_language
            file_count = 0

            for file_path, file_entries in grouped.items():
                # 处理文件路径
                # file_path 格式: Languages/English/DefInjected/ThingDef/Items.xml
                # 需要提取: DefInjected/ThingDef/Items.xml
                path_parts = Path(file_path).parts

                # 如果路径包含 Languages/xxx/，去掉前两级
                if len(path_parts) > 2 and path_parts[0] == "Languages":
                    # 跳过 Languages 和语言名 (English/ChineseSimplified 等)
                    relative_file_path = Path(*path_parts[2:])
                else:
                    # 如果不符合预期格式，直接使用原路径
                    relative_file_path = Path(file_path)

                # 构建目标文件路径: MOD/Languages/ChineseSimplified/DefInjected/...
                target_file = target_base / relative_file_path

                # 生成 XML
                xml_root = self.translator.build_xml(file_entries)

                # 保存文件
                self.file_storage.write_xml(target_file, xml_root)
                file_count += 1

            return {
                "total_files": file_count,
                "target_path": str(target_base),
                "exported_entries": len(entries)
            }

        except Exception as e:
            raise RimworldTranslatorError(f"导出翻译失败: {e}") from e

    def import_glossary(
        self,
        csv_path: str,
        replace_existing: bool = False
    ) -> int:
        """
        导入术语库

        Args:
            csv_path: CSV 文件路径
            replace_existing: 是否替换已存在的术语

        Returns:
            int: 导入的术语数量

        Raises:
            RimworldTranslatorError: 导入失败
        """
        try:
            import csv

            path = Path(csv_path)
            if not path.exists():
                raise FileNotFoundError(f"术语库文件不存在: {csv_path}")

            entries = []
            with open(path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    entry = GlossaryEntry(
                        term_en=row.get('term_en', '').strip(),
                        term_zh=row.get('term_zh', '').strip(),
                        category=row.get('category', '').strip() or None,
                        note=row.get('note', '').strip() or None,
                        priority=int(row.get('priority', 0)),
                        source='user'
                    )
                    if entry.term_en and entry.term_zh:
                        entries.append(entry)

            if not entries:
                raise RimworldTranslatorError("术语库文件为空或格式错误")

            # 批量保存
            if replace_existing:
                # 先删除所有用户术语
                self.glossary_repo.delete_by_source('user')

            count = self.glossary_repo.save_batch(entries)
            return count

        except Exception as e:
            raise RimworldTranslatorError(f"导入术语库失败: {e}") from e

    def update_translation(
        self,
        entry_id: int,
        translated_text: str,
        status: str = "completed"
    ) -> bool:
        """
        更新单个翻译

        Args:
            entry_id: 条目 ID
            translated_text: 翻译文本
            status: 状态 (completed/pending/skipped)

        Returns:
            bool: 是否更新成功
        """
        try:
            entry = self.translation_repo.find_by_id(entry_id)
            if not entry:
                return False

            entry.translated_text = translated_text
            entry.status = status

            self.translation_repo.save(entry)
            return True

        except Exception as e:
            raise RimworldTranslatorError(f"更新翻译失败: {e}") from e

    def get_translations(
        self,
        mod_name: str,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[TranslationEntry]:
        """
        获取翻译条目列表

        Args:
            mod_name: MOD 名称
            status: 状态过滤 (None=全部)
            limit: 每页条目数
            offset: 偏移量

        Returns:
            List[TranslationEntry]: 翻译条目列表
        """
        try:
            if status:
                entries = self.translation_repo.find_by_status(
                    mod_name, status, limit, offset
                )
            else:
                entries = self.translation_repo.find_by_mod(
                    mod_name, status=None, limit=limit, offset=offset
                )
            return entries

        except Exception as e:
            raise RimworldTranslatorError(f"获取翻译条目失败: {e}") from e

    def search_glossary(
        self,
        keyword: str,
        category: Optional[str] = None
    ) -> List[GlossaryEntry]:
        """
        搜索术语库

        Args:
            keyword: 关键词 (英文或中文)
            category: 分类过滤

        Returns:
            List[GlossaryEntry]: 匹配的术语列表
        """
        try:
            return self.glossary_repo.search(keyword, category)
        except Exception as e:
            raise RimworldTranslatorError(f"搜索术语失败: {e}") from e

    def backup_database(self, backup_path: Optional[str] = None) -> str:
        """
        备份数据库

        Args:
            backup_path: 备份路径 (可选,默认自动生成)

        Returns:
            str: 备份文件路径
        """
        try:
            from datetime import datetime

            if not backup_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = f"data/backups/translations_{timestamp}.db"

            self.db.backup(backup_path)
            return backup_path

        except Exception as e:
            raise RimworldTranslatorError(f"备份数据库失败: {e}") from e

    def close(self):
        """关闭服务,释放资源"""
        if self.db:
            self.db.close()
