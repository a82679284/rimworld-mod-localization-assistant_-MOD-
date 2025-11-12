"""
主程序入口 - GUI 模式
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def main():
    """主函数 - 启动 GUI"""
    try:
        from src.ui.gui import start_gui
        start_gui()
    except ImportError as e:
        print(f"错误: GUI 模块导入失败 - {e}")
        print("请确保已安装 tkinter")
        sys.exit(1)
    except Exception as e:
        print(f"错误: GUI 启动失败 - {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
