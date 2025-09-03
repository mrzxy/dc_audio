import sys
import sound
import logging
import asyncio
import os

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
        max_retries = 30
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                print(f"正在连接到语音频道... (尝试 {retry_count + 1}/{max_retries})")
                voice_connection = await current_channel.connect(reconnect=True, self_deaf=False, self_mute=False)
                break
            except Exception as e:
                retry_count += 1
                print(f"连接失败: {e}")
                if retry_count < max_retries:
                    print(f"等待5秒后重试...")
                    await asyncio.sleep(5)
                else:
                    print("达到最大重试次数，连接失败")
                    raise
        
        if not voice_connection:
            print("无法建立语音连接")
            return
            
        
        connection_start_time = datetime.datetime.now()
        
        voice_connection.play(stream)
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
                    try:
                        # 重新启动音频流
                        voice_connection.play(audio_stream)
                        print("🔄 音频流已重新启动")
                    except Exception as e:
                        print(f"⚠️ 音频流重启失败: {e}")
                        
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

async def try_reconnect(bot,    channel_id):
    return 
    """尝试重新连接到语音频道"""
    import datetime
    
    try:
        global voice_connection, current_channel, connection_start_time
        
        channel = bot.get_channel(channel_id)
        if not channel:
            print(f"错误: 找不到频道ID {channel_id}")
            return
        
        
        # 清理旧连接
        if voice_connection and voice_connection.is_connected():
            try:
                voice_connection.stop()
                await voice_connection.disconnect()
            except:
                pass
        
        # 重新连接
        voice_connection = await channel.connect(reconnect=True, self_deaf=False, self_mute=False)
        connection_start_time = datetime.datetime.now()
        
        # 如果有音频流，重新开始播放
        if audio_stream:
            voice_connection.play(audio_stream)
            print(f"✅ 成功重新连接到 {channel.name}，音频流已恢复")
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