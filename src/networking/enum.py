
from enum import Enum

class JEPacketConnectionState(Enum):
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
    v1_21_10 = 773
    v1_21_9 = 773
    v1_21_8 = 772
    v1_21_7 = 772
    v1_21_6 = 771
    v1_21_5 = 770
    v1_21_4 = 769
    v1_21_3 = 768
    v1_21_2 = 768
    v1_21_1 = 767
    v1_21 = 767

    # https://minecraft.wiki/w/Java_Edition_1.7
    v1_7_5 = 4
    v1_7_4 = 4
    v1_7_2 = 4

class JEPacketIDMapping(Enum):
    '''
    Mapping of packet IDs for different protocol versions.
    '''
    p773 = {
        'protocol': '773',
        'versions': [JEProtocolVersion.v1_21_10, JEProtocolVersion.v1_21_9],
        'handshaking': {
            'c2s': ['intention'],
            's2c': []
        },
        'configuration': {
            'c2s': [],
            's2c': ['disconnect', 'finish_configuration', 'registry_data', 'known_packs']
        }
    }
    p722 = {

    }