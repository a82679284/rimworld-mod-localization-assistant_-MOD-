"""
GUI 图形界面 - 基于 Tkinter
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from pathlib import Path
from typing import Optional, List
import threading
from datetime import datetime

from ..services.translation_service import TranslationService
from ..logic.batch_translator import BatchTranslatorLogic
from ..logic.translation_memory import TranslationMemoryLogic
from ..data.translation_memory_repository import TranslationMemoryRepository
from ..data.session_repository import SessionRepository
from ..models.translation_entry import TranslationEntry
from ..utils.config import Config
from ..utils.auto_save import AutoSaveManager


class RimworldTranslatorGUI:
    """Rimworld MOD 汉化助手 GUI 主窗口"""

    def __init__(self):
        """初始化 GUI"""
        self.root = tk.Tk()
        self.root.title("Rimworld MOD 汉化助手")
        self.root.geometry("1200x800")

        # 初始化服务
        self.config = Config()
        self.service = TranslationService()
        self.memory_repo = TranslationMemoryRepository(self.service.db)
        self.memory_logic = TranslationMemoryLogic(self.memory_repo, self.service.glossary_repo)
        self.batch_translator = BatchTranslatorLogic(self.config, self.memory_logic)
        self.session_repo = SessionRepository(self.service.db)

        # 自动保存管理器
        auto_save_interval = self.config.get_translation_config().get('auto_save_interval', 30)
        self.auto_save = AutoSaveManager(interval=auto_save_interval)

        # 当前状态
        self.current_mod_name: Optional[str] = None
        self.current_mod_path: Optional[str] = None
        self.current_entries: List[TranslationEntry] = []
        self.current_page = 0
        self.page_size = 50

        # 构建界面
        self._build_ui()

        # 检查并恢复会话
        self._check_and_resume_session()

    def _build_ui(self):
        """构建用户界面"""
        # 主容器
        main_container = ttk.Frame(self.root, padding="10")
        main_container.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_container.columnconfigure(0, weight=1)
        main_container.rowconfigure(2, weight=1)

        # 1. 顶部工具栏
        self._build_toolbar(main_container)

        # 2. MOD 信息区
        self._build_mod_info_section(main_container)

        # 3. 翻译表格区
        self._build_translation_table(main_container)

        # 4. 底部状态栏和操作按钮
        self._build_bottom_panel(main_container)

    def _build_toolbar(self, parent):
        """构建顶部工具栏"""
        toolbar = ttk.Frame(parent)
        toolbar.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))

        # MOD 路径选择
        ttk.Label(toolbar, text="MOD 路径:").grid(row=0, column=0, padx=5)

        self.mod_path_var = tk.StringVar()
        mod_path_entry = ttk.Entry(toolbar, textvariable=self.mod_path_var, width=50)
        mod_path_entry.grid(row=0, column=1, padx=5)

        ttk.Button(
            toolbar,
            text="浏览...",
            command=self._browse_mod_folder
        ).grid(row=0, column=2, padx=5)

        ttk.Button(
            toolbar,
            text="提取 MOD",
            command=self._extract_mod
        ).grid(row=0, column=3, padx=5)

        ttk.Button(
            toolbar,
            text="导出翻译",
            command=self._export_translations
        ).grid(row=0, column=4, padx=5)

    def _build_mod_info_section(self, parent):
        """构建 MOD 信息区"""
        info_frame = ttk.LabelFrame(parent, text="MOD 信息", padding="5")
        info_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))

        # MOD 名称
        ttk.Label(info_frame, text="名称:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.mod_name_label = ttk.Label(info_frame, text="未加载", foreground="gray")
        self.mod_name_label.grid(row=0, column=1, sticky=tk.W, padx=5)

        # 进度信息
        ttk.Label(info_frame, text="进度:").grid(row=0, column=2, sticky=tk.W, padx=20)
        self.progress_label = ttk.Label(info_frame, text="0/0 (0%)", foreground="gray")
        self.progress_label.grid(row=0, column=3, sticky=tk.W, padx=5)

        # 翻译引擎选择
        ttk.Label(info_frame, text="翻译引擎:").grid(row=0, column=4, sticky=tk.W, padx=20)
        self.provider_var = tk.StringVar()
        providers = self.batch_translator.get_available_providers()
        if providers:
            self.provider_var.set(providers[0])
        self.provider_combo = ttk.Combobox(
            info_frame,
            textvariable=self.provider_var,
            values=providers,
            state="readonly",
            width=15
        )
        self.provider_combo.grid(row=0, column=5, padx=5)

    def _build_translation_table(self, parent):
        """构建翻译表格"""
        table_frame = ttk.Frame(parent)
        table_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)

        # 创建 Treeview
        columns = ("id", "file_path", "xml_path", "original", "translation", "status")
        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            selectmode="browse"
        )

        # 定义列
        self.tree.heading("id", text="ID")
        self.tree.heading("file_path", text="文件路径")
        self.tree.heading("xml_path", text="XML 路径")
        self.tree.heading("original", text="原文")
        self.tree.heading("translation", text="译文")
        self.tree.heading("status", text="状态")

        # 设置列宽
        self.tree.column("id", width=50, anchor=tk.CENTER)
        self.tree.column("file_path", width=200)
        self.tree.column("xml_path", width=150)
        self.tree.column("original", width=250)
        self.tree.column("translation", width=250)
        self.tree.column("status", width=80, anchor=tk.CENTER)

        # 添加滚动条
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        # 布局
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        vsb.grid(row=0, column=1, sticky=(tk.N, tk.S))
        hsb.grid(row=1, column=0, sticky=(tk.W, tk.E))

        # 双击编辑
        self.tree.bind("<Double-1>", self._on_double_click)

    def _build_bottom_panel(self, parent):
        """构建底部面板"""
        bottom_frame = ttk.Frame(parent)
        bottom_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(10, 0))

        # 左侧: 分页控制
        page_frame = ttk.Frame(bottom_frame)
        page_frame.grid(row=0, column=0, sticky=tk.W)

        ttk.Button(
            page_frame,
            text="上一页",
            command=self._prev_page
        ).grid(row=0, column=0, padx=2)

        self.page_label = ttk.Label(page_frame, text="页 1/1")
        self.page_label.grid(row=0, column=1, padx=10)

        ttk.Button(
            page_frame,
            text="下一页",
            command=self._next_page
        ).grid(row=0, column=2, padx=2)

        # 右侧: 操作按钮
        button_frame = ttk.Frame(bottom_frame)
        button_frame.grid(row=0, column=1, sticky=tk.E)
        bottom_frame.columnconfigure(1, weight=1)

        ttk.Button(
            button_frame,
            text="批量翻译",
            command=self._batch_translate
        ).grid(row=0, column=0, padx=5)

        ttk.Button(
            button_frame,
            text="保存",
            command=self._save_translations
        ).grid(row=0, column=1, padx=5)

        ttk.Button(
            button_frame,
            text="术语库",
            command=self._open_glossary_manager
        ).grid(row=0, column=2, padx=5)

        ttk.Button(
            button_frame,
            text="翻译记忆",
            command=self._open_memory_manager
        ).grid(row=0, column=3, padx=5)

        ttk.Button(
            button_frame,
            text="设置",
            command=self._open_settings
        ).grid(row=0, column=4, padx=5)

        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(
            parent,
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        status_bar.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=(5, 0))

    # ==================== 事件处理 ====================

    def _browse_mod_folder(self):
        """浏览选择 MOD 文件夹"""
        folder = filedialog.askdirectory(title="选择 MOD 目录或 MOD 管理根目录")
        if folder:
            folder_path = Path(folder)

            # 检测是否为MOD管理根目录 (包含多个MOD子目录)
            if self._is_mods_root_folder(folder_path):
                # 显示MOD选择对话框
                self._show_mod_selection_dialog(folder)
            else:
                # 单个MOD,直接设置路径
                self.mod_path_var.set(folder)

    def _is_mods_root_folder(self, folder_path: Path) -> bool:
        """
        判断是否为MOD管理根目录

        规则: 如果包含3个以上子目录,且至少有2个子目录包含About/About.xml,则视为根目录
        """
        if not folder_path.is_dir():
            return False

        subdirs = [d for d in folder_path.iterdir() if d.is_dir()]
        if len(subdirs) < 3:
            return False

        # 检查前5个子目录中有About/About.xml的数量
        valid_mod_count = 0
        for subdir in subdirs[:5]:
            about_xml = subdir / "About" / "About.xml"
            if about_xml.exists():
                valid_mod_count += 1

        return valid_mod_count >= 2

    def _show_mod_selection_dialog(self, root_path: str):
        """显示MOD选择对话框"""
        dialog = tk.Toplevel(self.root)
        dialog.title("选择 MOD")
        dialog.geometry("900x600")
        dialog.transient(self.root)
        dialog.grab_set()

        # 提示标签
        ttk.Label(
            dialog,
            text="正在扫描MOD...",
            font=("", 12)
        ).pack(pady=20)

        # 创建表格
        table_frame = ttk.Frame(dialog)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        columns = ("name", "author", "has_chinese", "completeness")
        tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            selectmode="browse"
        )

        tree.heading("name", text="MOD 名称")
        tree.heading("author", text="作者")
        tree.heading("has_chinese", text="汉化状态")
        tree.heading("completeness", text="完成度")

        tree.column("name", width=350)
        tree.column("author", width=200)
        tree.column("has_chinese", width=100, anchor=tk.CENTER)
        tree.column("completeness", width=100, anchor=tk.CENTER)

        # 滚动条
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)

        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        # 按钮区
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        selected_mod_path = [None]

        def on_select():
            selection = tree.selection()
            if selection:
                item = tree.item(selection[0])
                mod_path = item['values'][4]  # 隐藏的路径列
                selected_mod_path[0] = mod_path
                dialog.destroy()

        def on_double_click(event):
            on_select()

        tree.bind("<Double-1>", on_double_click)

        ttk.Button(button_frame, text="选择", command=on_select).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="取消", command=dialog.destroy).pack(side=tk.RIGHT)

        # 后台扫描MOD
        def scan_thread():
            try:
                mods = self.service.scan_mods_folder(root_path)

                def update_ui():
                    # 清除提示
                    for widget in dialog.winfo_children():
                        if isinstance(widget, ttk.Label):
                            widget.destroy()

                    # 添加隐藏的路径列
                    tree.column("completeness", width=100, anchor=tk.CENTER)

                    # 填充数据
                    for mod_data in mods:
                        mod_info = mod_data['info']
                        has_chinese = mod_data['has_chinese']
                        completeness = mod_data['chinese_complete']

                        status_text = "✓ 已汉化" if has_chinese else "✗ 未汉化"
                        complete_text = f"{completeness}%" if has_chinese else "-"

                        # values中包含隐藏的路径
                        tree.insert("", tk.END, values=(
                            mod_info.name,
                            mod_info.author or "-",
                            status_text,
                            complete_text,
                            str(mod_data['path'])  # 隐藏列
                        ))

                dialog.after(0, update_ui)

            except Exception as e:
                def show_error():
                    messagebox.showerror("错误", f"扫描MOD失败:\n{e}")
                    dialog.destroy()
                dialog.after(0, show_error)

        threading.Thread(target=scan_thread, daemon=True).start()

        # 等待对话框关闭
        self.root.wait_window(dialog)

        # 设置选择的MOD路径
        if selected_mod_path[0]:
            self.mod_path_var.set(selected_mod_path[0])

    def _extract_mod(self):
        """提取 MOD 可翻译内容"""
        mod_path = self.mod_path_var.get()
        if not mod_path:
            messagebox.showwarning("警告", "请先选择 MOD 目录")
            return

        self.status_var.set("正在提取 MOD...")
        self.root.update()

        try:
            result = self.service.extract_mod(mod_path)

            mod_info = result['mod_info']
            self.current_mod_name = mod_info.name
            self.current_mod_path = mod_path

            messagebox.showinfo(
                "提取完成",
                f"MOD: {mod_info.name}\n"
                f"总条目: {result['total_entries']}\n"
                f"新增: {result['new_entries']}\n"
                f"更新: {result['updated_entries']}"
            )

            # 加载翻译条目
            self._load_translations()

            # 更新 MOD 信息显示
            self.mod_name_label.config(text=mod_info.name, foreground="black")
            self._update_progress()

        except Exception as e:
            messagebox.showerror("错误", f"提取 MOD 失败:\n{e}")
            self.status_var.set("提取失败")
        else:
            self.status_var.set("提取完成")

    def _load_translations(self):
        """加载翻译条目"""
        if not self.current_mod_name:
            return

        try:
            # 获取当前页的条目
            self.current_entries = self.service.get_translations(
                self.current_mod_name,
                limit=self.page_size,
                offset=self.current_page * self.page_size
            )

            # 清空表格
            for item in self.tree.get_children():
                self.tree.delete(item)

            # 填充数据
            for entry in self.current_entries:
                status_text = {
                    'completed': '✓ 完成',
                    'pending': '⏳ 待译',
                    'skipped': '⊘ 跳过',
                    'failed': '✗ 失败'
                }.get(entry.status, entry.status)

                self.tree.insert("", tk.END, values=(
                    entry.id,
                    entry.file_path,
                    entry.xml_path,
                    entry.original_text[:50] + "..." if len(entry.original_text) > 50 else entry.original_text,
                    (entry.translated_text[:50] + "...") if entry.translated_text and len(
                        entry.translated_text) > 50 else (entry.translated_text or ""),
                    status_text
                ))

            # 更新分页信息
            total_entries = self.service.translation_repo.count_by_mod(self.current_mod_name)
            total_pages = (total_entries + self.page_size - 1) // self.page_size
            self.page_label.config(text=f"页 {self.current_page + 1}/{max(1, total_pages)}")

        except Exception as e:
            messagebox.showerror("错误", f"加载翻译条目失败:\n{e}")

    def _update_progress(self):
        """更新进度显示"""
        if not self.current_mod_name:
            return

        try:
            stats = self.service.get_translation_progress(self.current_mod_name)
            total = stats['total']
            completed = stats['completed']
            progress = (completed / total * 100) if total > 0 else 0

            self.progress_label.config(
                text=f"{completed}/{total} ({progress:.1f}%)",
                foreground="green" if progress == 100 else "black"
            )
        except Exception as e:
            print(f"更新进度失败: {e}")

    def _prev_page(self):
        """上一页"""
        if self.current_page > 0:
            self.current_page -= 1
            self._load_translations()

    def _next_page(self):
        """下一页"""
        if not self.current_mod_name:
            return

        total_entries = self.service.translation_repo.count_by_mod(self.current_mod_name)
        total_pages = (total_entries + self.page_size - 1) // self.page_size

        if self.current_page < total_pages - 1:
            self.current_page += 1
            self._load_translations()

    def _on_double_click(self, event):
        """双击编辑条目"""
        selection = self.tree.selection()
        if not selection:
            return

        item = self.tree.item(selection[0])
        entry_id = item['values'][0]

        # 查找对应的条目
        entry = next((e for e in self.current_entries if e.id == entry_id), None)
        if not entry:
            return

        # 打开编辑对话框
        self._open_edit_dialog(entry)

    def _open_edit_dialog(self, entry: TranslationEntry):
        """打开编辑对话框"""
        dialog = tk.Toplevel(self.root)
        dialog.title(f"编辑翻译 - {entry.xml_path}")
        dialog.geometry("800x600")
        dialog.transient(self.root)
        dialog.grab_set()

        # 原文
        ttk.Label(dialog, text="原文:").pack(anchor=tk.W, padx=10, pady=(10, 0))
        original_text = scrolledtext.ScrolledText(dialog, height=8, wrap=tk.WORD)
        original_text.pack(fill=tk.BOTH, padx=10, pady=5)
        original_text.insert(1.0, entry.original_text)
        original_text.config(state=tk.DISABLED)

        # 翻译辅助工具栏
        assist_frame = ttk.Frame(dialog)
        assist_frame.pack(fill=tk.X, padx=10, pady=5)

        # 翻译记忆建议
        ttk.Label(assist_frame, text="翻译记忆:").pack(side=tk.LEFT)

        def check_memory():
            match = self.memory_logic.find_translation(entry.original_text)
            if match:
                translation_text.delete(1.0, tk.END)
                translation_text.insert(1.0, match['translation'])
                messagebox.showinfo("翻译记忆", f"找到匹配 (相似度: {match.get('similarity', 100):.1f}%)")
            else:
                messagebox.showinfo("翻译记忆", "没有找到匹配的翻译")

        ttk.Button(assist_frame, text="查询", command=check_memory).pack(side=tk.LEFT, padx=5)

        # 术语库查询
        ttk.Label(assist_frame, text="术语库:").pack(side=tk.LEFT, padx=(20, 0))

        def check_glossary():
            """查询术语库中的相关术语"""
            # 搜索原文中的关键词
            words = entry.original_text.split()
            results = []

            for word in words:
                if len(word) < 3:  # 跳过太短的词
                    continue
                matches = self.service.glossary_repo.search_terms(word)
                results.extend(matches)

            if results:
                # 去重并显示结果
                seen = set()
                unique_results = []
                for r in results:
                    key = (r.term_en, r.term_zh)
                    if key not in seen:
                        seen.add(key)
                        unique_results.append(r)

                # 创建结果显示窗口
                result_dialog = tk.Toplevel(dialog)
                result_dialog.title("术语库查询结果")
                result_dialog.geometry("600x400")
                result_dialog.transient(dialog)

                # 结果列表
                result_frame = ttk.Frame(result_dialog)
                result_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

                tree = ttk.Treeview(result_frame, columns=("英文", "中文", "分类"), show="headings", height=15)
                tree.heading("英文", text="英文")
                tree.heading("中文", text="中文")
                tree.heading("分类", text="分类")
                tree.column("英文", width=200)
                tree.column("中文", width=200)
                tree.column("分类", width=150)

                scrollbar = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=tree.yview)
                tree.configure(yscrollcommand=scrollbar.set)

                tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
                scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

                for r in unique_results:
                    tree.insert("", tk.END, values=(r.term_en, r.term_zh, r.category or ""))

                # 双击应用翻译
                def apply_term(event):
                    selection = tree.selection()
                    if selection:
                        item = tree.item(selection[0])
                        term_en = item['values'][0]
                        term_zh = item['values'][1]

                        # 将术语替换到译文中
                        current_text = translation_text.get(1.0, tk.END).strip()
                        if not current_text:
                            # 如果译文为空,尝试智能替换
                            new_text = entry.original_text.replace(term_en, term_zh)
                            translation_text.delete(1.0, tk.END)
                            translation_text.insert(1.0, new_text)
                        else:
                            # 如果译文不为空,在光标处插入术语
                            translation_text.insert(tk.INSERT, term_zh)

                        result_dialog.destroy()

                tree.bind("<Double-1>", apply_term)

                # 关闭按钮
                ttk.Button(result_dialog, text="关闭", command=result_dialog.destroy).pack(pady=5)

            else:
                messagebox.showinfo("术语库", "没有找到相关术语")

        ttk.Button(assist_frame, text="查询", command=check_glossary).pack(side=tk.LEFT, padx=5)

        # AI 翻译
        ttk.Label(assist_frame, text="AI翻译:").pack(side=tk.LEFT, padx=(20, 0))

        def ai_translate():
            """使用 AI 翻译当前条目"""
            provider_name = self.provider_var.get()
            if not provider_name:
                messagebox.showwarning("警告", "请先在主界面选择翻译引擎")
                return

            # 获取翻译器
            if provider_name not in self.batch_translator.providers:
                messagebox.showerror("错误", f"翻译引擎 '{provider_name}' 不可用")
                return

            provider = self.batch_translator.providers[provider_name]

            try:
                # 显示加载状态
                self.status_var.set(f"正在使用 {provider_name} 翻译...")
                self.root.update()

                # 翻译
                result = provider.translate(entry.original_text, 'en', 'zh')

                if result:
                    # 将翻译结果填入译文框
                    translation_text.delete(1.0, tk.END)
                    translation_text.insert(1.0, result)
                    self.status_var.set(f"翻译完成 - {provider_name}")
                    messagebox.showinfo("AI翻译", "翻译完成")
                else:
                    self.status_var.set("翻译失败")
                    messagebox.showerror("错误", "AI 翻译失败,请检查配置")

            except Exception as e:
                self.status_var.set("翻译失败")
                messagebox.showerror("错误", f"AI 翻译失败:\n{e}")

        ttk.Button(assist_frame, text="翻译", command=ai_translate).pack(side=tk.LEFT, padx=5)

        # 百度翻译
        ttk.Label(assist_frame, text="百度翻译:").pack(side=tk.LEFT, padx=(20, 0))

        def baidu_translate():
            """使用百度翻译"""
            if 'baidu' not in self.batch_translator.providers:
                messagebox.showwarning("警告", "百度翻译未配置或不可用\n\n请在设置中配置百度翻译 API")
                return

            provider = self.batch_translator.providers['baidu']

            try:
                # 显示加载状态
                self.status_var.set("正在使用百度翻译...")
                self.root.update()

                # 翻译
                result = provider.translate(entry.original_text, 'en', 'zh')

                if result:
                    # 将翻译结果填入译文框
                    translation_text.delete(1.0, tk.END)
                    translation_text.insert(1.0, result)
                    self.status_var.set("百度翻译完成")
                    messagebox.showinfo("百度翻译", "翻译完成")
                else:
                    self.status_var.set("翻译失败")
                    messagebox.showerror("错误", "百度翻译失败,请检查配置")

            except Exception as e:
                self.status_var.set("翻译失败")
                messagebox.showerror("错误", f"百度翻译失败:\n{e}")

        ttk.Button(assist_frame, text="翻译", command=baidu_translate).pack(side=tk.LEFT, padx=5)

        # 译文
        ttk.Label(dialog, text="译文:").pack(anchor=tk.W, padx=10, pady=(10, 0))
        translation_text = scrolledtext.ScrolledText(dialog, height=8, wrap=tk.WORD)
        translation_text.pack(fill=tk.BOTH, padx=10, pady=5)
        if entry.translated_text:
            translation_text.insert(1.0, entry.translated_text)

        # 按钮
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        def save_and_close():
            translated_text = translation_text.get(1.0, tk.END).strip()
            if translated_text:
                entry.translated_text = translated_text
                entry.status = 'completed'
                self.service.translation_repo.save(entry)

                # 保存到翻译记忆
                self.memory_logic.save_translation(entry.original_text, translated_text, entry.xml_path)

                self._load_translations()
                self._update_progress()
                dialog.destroy()
            else:
                messagebox.showwarning("警告", "译文不能为空")

        def skip_and_close():
            entry.status = 'skipped'
            self.service.translation_repo.save(entry)
            self._load_translations()
            self._update_progress()
            dialog.destroy()

        ttk.Button(button_frame, text="保存", command=save_and_close).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="跳过", command=skip_and_close).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="取消", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)

    def _batch_translate(self):
        """批量翻译"""
        if not self.current_mod_name:
            messagebox.showwarning("警告", "请先提取 MOD")
            return

        provider_name = self.provider_var.get()
        if not provider_name:
            messagebox.showwarning("警告", "请选择翻译引擎")
            return

        # 确认对话框
        stats = self.service.get_translation_progress(self.current_mod_name)
        pending_count = stats['pending']

        if pending_count == 0:
            messagebox.showinfo("提示", "没有待翻译的条目")
            return

        if not messagebox.askyesno(
                "确认",
                f"将使用 {provider_name} 翻译 {pending_count} 条待翻译条目\n\n是否继续?"
        ):
            return

        # 在后台线程执行批量翻译
        def translate_thread():
            try:
                # 获取待翻译条目
                entries = self.service.get_translations(
                    self.current_mod_name,
                    status='pending',
                    limit=1000
                )

                total = len(entries)
                if total == 0:
                    self.root.after(0, lambda: messagebox.showinfo("提示", "没有待翻译的条目"))
                    return

                # 创建进度对话框
                progress_dialog = [None]  # 使用列表以便在闭包中修改

                def create_progress_dialog():
                    dialog = tk.Toplevel(self.root)
                    dialog.title("批量翻译进度")
                    dialog.geometry("500x150")
                    dialog.transient(self.root)
                    dialog.grab_set()

                    # 进度标签
                    status_label = ttk.Label(dialog, text="正在初始化...", font=("", 10))
                    status_label.pack(pady=20)

                    # 进度条
                    progress = ttk.Progressbar(dialog, length=400, mode='determinate')
                    progress.pack(pady=10)
                    progress['maximum'] = total
                    progress['value'] = 0

                    # 进度文本
                    progress_text = ttk.Label(dialog, text=f"0 / {total} (0%)")
                    progress_text.pack(pady=10)

                    dialog.protocol("WM_DELETE_WINDOW", lambda: None)  # 禁止关闭

                    progress_dialog[0] = {
                        'dialog': dialog,
                        'status_label': status_label,
                        'progress': progress,
                        'progress_text': progress_text
                    }

                self.root.after(0, create_progress_dialog)

                # 等待对话框创建
                import time
                while progress_dialog[0] is None:
                    time.sleep(0.1)

                # 进度回调函数
                def progress_callback(current, total_count, entry):
                    def update():
                        if progress_dialog[0]:
                            pd = progress_dialog[0]
                            pd['progress']['value'] = current
                            percentage = int(current / total_count * 100)
                            pd['progress_text']['text'] = f"{current} / {total_count} ({percentage}%)"
                            # 显示当前翻译的文本
                            text_preview = entry.original_text[:50] if hasattr(entry, 'original_text') else "..."
                            pd['status_label']['text'] = f"正在翻译: {text_preview}..."
                    self.root.after(0, update)

                self.status_var.set(f"正在使用 {provider_name} 批量翻译...")

                # 执行翻译
                result = self.batch_translator.batch_translate(
                    entries,
                    provider_name=provider_name,
                    use_memory=True,
                    progress_callback=progress_callback
                )

                # 保存结果到数据库
                saved_count = 0
                for entry in result['results']:
                    if entry.translated_text and entry.translated_text.strip():
                        try:
                            self.service.translation_repo.save(entry)
                            saved_count += 1
                        except Exception as e:
                            print(f"保存条目失败 {entry.id}: {e}")

                print(f"批量翻译完成: 成功={result['success_count']}, 失败={result['failed_count']}, 已保存={saved_count}")

                # 关闭进度对话框
                def close_progress():
                    if progress_dialog[0]:
                        progress_dialog[0]['dialog'].destroy()
                        progress_dialog[0] = None

                self.root.after(0, close_progress)

                # 更新界面 (确保保存完成后再刷新)
                self.root.after(0, lambda: self._on_batch_translate_complete(result))

            except Exception as e:
                # 关闭进度对话框
                if progress_dialog[0]:
                    self.root.after(0, lambda: progress_dialog[0]['dialog'].destroy())

                self.root.after(0, lambda: messagebox.showerror("错误", f"批量翻译失败:\n{e}"))
                self.root.after(0, lambda: self.status_var.set("翻译失败"))

        threading.Thread(target=translate_thread, daemon=True).start()

    def _on_batch_translate_complete(self, result):
        """批量翻译完成回调"""
        messagebox.showinfo(
            "翻译完成",
            f"成功: {result['success_count']}\n"
            f"失败: {result['failed_count']}\n"
            f"来自翻译记忆: {result['memory_hit_count']}"
        )

        self._load_translations()
        self._update_progress()
        self.status_var.set("批量翻译完成")

    def _save_translations(self):
        """保存翻译 (手动触发)"""
        if not self.current_mod_name:
            return

        try:
            # 更新会话
            stats = self.service.get_translation_progress(self.current_mod_name)
            self.session_repo.update_or_create(
                mod_name=self.current_mod_name,
                mod_path=self.current_mod_path,
                total_entries=stats['total'],
                translated_entries=stats['completed'],
                current_page=self.current_page
            )

            messagebox.showinfo("成功", "翻译进度已保存")
            self.status_var.set(f"已保存 - {datetime.now().strftime('%H:%M:%S')}")

        except Exception as e:
            messagebox.showerror("错误", f"保存失败:\n{e}")

    def _auto_save_translations(self):
        """自动保存翻译 (定时触发,静默保存)"""
        if not self.current_mod_name:
            return

        try:
            # 更新会话
            stats = self.service.get_translation_progress(self.current_mod_name)
            self.session_repo.update_or_create(
                mod_name=self.current_mod_name,
                mod_path=self.current_mod_path,
                total_entries=stats['total'],
                translated_entries=stats['completed'],
                current_page=self.current_page
            )

            # 静默更新状态栏
            self.status_var.set(f"✓ 自动保存 - {datetime.now().strftime('%H:%M:%S')}")

        except Exception as e:
            # 静默失败,只更新状态栏
            self.status_var.set(f"✗ 自动保存失败 - {datetime.now().strftime('%H:%M:%S')}")

    def _export_translations(self):
        """导出翻译"""
        if not self.current_mod_name or not self.current_mod_path:
            messagebox.showwarning("警告", "请先提取 MOD")
            return

        try:
            result = self.service.export_translations(
                self.current_mod_name,
                self.current_mod_path
            )

            messagebox.showinfo(
                "导出成功",
                f"生成文件数: {result['total_files']}\n"
                f"导出条目数: {result['exported_entries']}\n"
                f"目标路径: {result['target_path']}"
            )

        except Exception as e:
            messagebox.showerror("错误", f"导出失败:\n{e}")

    def _open_glossary_manager(self):
        """打开术语库管理器"""
        try:
            from .glossary_dialog import GlossaryDialog
            dialog = GlossaryDialog(self.root, self.service.glossary_repo)
        except Exception as e:
            messagebox.showerror("错误", f"打开术语库管理器失败:\n{e}")

    def _open_memory_manager(self):
        """打开翻译记忆管理器"""
        try:
            from .memory_dialog import MemoryDialog
            from ..logic.translation_memory import TranslationMemoryLogic
            from ..data.translation_memory_repository import TranslationMemoryRepository

            # 创建翻译记忆逻辑层
            memory_repo = TranslationMemoryRepository(self.service.db)
            memory_logic = TranslationMemoryLogic(memory_repo, self.service.glossary_repo)

            dialog = MemoryDialog(self.root, memory_logic)
        except Exception as e:
            messagebox.showerror("错误", f"打开翻译记忆管理器失败:\n{e}")

    def _open_settings(self):
        """打开设置对话框"""
        try:
            from .settings_dialog import SettingsDialog
            dialog = SettingsDialog(self.root, self.config)

            # 设置对话框关闭后,重新初始化翻译器并刷新翻译引擎列表
            self.root.wait_window(dialog.dialog)
            self._reinitialize_translator()
            self._refresh_provider_list()

        except Exception as e:
            messagebox.showerror("错误", f"打开设置对话框失败:\n{e}")

    def _reinitialize_translator(self):
        """重新初始化翻译器 - 使配置更改立即生效"""
        try:
            # 重新加载配置
            self.config._load_config()

            # 重新初始化批量翻译器
            self.batch_translator = BatchTranslatorLogic(self.config, self.memory_logic)

            # 更新状态栏
            self.status_var.set("翻译引擎配置已更新")

        except Exception as e:
            print(f"重新初始化翻译器失败: {e}")
            messagebox.showwarning("警告", f"翻译引擎重新加载失败:\n{e}\n请重启应用以应用新配置")

    def _refresh_provider_list(self):
        """刷新翻译引擎下拉列表"""
        providers = self.batch_translator.get_available_providers()
        self.provider_combo['values'] = providers

        # 如果当前选择的引擎不可用,选择第一个可用的
        if self.provider_var.get() not in providers and providers:
            self.provider_var.set(providers[0])

    def _check_and_resume_session(self):
        """检查并恢复会话"""
        try:
            sessions = self.session_repo.get_all_active()
            if not sessions:
                return

            # 只处理第一个会话
            session = sessions[0]

            if messagebox.askyesno(
                    "恢复会话",
                    f"发现未完成的翻译会话:\n\n"
                    f"MOD: {session['mod_name']}\n"
                    f"进度: {session['translated_entries']}/{session['total_entries']}\n\n"
                    f"是否继续?"
            ):
                self.current_mod_name = session['mod_name']
                self.current_mod_path = session['mod_path']
                self.current_page = session['current_page']

                self.mod_path_var.set(session['mod_path'])
                self.mod_name_label.config(text=session['mod_name'], foreground="black")

                self._load_translations()
                self._update_progress()

                self.status_var.set("已恢复会话")

        except Exception as e:
            print(f"恢复会话失败: {e}")

    def run(self):
        """运行 GUI"""
        # 启动自动保存 (使用静默保存方法)
        self.auto_save.start_auto_save(self._auto_save_translations)

        # 设置关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

        # 运行主循环
        self.root.mainloop()

    def _on_closing(self):
        """关闭窗口事件"""
        # 停止自动保存
        self.auto_save.stop_auto_save()

        # 保存当前进度
        if self.current_mod_name:
            try:
                self._save_translations()
            except Exception:
                pass

        # 关闭数据库
        self.service.close()

        # 销毁窗口
        self.root.destroy()


def start_gui():
    """启动 GUI 应用"""
    app = RimworldTranslatorGUI()
    app.run()
