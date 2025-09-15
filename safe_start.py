#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安全启动脚本 - 防止段错误
"""

import sys
import os
import signal
import faulthandler
import gc
import atexit

# 启用详细的错误报告
faulthandler.enable()

def setup_crash_protection():
    """设置崩溃保护"""
    
    def cleanup_on_exit():
        """退出时清理"""
        print("🧹 正在清理资源...")
        gc.collect()
    
    def signal_handler(signum, frame):
        """信号处理器"""
        print(f"\n🚨 程序收到信号 {signum}")
        
        # 尝试优雅地关闭
        try:
            import cli
            if hasattr(cli, 'audio_stream') and cli.audio_stream:
                print("🔊 正在停止音频流...")
                # 不直接操作音频流，避免段错误
        except:
            pass
        
        print("🛑 程序即将退出...")
        sys.exit(0)
    
    # 注册处理器
    signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # 终止信号
    
    # 注册退出清理
    atexit.register(cleanup_on_exit)
    
    print("🛡️ 崩溃保护已启用")

def check_environment():
    """检查运行环境"""
    issues = []
    
    # 检查Python版本
    if sys.version_info < (3, 8):
        issues.append("Python版本过低，建议使用3.8+")
    
    # 检查必要的库
    required_libs = ['discord', 'sounddevice', 'numpy']
    for lib in required_libs:
        try:
            __import__(lib)
        except ImportError:
            issues.append(f"缺少必要库: {lib}")
    
    # 检查音频系统
    try:
        import sounddevice as sd
        devices = sd.query_devices()
        input_devices = [d for d in devices if d['max_input_channels'] > 0]
        if not input_devices:
            issues.append("没有找到可用的音频输入设备")
    except Exception as e:
        issues.append(f"音频系统检查失败: {e}")
    
    return issues

def safe_import_modules():
    """安全导入模块"""
    try:
        print("📦 导入必要模块...")
        
        # 逐个导入，便于定位问题
        import discord
        print(f"   ✅ discord.py {discord.__version__}")
        
        import sounddevice as sd
        print(f"   ✅ sounddevice {sd.__version__}")
        
        import numpy as np
        print(f"   ✅ numpy {np.__version__}")
        
        # 导入项目模块
        import sound
        print("   ✅ sound模块")
        
        import cli
        print("   ✅ cli模块")
        
        return True
        
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 导入异常: {e}")
        return False

def run_with_args():
    """使用命令行参数运行"""
    args = sys.argv[1:]
    
    if not args:
        print("❌ 请提供命令行参数")
        print("示例: python safe_start.py -d 1 -c 1404733922159497311")
        return False
    
    try:
        # 修改sys.argv以传递给main.py
        sys.argv = ['main.pyw'] + args
        
        # 导入并运行
        print("🚀 启动主程序...")
        import main
        
        return True
        
    except SystemExit:
        # 正常退出
        return True
    except Exception as e:
        print(f"❌ 运行失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("🚀 Discord音频管道安全启动器")
    print("=" * 40)
    
    # 设置保护
    setup_crash_protection()
    
    # 检查环境
    print("🔍 检查运行环境...")
    issues = check_environment()
    
    if issues:
        print("⚠️ 发现以下问题:")
        for issue in issues:
            print(f"   - {issue}")
        print()
        
        response = input("是否继续运行? (y/N): ")
        if response.lower() != 'y':
            print("❌ 用户取消运行")
            return
    else:
        print("✅ 环境检查通过")
    
    # 安全导入模块
    if not safe_import_modules():
        print("❌ 模块导入失败，无法继续")
        return
    
    # 强制垃圾回收
    gc.collect()
    
    # 运行主程序
    success = run_with_args()
    
    if success:
        print("✅ 程序正常结束")
    else:
        print("❌ 程序异常结束")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 用户中断程序")
    except Exception as e:
        print(f"\n💥 未处理的异常: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("🏁 程序退出")
