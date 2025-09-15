#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
段错误调试和防护脚本
"""

import sys
import os
import signal
import traceback
import faulthandler
import gc

# 启用fault handler来捕获段错误
faulthandler.enable()

def setup_segfault_protection():
    """设置段错误防护"""
    
    def signal_handler(signum, frame):
        print(f"\n🚨 收到信号 {signum}")
        print("📍 当前调用栈:")
        traceback.print_stack(frame)
        
        # 强制垃圾回收
        gc.collect()
        
        print("🛑 程序即将退出...")
        sys.exit(1)
    
    # 注册信号处理器
    signal.signal(signal.SIGSEGV, signal_handler)  # 段错误
    signal.signal(signal.SIGABRT, signal_handler)  # 异常终止
    signal.signal(signal.SIGFPE, signal_handler)   # 浮点异常
    
    print("✅ 段错误防护已启用")

def check_system_requirements():
    """检查系统要求"""
    print("🔍 系统环境检查:")
    print(f"   Python版本: {sys.version}")
    print(f"   操作系统: {os.name}")
    print(f"   平台: {sys.platform}")
    
    # 检查内存使用
    try:
        import psutil
        memory = psutil.virtual_memory()
        print(f"   可用内存: {memory.available / 1024 / 1024:.1f} MB")
        print(f"   内存使用率: {memory.percent}%")
    except ImportError:
        print("   无法检查内存信息 (需要 psutil)")
    
    print()

def check_audio_system():
    """检查音频系统"""
    print("🔊 音频系统检查:")
    
    try:
        import sounddevice as sd
        print(f"   sounddevice版本: {sd.__version__}")
        
        # 检查默认设备
        try:
            default_device = sd.default.device
            print(f"   默认设备: {default_device}")
        except Exception as e:
            print(f"   ⚠️ 获取默认设备失败: {e}")
        
        # 检查可用设备
        try:
            devices = sd.query_devices()
            input_devices = [d for d in devices if d['max_input_channels'] > 0]
            print(f"   输入设备数量: {len(input_devices)}")
            
            for i, device in enumerate(input_devices[:3]):  # 只显示前3个
                print(f"     {i}: {device['name']}")
                
        except Exception as e:
            print(f"   ⚠️ 查询设备失败: {e}")
            
    except ImportError:
        print("   ❌ sounddevice 未安装")
    except Exception as e:
        print(f"   ❌ 音频系统检查失败: {e}")
    
    print()

def check_discord_library():
    """检查Discord库"""
    print("🤖 Discord库检查:")
    
    try:
        import discord
        print(f"   discord.py版本: {discord.__version__}")
        
        # 检查语音支持
        if discord.opus.is_loaded():
            print("   ✅ Opus编码器已加载")
        else:
            print("   ⚠️ Opus编码器未加载")
            
        # 检查FFmpeg
        try:
            import discord.FFmpegPCMAudio
            print("   ✅ FFmpeg支持可用")
        except Exception:
            print("   ⚠️ FFmpeg支持不可用")
            
    except ImportError:
        print("   ❌ discord.py 未安装")
    except Exception as e:
        print(f"   ❌ Discord库检查失败: {e}")
    
    print()

def suggest_fixes():
    """建议修复方案"""
    print("💡 段错误可能的原因和修复建议:")
    print()
    
    print("1. 音频设备问题:")
    print("   - 检查音频设备是否被其他程序占用")
    print("   - 尝试使用不同的设备ID")
    print("   - 检查设备驱动程序")
    print()
    
    print("2. 内存管理问题:")
    print("   - 确保有足够的可用内存")
    print("   - 避免同时运行多个实例")
    print("   - 定期重启程序")
    print()
    
    print("3. 库版本冲突:")
    print("   - 更新discord.py到最新版本")
    print("   - 检查sounddevice版本兼容性")
    print("   - 重新安装依赖库")
    print()
    
    print("4. 系统级问题:")
    print("   - 在macOS上，检查音频权限设置")
    print("   - 在Linux上，检查ALSA/PulseAudio配置")
    print("   - 在Windows上，尝试以管理员权限运行")
    print()

def safe_run_with_protection():
    """安全运行主程序"""
    print("🛡️ 启动带保护的程序运行...")
    
    try:
        # 设置保护
        setup_segfault_protection()
        
        # 强制垃圾回收
        gc.collect()
        
        # 导入并运行主程序
        print("📥 导入主程序模块...")
        import main
        
        print("🚀 启动主程序...")
        # 这里可以添加主程序的启动逻辑
        
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
    except Exception as e:
        print(f"❌ 运行错误: {e}")
        traceback.print_exc()

def run_safe_test():
    """运行安全测试"""
    print("🧪 运行安全测试...")
    
    try:
        # 测试音频流创建
        print("1. 测试音频流创建...")
        import sound
        test_stream = sound.PCMStream()
        print("   ✅ 音频流创建成功")
        
        # 测试设备切换
        print("2. 测试设备切换...")
        try:
            test_stream.change_device(0)  # 使用设备0
            print("   ✅ 设备切换成功")
        except Exception as e:
            print(f"   ⚠️ 设备切换失败: {e}")
        
        # 清理
        del test_stream
        gc.collect()
        print("3. ✅ 资源清理完成")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    print("🔧 Discord音频管道段错误调试工具\n")
    
    # 系统检查
    check_system_requirements()
    check_audio_system()
    check_discord_library()
    
    # 建议修复方案
    suggest_fixes()
    
    # 运行安全测试
    run_safe_test()
    
    print("🎯 调试完成！如果仍然出现段错误，请:")
    print("1. 尝试使用不同的音频设备")
    print("2. 重新安装音频驱动")
    print("3. 在虚拟环境中运行")
    print("4. 检查系统日志获取更多信息")
