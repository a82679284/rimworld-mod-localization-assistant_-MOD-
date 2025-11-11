"""
设置对话框 - API 配置管理
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Dict
from pathlib import Path


class SettingsDialog:
    """设置对话框"""

    def __init__(self, parent: tk.Tk, config):
        """
        初始化设置对话框

        Args:
            parent: 父窗口
            config: Config 实例
        """
        self.config = config
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("设置")
        self.dialog.geometry("700x600")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # 配置数据
        self.providers_config = config.get_translation_config().get('providers', {})
        self.rimworld_path = config.get_translation_config().get('rimworld_path', '')
        self.auto_save_interval = config.get_translation_config().get('auto_save_interval', 30)

        self._build_ui()

    def _build_ui(self):
        """构建界面"""
        # 创建选项卡
        notebook = ttk.Notebook(self.dialog)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # API 配置选项卡
        api_frame = ttk.Frame(notebook)
        notebook.add(api_frame, text="API 配置")
        self._build_api_tab(api_frame)

        # 通用设置选项卡
        general_frame = ttk.Frame(notebook)
        notebook.add(general_frame, text="通用设置")
        self._build_general_tab(general_frame)

        # 底部按钮
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(button_frame, text="保存", command=self._save_settings).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="取消", command=self.dialog.destroy).pack(side=tk.RIGHT)

    def _build_api_tab(self, parent):
        """构建 API 配置选项卡"""
        # 滚动框架
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # DeepSeek 配置
        self._build_deepseek_config(scrollable_frame)

        # Baidu 配置
        self._build_baidu_config(scrollable_frame)

        # Ollama 配置
        self._build_ollama_config(scrollable_frame)

    def _build_deepseek_config(self, parent):
        """构建 DeepSeek 配置"""
        frame = ttk.LabelFrame(parent, text="DeepSeek API", padding="10")
        frame.pack(fill=tk.X, padx=10, pady=10)

        deepseek_config = self.providers_config.get('deepseek', {})

        # 启用复选框
        self.deepseek_enabled_var = tk.BooleanVar(value=deepseek_config.get('enabled', False))
        ttk.Checkbutton(frame, text="启用 DeepSeek", variable=self.deepseek_enabled_var).grid(
            row=0, column=0, columnspan=2, sticky=tk.W, pady=5
        )

        # API Key
        ttk.Label(frame, text="API Key:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.deepseek_api_key_var = tk.StringVar(value=deepseek_config.get('api_key', ''))
        ttk.Entry(frame, textvariable=self.deepseek_api_key_var, width=50, show="*").grid(
            row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=5
        )

        # Base URL
        ttk.Label(frame, text="Base URL:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.deepseek_base_url_var = tk.StringVar(
            value=deepseek_config.get('base_url', 'https://api.deepseek.com/v1')
        )
        ttk.Entry(frame, textvariable=self.deepseek_base_url_var, width=50).grid(
            row=2, column=1, sticky=(tk.W, tk.E), pady=5, padx=5
        )

        # Model
        ttk.Label(frame, text="Model:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.deepseek_model_var = tk.StringVar(
            value=deepseek_config.get('model', 'deepseek-chat')
        )
        ttk.Entry(frame, textvariable=self.deepseek_model_var, width=50).grid(
            row=3, column=1, sticky=(tk.W, tk.E), pady=5, padx=5
        )

        frame.columnconfigure(1, weight=1)

    def _build_baidu_config(self, parent):
        """构建百度翻译配置"""
        frame = ttk.LabelFrame(parent, text="百度翻译 API", padding="10")
        frame.pack(fill=tk.X, padx=10, pady=10)

        baidu_config = self.providers_config.get('baidu', {})

        # 启用复选框
        self.baidu_enabled_var = tk.BooleanVar(value=baidu_config.get('enabled', False))
        ttk.Checkbutton(frame, text="启用百度翻译", variable=self.baidu_enabled_var).grid(
            row=0, column=0, columnspan=2, sticky=tk.W, pady=5
        )

        # API Key
        ttk.Label(frame, text="API Key:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.baidu_api_key_var = tk.StringVar(value=baidu_config.get('api_key', ''))
        ttk.Entry(frame, textvariable=self.baidu_api_key_var, width=50, show="*").grid(
            row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=5
        )

        # Secret Key
        ttk.Label(frame, text="Secret Key:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.baidu_secret_key_var = tk.StringVar(value=baidu_config.get('secret_key', ''))
        ttk.Entry(frame, textvariable=self.baidu_secret_key_var, width=50, show="*").grid(
            row=2, column=1, sticky=(tk.W, tk.E), pady=5, padx=5
        )

        # QPS Limit
        ttk.Label(frame, text="QPS 限制:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.baidu_qps_var = tk.IntVar(value=baidu_config.get('qps_limit', 10))
        ttk.Spinbox(frame, from_=1, to=100, textvariable=self.baidu_qps_var, width=48).grid(
            row=3, column=1, sticky=(tk.W, tk.E), pady=5, padx=5
        )

        frame.columnconfigure(1, weight=1)

    def _build_ollama_config(self, parent):
        """构建 Ollama 配置"""
        frame = ttk.LabelFrame(parent, text="Ollama (本地模型)", padding="10")
        frame.pack(fill=tk.X, padx=10, pady=10)

        ollama_config = self.providers_config.get('ollama', {})

        # 启用复选框
        self.ollama_enabled_var = tk.BooleanVar(value=ollama_config.get('enabled', False))
        ttk.Checkbutton(frame, text="启用 Ollama", variable=self.ollama_enabled_var).grid(
            row=0, column=0, columnspan=2, sticky=tk.W, pady=5
        )

        # Base URL
        ttk.Label(frame, text="Base URL:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.ollama_base_url_var = tk.StringVar(
            value=ollama_config.get('base_url', 'http://localhost:11434')
        )
        ttk.Entry(frame, textvariable=self.ollama_base_url_var, width=50).grid(
            row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=5
        )

        # Model
        ttk.Label(frame, text="Model:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.ollama_model_var = tk.StringVar(
            value=ollama_config.get('model', 'qwen2.5:7b')
        )
        ttk.Entry(frame, textvariable=self.ollama_model_var, width=50).grid(
            row=2, column=1, sticky=(tk.W, tk.E), pady=5, padx=5
        )

        frame.columnconfigure(1, weight=1)

    def _build_general_tab(self, parent):
        """构建通用设置选项卡"""
        # Rimworld 路径
        path_frame = ttk.LabelFrame(parent, text="Rimworld 游戏路径", padding="10")
        path_frame.pack(fill=tk.X, padx=10, pady=10)

        self.rimworld_path_var = tk.StringVar(value=self.rimworld_path)
        path_entry = ttk.Entry(path_frame, textvariable=self.rimworld_path_var, width=60)
        path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        ttk.Button(path_frame, text="浏览...", command=self._browse_rimworld_path).pack(side=tk.RIGHT)

        # 自动保存间隔
        save_frame = ttk.LabelFrame(parent, text="自动保存", padding="10")
        save_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(save_frame, text="自动保存间隔 (秒):").pack(side=tk.LEFT, padx=5)
        self.auto_save_var = tk.IntVar(value=self.auto_save_interval)
        ttk.Spinbox(save_frame, from_=10, to=300, textvariable=self.auto_save_var, width=10).pack(
            side=tk.LEFT, padx=5
        )

    def _browse_rimworld_path(self):
        """浏览 Rimworld 路径"""
        path = filedialog.askdirectory(title="选择 Rimworld 游戏根目录")
        if path:
            self.rimworld_path_var.set(path)

    def _save_settings(self):
        """保存设置"""
        try:
            # 更新配置
            config_data = self.config.get_translation_config()

            # 更新 DeepSeek 配置
            if 'providers' not in config_data:
                config_data['providers'] = {}

            config_data['providers']['deepseek'] = {
                'enabled': self.deepseek_enabled_var.get(),
                'api_key': self.deepseek_api_key_var.get(),
                'base_url': self.deepseek_base_url_var.get(),
                'model': self.deepseek_model_var.get()
            }

            # 更新百度配置
            config_data['providers']['baidu'] = {
                'enabled': self.baidu_enabled_var.get(),
                'api_key': self.baidu_api_key_var.get(),
                'secret_key': self.baidu_secret_key_var.get(),
                'qps_limit': self.baidu_qps_var.get()
            }

            # 更新 Ollama 配置
            config_data['providers']['ollama'] = {
                'enabled': self.ollama_enabled_var.get(),
                'base_url': self.ollama_base_url_var.get(),
                'model': self.ollama_model_var.get()
            }

            # 更新通用设置
            config_data['rimworld_path'] = self.rimworld_path_var.get()
            config_data['auto_save_interval'] = self.auto_save_var.get()

            # 保存配置
            self.config.save_translation_config(config_data)

            messagebox.showinfo("成功", "设置已保存")
            self.dialog.destroy()

        except Exception as e:
            messagebox.showerror("错误", f"保存设置失败:\n{e}")
