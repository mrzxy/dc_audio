import sys
import sound
import logging
import asyncio


async def connect(bot, device_id, channel_id):
    import datetime
    
    try:
        print(f"设备ID: {device_id}, 频道ID: {channel_id}")
        print("正在连接到Discord...")
        
        await bot.wait_until_ready()
        print(f"已登录为: {bot.user.name}")

        stream = sound.PCMStream()
        channel = bot.get_channel(channel_id)
        if not channel:
            print(f"错误: 找不到频道ID {channel_id}")
            return
            
        print(f"找到频道: {channel.name} (服务器: {channel.guild.name})")
        stream.change_device(device_id)

        voice = None
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                print(f"正在连接到语音频道... (尝试 {retry_count + 1}/{max_retries})")
                voice = await channel.connect(reconnect=True, self_deaf=False, self_mute=False)
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
        
        if not voice:
            print("无法建立语音连接")
            return
            
        # 更新全局状态变量
        import main
        main.voice_connection = voice
        main.current_channel = channel
        main.connection_start_time = datetime.datetime.now()
        
        voice.play(stream)
        print(f"✅ 成功连接到语音频道: {channel.name}")
        print(f"🎵 音频流已启动，监听设备: {device_id}")
        print("📊 语音频道状态监听已激活...")
        print("⌨️  按 Ctrl+C 停止")

        # 连接状态监控循环
        connection_check_interval = 5  # 每5秒检查一次
        last_status_time = datetime.datetime.now()
        status_interval = 60  # 每60秒显示一次状态
        
        try:
            while voice.is_connected():
                await asyncio.sleep(connection_check_interval)
                
                # 定期显示连接状态
                current_time = datetime.datetime.now()
                if (current_time - last_status_time).seconds >= status_interval:
                    uptime = current_time - main.connection_start_time
                    member_count = len(channel.members) if channel.members else 0
                    print(f"[状态检查] 连接时间: {uptime}, 频道人数: {member_count}, 延迟: {round(bot.latency * 1000)}ms")
                    last_status_time = current_time
                
                # 检查语音连接健康状态
                if not voice.is_playing() and stream:
                    try:
                        # 重新启动音频流
                        voice.play(stream)
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
                if voice and voice.is_connected():
                    voice.stop()
                    await voice.disconnect()
                    print("✅ 已断开语音连接")
                
                # 重置全局状态
                main.voice_connection = None
                main.current_channel = None
                main.connection_start_time = None
                
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
