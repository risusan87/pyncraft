
import io
import os
import zlib

import nbtlib

from core.logger import logger
from core import WORLD_PATH
from core.level.chunk import Chunk

class Level:
    def __init__(self, name: str = 'world'):
        self.name = name
        self.world_height = 256
    

class Region:
    def __init__(self, region_x: int, region_z: int):
        self.region_x = region_x
        self.region_z = region_z
        self.chunks: list[Chunk] = []
        self._region_path = f'{WORLD_PATH}/region/r.{self.region_x}.{self.region_z}.mca'

    async def read(self):
        if not os.path.exists(self._region_path):
            return Region(self.region_x, self.region_z)
        with open(self._region_path, 'rb') as file:
            data = file.read()
        if len(data) < 0x2000:
            return Region(self.region_x, self.region_z)
        # Region files begin with an 8KiB header, split into two 4KiB tables. 
        # The first containing the offsets of chunks in the region file itself, the second providing timestamps for the last updates of those chunks.
        header = data[:0x2000] 
        chunk_locations, timestamps = header[:0x1000], header[0x1000:0x2000]
        base_chunk_x, base_chunk_z = self.region_x * 32, self.region_z * 32
        for region_chunk_z in range(32):
            for region_chunk_x in range(32):
                offset = 4 * (region_chunk_x + region_chunk_z * 32)
                chunk_offset, sector_count = int.from_bytes(chunk_locations[offset:offset + 3], 'big'), chunk_locations[offset + 3]
                timestamp = int.from_bytes(timestamps[offset:offset + 4], 'big')
                chunk_x, chunk_z = base_chunk_x + region_chunk_x, base_chunk_z + region_chunk_z
                if chunk_offset != 0 and sector_count != 0:
                    # read chunk data here
                    chunk_data_offset, chunk_data_legnth = chunk_offset * 0x1000, sector_count * 0x1000
                    chunk_data = data[chunk_data_offset:chunk_data_offset + chunk_data_legnth]
                    chunk_data_length = int.from_bytes(chunk_data[:4], 'big')
                    compression_type = chunk_data[4:5]
                    chunk_data = chunk_data[5:chunk_data_length + 5]
                    # TODO: Handle different compression types (https://minecraft.wiki/w/Region_file_format)
                    if compression_type == b'\x02': # Zlib
                        chunk_data = zlib.decompress(chunk_data)
                    chunk_nbt = None if len(chunk_data) == 1 else nbtlib.File.parse(io.BytesIO(chunk_data))
                    self.chunks.append(Chunk.from_nbt(chunk_nbt) if chunk_nbt else None)

    def write(self):
        pass