
from enum import Enum

class JEPacketConnectionState(Enum):
    # パケットの接続状態
    HANDSHAKING = 0
    STATUS = 1
    LOGIN = 2
    CONFIGURATION = 3
    PLAY = 4
    CLOSED = 5