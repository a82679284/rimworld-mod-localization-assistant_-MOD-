"""
翻译记忆管理对话框
"""
import tkinter as tk
from tkinter import ttk, messagebox
from ..data.translation_memory_repository import TranslationMemoryRepository
from ..logic.translation_memory import TranslationMemoryLogic


class MemoryDialog:
    """翻译记忆管理对话框"""

    def __init__(
        self,
        parent: tk.Tk,
        memory_logic: TranslationMemoryLogic
    ):
        """
        初始化翻译记忆对话框

        Args:
            parent: 父窗口
            memory_logic: 翻译记忆逻辑层
        """
        self.memory_logic = memory_logic
        self.memory_repo = memory_logic.memory_repo

        # 创建顶层窗口
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("翻译记忆管理")
        self.dialog.geometry("900x600")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self._create_widgets()
        self._load_statistics()

    def _create_widgets(self):
        """创建界面组件"""
        # 主容器
        main_frame = ttk.Frame(self.dialog, padding=10)
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.dialog.columnconfigure(0, weight=1)
        self.dialog.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)

        # ========== 统计信息区域 ==========
        stats_frame = ttk.LabelFrame(main_frame, text="翻译记忆统计", padding=10)
        stats_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))

        self.stats_label = ttk.Label(stats_frame, text="加载中...", font=("Arial", 10))
        self.stats_label.pack(anchor=tk.W)

        # ========== 搜索测试区域 ==========
        search_frame = ttk.LabelFrame(main_frame, text="搜索翻译记忆", padding=10)
        search_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))

        # 搜索输入
        input_frame = ttk.Frame(search_frame)
        input_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(input_frame, text="源文本:").pack(side=tk.LEFT, padx=(0, 5))
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(input_frame, textvariable=self.search_var, width=50)
        search_entry.pack(side=tk.LEFT, padx=(0, 10), fill=tk.X, expand=True)

        ttk.Button(
            input_frame,
            text="🔍 精确匹配",
            command=self._exact_search
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            input_frame,
            text="🔎 模糊匹配",
            command=self._fuzzy_search
        ).pack(side=tk.LEFT, padx=2)

        # 搜索结果
        self.result_text = tk.Text(search_frame, height=8, wrap=tk.WORD)
        self.result_text.pack(fill=tk.BOTH, expand=True)

        result_scroll = ttk.Scrollbar(
            search_frame,
            orient=tk.VERTICAL,
            command=self.result_text.yview
        )
        self.result_text.configure(yscrollcommand=result_scroll.set)

        # ========== 操作按钮区域 ==========
        action_frame = ttk.LabelFrame(main_frame, text="维护操作", padding=10)
        action_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 10))

        ttk.Label(
            action_frame,
            text="⚠ 清理操作将删除超过指定天数未使用的翻译记忆条目",
            foreground="red"
        ).pack(anchor=tk.W, pady=(0, 10))

        cleanup_frame = ttk.Frame(action_frame)
        cleanup_frame.pack(fill=tk.X)

        ttk.Label(cleanup_frame, text="保留天数:").pack(side=tk.LEFT, padx=(0, 5))
        self.days_var = tk.IntVar(value=365)
        ttk.Spinbox(
            cleanup_frame,
            from_=30,
            to=3650,
            textvariable=self.days_var,
            width=10
        ).pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(
            cleanup_frame,
            text="🗑 清理旧条目",
            command=self._cleanup_old_entries
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            cleanup_frame,
            text="🔄 刷新统计",
            command=self._load_statistics
        ).pack(side=tk.LEFT, padx=5)

        # ========== 状态栏 ==========
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(
            main_frame,
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        status_bar.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(10, 0))

    def _load_statistics(self):
        """加载统计信息"""
        try:
            stats = self.memory_logic.get_statistics()

            stats_text = (
                f"📊 总记忆条目: {stats['total_entries']} 个\n"
                f"🔢 总使用次数: {stats['total_uses']} 次\n"
                f"📈 平均使用次数: {stats['avg_uses']} 次/条目"
            )

            self.stats_label.config(text=stats_text)
            self.status_var.set("统计信息已更新")

        except Exception as e:
            messagebox.showerror("错误", f"加载统计信息失败:\n{e}")

    def _exact_search(self):
        """精确匹配搜索"""
        source_text = self.search_var.get().strip()
        if not source_text:
            messagebox.showwarning("警告", "请输入要搜索的源文本")
            return

        try:
            result = self.memory_repo.find_exact_match(source_text)

            self.result_text.delete("1.0", tk.END)

            if result:
                self.result_text.insert("1.0", f"✅ 找到精确匹配:\n\n{result}")
                self.status_var.set("找到精确匹配")
            else:
                self.result_text.insert("1.0", "❌ 未找到精确匹配的翻译记忆")
                self.status_var.set("未找到匹配")

        except Exception as e:
            messagebox.showerror("错误", f"搜索失败:\n{e}")

    def _fuzzy_search(self):
        """模糊匹配搜索"""
        source_text = self.search_var.get().strip()
        if not source_text:
            messagebox.showwarning("警告", "请输入要搜索的源文本")
            return

        try:
            matches = self.memory_repo.find_similar_matches(source_text, limit=5)

            self.result_text.delete("1.0", tk.END)

            if matches:
                self.result_text.insert("1.0", f"🔎 找到 {len(matches)} 个相似匹配:\n\n")

                for i, (src, tgt, similarity) in enumerate(matches, 1):
                    self.result_text.insert(
                        tk.END,
                        f"[{i}] 相似度: {similarity:.2%}\n"
                        f"源: {src}\n"
                        f"译: {tgt}\n\n"
                    )

                self.status_var.set(f"找到 {len(matches)} 个相似匹配")
            else:
                self.result_text.insert("1.0", "❌ 未找到相似的翻译记忆")
                self.status_var.set("未找到匹配")

        except Exception as e:
            messagebox.showerror("错误", f"搜索失败:\n{e}")

    def _cleanup_old_entries(self):
        """清理旧条目"""
        days = self.days_var.get()

        if not messagebox.askyesno(
            "确认",
            f"确定要清理超过 {days} 天未使用的翻译记忆条目吗?\n此操作不可恢复!"
        ):
            return

        try:
            deleted = self.memory_logic.cleanup_old_entries(days)
            messagebox.showinfo("成功", f"已清理 {deleted} 个旧条目")
            self._load_statistics()

        except Exception as e:
            messagebox.showerror("错误", f"清理失败:\n{e}")
