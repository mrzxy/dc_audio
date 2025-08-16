import os
import sys
import sound
import asyncio
import logging
import discord
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtGui import QFontDatabase, QFontMetrics, QIcon
from PyQt5.QtCore import Qt, QCoreApplication, QEventLoop, QDir, pyqtSignal
from PyQt5.QtWidgets import (
    QMainWindow,
    QPushButton,
    QWidget,
    QFrame,
    QGridLayout,
    QComboBox,
    QLabel,
    QHBoxLayout,
    QStyledItemDelegate,    QListView
)

# 获取logger
logger = logging.getLogger(__name__)

if getattr(sys, "frozen", False):
    bundle_dir = sys._MEIPASS
else:
    bundle_dir = os.path.dirname(os.path.abspath(__file__))


class Dropdown(QComboBox):
    changed = pyqtSignal(object, object)

    def __init__(self):
        super(Dropdown, self).__init__()

        self.setItemDelegate(QStyledItemDelegate())
        self.setPlaceholderText("None")
        self.setView(QListView())

        self.deselected = None
        self.currentIndexChanged.connect(self.changed_signal)

    def changed_signal(self, selected):
        self.changed.emit(self.deselected, selected)
        self.deselected = selected

    def setRowHidden(self, idx, hidden):
        self.view().setRowHidden(idx, hidden)


class SVGButton(QPushButton):
    def __init__(self, text=None):
        super(SVGButton, self).__init__(text)

        self.layout = QHBoxLayout()
        self.setLayout(self.layout)

        self.svg = QSvgWidget("./assets/loading.svg", self)
        self.svg.setVisible(False)

        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addWidget(self.svg)

    def setEnabled(self, enabled):
        super().setEnabled(enabled)
        self.svg.setVisible(not enabled)


