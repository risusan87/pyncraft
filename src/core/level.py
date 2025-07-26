import os

from core import WORLD_PATH
class Level:
    def __init__(self, name: str):
        self.name = name

class Chunk:
    def __init__(self, x: int, z: int):
        self.x = x
        self.z = z
        self.blocks = {}
    
    def tick(self):
        # チャンクのtick処理
        pass

class Region:
    def __init__(self, x: int, z: int):
        self.x = x
        self.z = z
        self.chunks = {}

class RegionFile:
    def __init__(self, region_x: int, region_z: int):
        self.region_x = region_x
        self.region_z = region_z
        self.chunks = []

    def read(self, region_x: int, region_z: int):
        region_path = f'{WORLD_PATH}/region/r.{region_x}.{region_z}.mca'
        if os.path.exists(region_path):
            with open(region_path, 'rb') as file:
                data = file.read()
            if len(data) > 0x2000:
                header = data[:0x2000]
                chunk_locations = header[0x0:0x1000]
                timestamps = header[0x1000:0x2000]
                for region_chunk_z in range(32):
                    for region_chunk_x in range(32):
                        offset = 4 * (region_chunk_x + region_chunk_z * 32)
                        chunk_offset = int.from_bytes(chunk_locations[offset:offset + 3], 'big')
                        sector_count = chunk_locations[offset + 3]
                        print(f'region_chunk_x: {region_chunk_x}, region_chunk_z: {region_chunk_z}, offset: {chunk_offset}, sector_count: {sector_count}')
        return Region(region_x, region_z)
        pass

    def write(self):
        pass