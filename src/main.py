"""
主程序入口
"""
import sys
import argparse
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.services.translation_service import TranslationService
from src.logic.batch_translator import BatchTranslatorLogic
from src.logic.translation_memory import TranslationMemoryLogic
from src.data.translation_memory_repository import TranslationMemoryRepository
from src.data.session_repository import SessionRepository
from src.utils.config import Config
from src.utils.exceptions import RimworldTranslatorError


def _glossary_menu(service: TranslationService):
    """术语库管理子菜单"""
    while True:
        print("\n" + "-" * 50)
        print("术语库管理")
        print("-" * 50)
        print("1. 导入术语库 (CSV)")
        print("2. 搜索术语")
        print("3. 查看术语统计")
        print("0. 返回主菜单")
        print()

        choice = input("请选择 (0-3): ").strip()

        if choice == "1":
            csv_path = input("请输入 CSV 文件路径: ").strip()
            replace = input("是否替换现有术语? (y/n): ").strip().lower() == 'y'

            try:
                count = service.import_glossary(csv_path, replace)
                print(f"✓ 成功导入 {count} 条术语")
            except Exception as e:
                print(f"✗ 错误: {e}")

        elif choice == "2":
            keyword = input("请输入搜索关键词: ").strip()
            if not keyword:
                print("关键词不能为空")
                continue

            try:
                results = service.search_glossary(keyword)
                if not results:
                    print("没有找到匹配的术语")
                else:
                    print(f"\n找到 {len(results)} 条术语:")
                    for entry in results[:10]:  # 只显示前10条
                        print(f"  {entry.term_en} -> {entry.term_zh} [{entry.category or '通用'}]")
            except Exception as e:
                print(f"错误: {e}")

        elif choice == "3":
            try:
                total = service.glossary_repo.count_all()
                categories = service.glossary_repo.get_categories()

                print(f"\n术语库统计:")
                print(f"  总数: {total}")
                print(f"  分类数: {len(categories)}")

                if categories:
                    print(f"\n分类详情:")
                    for cat in categories:
                        count = service.glossary_repo.count_by_category(cat)
                        print(f"    {cat}: {count}")
            except Exception as e:
                print(f"错误: {e}")

        elif choice == "0":
            break
        else:
            print("无效选项")


def _translation_memory_menu(memory_logic: TranslationMemoryLogic):
    """翻译记忆管理子菜单"""
    while True:
        print("\n" + "-" * 50)
        print("翻译记忆管理")
        print("-" * 50)
        print("1. 查询翻译")
        print("2. 添加翻译记录")
        print("3. 查看统计信息")
        print("4. 清理旧记录")
        print("0. 返回主菜单")
        print()

        choice = input("请选择 (0-4): ").strip()

        if choice == "1":
            text = input("请输入要查询的原文: ").strip()
            if not text:
                print("原文不能为空")
                continue

            try:
                match = memory_logic.find_translation(text)
                if match:
                    print(f"\n找到翻译:")
                    print(f"  原文: {match['source']}")
                    print(f"  译文: {match['translation']}")
                    print(f"  类型: {match['type']}")
                    print(f"  相似度: {match.get('similarity', 100):.1f}%")
                else:
                    print("✗ 没有找到匹配的翻译")
            except Exception as e:
                print(f"错误: {e}")

        elif choice == "2":
            source = input("请输入原文: ").strip()
            target = input("请输入译文: ").strip()

            if not source or not target:
                print("原文和译文都不能为空")
                continue

            try:
                memory_logic.save_translation(source, target)
                print("✓ 翻译记录已保存")
            except Exception as e:
                print(f"错误: {e}")

        elif choice == "3":
            try:
                stats = memory_logic.get_statistics()
                print(f"\n翻译记忆统计:")
                print(f"  总记录数: {stats['total']}")
                print(f"  独特源文本: {stats['unique_sources']}")
                print(f"  平均使用次数: {stats['avg_use_count']:.1f}")
            except Exception as e:
                print(f"错误: {e}")

        elif choice == "4":
            days = input("删除多少天前未使用的记录? (默认30): ").strip()
            try:
                days = int(days) if days else 30
                count = memory_logic.cleanup_old_entries(days)
                print(f"✓ 已删除 {count} 条旧记录")
            except ValueError:
                print("✗ 请输入有效的数字")
            except Exception as e:
                print(f"错误: {e}")

        elif choice == "0":
            break
        else:
            print("无效选项")