class Connection:
    def __init__(self, layer, parent):
        logger.info(f"初始化连接层 {layer}")
        self.stream = sound.PCMStream()
        self.parent = parent
        self.voice = None

        # dropdowns
        self.devices = Dropdown()
        self.servers = Dropdown()
        self.channels = Dropdown()

        for device, idx in parent.devices.items():
            self.devices.addItem(device + "   ", idx)
            logger.debug(f"添加音频设备: {device} (ID: {idx})")

        # mute
        self.mute = SVGButton("Mute")
        self.mute.setObjectName("mute")

        # add widgets
        parent.layout.addWidget(self.devices, layer, 0)
        parent.layout.addWidget(self.servers, layer, 1)
        parent.layout.addWidget(self.channels, layer, 2)
        parent.layout.addWidget(self.mute, layer, 3)

        # events
        self.devices.changed.connect(self.change_device)
        self.servers.changed.connect(
            lambda deselected, selected: asyncio.ensure_future(
                self.change_server(deselected, selected)
            )
        )
        self.channels.changed.connect(
            lambda: asyncio.ensure_future(self.change_channel())
        )

        self.mute.clicked.connect(self.toggle_mute)

    @staticmethod
    def resize_combobox(combobox):
        font = combobox.property("font")
        metrics = QFontMetrics(font)
        min_width = 0

        for i in range(combobox.count()):
            size = metrics.horizontalAdvance(combobox.itemText(i))
            if size > min_width:
                min_width = size

        combobox.setMinimumWidth(min_width + 30)

    def setEnabled(self, enabled):
        self.devices.setEnabled(enabled)
        self.servers.setEnabled(enabled)
        self.channels.setEnabled(enabled)
        self.mute.setEnabled(enabled)
        self.mute.setText("Mute" if enabled else "")

    def set_servers(self, guilds):
        logger.info(f"设置服务器列表，共 {len(guilds)} 个服务器")
        for guild in guilds:
            self.servers.addItem(guild.name, guild)
            logger.debug(f"添加服务器: {guild.name}")

    def change_device(self):
        try:
            selection = self.devices.currentData()
            logger.info(f"切换音频设备到: {selection}")
            self.mute.setText("Mute")

            if self.voice is not None:
                logger.info("停止当前音频播放并切换设备")
                self.voice.stop()
                self.stream.change_device(selection)

                if self.voice.is_connected():
                    logger.info("重新开始播放音频流")
                    self.voice.play(self.stream)

            else:
                logger.info("语音连接未建立，仅切换设备")
                self.stream.change_device(selection)

        except Exception as e:
            logger.error(f"切换音频设备时发生错误: {e}")
            logging.exception("Error on change_device")

    async def change_server(self, deselcted, selected):
        try:
            selection = self.servers.itemData(selected)
            logger.info(f"切换服务器: {selection.name if selection else 'None'}")

            self.parent.exclude(deselcted, selected)
            self.channels.clear()
            self.channels.addItem("None", None)

            voice_channels = []
            for channel in selection.channels:
                if isinstance(channel, discord.VoiceChannel):
                    self.channels.addItem(channel.name, channel)
                    voice_channels.append(channel.name)

            logger.info(f"服务器 {selection.name} 中找到 {len(voice_channels)} 个语音频道: {voice_channels}")
            Connection.resize_combobox(self.channels)

        except Exception as e:
            logger.error(f"切换服务器时发生错误: {e}")
            logging.exception("Error on change_server")

    async def change_channel(self):
        try:
            selection = self.channels.currentData()
            logger.info(f"切换语音频道: {selection.name if selection else 'None'}")
            self.mute.setText("Mute")
            self.setEnabled(False)

            if selection is not None:
                not_connected = (
                    self.voice is None
                    or self.voice is not None
                    and not self.voice.is_connected()
                )

                if not_connected:
                    logger.info(f"连接到语音频道: {selection.name}")
                    self.voice = await selection.connect(timeout=10)
                    logger.info(f"成功连接到语音频道: {selection.name}")
                else:
                    logger.info(f"移动到语音频道: {selection.name}")
                    await self.voice.move_to(selection)

                not_playing = (
                    self.devices.currentData() is not None
                    and not self.voice.is_playing()
                )

                if not_playing:
                    logger.info(f"开始播放音频流到频道: {selection.name}")
                    self.voice.play(self.stream)
                else:
                    logger.info(f"音频流已在播放中，频道: {selection.name}")

            else:
                if self.voice is not None:
                    logger.info("断开语音连接")
                    await self.voice.disconnect()

        except asyncio.TimeoutError:
            logger.error("连接语音频道超时，机器人可能没有权限加入该频道")
            logging.exception("Timed out connecting to channel. The bot may not have permissions to join the channel due to custom roles.")

        except Exception as e:
            logger.error(f"切换语音频道时发生错误: {e}")
            logging.exception("Error on change_channel")

        finally:
            self.setEnabled(True)

    def toggle_mute(self):
        try:
            if self.voice is not None:
                if self.voice.is_playing():
                    logger.info("暂停音频播放")
                    self.voice.pause()
                    self.mute.setText("Resume")
                else:
                    logger.info("恢复音频播放")
                    self.voice.resume()
                    self.mute.setText("Mute")

        except Exception as e:
            logger.error(f"切换静音状态时发生错误: {e}")
            logging.exception("Error on toggle_mute")


class TitleBar(QFrame):
    def __init__(self, parent):
        # title bar
        super(TitleBar, self).__init__()
        self.setObjectName("titlebar")

        # discord
        self.parent = parent
        self.bot = parent.bot

        # layout
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        # window title
        title = QLabel("监听t3到discord")

        # minimize
        minimize_button = QPushButton("—")
        minimize_button.setObjectName("最小化")
        layout.addWidget(minimize_button)

        # close
        close_button = QPushButton("✕")
        close_button.setObjectName("关闭")
        layout.addWidget(close_button)

        # add widgets
        layout.addWidget(title)
        layout.addStretch()
        layout.addWidget(minimize_button)
        layout.addWidget(close_button)

        # events
        minimize_button.clicked.connect(self.minimize)
        close_button.clicked.connect(lambda: asyncio.ensure_future(self.close()))

    async def close(self):
        # workaround for logout bug
        for voice in self.bot.voice_clients:
            try:
                await voice.disconnect()
            except Exception:
                pass

        self.bot._closed = True
        await self.bot.ws.close()
        self.parent.close()

    def minimize(self):
        self.parent.showMinimized()


