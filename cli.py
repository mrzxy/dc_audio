import sys
import sound
import logging
import asyncio
import os
import discord

# Windows编码兼容性修复
if sys.platform.startswith('win'):
    # 设置标准输出编码为UTF-8
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    elif hasattr(sys.stdout, 'buffer'):
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    # 设置环境变量
    os.environ['PYTHONIOENCODING'] = 'utf-8'


audio_stream = None

def get_audio_stream(device_id):
    global audio_stream
    if not audio_stream:
        audio_stream = sound.PCMStream()
        audio_stream.change_device(device_id)
    return audio_stream


async def safe_play_audio(voice_connection, audio_source, max_retries=3):
    """安全播放音频，处理'Already playing audio'异常"""
    for attempt in range(max_retries):
        try:
            # 检查是否已经在播放
            if voice_connection.is_playing():
                print(f"🔊 检测到音频正在播放，停止当前播放...")
                voice_connection.stop()
                await asyncio.sleep(0.5)  # 等待停止完成
            
            # 开始播放
            voice_connection.play(audio_source)
            print(f"🎵 音频流已开始播放")
            return True
            
        except discord.ClientException as e:
            if "Already playing audio" in str(e):
                print(f"⚠️ 尝试 {attempt + 1}/{max_retries}: 音频仍在播放，强制停止...")
                voice_connection.stop()
                await asyncio.sleep(1)
                if attempt == max_retries - 1:
                    print(f"❌ 无法停止现有音频播放")
                    return False
            else:
                print(f"❌ 音频播放异常: {e}")
                return False
        except Exception as e:
            print(f"❌ 音频播放错误: {e}")
            return False
    
    return False


async def ensure_voice_connection(channel):
    """确保语音连接，处理已连接的情况"""
    # 检查机器人是否已经连接到语音频道
    existing_voice = channel.guild.voice_client
    
    if existing_voice and existing_voice.is_connected():
        if existing_voice.channel == channel:
            print(f"✅ 机器人已连接到目标频道 {channel.name}")
            return existing_voice
        else:
            print(f"🔄 机器人已连接到其他频道 {existing_voice.channel.name}，正在切换...")
            await existing_voice.disconnect()
            await asyncio.sleep(1)
    
    # 创建新连接
    max_retries = 30
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            print(f"🔗 正在连接到语音频道... (尝试 {retry_count + 1}/{max_retries})")
            voice_connection = await channel.connect(reconnect=True, self_deaf=False, self_mute=False)
            print(f"✅ 成功连接到语音频道 {channel.name}")
            return voice_connection
            
        except discord.ClientException as e:
            if "Already connected to a voice channel" in str(e):
                print("🔍 检测到已有连接，尝试获取现有连接...")
                voice_connection = channel.guild.voice_client
                if voice_connection and voice_connection.is_connected():
                    print(f"✅ 使用现有连接到 {voice_connection.channel.name}")
                    return voice_connection
                else:
                    print("⚠️ 现有连接无效，继续重试...")
            
            retry_count += 1
            print(f"❌ 连接失败: {e}")
            if retry_count < max_retries:
                print(f"⏳ 等待5秒后重试...")
                await asyncio.sleep(5)
            else:
                print("🚫 达到最大重试次数，连接失败")
                raise
                
        except Exception as e:
            retry_count += 1
            print(f"❌ 连接失败: {e}")
            if retry_count < max_retries:
                print(f"⏳ 等待5秒后重试...")
                await asyncio.sleep(5)
            else:
                print("🚫 达到最大重试次数，连接失败")
                raise
    
    return None