def _session_menu(session_repo: SessionRepository, service: TranslationService):
    """会话管理子菜单"""
    while True:
        print("\n" + "-" * 50)
        print("会话管理")
        print("-" * 50)
        print("1. 查看活动会话")
        print("2. 恢复会话")
        print("3. 删除会话")
        print("0. 返回主菜单")
        print()

        choice = input("请选择 (0-3): ").strip()

        if choice == "1":
            try:
                sessions = session_repo.get_all_active()
                if not sessions:
                    print("\n没有活动会话")
                else:
                    print(f"\n活动会话列表:")
                    for session in sessions:
                        print(f"  MOD: {session.mod_name}")
                        print(f"    路径: {session.mod_path}")
                        print(f"    进度: {session.translated_entries}/{session.total_entries}")
                        print(f"    最后保存: {session.last_save}")
                        print()
            except Exception as e:
                print(f"错误: {e}")

        elif choice == "2":
            mod_name = input("请输入要恢复的 MOD 名称: ").strip()
            if not mod_name:
                continue

            try:
                session = session_repo.find_by_mod(mod_name)
                if not session:
                    print(f"✗ 没有找到 MOD '{mod_name}' 的会话")
                    continue

                print(f"\n会话信息:")
                print(f"  MOD: {session.mod_name}")
                print(f"  进度: {session.translated_entries}/{session.total_entries}")
                print(f"  最后保存: {session.last_save}")

                confirm = input("\n是否加载此会话? (y/n): ").strip().lower()
                if confirm == 'y':
                    # 获取该会话的翻译条目
                    entries = service.get_translations(
                        session.mod_name,
                        limit=100,
                        offset=session.current_page * 100
                    )
                    print(f"✓ 已加载 {len(entries)} 条翻译条目")
                    print(f"提示: 可以继续翻译或使用批量翻译功能")

            except Exception as e:
                print(f"错误: {e}")

        elif choice == "3":
            mod_name = input("请输入要删除的 MOD 名称: ").strip()
            if not mod_name:
                continue

            confirm = input(f"确认删除 '{mod_name}' 的会话? (y/n): ").strip().lower()
            if confirm != 'y':
                print("已取消")
                continue

            try:
                session_repo.delete(mod_name)
                print(f"✓ 已删除会话")
            except Exception as e:
                print(f"错误: {e}")

        elif choice == "0":
            break
        else:
            print("无效选项")