class GUI(QMainWindow):
    def __init__(self, app, bot):
        # app
        super(GUI, self).__init__()
        QDir.setCurrent(bundle_dir)
        self.app = app

        # window info
        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)
        window_icon = QIcon("./assets/favicon.ico")
        self.setWindowTitle("Discord Audio Pipe")
        self.app.setWindowIcon(window_icon)
        self.position = None

        # discord
        self.bot = bot

        # layout
        central = QWidget()
        self.layout = QGridLayout()
        central.setLayout(self.layout)

        # labels
        self.info = QLabel("Connecting...")
        device_lb = QLabel("Devices")
        device_lb.setObjectName("label")
        server_lb = QLabel("Servers     ")
        server_lb.setObjectName("label")
        channel_lb = QLabel("Channels  ")
        channel_lb.setObjectName("label")

        # connections
        self.devices = sound.query_devices()
        self.connections = [Connection(2, self)]
        self.connected_servers = set()

        # new connections
        self.connection_btn = QPushButton("＋", self)
        self.connection_btn.setObjectName("connection_btn")

        # add widgets
        self.layout.addWidget(self.info, 0, 0, 1, 3)
        self.layout.addWidget(device_lb, 1, 0)
        self.layout.addWidget(server_lb, 1, 1)
        self.layout.addWidget(channel_lb, 1, 2)
        self.layout.addWidget(self.connection_btn, 2, 4)

        # events
        self.connection_btn.clicked.connect(self.add_connection)

        # build window
        titlebar = TitleBar(self)
        self.setMenuWidget(titlebar)
        self.setCentralWidget(central)
        self.setEnabled(False)

        # load styles
        QFontDatabase.addApplicationFont("./assets/Roboto-Black.ttf")
        with open("./assets/style.qss", "r") as qss:
            self.app.setStyleSheet(qss.read())

        # show window
        self.show()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.position = event.pos()
            event.accept()

    def mouseMoveEvent(self, event):
        if self.position is not None and event.buttons() == Qt.LeftButton:
            self.move(self.pos() + event.pos() - self.position)
            event.accept()

    def mouseReleaseEvent(self, event):
        self.position = None
        event.accept()

    def setEnabled(self, enabled):
        self.connection_btn.setEnabled(enabled)
        for connection in self.connections:
            connection.setEnabled(enabled)

    def add_connection(self):
        layer = len(self.connections) + 2

        new_connection = Connection(layer, self)
        new_connection.set_servers(self.bot.guilds)

        for idx in range(new_connection.servers.count()):
            if idx in self.connected_servers:
                new_connection.servers.setRowHidden(idx, True)

        self.layout.removeWidget(self.connection_btn)
        self.layout.addWidget(self.connection_btn, layer, 4)

        self.connections.append(new_connection)

    def exclude(self, deselected, selected):
        self.connected_servers.add(selected)
        
        if deselected is not None:
            self.connected_servers.remove(deselected)

        for connection in self.connections:
            connection.servers.setRowHidden(selected, True)

            if deselected is not None:
                connection.servers.setRowHidden(deselected, False)

    async def run_Qt(self, interval=0.01):
        while True:
            QCoreApplication.processEvents(QEventLoop.AllEvents, int(interval * 1000))
            await asyncio.sleep(interval)

    async def ready(self):
        await self.bot.wait_until_ready()

        self.info.setText(f"Logged in as: {self.bot.user.name}")
        self.connections[0].set_servers(self.bot.guilds)
        Connection.resize_combobox(self.connections[0].servers)
        self.setEnabled(True)
