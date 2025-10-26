
import time
import math
import sys

import nbtlib

from core.level.level import Region
from core.level.chunk import LightData
from core.logger import logger
from core.level.enum import HeightmapType

import networking.mcpacket.clientbound.play as play
from networking.mcpacket.io import JEPacketBuffer


def test_loadchunk():
    logger.debug(f'Loading region')
    region00 = Region(0, 0)
    region00.read()
    logger.debug(f'{len(region00.chunks)} chunks loaded')

    sample_chunk = region00.chunks[0]
    buff = JEPacketBuffer()
    timestamp = time.time_ns()
    sample_chunk.write_buffer(buff)
    logger.debug(f'Time took {(time.time_ns() - timestamp) // 1000000} ms for section')
    
            

def test_util():
    from core.util import to_signed, to_unsigned
    assert to_signed(0xFFFFFFFFFFFFFFFF, 64) == -1
    assert to_unsigned(-1, 64) == 0xFFFFFFFFFFFFFFFF
    assert to_signed(0x7FFFFFFFFFFFFFFF, 64) == 0x7FFFFFFFFFFFFFFF
    assert to_unsigned(0x7FFFFFFFFFFFFFFF, 64) == 0x7FFFFFFFFFFFFFFF