def cli_mode():
    """CLI 模式"""
    print("=" * 50)
    print("Rimworld MOD 汉化助手 - CLI 模式")
    print("=" * 50)
    print()

    # 初始化服务
    try:
        config = Config()
        service = TranslationService()

        # 初始化批量翻译和翻译记忆
        memory_repo = TranslationMemoryRepository(service.db)
        memory_logic = TranslationMemoryLogic(memory_repo, service.glossary_repo)
        batch_translator = BatchTranslatorLogic(config, memory_logic)
        session_repo = SessionRepository(service.db)

        print(f"\n可用的翻译引擎: {', '.join(batch_translator.get_available_providers())}")

    except Exception as e:
        print(f"错误: 初始化失败 - {e}")
        return

    # 主菜单
    while True:
        print("\n" + "=" * 50)
        print("主菜单")
        print("=" * 50)
        print("1. 提取 MOD 可翻译内容")
        print("2. 批量翻译 (使用 AI)")
        print("3. 查看翻译进度")
        print("4. 导出已翻译内容")
        print("5. 术语库管理")
        print("6. 翻译记忆管理")
        print("7. 会话管理")
        print("0. 退出")
        print()

        choice = input("请输入选项 (0-7): ").strip()

        if choice == "1":
            # 提取 MOD
            mod_path_str = input("请输入 MOD 目录路径: ").strip()

            try:
                print("\n正在处理 MOD...")
                result = service.extract_mod(mod_path_str)

                mod_info = result['mod_info']
                print(f"\nMOD 信息:")
                print(f"  名称: {mod_info.name}")
                print(f"  作者: {mod_info.author or '未知'}")
                print(f"  版本: {mod_info.version or '未知'}")

                print(f"\n提取结果:")
                print(f"  总条目: {result['total_entries']}")
                print(f"  新增: {result['new_entries']}")
                print(f"  更新: {result['updated_entries']}")
                print("\n提取成功!")

            except RimworldTranslatorError as e:
                print(f"错误: {e}")

        elif choice == "2":
            # 批量翻译
            mod_name = input("请输入 MOD 名称: ").strip()

            if not mod_name:
                print("错误: MOD 名称不能为空")
                continue

            try:
                # 选择翻译引擎
                providers = batch_translator.get_available_providers()
                if not providers:
                    print("错误: 没有可用的翻译引擎,请检查配置")
                    continue

                print(f"\n可用的翻译引擎:")
                for idx, p in enumerate(providers, 1):
                    print(f"  {idx}. {p}")

                provider_idx = input(f"\n请选择引擎 (1-{len(providers)}): ").strip()
                try:
                    provider_name = providers[int(provider_idx) - 1]
                except (ValueError, IndexError):
                    print("错误: 无效的选择")
                    continue

                # 获取待翻译条目
                entries = service.get_translations(mod_name, status='pending', limit=1000)

                if not entries:
                    print(f"\nMOD '{mod_name}' 没有待翻译的条目")
                    continue

                print(f"\n找到 {len(entries)} 条待翻译条目")
                confirm = input("是否开始批量翻译? (y/n): ").strip().lower()

                if confirm != 'y':
                    print("已取消")
                    continue

                print(f"\n开始使用 {provider_name} 翻译...")

                # 定义进度回调
                def progress_callback(current, total, entry):
                    print(f"  [{current}/{total}] {entry.original_text[:40]}...")

                # 执行批量翻译
                result = batch_translator.batch_translate(
                    entries,
                    provider_name=provider_name,
                    use_memory=True,
                    progress_callback=progress_callback
                )

                # 保存翻译结果
                for entry in result['results']:
                    if entry.translated_text:
                        service.translation_repo.save(entry)

                print(f"\n翻译完成!")
                print(f"  成功: {result['success_count']}")
                print(f"  失败: {result['failed_count']}")
                print(f"  来自翻译记忆: {result['memory_hit_count']}")

            except Exception as e:
                print(f"错误: {e}")

        elif choice == "3":
            # 查看进度
            mod_name = input("请输入 MOD 名称 (留空查看所有): ").strip()

            try:
                if mod_name:
                    stats = service.get_translation_progress(mod_name)
                    print(f"\n翻译进度 - {mod_name}:")
                    print(f"  总条目: {stats['total']}")
                    print(f"  已完成: {stats['completed']}")
                    print(f"  待翻译: {stats['pending']}")
                    print(f"  已跳过: {stats['skipped']}")

                    if stats['total'] > 0:
                        progress = (stats['completed'] / stats['total']) * 100
                        print(f"  完成度: {progress:.1f}%")
                else:
                    # 查看所有MOD
                    all_mods = service.translation_repo.get_all_mod_names()
                    if not all_mods:
                        print("\n数据库中没有任何 MOD 记录")
                    else:
                        print(f"\n数据库中的 MOD 列表:")
                        for mod in all_mods:
                            stats = service.get_translation_progress(mod)
                            progress = (stats['completed'] / stats['total'] * 100) if stats['total'] > 0 else 0
                            print(f"  {mod}: {stats['completed']}/{stats['total']} ({progress:.1f}%)")

            except Exception as e:
                print(f"错误: {e}")

        elif choice == "4":
            # 导出翻译
            mod_name = input("请输入 MOD 名称: ").strip()
            mod_path_str = input("请输入 MOD 目录路径: ").strip()

            if not mod_name or not mod_path_str:
                print("错误: 输入不能为空")
                continue

            try:
                print("\n正在导出翻译...")
                result = service.export_translations(mod_name, mod_path_str)

                print(f"\n导出成功!")
                print(f"  生成文件数: {result['total_files']}")
                print(f"  导出条目数: {result['exported_entries']}")
                print(f"  目标路径: {result['target_path']}")

            except Exception as e:
                print(f"错误: {e}")

        elif choice == "5":
            # 术语库管理子菜单
            _glossary_menu(service)

        elif choice == "6":
            # 翻译记忆管理子菜单
            _translation_memory_menu(memory_logic)

        elif choice == "7":
            # 会话管理子菜单
            _session_menu(session_repo, service)

        elif choice == "0":
            print("\n感谢使用! 再见!")
            service.close()
            break

        else:
            print("无效的选项,请重新输入")


def gui_mode():
    """GUI 模式"""
    try:
        from src.ui.gui import start_gui
        start_gui()
    except ImportError as e:
        print(f"错误: GUI 模块导入失败 - {e}")
        print("请确保已安装 tkinter")
    except Exception as e:
        print(f"错误: GUI 启动失败 - {e}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Rimworld MOD 汉化助手"
    )
    parser.add_argument(
        "--cli",
        action="store_true",
        help="启动 CLI 模式"
    )
    parser.add_argument(
        "--gui",
        action="store_true",
        help="启动 GUI 模式 (待实现)"
    )

    args = parser.parse_args()

    if args.cli:
        cli_mode()
    elif args.gui:
        gui_mode()
    else:
        # 默认显示帮助
        parser.print_help()
        print("\n提示: 使用 --cli 启动命令行模式, 或 --gui 启动图形界面模式")


if __name__ == "__main__":
    main()
