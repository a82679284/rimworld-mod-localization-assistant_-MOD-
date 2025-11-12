"""
批量翻译业务逻辑层
"""
from typing import List, Optional, Dict
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from ..models.translation_entry import TranslationEntry
from ..providers.base import TranslationProvider
from ..providers.deepseek_translator import DeepSeekTranslator
from ..providers.baidu_translator import BaiduTranslator
from ..providers.ollama_translator import OllamaTranslator
from ..logic.translation_memory import TranslationMemoryLogic
from ..utils.config import Config


class BatchTranslatorLogic:
    """批量翻译业务逻辑"""

    def __init__(
        self,
        config: Config,
        translation_memory: Optional[TranslationMemoryLogic] = None
    ):
        """
        初始化批量翻译器

        Args:
            config: 配置对象
            translation_memory: 翻译记忆逻辑(可选)
        """
        self.config = config
        self.translation_memory = translation_memory
        self.providers: Dict[str, TranslationProvider] = {}
        self._initialize_providers()
        self.optimal_workers = None  # 缓存最优线程数

    def _initialize_providers(self):
        """初始化所有翻译提供商"""
        provider_config = self.config.get_translation_config()

        # 注册所有支持的翻译器
        provider_classes = {
            'deepseek': DeepSeekTranslator,
            'baidu': BaiduTranslator,
            'ollama': OllamaTranslator
        }

        # 获取术语库仓库 (用于 DeepSeek)
        glossary_repo = None
        if self.translation_memory:
            glossary_repo = self.translation_memory.glossary_repo

        for name, provider_class in provider_classes.items():
            if name in provider_config.get('providers', {}):
                config_dict = provider_config['providers'][name]
                try:
                    # DeepSeek 需要术语库支持
                    if name == 'deepseek' and glossary_repo:
                        provider = provider_class(config_dict, glossary_repo)
                    else:
                        provider = provider_class(config_dict)

                    if provider.is_available():
                        self.providers[name] = provider
                        print(f"✓ {name.capitalize()} 翻译器已加载")
                    else:
                        print(f"✗ {name.capitalize()} 翻译器不可用 (请检查配置)")
                except Exception as e:
                    print(f"✗ {name.capitalize()} 翻译器初始化失败: {e}")

    def get_available_providers(self) -> List[str]:
        """获取可用的翻译提供商列表"""
        return list(self.providers.keys())

    def batch_translate(
        self,
        entries: List[TranslationEntry],
        provider_name: Optional[str] = None,
        use_memory: bool = True,
        progress_callback: Optional[callable] = None
    ) -> Dict[str, any]:
        """
        批量翻译条目

        Args:
            entries: 翻译条目列表
            provider_name: 指定的翻译提供商,None 则使用默认
            use_memory: 是否使用翻译记忆
            progress_callback: 进度回调函数 callback(current, total, entry)

        Returns:
            Dict: {
                'success_count': int,
                'failed_count': int,
                'memory_hit_count': int,
                'results': List[TranslationEntry]
            }
        """
        # 选择翻译提供商
        if not provider_name:
            provider_name = self.config.get_translation_config().get('default_provider', 'deepseek')

        provider = self.providers.get(provider_name)
        if not provider:
            print(f"错误: 翻译提供商 '{provider_name}' 不可用")
            return {
                'success_count': 0,
                'failed_count': len(entries),
                'memory_hit_count': 0,
                'results': entries
            }

        success_count = 0
        failed_count = 0
        memory_hit_count = 0

        # 批量处理
        for i, entry in enumerate(entries):
            # 跳过已翻译的条目
            if entry.translated_text and entry.translated_text.strip():
                # 确保状态正确
                if entry.status != 'completed':
                    entry.status = 'completed'
                success_count += 1
                if progress_callback:
                    progress_callback(i + 1, len(entries), entry)
                continue

            # 1. 尝试从翻译记忆获取
            if use_memory and self.translation_memory:
                match = self.translation_memory.find_translation(entry.original_text)
                if match and match['type'] == 'exact':
                    entry.translated_text = match['translation']
                    entry.status = 'completed'  # 设置状态为已完成
                    memory_hit_count += 1
                    success_count += 1
                    if progress_callback:
                        progress_callback(i + 1, len(entries), entry)
                    continue

            # 2. 使用 API 翻译
            try:
                translation = provider.translate(entry.original_text)
                if translation:
                    entry.translated_text = translation
                    entry.status = 'completed'
                    success_count += 1

                    # 保存到翻译记忆
                    if self.translation_memory:
                        self.translation_memory.save_translation(
                            entry.original_text,
                            translation,
                            entry.xml_path
                        )
                else:
                    entry.status = 'failed'
                    failed_count += 1

            except Exception as e:
                print(f"翻译失败: {entry.original_text[:30]}... - {e}")
                entry.status = 'failed'
                failed_count += 1

            # 进度回调
            if progress_callback:
                progress_callback(i + 1, len(entries), entry)

        return {
            'success_count': success_count,
            'failed_count': failed_count,
            'memory_hit_count': memory_hit_count,
            'results': entries
        }

    def _translate_single_entry(
        self,
        entry: TranslationEntry,
        provider: TranslationProvider,
        use_memory: bool,
        lock: threading.Lock,
        counters: Dict[str, int]
    ) -> TranslationEntry:
        """
        翻译单个条目(线程安全)

        Args:
            entry: 翻译条目
            provider: 翻译提供商
            use_memory: 是否使用翻译记忆
            lock: 线程锁
            counters: 共享计数器字典

        Returns:
            TranslationEntry: 翻译后的条目
        """
        # 跳过已翻译的条目
        if entry.translated_text and entry.translated_text.strip():
            if entry.status != 'completed':
                entry.status = 'completed'
            with lock:
                counters['success'] += 1
            return entry

        # 1. 尝试从翻译记忆获取
        if use_memory and self.translation_memory:
            match = self.translation_memory.find_translation(entry.original_text)
            if match and match['type'] == 'exact':
                entry.translated_text = match['translation']
                entry.status = 'completed'
                with lock:
                    counters['success'] += 1
                    counters['memory_hit'] += 1
                return entry

        # 2. 使用 API 翻译
        try:
            translation = provider.translate(entry.original_text)
            if translation:
                entry.translated_text = translation
                entry.status = 'completed'
                with lock:
                    counters['success'] += 1

                # 保存到翻译记忆
                if self.translation_memory:
                    self.translation_memory.save_translation(
                        entry.original_text,
                        translation,
                        entry.xml_path
                    )
            else:
                entry.status = 'failed'
                with lock:
                    counters['failed'] += 1

        except Exception as e:
            print(f"翻译失败: {entry.original_text[:30]}... - {e}")
            entry.status = 'failed'
            with lock:
                counters['failed'] += 1

        return entry

    def batch_translate_concurrent(
        self,
        entries: List[TranslationEntry],
        provider_name: Optional[str] = None,
        use_memory: bool = True,
        progress_callback: Optional[callable] = None,
        max_workers: Optional[int] = None
    ) -> Dict[str, any]:
        """
        多线程批量翻译条目

        Args:
            entries: 翻译条目列表
            provider_name: 指定的翻译提供商,None 则使用默认
            use_memory: 是否使用翻译记忆
            progress_callback: 进度回调函数 callback(current, total, entry)
            max_workers: 最大线程数,None 则自动测试最优值

        Returns:
            Dict: {
                'success_count': int,
                'failed_count': int,
                'memory_hit_count': int,
                'results': List[TranslationEntry],
                'workers_used': int
            }
        """
        # 选择翻译提供商
        if not provider_name:
            provider_name = self.config.get_translation_config().get('default_provider', 'deepseek')

        provider = self.providers.get(provider_name)
        if not provider:
            print(f"错误: 翻译提供商 '{provider_name}' 不可用")
            return {
                'success_count': 0,
                'failed_count': len(entries),
                'memory_hit_count': 0,
                'results': entries,
                'workers_used': 0
            }

        # 确定最优线程数
        if max_workers is None:
            if self.optimal_workers is None:
                print("首次运行,正在测试最优线程数...")
                self.optimal_workers = self._test_optimal_workers(entries[:50], provider, use_memory)
                print(f"✓ 测试完成,最优线程数: {self.optimal_workers}")
            max_workers = self.optimal_workers

        print(f"使用 {max_workers} 个线程进行批量翻译")

        # 线程安全的计数器
        counters = {
            'success': 0,
            'failed': 0,
            'memory_hit': 0,
            'completed': 0
        }
        lock = threading.Lock()

        # 使用线程池并发翻译
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            future_to_entry = {
                executor.submit(
                    self._translate_single_entry,
                    entry,
                    provider,
                    use_memory,
                    lock,
                    counters
                ): entry for entry in entries
            }

            # 处理完成的任务
            for future in as_completed(future_to_entry):
                entry = future_to_entry[future]
                try:
                    result_entry = future.result()
                    # 更新原条目
                    entry.translated_text = result_entry.translated_text
                    entry.status = result_entry.status

                    # 进度回调
                    with lock:
                        counters['completed'] += 1
                        if progress_callback:
                            progress_callback(counters['completed'], len(entries), entry)

                except Exception as e:
                    print(f"处理任务失败: {e}")
                    entry.status = 'failed'
                    with lock:
                        counters['failed'] += 1
                        counters['completed'] += 1
                        if progress_callback:
                            progress_callback(counters['completed'], len(entries), entry)

        return {
            'success_count': counters['success'],
            'failed_count': counters['failed'],
            'memory_hit_count': counters['memory_hit'],
            'results': entries,
            'workers_used': max_workers
        }

    def _test_optimal_workers(
        self,
        sample_entries: List[TranslationEntry],
        provider: TranslationProvider,
        use_memory: bool
    ) -> int:
        """
        测试最优线程数

        Args:
            sample_entries: 样本条目(建议 30-50 条)
            provider: 翻译提供商
            use_memory: 是否使用翻译记忆

        Returns:
            int: 最优线程数
        """
        test_workers = [1, 5, 10, 20, 50, 100]
        results = {}

        # 限制样本数量
        sample_size = min(len(sample_entries), 50)
        samples = sample_entries[:sample_size]

        print(f"使用 {sample_size} 条样本测试性能...")

        for workers in test_workers:
            print(f"测试 {workers} 线程...", end=' ')

            # 创建副本以避免修改原数据
            test_entries = [
                TranslationEntry(
                    id=e.id,
                    mod_name=e.mod_name,
                    file_path=e.file_path,
                    xml_path=e.xml_path,
                    original_text=e.original_text,
                    translated_text="",  # 重置为空,强制翻译
                    status='pending'
                ) for e in samples
            ]

            # 计时
            start_time = time.time()

            counters = {'success': 0, 'failed': 0, 'memory_hit': 0, 'completed': 0}
            lock = threading.Lock()

            try:
                with ThreadPoolExecutor(max_workers=workers) as executor:
                    futures = [
                        executor.submit(
                            self._translate_single_entry,
                            entry,
                            provider,
                            use_memory,
                            lock,
                            counters
                        ) for entry in test_entries
                    ]

                    for future in as_completed(futures):
                        future.result()

                elapsed = time.time() - start_time
                results[workers] = elapsed

                # 计算速率
                rate = sample_size / elapsed if elapsed > 0 else 0
                print(f"{elapsed:.2f}秒 ({rate:.2f} 条/秒)")

            except Exception as e:
                print(f"失败: {e}")
                results[workers] = float('inf')

            # 避免测试过快触发速率限制
            time.sleep(1)

        # 选择最快的配置
        optimal = min(results, key=results.get)
        print(f"\n性能测试结果:")
        for workers, elapsed in sorted(results.items()):
            if elapsed != float('inf'):
                rate = sample_size / elapsed
                marker = " ← 最优" if workers == optimal else ""
                print(f"  {workers} 线程: {elapsed:.2f}秒 ({rate:.2f} 条/秒){marker}")

        return optimal

    def translate_single(
        self,
        text: str,
        provider_name: Optional[str] = None,
        use_memory: bool = True
    ) -> Optional[str]:
        """
        翻译单个文本

        Args:
            text: 待翻译文本
            provider_name: 翻译提供商名称
            use_memory: 是否使用翻译记忆

        Returns:
            Optional[str]: 翻译结果
        """
        # 1. 尝试从翻译记忆获取
        if use_memory and self.translation_memory:
            match = self.translation_memory.find_translation(text)
            if match:
                return match['translation']

        # 2. 使用 API 翻译
        if not provider_name:
            provider_name = self.config.get_translation_config().get('default_provider', 'deepseek')

        provider = self.providers.get(provider_name)
        if not provider:
            return None

        try:
            translation = provider.translate(text)
            if translation and self.translation_memory:
                self.translation_memory.save_translation(text, translation)
            return translation
        except Exception as e:
            print(f"翻译失败: {e}")
            return None

    def get_provider_info(self, provider_name: str) -> Optional[Dict[str, any]]:
        """
        获取翻译提供商信息

        Args:
            provider_name: 提供商名称

        Returns:
            Optional[Dict]: 提供商信息
        """
        provider = self.providers.get(provider_name)
        if not provider:
            return None

        return {
            'name': provider.get_provider_name(),
            'available': provider.is_available(),
            'rate_limit': provider.get_rate_limit()
        }
