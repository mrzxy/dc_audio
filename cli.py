import sys
import sound
import logging
import asyncio


async def connect(bot, device_id, channel_id):
    try:
        print(device_id, channel_id)
        print("Connecting...")
        
        await bot.wait_until_ready()
        print(f"Logged in as {bot.user.name}")

        stream = sound.PCMStream()
        channel = bot.get_channel(channel_id)
        stream.change_device(device_id)

        try:
            voice = await channel.connect()
        except Exception as e:
            print(e)
            raise
        
        voice.play(stream)
        print(f"Playing audio in {channel.name}")
        print("音频流已启动，有声音时会显示提示...")

        # 等待直到机器人离开语音频道或用户中断
        try:
            while voice.is_connected():
                await asyncio.sleep(1)  # 每秒检查一次连接状态
        except KeyboardInterrupt:
            print("\n用户中断，正在停止...")
            voice.stop()
            await voice.disconnect()

    except Exception:
        logging.exception("Error on cli connect")
        sys.exit(1)


async def query(bot, token):
    await bot.login(token)

    async for guild in bot.fetch_guilds(limit=150):
        print(guild.id, guild.name)
        channels = await guild.fetch_channels()

        for channel in channels:
            print("\t", channel.id, channel.name)

    await bot.logout()
