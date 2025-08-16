import discord
import sounddevice as sd
from pprint import pformat
import numpy as np
import time
from datetime import datetime

DEFAULT = 0
sd.default.channels = 2
sd.default.dtype = "int16"
sd.default.latency = "low"
sd.default.samplerate = 48000


class PCMStream(discord.AudioSource):
    def __init__(self):
        discord.AudioSource.__init__(self)
        self.stream = None
        self.frame_count = 0
        self.last_audio_output = 0
        self.start_time = time.time()

        # Discord reads 20 ms worth of audio at a time (20 ms * 50 == 1000 ms == 1 sec)
        self.frames = int(sd.default.samplerate / 50)

    def detect_audio_level(self, data):
        """检测音频数据的音量级别"""
        try:
            # 将字节数据转换为numpy数组
            audio_array = np.frombuffer(data, dtype=np.int16)
            
            # 计算RMS音量
            rms = np.sqrt(np.mean(audio_array.astype(np.float32)**2))
            
            return rms
        except Exception:
            return 0

    def read(self):
        if self.stream is None:
            return

        try:
            data = self.stream.read(self.frames)[0]
            self.frame_count += 1
            
            # 检测音频级别
            rms = self.detect_audio_level(data)
            
            # 只有当有声音且距离上次输出超过50帧（约1秒）时才输出
            if rms > 100 and (self.frame_count - self.last_audio_output) > 50:
                current_time = datetime.now().strftime("%H:%M:%S")
                elapsed_time = time.time() - self.start_time
                print(f"[{current_time}] 检测到声音 - 音量: {rms:.0f} (运行时间: {elapsed_time:.1f}s)")
                self.last_audio_output = self.frame_count
            
            # 转换到PCM格式
            pcm_data = bytes(data)
            return pcm_data
            
        except Exception:
            return None

    def change_device(self, num):
        if self.stream is not None:
            self.stream.stop()
            self.stream.close()
        
        print("change_device", num)

        try:
            self.stream = sd.RawInputStream(device=num)
            self.stream.start()
            self.frame_count = 0
            self.last_audio_output = 0
            self.start_time = time.time()  # 重置开始时间
        except Exception as e:
            raise


class DeviceNotFoundError(Exception):
    def __init__(self):
        self.devices = sd.query_devices()
        self.host_apis = sd.query_hostapis()
        super().__init__("No Devices Found")

    def __str__(self):
        return (
            f"Devices \n"
            f"{self.devices} \n "
            f"Host APIs \n"
            f"{pformat(self.host_apis)}"
        )


def query_devices():
    options = {
        device.get("name"): index
        for index, device in enumerate(sd.query_devices())
        if (device.get("max_input_channels") > 0 and device.get("hostapi") == DEFAULT)
    }

    if not options:
        raise DeviceNotFoundError()

    return options
