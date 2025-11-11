"""
自动保存管理器
"""
import threading
from typing import Optional, Callable


class AutoSaveManager:
    """自动保存管理"""

    def __init__(self, interval: int = 30):
        """
        初始化自动保存管理器

        Args:
            interval: 自动保存间隔(秒)
        """
        self.interval = interval
        self.timer: Optional[threading.Timer] = None
        self.callback: Optional[Callable] = None
        self.is_running = False

    def start(self, callback: Callable):
        """
        启动自动保存

        Args:
            callback: 保存回调函数
        """
        if self.is_running:
            return

        self.callback = callback
        self.is_running = True
        self._schedule_next_save()
        print(f"✓ 自动保存已启动 (间隔: {self.interval}秒)")

    def start_auto_save(self, callback: Callable):
        """
        启动自动保存(与start方法相同,兼容旧代码)

        Args:
            callback: 保存回调函数
        """
        self.start(callback)

    def stop(self):
        """停止自动保存"""
        if self.timer:
            self.timer.cancel()
            self.timer = None

        self.is_running = False
        print("✓ 自动保存已停止")

    def stop_auto_save(self):
        """停止自动保存(与stop方法相同,兼容旧代码)"""
        self.stop()

    def _schedule_next_save(self):
        """调度下一次保存"""
        if not self.is_running:
            return

        self.timer = threading.Timer(self.interval, self._execute_save)
        self.timer.daemon = True  # 设置为守护线程
        self.timer.start()

    def _execute_save(self):
        """执行保存操作"""
        if self.callback and self.is_running:
            try:
                self.callback()
                print(f"✓ 自动保存完成")
            except Exception as e:
                print(f"✗ 自动保存失败: {e}")

        # 调度下一次保存
        self._schedule_next_save()

    def is_active(self) -> bool:
        """检查自动保存是否激活"""
        return self.is_running

    def set_interval(self, interval: int):
        """
        设置保存间隔

        Args:
            interval: 新的间隔(秒)
        """
        was_running = self.is_running
        if was_running:
            self.stop()

        self.interval = interval

        if was_running and self.callback:
            self.start(self.callback)