async def connect(bot, device_id, channel_id):
    import datetime
    
    try:
        print(f"设备ID: {device_id}, 频道ID: {channel_id}")
        print("正在连接到Discord...")
        
        await bot.wait_until_ready()
        print(f"已登录为: {bot.user.name}")

        current_channel = bot.get_channel(channel_id)
        if not current_channel:
            print(f"错误: 找不到频道ID {channel_id}")
            return
            
        print(f"找到频道: {current_channel.name} (服务器: {current_channel.guild.name})")

        stream = get_audio_stream(device_id)
        
        # 使用辅助函数确保语音连接
        voice_connection = await ensure_voice_connection(current_channel)
        
        if not voice_connection:
            print("无法建立语音连接")
            return
            
        
        connection_start_time = datetime.datetime.now()
        
        # 使用安全播放函数
        play_success = await safe_play_audio(voice_connection, stream)
        if not play_success:
            print("❌ 无法开始音频播放")
            return
        
        print(f"✅ 成功连接到语音频道: {current_channel.name}, 监听设备: {device_id}")

        # 连接状态监控循环
        connection_check_interval = 5  # 每5秒检查一次
        last_status_time = datetime.datetime.now()
        status_interval = 60  # 每60秒显示一次状态
        
        try:
            while voice_connection.is_connected():
               
                await asyncio.sleep(connection_check_interval)
                # 定期显示连接状态
                current_time = datetime.datetime.now()
                if (current_time - last_status_time).seconds >= status_interval:
                    uptime = current_time - connection_start_time
                    member_count = len(current_channel.members) if current_channel.members else 0
                    print(f"[状态检查] 连接时间: {uptime}, 频道人数: {member_count}, 延迟: {round(bot.latency * 1000)}ms")
                    last_status_time = current_time
                
                # 检查语音连接健康状态
                if not voice_connection.is_playing() and audio_stream:
                    print("🔄 检测到音频流停止，尝试重启...")
                    restart_success = await safe_play_audio(voice_connection, audio_stream)
                    if restart_success:
                        print("✅ 音频流已重新启动")
                    else:
                        print("⚠️ 音频流重启失败")
                        
        except KeyboardInterrupt:
            print("\n🛑 用户中断，正在停止...")
        except Exception as e:
            print(f"⚠️ 连接监控异常: {e}")
        finally:
            # 清理工作
            try:
                if voice_connection and voice_connection.is_connected():
                    voice_connection.stop()
                    await voice_connection.disconnect()
                    print("✅ 已断开语音连接")

                await asyncio.sleep(2)
                
                print("重新连接音频...")
                await connect(bot, device_id, channel_id)
                
                
            except Exception as e:
                print(f"⚠️ 清理资源时出错: {e}")

    except Exception as e:
        logging.exception("Error on cli connect")
        print(f"❌ 连接过程中发生错误: {e}")
        sys.exit(1)


async def query(bot, token):
    await bot.login(token)

    async for guild in bot.fetch_guilds(limit=150):
        print(guild.id, guild.name)
        channels = await guild.fetch_channels()

        for channel in channels:
            print("\t", channel.id, channel.name)

    await bot.logout()

async def try_reconnect(bot, channel_id):
    """尝试重新连接到语音频道"""
    import datetime
    
    try:
        global audio_stream
        
        channel = bot.get_channel(channel_id)
        if not channel:
            print(f"❌ 错误: 找不到频道ID {channel_id}")
            return False
        
        print(f"🔄 尝试重新连接到 {channel.name}...")
        
        # 清理旧连接
        existing_voice = channel.guild.voice_client
        if existing_voice and existing_voice.is_connected():
            try:
                existing_voice.stop()
                await existing_voice.disconnect()
                await asyncio.sleep(1)
            except Exception as e:
                print(f"⚠️ 清理旧连接时出错: {e}")
        
        # 使用辅助函数重新连接
        voice_connection = await ensure_voice_connection(channel)
        
        if not voice_connection:
            print("❌ 无法建立语音连接")
            return False
        
        connection_start_time = datetime.datetime.now()
        
        # 如果有音频流，重新开始播放
        if audio_stream:
            play_success = await safe_play_audio(voice_connection, audio_stream)
            if play_success:
                print(f"✅ 成功重新连接到 {channel.name}，音频流已恢复")
            else:
                print(f"⚠️ 重新连接到 {channel.name}，但音频流启动失败")
        else:
            print(f"✅ 成功重新连接到 {channel.name}")
        
        return True
        
    except Exception as e:
        print(f"❌ 重连失败: {str(e)}")
        return False


def get_connection_status():
    """获取当前连接状态"""
    import datetime
    
    global voice_connection, current_channel, connection_start_time, audio_stream
    
    if not voice_connection or not current_channel:
        return {
            'connected': False,
            'playing': False,
            'channel': None,
            'uptime': None,
            'has_stream': audio_stream is not None
        }
    
    return {
        'connected': voice_connection.is_connected(),
        'playing': voice_connection.is_playing(),
        'channel': current_channel.name,
        'uptime': datetime.datetime.now() - connection_start_time if connection_start_time else None,
        'has_stream': audio_stream is not None
    }