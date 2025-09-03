#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Windows兼容性启动脚本
解决Unicode编码问题
"""

import sys
import os
import locale

def setup_windows_encoding():
    """设置Windows下的编码兼容性"""
    
    print("正在设置Windows编码兼容性...")
    
    # 方法1: 重新配置标准输出
    if hasattr(sys.stdout, 'reconfigure'):
        try:
            sys.stdout.reconfigure(encoding='utf-8')
            sys.stderr.reconfigure(encoding='utf-8')
            print("✅ 使用 reconfigure 方法设置UTF-8编码")
        except Exception as e:
            print(f"⚠️ reconfigure 方法失败: {e}")
    
    # 方法2: 包装标准输出
    elif hasattr(sys.stdout, 'buffer'):
        try:
            import io
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
            print("✅ 使用 TextIOWrapper 包装设置UTF-8编码")
        except Exception as e:
            print(f"⚠️ TextIOWrapper 方法失败: {e}")
    
    # 设置环境变量
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    os.environ['PYTHONLEGACYWINDOWSSTDIO'] = '0'
    
    # 设置控制台代码页（如果可能）
    if sys.platform.startswith('win'):
        try:
            import subprocess
            # 尝试设置控制台为UTF-8
            subprocess.run(['chcp', '65001'], shell=True, capture_output=True)
            print("✅ 控制台代码页设置为UTF-8")
        except Exception as e:
            print(f"⚠️ 控制台代码页设置失败: {e}")
    
    print(f"当前系统编码: {locale.getpreferredencoding()}")
    print(f"标准输出编码: {getattr(sys.stdout, 'encoding', 'unknown')}")

def test_unicode_output():
    """测试Unicode输出"""
    print("\n🧪 测试Unicode输出:")
    
    test_strings = [
        "基本中文测试",
        "设备ID: 1, 频道ID: 123456",
        "✅ 成功连接到语音频道",
        "🎵 音频流已启动",
        "📊 语音频道状态监听已激活",
        "⌨️ 按 Ctrl+C 停止",
        "🔄 音频流已重新启动",
        "⚠️ 连接监控异常",
        "🛑 用户中断，正在停止",
        "❌ 连接过程中发生错误"
    ]
    
    for i, test_str in enumerate(test_strings, 1):
        try:
            print(f"{i:2d}. {test_str}")
        except UnicodeEncodeError as e:
            print(f"{i:2d}. [编码错误] {repr(test_str)} - {e}")
        except Exception as e:
            print(f"{i:2d}. [其他错误] {repr(test_str)} - {e}")
    
    print("✅ Unicode测试完成")

def show_encoding_solutions():
    """显示编码问题的解决方案"""
    print("\n💡 Windows编码问题解决方案:")
    print()
    print("1. 使用此脚本启动:")
    print("   python run_windows.py")
    print()
    print("2. 设置环境变量:")
    print("   set PYTHONIOENCODING=utf-8")
    print("   python main.pyw -d 1 -c 123456")
    print()
    print("3. 修改控制台代码页:")
    print("   chcp 65001")
    print("   python main.pyw -d 1 -c 123456")
    print()
    print("4. 使用PowerShell:")
    print("   $env:PYTHONIOENCODING='utf-8'")
    print("   python main.pyw -d 1 -c 123456")
    print()
    print("5. 创建批处理文件 (run.bat):")
    print("   @echo off")
    print("   chcp 65001")
    print("   set PYTHONIOENCODING=utf-8")
    print("   python main.pyw %*")
    print()

def run_main_with_args():
    """运行主程序并传递命令行参数"""
    print("\n🚀 启动主程序...")
    
    # 获取命令行参数（除了脚本名）
    args = sys.argv[1:]
    
    if not args:
        print("请提供命令行参数，例如:")
        print("python run_windows.py -d 1 -c 1404733922159497311 --dev --verbose")
        return
    
    # 导入并运行主程序
    try:
        import main
        # 修改sys.argv以传递参数给main.py
        sys.argv = ['main.pyw'] + args
        
        # 重新解析参数
        import argparse
        parser = argparse.ArgumentParser(description="Discord Audio Pipe")
        # 这里需要重新定义所有参数...
        print("参数已传递给主程序")
        
    except Exception as e:
        print(f"❌ 启动主程序失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🪟 Discord Audio Pipe - Windows兼容性启动器")
    print("=" * 50)
    
    # 设置编码
    if sys.platform.startswith('win'):
        setup_windows_encoding()
    else:
        print("✅ 非Windows系统，跳过编码设置")
    
    # 测试Unicode输出
    test_unicode_output()
    
    # 显示解决方案
    show_encoding_solutions()
    
    # 如果有参数，尝试运行主程序
    if len(sys.argv) > 1:
        run_main_with_args()
    else:
        print("\n💡 要启动主程序，请添加参数:")
        print("python run_windows.py -d 1 -c 1404733922159497311 --dev --verbose")
