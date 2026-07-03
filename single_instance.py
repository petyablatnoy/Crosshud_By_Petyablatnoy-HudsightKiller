import logging
from typing import Callable, Optional

from PySide6.QtCore import QObject, QTimer
from PySide6.QtNetwork import QLocalServer, QLocalSocket

from app_metadata import SINGLE_INSTANCE_SERVER_NAME


class SingleInstanceManager(QObject):
    SERVER_NAME = SINGLE_INSTANCE_SERVER_NAME
    COMMAND_SHOW = b"show\n"

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.server: Optional[QLocalServer] = None
        self.on_show: Optional[Callable[[], None]] = None

    @classmethod
    def notify_existing(cls, timeout_ms: int = 350) -> bool:
        socket = QLocalSocket()
        socket.connectToServer(cls.SERVER_NAME)
        if not socket.waitForConnected(timeout_ms):
            socket.abort()
            return False

        socket.write(cls.COMMAND_SHOW)
        socket.flush()
        socket.waitForBytesWritten(timeout_ms)
        socket.disconnectFromServer()
        return True

    def start(self, on_show: Callable[[], None]) -> bool:
        self.on_show = on_show
        self.server = QLocalServer(self)
        self.server.newConnection.connect(self._handle_connection)

        if self.server.listen(self.SERVER_NAME):
            return True

        logging.warning("Single-instance server failed, trying to remove stale server: %s", self.server.errorString())
        QLocalServer.removeServer(self.SERVER_NAME)
        if self.server.listen(self.SERVER_NAME):
            return True

        logging.error("Single-instance server unavailable: %s", self.server.errorString())
        return False

    def _handle_connection(self):
        if not self.server:
            return

        while self.server.hasPendingConnections():
            socket = self.server.nextPendingConnection()
            socket.readyRead.connect(lambda s=socket: self._read_command(s))
            if socket.bytesAvailable():
                self._read_command(socket)

    def _read_command(self, socket: QLocalSocket):
        data = bytes(socket.readAll()).strip()
        socket.disconnectFromServer()
        socket.deleteLater()
        if data == self.COMMAND_SHOW.strip() and self.on_show:
            QTimer.singleShot(0, self.on_show)
