#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试简化音频检测功能的脚本
"""

import time
import sound

def test_simple_audio():
    """测试简化的音频检测功能"""
    print("测试简化音频检测功能...")
    
    try:
        # 查询设备
        devices = sound.query_devices()
        if not devices:
            print("没有找到音频设备")
            return
        
        # 选择第一个设备
        device_name, device_id = list(devices.items())[0]
        print(f"使用设备: {device_name} (ID: {device_id})")
        
        # 创建PCM流
        stream = sound.PCMStream()
        print("PCM流创建成功")
        
        # 切换到设备
        stream.change_device(device_id)
        print("设备切换成功")
        
        # 监控音频10秒
        print("开始监控音频输入（10秒），有声音时会显示...")
        start_time = time.time()
        
        while time.time() - start_time < 10:
            # 模拟读取音频数据
            if stream.stream and stream.stream.active:
                # 这里只是测试，实际音频数据会在Discord中使用
                time.sleep(0.1)
        
        # 停止流
        if stream.stream:
            stream.stream.stop()
            stream.stream.close()
        
        print("测试完成！")
        
    except Exception as e:
        print(f"测试过程中发生错误: {e}")

if __name__ == "__main__":
    test_simple_audio()
