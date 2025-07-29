
from enum import Enum

class JEPacketConnectionState(Enum):
    # パケットの接続状態
    HANDSHAKING = 0
    STATUS = 1
    LOGIN = 2
    CONFIGURATION = 3
    PLAY = 4
    CLOSED = 5

class JEProtocolVersion(Enum):
    '''
    https://minecraft.wiki/w/Minecraft_Wiki:Projects/wiki.vg_merge/Protocol_version_numbers
    '''
    # https://minecraft.wiki/w/Java_Edition_1.21
    # 1.21 Tricky Trials update
    v1_21_8 = 772

    # https://minecraft.wiki/w/Java_Edition_1.7
    v1_7_2 = 4