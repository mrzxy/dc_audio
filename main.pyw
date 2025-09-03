import logging

# error logging
error_formatter = logging.Formatter(
    fmt="%(asctime)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)

error_handler = logging.FileHandler("DAP_errors.log", delay=True)
error_handler.setLevel(logging.INFO)
error_handler.setFormatter(error_formatter)

base_logger = logging.getLogger()
base_logger.addHandler(error_handler)

import sys
import cli
import sound
from cli import try_reconnect
import asyncio
import discord
from discord.ext import commands, tasks
import argparse

# commandline args
parser = argparse.ArgumentParser(description="Discord Audio Pipe")
connect = parser.add_argument_group("Command Line Mode")
query = parser.add_argument_group("Queries")
current_channel = None
voice_connection=None

parser.add_argument(
    "-t",
    "--token",
    dest="token",
    action="store",
    default=None,
    help="The token for the bot",
)

parser.add_argument(
    "-v",
    "--verbose",
    dest="verbose",
    action="store_true",
    help="Enable verbose logging",
)

connect.add_argument(
    "-c",
    "--channel",
    dest="channel",
    action="store",
    type=int,
    help="The channel to connect to as an id",
)

connect.add_argument(
    "-d",
    "--device",
    dest="device",
    action="store",
    type=int,
    help="The device to listen from as an index",
)

query.add_argument(
    "-D",
    "--devices",
    dest="query",
    action="store_true",
    help="Query compatible audio devices",
)

query.add_argument(
    "-C",
    "--channels",
    dest="online",
    action="store_true",
    help="Query servers and channels (requires token)",
)

connect.add_argument(
    "-dev",
    "--dev",
    dest="dev",
    action="store_true",
    help="dev mode",
)

args = parser.parse_args()
is_gui = not any([args.channel, args.device, args.query, args.online])

# CLI模式下的日志配置
if not is_gui:
    # 为CLI模式配置控制台日志
    cli_formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    cli_handler = logging.StreamHandler()
    cli_handler.setLevel(logging.INFO)
    cli_handler.setFormatter(cli_formatter)
    
    # 获取根logger并添加CLI handler
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(cli_handler)
    
    # 确保sound和cli模块的logger级别正确
    logging.getLogger('sound').setLevel(logging.INFO)
    logging.getLogger('cli').setLevel(logging.INFO)

# verbose logs
if args.verbose:
    debug_formatter = logging.Formatter(
        fmt="%(asctime)s:%(levelname)s:%(name)s: %(message)s"
    )

    debug_handler = logging.FileHandler(
        filename="discord.log", encoding="utf-8", mode="w"
    )
    debug_handler.setFormatter(debug_formatter)

    debug_logger = logging.getLogger("discord")
    debug_logger.setLevel(logging.DEBUG)
    debug_logger.addHandler(debug_handler)

# don't import qt stuff if not using gui
if is_gui:
    import gui
    from PyQt5.QtWidgets import QApplication, QMessageBox

    app = QApplication(sys.argv)
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Information)


# main
async def main(bot):
    try:
        # query devices
        if args.query:
            for device, index in sound.query_devices().items():
                print(index, device)

            return

        # check for token
        token = args.token
        if token is None:
            token = open("token.txt", "r").read()

        # query servers and channels
        if args.online:
            await cli.query(bot, token)

            return

        # GUI
        if is_gui:
            bot_ui = gui.GUI(app, bot)
            asyncio.ensure_future(bot_ui.ready())
            asyncio.ensure_future(bot_ui.run_Qt())

        # CLI
        else:
            asyncio.ensure_future(cli.connect(bot, args.device, args.channel))
            print("cli over")

        

        await bot.start(token)
        print("over")

    except FileNotFoundError:
        if is_gui:
            msg.setWindowTitle("Token Error")
            msg.setText("No Token Provided")
            msg.exec()

        else:
            print("No Token Provided")

    except discord.errors.LoginFailure:
        if is_gui:
            msg.setWindowTitle("Login Failed")
            msg.setText("Please check if the token is correct")
            msg.exec()

        else:
            print("Login Failed: Please check if the token is correct")

    except Exception:
        logging.exception("Error on main")


http_proxy = None
if args.dev:
    http_proxy = "http://127.0.0.1:7890"

# 配置机器人意图
import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.voice_states = True      # 启用语音状态监听
intents.members = True           # 启用成员监听（需要获取成员信息）
intents.message_content = True   # 启用消息内容意图（用于命令功能）

# 创建机器人实例
bot = commands.Bot(command_prefix='!', intents=intents, proxy=http_proxy,  reconnect=True )

@bot.event
async def on_voice_state_update(member, before, after):
    if member.id != bot.user.id:
        return
    
    # 检查是否断开连接
    if before.channel and not after.channel:
        print(f"机器人被断开连接或离开频道")
        # 如果之前是主动离开，不自动重连
        
        # 延迟后尝试重连
        await asyncio.sleep(2)

        await try_reconnect(bot, args.channel) 

@bot.event
async def on_connect():
    """连接到Discord时触发"""
    logging.info('已连接到Discord服务器')

@bot.event
async def on_disconnect():
    """与Discord断开连接时触发"""
    logging.info('与Discord服务器断开连接')

@bot.event
async def on_resumed():
    """连接恢复时触发"""
    logging.info('连接已恢复')
    
async def run_bot():
    """运行机器人的主函数"""
    try:
        await main(bot)
        print("main over")
    except KeyboardInterrupt:
        print("Exiting...")
        await bot.close()
        # this sleep prevents a bugged exception on Windows
        await asyncio.sleep(1)
    except Exception as e:
        print(e)

# 使用现代的asyncio.run()方法启动机器人
if __name__ == "__main__":
    try:
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        print("程序被用户中断")

