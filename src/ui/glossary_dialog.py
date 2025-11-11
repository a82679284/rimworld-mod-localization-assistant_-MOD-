"""
术语库管理对话框
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from typing import Optional, List, Dict
from pathlib import Path
from ..data.glossary_repository import GlossaryRepository
from ..models.glossary_entry import GlossaryEntry


class GlossaryDialog:
    """术语库管理对话框"""

    def __init__(self, parent: tk.Tk, glossary_repo: GlossaryRepository):
        """
        初始化术语库对话框

        Args:
            parent: 父窗口
            glossary_repo: 术语库Repository
        """
        self.glossary_repo = glossary_repo

        # 创建顶层窗口
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("术语库管理")
        self.dialog.geometry("900x600")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self._create_widgets()
        self._load_terms()

    def _create_widgets(self):
        """创建界面组件"""
        # 主容器
        main_frame = ttk.Frame(self.dialog, padding=10)
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.dialog.columnconfigure(0, weight=1)
        self.dialog.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)

        # ========== 顶部工具栏 ==========
        toolbar = ttk.Frame(main_frame)
        toolbar.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))

        # 搜索框
        ttk.Label(toolbar, text="搜索:").pack(side=tk.LEFT, padx=(0, 5))
        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *args: self._on_search())
        search_entry = ttk.Entry(toolbar, textvariable=self.search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=(0, 20))

        # 操作按钮
        ttk.Button(
            toolbar,
            text="➕ 添加术语",
            command=self._add_term
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            toolbar,
            text="✏ 编辑",
            command=self._edit_term
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            toolbar,
            text="🗑 删除",
            command=self._delete_term
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            toolbar,
            text="📥 导入CSV",
            command=self._import_csv
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            toolbar,
            text="🎮 导入官方术语",
            command=self._import_from_rimworld
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            toolbar,
            text="🔍 在线搜索",
            command=self._online_search
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            toolbar,
            text="📊 统计",
            command=self._show_statistics
        ).pack(side=tk.LEFT, padx=2)

        # ========== 术语列表 ==========
        list_frame = ttk.Frame(main_frame)
        list_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        # 创建Treeview
        columns = ("ID", "英文", "中文", "分类", "优先级", "备注")
        self.tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show="headings",
            selectmode="browse"
        )

        # 设置列
        self.tree.heading("ID", text="ID")
        self.tree.heading("英文", text="英文术语")
        self.tree.heading("中文", text="中文术语")
        self.tree.heading("分类", text="分类")
        self.tree.heading("优先级", text="优先级")
        self.tree.heading("备注", text="备注")

        self.tree.column("ID", width=50, anchor=tk.CENTER)
        self.tree.column("英文", width=200, anchor=tk.W)
        self.tree.column("中文", width=200, anchor=tk.W)
        self.tree.column("分类", width=100, anchor=tk.CENTER)
        self.tree.column("优先级", width=80, anchor=tk.CENTER)
        self.tree.column("备注", width=250, anchor=tk.W)

        # 添加滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

        # 双击编辑
        self.tree.bind("<Double-Button-1>", lambda e: self._edit_term())

        # ========== 底部状态栏 ==========
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(
            main_frame,
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        status_bar.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(10, 0))

    def _load_terms(self, keyword: Optional[str] = None):
        """加载术语列表"""
        try:
            # 清空列表
            for item in self.tree.get_children():
                self.tree.delete(item)

            # 获取术语
            if keyword:
                terms = self.glossary_repo.search_terms(keyword)
            else:
                terms = self.glossary_repo.find_all()

            # 填充数据
            for term in terms:
                self.tree.insert("", tk.END, values=(
                    term.id,
                    term.term_en,
                    term.term_zh,
                    term.category or "",
                    term.priority,
                    (term.note[:50] + "...") if term.note and len(term.note) > 50 else (term.note or "")
                ))

            # 更新状态
            self.status_var.set(f"共 {len(terms)} 个术语")

        except Exception as e:
            messagebox.showerror("错误", f"加载术语列表失败:\n{e}")

    def _on_search(self):
        """搜索事件"""
        keyword = self.search_var.get().strip()
        self._load_terms(keyword if keyword else None)

    def _add_term(self):
        """添加术语"""
        dialog = TermEditDialog(self.dialog, None, self.glossary_repo)
        self.dialog.wait_window(dialog.dialog)
        if dialog.result:
            self._load_terms()

    def _edit_term(self):
        """编辑术语"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请选择要编辑的术语")
            return

        # 获取选中的术语ID
        item = self.tree.item(selection[0])
        term_id = item['values'][0]

        # 获取术语详情
        term = self.glossary_repo.find_by_id(term_id)
        if not term:
            messagebox.showerror("错误", "找不到该术语")
            return

        # 打开编辑对话框
        dialog = TermEditDialog(self.dialog, term, self.glossary_repo)
        self.dialog.wait_window(dialog.dialog)
        if dialog.result:
            self._load_terms()

    def _delete_term(self):
        """删除术语"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请选择要删除的术语")
            return

        if not messagebox.askyesno("确认", "确定要删除选中的术语吗?"):
            return

        item = self.tree.item(selection[0])
        term_id = item['values'][0]

        try:
            if self.glossary_repo.delete_by_id(term_id):
                messagebox.showinfo("成功", "术语已删除")
                self._load_terms()
            else:
                messagebox.showerror("错误", "删除失败")
        except Exception as e:
            messagebox.showerror("错误", f"删除失败:\n{e}")

    def _import_csv(self):
        """导入CSV文件"""
        file_path = filedialog.askopenfilename(
            title="选择CSV文件",
            filetypes=[("CSV文件", "*.csv"), ("所有文件", "*.*")]
        )

        if not file_path:
            return

        try:
            count = self.glossary_repo.import_from_csv(Path(file_path))
            messagebox.showinfo("成功", f"已导入 {count} 个术语")
            self._load_terms()
        except Exception as e:
            messagebox.showerror("错误", f"导入失败:\n{e}")

    def _import_from_rimworld(self):
        """从Rimworld游戏目录导入官方术语"""
        # 询问游戏路径
        game_path = filedialog.askdirectory(
            title="选择Rimworld游戏根目录",
            mustexist=True
        )

        if not game_path:
            return

        try:
            from ..logic.glossary_importer import GlossaryImporter

            importer = GlossaryImporter(self.glossary_repo)

            # 检查路径是否有效
            game_path_obj = Path(game_path)
            if not (game_path_obj / "Data" / "Core").exists():
                messagebox.showerror(
                    "错误",
                    "无效的Rimworld游戏目录!\n请确保选择的是游戏根目录,包含Data文件夹。"
                )
                return

            # 获取支持的分类
            categories = importer.get_supported_categories(game_path_obj)

            if not categories:
                messagebox.showerror("错误", "未找到可导入的术语分类")
                return

            # 询问用户选择分类
            dialog = CategorySelectDialog(self.dialog, categories)
            self.dialog.wait_window(dialog.dialog)

            if not dialog.selected_categories:
                return

            # 显示进度对话框
            progress_window = tk.Toplevel(self.dialog)
            progress_window.title("导入中")
            progress_window.geometry("400x150")
            progress_window.transient(self.dialog)
            progress_window.grab_set()

            ttk.Label(
                progress_window,
                text="正在从Rimworld游戏目录导入术语...\n这可能需要几分钟时间,请耐心等待。",
                padding=20
            ).pack()

            progress_bar = ttk.Progressbar(
                progress_window,
                mode='indeterminate',
                length=300
            )
            progress_bar.pack(pady=10)
            progress_bar.start()

            # 在后台线程执行导入
            import threading

            def do_import():
                try:
                    result = importer.import_from_rimworld(
                        game_path_obj,
                        dialog.selected_categories
                    )

                    # 在主线程显示结果
                    self.dialog.after(0, lambda: self._show_import_result(result, progress_window))

                except Exception as e:
                    self.dialog.after(
                        0,
                        lambda: messagebox.showerror("错误", f"导入失败:\n{e}")
                    )
                    self.dialog.after(0, progress_window.destroy)

            thread = threading.Thread(target=do_import, daemon=True)
            thread.start()

        except Exception as e:
            messagebox.showerror("错误", f"导入失败:\n{e}")

    def _show_import_result(self, result: dict, progress_window):
        """显示导入结果"""
        progress_window.destroy()

        stats_text = (
            f"导入完成!\n\n"
            f"总计: {result['total']} 个\n"
            f"成功: {result['success']} 个\n"
            f"失败: {result['failed']} 个\n\n"
            f"分类统计:\n"
        )

        for cat, count in result['categories'].items():
            stats_text += f"  {cat}: {count} 个\n"

        messagebox.showinfo("导入完成", stats_text)
        self._load_terms()

    def _online_search(self):
        """在线搜索术语翻译"""
        # 询问要搜索的术语
        search_term = tk.simpledialog.askstring(
            "在线搜索",
            "请输入要搜索的英文术语:",
            parent=self.dialog
        )

        if not search_term or not search_term.strip():
            return

        try:
            from ..logic.online_translation_searcher import OnlineTranslationSearcher

            searcher = OnlineTranslationSearcher()

            # 显示进度对话框
            progress_window = tk.Toplevel(self.dialog)
            progress_window.title("搜索中")
            progress_window.geometry("300x100")
            progress_window.transient(self.dialog)
            progress_window.grab_set()

            ttk.Label(
                progress_window,
                text=f"正在搜索 \"{search_term}\" 的翻译...",
                padding=20
            ).pack()

            progress_bar = ttk.Progressbar(
                progress_window,
                mode='indeterminate',
                length=250
            )
            progress_bar.pack(pady=10)
            progress_bar.start()

            # 在后台线程执行搜索
            import threading

            def do_search():
                try:
                    sources = ['baidu', 'deepseek']  # 使用快速可靠的来源
                    results = searcher.search_all_sources(search_term, sources)

                    # 在主线程显示结果
                    self.dialog.after(
                        0,
                        lambda: self._show_search_results(search_term, results, progress_window)
                    )

                except Exception as e:
                    self.dialog.after(
                        0,
                        lambda: messagebox.showerror("错误", f"搜索失败:\n{e}")
                    )
                    self.dialog.after(0, progress_window.destroy)

            thread = threading.Thread(target=do_search, daemon=True)
            thread.start()

        except Exception as e:
            messagebox.showerror("错误", f"搜索失败:\n{e}")

    def _show_search_results(self, term_en: str, results: list, progress_window):
        """显示搜索结果"""
        progress_window.destroy()

        if not results:
            messagebox.showinfo("搜索结果", f"未找到 \"{term_en}\" 的翻译")
            return

        # 创建结果选择对话框
        dialog = SearchResultDialog(self.dialog, term_en, results, self.glossary_repo)
        self.dialog.wait_window(dialog.dialog)

        if dialog.saved:
            self._load_terms()

    def _show_statistics(self):
        """显示统计信息"""
        try:
            total = self.glossary_repo.count_all()
            categories = self.glossary_repo.get_categories()

            stats_text = f"总术语数: {total}\n\n"
            stats_text += "分类统计:\n"

            for cat in categories:
                count = self.glossary_repo.count_by_category(cat)
                stats_text += f"  {cat}: {count}\n"

            messagebox.showinfo("术语库统计", stats_text)
        except Exception as e:
            messagebox.showerror("错误", f"获取统计信息失败:\n{e}")


class TermEditDialog:
    """术语编辑对话框"""

    def __init__(
        self,
        parent: tk.Toplevel,
        term: Optional[GlossaryEntry],
        glossary_repo: GlossaryRepository
    ):
        """
        初始化编辑对话框

        Args:
            parent: 父窗口
            term: 术语条目(None表示新增)
            glossary_repo: 术语库Repository
        """
        self.term = term
        self.glossary_repo = glossary_repo
        self.result = False

        # 创建对话框
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("编辑术语" if term else "添加术语")
        self.dialog.geometry("500x400")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self._create_widgets()

        if term:
            self._load_term_data()

    def _create_widgets(self):
        """创建界面组件"""
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.dialog.columnconfigure(0, weight=1)
        self.dialog.rowconfigure(0, weight=1)

        # 英文术语
        ttk.Label(main_frame, text="英文术语:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.term_en_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.term_en_var, width=40).grid(
            row=0, column=1, sticky=(tk.W, tk.E), pady=5
        )

        # 中文术语
        ttk.Label(main_frame, text="中文术语:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.term_zh_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.term_zh_var, width=40).grid(
            row=1, column=1, sticky=(tk.W, tk.E), pady=5
        )

        # 分类
        ttk.Label(main_frame, text="分类:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.category_var = tk.StringVar()
        category_combo = ttk.Combobox(
            main_frame,
            textvariable=self.category_var,
            values=["物品", "角色", "技能", "建筑", "事件", "其他"],
            width=37
        )
        category_combo.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5)

        # 优先级
        ttk.Label(main_frame, text="优先级:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.priority_var = tk.IntVar(value=0)
        ttk.Spinbox(
            main_frame,
            from_=0,
            to=100,
            textvariable=self.priority_var,
            width=38
        ).grid(row=3, column=1, sticky=(tk.W, tk.E), pady=5)

        # 备注
        ttk.Label(main_frame, text="备注:").grid(row=4, column=0, sticky=(tk.W, tk.N), pady=5)
        self.note_text = tk.Text(main_frame, width=40, height=6)
        self.note_text.grid(row=4, column=1, sticky=(tk.W, tk.E), pady=5)

        # 按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=2, pady=20)

        ttk.Button(button_frame, text="保存", command=self._save).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="取消", command=self.dialog.destroy).pack(side=tk.LEFT, padx=5)

        main_frame.columnconfigure(1, weight=1)

    def _load_term_data(self):
        """加载术语数据"""
        if not self.term:
            return

        self.term_en_var.set(self.term.term_en)
        self.term_zh_var.set(self.term.term_zh)
        self.category_var.set(self.term.category or "")
        self.priority_var.set(self.term.priority)
        if self.term.note:
            self.note_text.insert("1.0", self.term.note)

    def _save(self):
        """保存术语"""
        term_en = self.term_en_var.get().strip()
        term_zh = self.term_zh_var.get().strip()

        if not term_en or not term_zh:
            messagebox.showwarning("警告", "英文术语和中文术语不能为空")
            return

        try:
            entry = GlossaryEntry(
                id=self.term.id if self.term else None,
                term_en=term_en,
                term_zh=term_zh,
                category=self.category_var.get().strip() or None,
                priority=self.priority_var.get(),
                note=self.note_text.get("1.0", tk.END).strip() or None,
                source="user"
            )

            self.glossary_repo.save(entry)
            self.result = True
            messagebox.showinfo("成功", "术语已保存")
            self.dialog.destroy()

        except Exception as e:
            messagebox.showerror("错误", f"保存失败:\n{e}")


class CategorySelectDialog:
    """分类选择对话框"""

    def __init__(self, parent: tk.Toplevel, categories: List[str]):
        """
        初始化分类选择对话框

        Args:
            parent: 父窗口
            categories: 可选分类列表
        """
        self.selected_categories = []

        # 创建对话框
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("选择要导入的分类")
        self.dialog.geometry("400x500")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # 说明
        ttk.Label(
            self.dialog,
            text="请选择要导入的术语分类:",
            padding=10
        ).pack(anchor=tk.W)

        # 分类列表(可多选)
        list_frame = ttk.Frame(self.dialog, padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True)

        self.listbox = tk.Listbox(list_frame, selectmode=tk.MULTIPLE, height=20)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=scrollbar.set)

        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 填充分类
        for cat in categories:
            self.listbox.insert(tk.END, cat)

        # 按钮
        button_frame = ttk.Frame(self.dialog, padding=10)
        button_frame.pack(fill=tk.X)

        ttk.Button(button_frame, text="全选", command=self._select_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="全不选", command=self._deselect_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="确定", command=self._confirm).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="取消", command=self.dialog.destroy).pack(side=tk.RIGHT, padx=5)

    def _select_all(self):
        """全选"""
        self.listbox.select_set(0, tk.END)

    def _deselect_all(self):
        """全不选"""
        self.listbox.selection_clear(0, tk.END)

    def _confirm(self):
        """确认"""
        selection = self.listbox.curselection()
        self.selected_categories = [self.listbox.get(i) for i in selection]
        self.dialog.destroy()


class SearchResultDialog:
    """搜索结果选择对话框"""

    def __init__(
        self,
        parent: tk.Toplevel,
        term_en: str,
        results: List[Dict],
        glossary_repo: GlossaryRepository
    ):
        """
        初始化搜索结果对话框

        Args:
            parent: 父窗口
            term_en: 英文术语
            results: 搜索结果列表
            glossary_repo: 术语库Repository
        """
        self.term_en = term_en
        self.results = results
        self.glossary_repo = glossary_repo
        self.saved = False

        # 创建对话框
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("搜索结果")
        self.dialog.geometry("600x400")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # 标题
        ttk.Label(
            self.dialog,
            text=f"为 \"{term_en}\" 找到以下翻译:",
            font=("Arial", 10, "bold"),
            padding=10
        ).pack(anchor=tk.W)

        # 结果列表
        list_frame = ttk.Frame(self.dialog, padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("翻译", "来源", "置信度", "备注")
        self.tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show="headings",
            selectmode="browse"
        )

        self.tree.heading("翻译", text="中文翻译")
        self.tree.heading("来源", text="来源")
        self.tree.heading("置信度", text="置信度")
        self.tree.heading("备注", text="备注")

        self.tree.column("翻译", width=200)
        self.tree.column("来源", width=120)
        self.tree.column("置信度", width=80, anchor=tk.CENTER)
        self.tree.column("备注", width=180)

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 填充结果
        for result in results:
            self.tree.insert("", tk.END, values=(
                result['term_zh'],
                result['source'],
                f"{result['confidence']:.0%}",
                result['note']
            ))

        # 按钮
        button_frame = ttk.Frame(self.dialog, padding=10)
        button_frame.pack(fill=tk.X)

        ttk.Button(
            button_frame,
            text="保存选中的翻译",
            command=self._save_selected
        ).pack(side=tk.RIGHT, padx=5)

        ttk.Button(
            button_frame,
            text="关闭",
            command=self.dialog.destroy
        ).pack(side=tk.RIGHT, padx=5)

    def _save_selected(self):
        """保存选中的翻译"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请选择一个翻译结果")
            return

        item = self.tree.item(selection[0])
        values = item['values']
        term_zh = values[0]
        source = values[1]

        try:
            entry = GlossaryEntry(
                term_en=self.term_en,
                term_zh=term_zh,
                category="在线搜索",
                priority=70,  # 在线搜索结果优先级
                source=source,
                note=f"通过在线搜索获得"
            )

            self.glossary_repo.save(entry)
            self.saved = True
            messagebox.showinfo("成功", "术语已保存到术语库")
            self.dialog.destroy()

        except Exception as e:
            messagebox.showerror("错误", f"保存失败:\n{e}")

