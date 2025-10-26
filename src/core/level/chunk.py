
import time
import re
import math
import numpy as np

import nbtlib

from core.logger import logger
from core.level.enum import HeightmapType
from core.registry import CORE_REGISTRY
from core.util.io import NBTSerializable, NetworkSerializable
from core.util import to_signed
from core.util import BitsetsSerializer

from networking.mcpacket.io import JEPacketBuffer

class Chunk(NBTSerializable, NetworkSerializable):
    CHUNK_SIZE = 16
    '''
    Chunk size is 16 blocks wide
    '''

    def __init__(self, x: int, z: int):
        self.x = x
        self.z = z
        
        # Chunk information
        self.heightmaps: dict[HeightmapType, Heightmap] = {}
        self.sections: list[ChunkSection] = []
        self._light_data: LightData = None

    @property
    def light_data(self) -> 'LightData':
        return self._light_data

    def tick(self):
        # チャンクのtick処理
        pass
    
    @classmethod
    def from_nbt(cls, nbt_data: nbtlib.File) -> 'Chunk':
        '''
        Load chunk data from NBT format
        https://minecraft.wiki/w/Chunk_format
        '''
        if 'Status' in nbt_data and nbt_data['Status'] != 'minecraft:full':
            # logger.debug(f'Discarding load of chunk {nbt_data['xPos']}, {nbt_data['zPos']} as it\'s not fully loaded; Status is {nbt_data['Status']}')
            return
        chunk = cls(nbt_data['xPos'], nbt_data['zPos'])
        # Load heightmap info
        for heightmap_type, bitset_list in nbt_data['Heightmaps'].items():
            chunk.heightmaps[HeightmapType[heightmap_type]] = Heightmap.from_nbt(HeightmapType[heightmap_type], bitset_list)
        # Load chunk sections and biomes
        for section_nbt in nbt_data['sections']:
            chunk.sections.append(ChunkSection.from_nbt(section_nbt))
        # Load light data
        chunk._light_data = LightData.from_nbt(nbt_data['sections'])

        return chunk

    def to_nbt(self) -> nbtlib.File:
        '''
        Convert the chunk to NBT format
        '''
        nbt_data = {}
        nbt_data['xPos'] = nbtlib.Int(self.x)
        nbt_data['zPos'] = nbtlib.Int(self.z)
        nbt_data['Status'] = nbtlib.String('minecraft:full')
        # Chunk Sections
        sections = []
        for section, light_data in zip(self.sections, self.light_data.to_nbt()):
            section_nbt = section.to_nbt()
            for light_type, byte_array_nbt in light_data.items():
                section_nbt[light_type] = byte_array_nbt
            sections.append(section_nbt)
        nbt_data['sections'] = nbtlib.List[nbtlib.Compound](sections)
        return nbtlib.Compound(nbt_data)

    def write_buffer(self, packet_buffer: JEPacketBuffer) -> None:
        # heightmaps
        heightmaps: dict[int, list[int]] = {}
        if HeightmapType.WORLD_SURFACE in self.heightmaps:
            heightmaps[1] = self.heightmaps[HeightmapType.WORLD_SURFACE].heightmap_bitsets
        if HeightmapType.MOTION_BLOCKING in self.heightmaps:
            heightmaps[4] = self.heightmaps[HeightmapType.MOTION_BLOCKING].heightmap_bitsets
        if HeightmapType.MOTION_BLOCKING_NO_LEAVES in self.heightmaps:
            heightmaps[5] = self.heightmaps[HeightmapType.MOTION_BLOCKING_NO_LEAVES].heightmap_bitsets
        packet_buffer.write_varint(len(heightmaps)) # size of heightmaps array
        for heightmap_type, heightmap_bitsets in heightmaps.items():
            packet_buffer.write_varint(heightmap_type) # heightmap type enum
            packet_buffer.write_varint(len(heightmap_bitsets)) # size of heightmap data
            for bitset in heightmap_bitsets:
                packet_buffer.write_int64(bitset) # heightmap data
        
        # Data (THIS IS PREFIXED ARRAY OF BYTES)
        data_structure_buffer = JEPacketBuffer()
        for section in self.sections: # length of this array is always the world height divided by 16
            # chunk section
            air_blocks = (0, 14013, 14014)
            is_not_air_mask = np.isin(section.blocks, air_blocks, invert=True)
            non_air_block_count = np.count_nonzero(is_not_air_mask)
            data_structure_buffer.write_int16(non_air_block_count) # block count
            # Paletted Containers
            # block states
            block_state_palette = section.block_state_palette
            bpe = math.ceil(math.log2(len(block_state_palette)))
            bpe = 0 if bpe == 0 else 4 if bpe < 4 else bpe
            data_structure_buffer.write_uint8(bpe) # bits per entry
            if bpe == 0: # Single Valued
                data_structure_buffer.write_varint(block_state_palette[0]) # Value
            else: # Indirect
                data_structure_buffer.write_varint(len(block_state_palette)) # palette length
                for block_id in block_state_palette: # palette
                    data_structure_buffer.write_varint(block_id)
                for bitset in section.block_state_bitsets: # data array
                    data_structure_buffer.write_int64(to_signed(bitset, 64))
            # biomes
            biome_palette = section.biome_palette
            bpe = math.ceil(math.log2(len(biome_palette)))
            data_structure_buffer.write_uint8(bpe) # bits per entry
            if bpe == 0: # Single Valued
                data_structure_buffer.write_varint(biome_palette[0]) # Value
            else: # Indirect
                data_structure_buffer.write_varint(len(biome_palette)) # palette length
                for biome_id in biome_palette: # palette
                    data_structure_buffer.write_varint(biome_id)
                for bitset in section.biome_bitsets: # data array
                    data_structure_buffer.write_int64(to_signed(bitset, 64))
        data_bytes = data_structure_buffer.get_value()
        logger.debug(f'Byte array size of chunk data: {len(data_bytes)}')
        packet_buffer.write_varint(len(data_bytes)) # size of sections data
        packet_buffer.write(data_bytes)

        # block entities
        packet_buffer.write_varint(0) # block entities count

        return packet_buffer
    
    @classmethod
    def read_buffer(cls, buffer):
        pass

    # def heightmaps(self) -> dict[HeightmapType, list[int]]:
    #     '''
    #     PROTOCOL SPECIFICATION - not used by logical server
    #     Extracts a copy of heightmaps in the chunk as per the chunk format protocol
    #     '''
    #     heightmaps = {}
    #     if self.chunk_data and 'Heightmaps' in self.chunk_data:
    #         heightmaps_nbt = self.chunk_data['Heightmaps']
    #         for heightmap_type in heightmaps_nbt:
    #             heightmaps[HeightmapType[heightmap_type]] = [int(long_nbt) for long_nbt in heightmaps_nbt[heightmap_type]]
    #     return heightmaps
    
    # def data(self, biomes) -> dict:
    #     '''
    #     PROTOCOL SPECIFICATION - not used by logical server
    #     Extracts a copy of chunk sections as per the chunk format protocol
    #     '''
    #     nbt_sections = self.chunk_data['sections'] if self.chunk_data and 'sections' in self.chunk_data else None
    #     if not nbt_sections:
    #         return []
    #     sections = {'block_states': [], 'biomes': []}
    #     for nbt_section in nbt_sections:
    #         # block states
    #         nbt_block_states = nbt_section['block_states']
    #         palette = []
    #         non_air_palette = []
    #         for nbt_palette in nbt_block_states['palette']:
    #             state_key = str(nbt_palette['Name'])
    #             if 'Properties' in nbt_palette:
    #                 properties = dict(nbt_palette['Properties'])
    #                 sorted_keys = sorted(properties.keys())
    #                 state_key += '[' + ','.join(f'{key}={properties[key]}' for key in sorted_keys) + ']'
    #             block_state_id = CORE_REGISTRY.block_ids[state_key]
    #             palette.append(block_state_id)
    #             # air, cave air and void air are air blocks
    #             if block_state_id not in (0, 14014, 14013):
    #                 non_air_palette.append(block_state_id)
    #         # Count non-air blocks
    #         non_air_block_count = 0
    #         section_data = [int(entry) for entry in nbt_block_states['data']] if 'data' in nbt_block_states else None
    #         bpe = math.ceil(math.log2(len(palette))) if len(palette) > 1 else 0
    #         bpe = 4 if bpe < 4 else bpe
    #         for non_air_index in set(non_air_palette):
    #             all_entries = []
    #             for section_data_entry in section_data:
    #                 for entry_index in range(32 // bpe):
    #                     entry = (section_data_entry >> (entry_index * bpe)) & ((1 << bpe) - 1)
    #                     all_entries.append(entry)
    #             non_air_block_count += all_entries.count(non_air_index)
    #         sections['block_states'].append({'block_count': non_air_block_count, 'palette': palette, 'data': [int(entry) for entry in nbt_block_states['data']] if 'data' in nbt_block_states else None})
    #         # biomes
    #         nbt_biomes = nbt_section['biomes']
    #         palette = []
    #         for nbt_palette in nbt_biomes['palette']:
    #             palette.append(CORE_REGISTRY.core['minecraft:worldgen/biome'][str(nbt_palette)])
    #         sections['biomes'].append({'palette': palette, 'data': [int(entry) for entry in nbt_biomes['data']] if 'data' in nbt_biomes else None})
    #     return sections
    
    # def block_entities(self) -> list:
    #     '''
    #     PROTOCOL SPECIFICATION - not used by logical server
    #     Extracts a copy of block entities in the chunk.
    #     '''
    #     pass
    
    # def light_data(self) -> dict:
    #     '''
    #     PROTOCOL SPECIFICATION - only used by networking module
    #     Extracts a copy of light data in the chunk.
    #     '''
    #     nbt_sections = self.chunk_data['sections'] if self.chunk_data and 'sections' in self.chunk_data else None
    #     if not nbt_sections:
    #         return None
    #     block_light_mask = []
    #     sky_light_mask = []
    #     empty_sky_light_mask = []
    #     empty_block_light_mask = []
    #     block_light_array = []
    #     sky_light_array = []
    #     for y, section in enumerate(sorted(nbt_sections, key=lambda x: int(x['Y']))):
    #         logger.debug(f'Getting light information for section {section['Y']} in chunk {self.x}, {self.z}')
    #         block_light = section['BlockLight'] if 'BlockLight' in section else None
    #         sky_light = section['SkyLight'] if 'SkyLight' in section else None
    #         if y % 31 == 0:
    #             block_light_mask.append(0)
    #             sky_light_mask.append(0)
    #             empty_sky_light_mask.append(0)
    #             empty_block_light_mask.append(0)
    #         if block_light is not None:
    #             block_light_mask[-1] |= (1 << (y % 31 + 1))
    #             empty_block_light_mask_preserve = 1
    #             for i in block_light:
    #                 if int(i) != 0:
    #                     empty_block_light_mask_preserve = 0
    #                     break
    #             if empty_block_light_mask_preserve == 1:
    #                 empty_block_light_mask[-1] |= (1 << (y % 31 + 1))
    #             block_light_array.append([int(i) for i in block_light])
    #         if sky_light is not None:
    #             sky_light_mask[-1] |= (1 << (y % 31 + 1))
    #             empty_sky_light_mask_preserve = 1
    #             for i in sky_light:
    #                 if int(i) != 0:
    #                     empty_sky_light_mask_preserve = 0
    #                     break
    #             if empty_sky_light_mask_preserve == 1:
    #                 empty_sky_light_mask[-1] |= (1 << (y % 31 + 1))
    #             sky_light_array.append([int(i) for i in sky_light])
    #     return {
    #         'block_light_mask': [0],
    #         'sky_light_mask': [0],
    #         'empty_block_light_mask': [0],
    #         'empty_sky_light_mask': [0],
    #         'block_light_array': [],
    #         'sky_light_array': []
    #     }

    def surface_level(self, x: int, z: int) -> int:
        '''
        Gets the surface level of the block at the given x, z coordinates.
        Coordinates are relative to the chunk's origin (Not absolute coordinates).
        Returning int is in range of 0 - 384, where 0 is the lowest level and 384 is the highest level.
        '''
        if HeightmapType.WORLD_SURFACE not in self.heightmaps:
            logger.warning(f'World surface heightmap not found in chunk {self.x}, {self.z}')
            return None
        return int(self.heightmaps[HeightmapType.WORLD_SURFACE].map[x, z])

    def section_blocks(self, section_y: int) -> np.ndarray:
        '''
        Extracts a copy of chunk sections as section_length x 16 x 16 x 16 numpy arrays.
        shape represents (x, z, y), and is relative to the chunk's origin (Not absolute coordinates).
        Sections' y level at 1.18+ starts at -4
        '''
        nbt_sections = self.chunk_data['sections'] if self.chunk_data and 'sections' in self.chunk_data else None
        if not nbt_sections:
            return None
        sections = np.zeros((16, 16, 16), dtype=np.int16)
        level_indices = [int(sec['Y']) for sec in nbt_sections]
        if section_y not in level_indices:
            logger.warning(f'Section level {section_y} not found or out of range {self.x}, {self.z}')
            return None
        section = nbt_sections[level_indices.index(section_y)]
        palette = []
        for nbt_palette in section['block_states']['palette']:
            state_key = str(nbt_palette['Name'])
            if 'Properties' in nbt_palette:
                properties = dict(nbt_palette['Properties'])
                sorted_keys = sorted(properties.keys())
                state_key += '[' + ','.join(f'{key}={properties[key]}' for key in sorted_keys) + ']'
            palette.append(CORE_REGISTRY.block_ids[state_key])
        bpe = math.ceil(math.log2(len(palette)))
        bpe = 0 if bpe == 0 else 4 if bpe <= 4 else bpe
        bpe_mask = (1 << bpe) - 1
        for data_idx, data in enumerate(section['block_states']['data']):
            entries_per_32int = 32 // bpe
            for i in range(entries_per_32int):
                pos = i * bpe
                shifted_entry = data >> pos
                entry = shifted_entry & bpe_mask
                block_pos = data_idx * 16 + i
                x, z, y = block_pos % 16, (block_pos // 16) % 16, (block_pos // 16) // 16
                sections[x, z, y] = palette[entry]
        return sections

class ChunkSection(NBTSerializable):
    '''
    Represents a chunk section in the chunk.
    A chunk section is a 16x16x16 block area within a chunk.
    '''
    VALUES_PER_BLOCK_STATE = Chunk.CHUNK_SIZE * Chunk.CHUNK_SIZE * Chunk.CHUNK_SIZE
    '''
    Number of blocks in a chunk section, which is 16 x 16 x 16 = 4096
    '''
    VALUES_PER_BIOME = 64
    '''
    Number of biomes in a chunk section, which is 4 x 4 x 4 = 64
    Biome size is fixed as of 1.21.8
    '''
    def __init__(self, y: int):
        self.y = y
        self.blocks: np.ndarray = None
        self.biomes: np.ndarray = None
        self._block_state_palette: list[int] = None
        self._biome_palette: list[int] = None
        self._block_state_bitsets: list[int] = None
        self._biome_bitsets: list[int] = None
    
    @property
    def is_direct(self) -> bool:
        return False
    
    @property
    def block_state_palette(self) -> list[int]:
        if self._block_state_palette is None:
            self._block_state_palette = [int(block_id) for block_id in np.unique(self.blocks)]
        return self._block_state_palette

    @property
    def block_state_bitsets(self) -> list[int]:
        if self._block_state_bitsets is None:
            if self.is_direct: # Direct
                # Direct BPE is 15 for vanilla servers
                # This will only to change if modded clients register more blocks
                bitset_serializer = BitsetsSerializer(15, 64)
                return bitset_serializer.to_bitsets(self.blocks.flatten().tolist())
            bpe = math.ceil(math.log2(len(self.block_state_palette)))
            if bpe == 0: # Single Valued
                return None
            bitset_serializer = BitsetsSerializer(4 if bpe < 4 else bpe, 64)
            entries = [self.block_state_palette.index(block_id) for block_id in self.blocks.flatten().tolist()]
            self._block_state_bitsets = bitset_serializer.to_bitsets(entries)
        return self._block_state_bitsets

    @property
    def biome_palette(self) -> list[int]:
        if self._biome_palette is None:
            self._biome_palette = [int(biome_id) for biome_id in np.unique(self.biomes)]
        return self._biome_palette

    @property
    def biome_bitsets(self) -> list[int]:
        if self._biome_bitsets is None:
            if self.is_direct:  # Direct
                # Direct BPE is 6 for vanilla servers, varies depending on contents of Registry Data packet
                bitset_serializer = BitsetsSerializer(6, 64) 
                return bitset_serializer.to_bitsets(self.biomes.flatten().tolist())
            bpe = math.ceil(math.log2(len(self.biome_palette)))
            if bpe == 0:  # Single Valued
                return None
            bitset_serializer = BitsetsSerializer(bpe, 64)
            entries = [self.biome_palette.index(biome_id) for biome_id in self.biomes.flatten().tolist()]
            self._biome_bitsets = bitset_serializer.to_bitsets(entries)
        return self._biome_bitsets

    def to_nbt(self) -> nbtlib.Compound:
        '''
        Convert the chunk section to NBT format.
        '''
        nbt_section = {}
        nbt_section['Y'] = nbtlib.Int(self.y)
        if self.blocks is not None:
            palettes = []
            for palette_entry in self.block_state_palette:
                block_state_str_id = [str_id for str_id, num_id in CORE_REGISTRY.block_ids.items() if num_id == palette_entry][0]
                properties = re.findall(r'\[(.*?)\]', block_state_str_id)
                properties = properties[0] if len(properties) > 0 else None
                namespace = block_state_str_id.replace(f'[{properties}]', '') if properties else block_state_str_id
                properties = {prop.split('=')[0]: prop.split('=')[1] for prop in properties.split(',') if prop} if properties else None
                palette_entry_nbt = {'Name': nbtlib.String(namespace)}
                if properties:
                    palette_entry_nbt['Properties'] = nbtlib.Compound({k: nbtlib.String(v) for k, v in properties.items()})
                palettes.append(nbtlib.Compound(palette_entry_nbt))
            block_states = {
                'palette': nbtlib.List[nbtlib.Compound](palettes)
            }
            if len(palettes) > 1:
                block_states['data'] = nbtlib.LongArray([to_signed(i, 64) for i in self.block_state_bitsets])
            nbt_section['block_states'] = nbtlib.Compound(block_states)
        if self.biomes is not None:
            biomes = {
                'palette': nbtlib.List[nbtlib.String]([nbtlib.String([biome_str_id for num_id, biome_str_id in enumerate(CORE_REGISTRY.core['minecraft:worldgen/biome'].items()) if num_id == biome][0]) for biome in self.biome_palette])
            }
            if len(self.biome_palette) > 1:
                biomes['data'] = nbtlib.LongArray([to_signed(i, 64) for i in self.biome_bitsets])
            nbt_section['biomes'] = nbtlib.Compound(biomes)
        return nbt_section
    
    @classmethod
    def from_nbt(cls, nbt_data: nbtlib.List[nbtlib.Compound]) -> 'ChunkSection':
        '''
        Creates a ChunkSection instance from NBT section data.
        nbt_data must be an nbt list of compound sections.
        '''
        # TODO: Encapsulate bitset logic
        chunk_section = cls(nbt_data['Y'])
        block_states = []
        palette = []
        for nbt_palette in nbt_data['block_states']['palette']:
            state_key = str(nbt_palette['Name'])
            if 'Properties' in nbt_palette:
                properties = dict(nbt_palette['Properties'])
                sorted_keys = sorted(properties.keys())
                state_key += '[' + ','.join(f'{key}={properties[key]}' for key in sorted_keys) + ']'
            palette.append(CORE_REGISTRY.block_ids[state_key])
        if len(palette) == 1:
            chunk_section.blocks = np.full((Chunk.CHUNK_SIZE, Chunk.CHUNK_SIZE, Chunk.CHUNK_SIZE), palette[0], dtype=np.int16)
        elif len(palette) > 1:
            data = nbt_data['block_states']['data']
            bpe = math.ceil(math.log2(len(palette)))
            bpe = 4 if bpe < 4 else bpe
            entrys_per_bitset = 64 // bpe
            for bitset in [int(i) for i in data]:
                for i in range(entrys_per_bitset):
                    entry = (bitset >> (i * bpe)) & ((1 << bpe) - 1)
                    block_states.append(palette[entry])
            chunk_section.blocks = np.array(block_states[:ChunkSection.VALUES_PER_BLOCK_STATE], dtype=np.int16).reshape(Chunk.CHUNK_SIZE, Chunk.CHUNK_SIZE, Chunk.CHUNK_SIZE) # x z y
        elif len(palette) == 0:
            data = nbt_data['block_states']['data']
            bpe = 15
            entrys_per_bitset = 64 // bpe
            for bitset in [int(i) for i in data]:
                for i in range(entrys_per_bitset):
                    entry = (bitset >> (i * bpe)) & ((1 << bpe) - 1)
                    block_states.append(entry)
            chunk_section.blocks = np.array(block_states[:ChunkSection.VALUES_PER_BLOCK_STATE], dtype=np.int16).reshape(Chunk.CHUNK_SIZE, Chunk.CHUNK_SIZE, Chunk.CHUNK_SIZE)
        # biomes
        biomes = []
        palette = []
        biome_ids = {k: i for i, k in enumerate(CORE_REGISTRY.core['minecraft:worldgen/biome'].keys())}
        for nbt_palette in nbt_data['biomes']['palette']:
            palette.append(biome_ids[str(nbt_palette)])
        if len(palette) == 1:
            chunk_section.biomes = np.full((4, 4, 4), palette[0], dtype=np.int16)
        elif len(palette) > 1:
            data = nbt_data['biomes']['data']
            bpe = math.ceil(math.log2(len(palette)))
            entrys_per_bitset = 64 // bpe
            for bitset in [int(i) for i in data]:
                for i in range(entrys_per_bitset):
                    entry = (bitset >> (i * bpe)) & ((1 << bpe) - 1)
                    biomes.append(palette[entry])
            chunk_section.biomes = np.array(biomes[:ChunkSection.VALUES_PER_BIOME], dtype=np.int16).reshape(4, 4, 4)
        elif len(palette) == 0:
            data = nbt_data['biomes']['data']
            bpe = 6
            entrys_per_bitset = 64 // bpe
            for bitset in [int(i) for i in data]:
                for i in range(entrys_per_bitset):
                    entry = (bitset >> (i * bpe)) & ((1 << bpe) - 1)
                    biomes.append(entry)
            chunk_section.biomes = np.array(biomes[:ChunkSection.VALUES_PER_BIOME], dtype=np.int16).reshape(4, 4, 4)
        return chunk_section

    def __str__(self):
        return f'ChunkSection(y={self.y}, blocks={self.blocks.tolist()})'
    
    def __repr__(self):
        return self.__str__()
    
class LightData(NBTSerializable, NetworkSerializable):
    '''
    LightData of a chunk.
    Will contain 4-bit length light value information for each chunk section in the chunk.
    '''
    def __init__(self):
        self.bitset_serializer = BitsetsSerializer(4, 8)
        self._block_light: list[np.ndarray] = None
        self._sky_light: list[np.ndarray] = None

    @property
    def block_light(self) -> list[np.ndarray]:
        return self._block_light

    @property
    def sky_light(self) -> list[np.ndarray]:
        return self._sky_light

    def to_nbt(self):
        '''
        Output is nbtlib.List of nbtlib.Compound of nbtlib.ByteArray, which contains zero, either, or both of:
        - 'BlockLight': nbtlib.ByteArray of block light values
        - 'SkyLight': nbtlib.ByteArray of sky light values
        '''
        light_nbt = []
        for block_light, sky_light in zip(self.block_light, self.sky_light):
            section_light = {}
            if block_light is not None:
                block_light_values = self.bitset_serializer.to_bitsets(block_light.flatten().tolist())
                section_light['BlockLight'] = nbtlib.ByteArray([to_signed(i, 8) for i in block_light_values])
            if sky_light is not None:
                sky_light_values = self.bitset_serializer.to_bitsets(sky_light.flatten().tolist())
                section_light['SkyLight'] = nbtlib.ByteArray([to_signed(i, 8) for i in sky_light_values])
            light_nbt.append(nbtlib.Compound(section_light))
        return nbtlib.List[nbtlib.Compound](light_nbt)

    @classmethod
    def from_nbt(cls, nbt_data) -> 'LightData':
        '''
        nbt_data must be an nbtlib.List of nbtlib.Compound, which contains zero, either, or both of:
        - 'BlockLight': nbtlib.ByteArray of block light values
        - 'SkyLight': nbtlib.ByteArray of sky light values
        For missing information, the server will compute lighting on the fly.
        '''
        light_data = cls()
        block_light_values = []
        sky_light_values = []
        for section_nbt in nbt_data:
            if 'BlockLight' in section_nbt:
                block_light_nbt = section_nbt['BlockLight']
                light_values = light_data.bitset_serializer.from_bitsets(4096, [int(i) for i in block_light_nbt])
                block_light_values.append(np.array(light_values, dtype=np.int8).reshape(Chunk.CHUNK_SIZE, Chunk.CHUNK_SIZE, Chunk.CHUNK_SIZE))
            else:
                block_light_values.append(None)
            if 'SkyLight' in section_nbt:
                sky_light_nbt = section_nbt['SkyLight']
                light_values = light_data.bitset_serializer.from_bitsets(4096, [int(i) for i in sky_light_nbt])
                sky_light_values.append(np.array(light_values, dtype=np.int8).reshape(Chunk.CHUNK_SIZE, Chunk.CHUNK_SIZE, Chunk.CHUNK_SIZE))
            else:
                sky_light_values.append(None)
        light_data._block_light = block_light_values
        light_data._sky_light = sky_light_values
        return light_data

    def write_buffer(self, packet_buffer):
        light_mask_serializer = BitsetsSerializer(1, 64)
        sky_light_mask = light_mask_serializer.to_bitsets([1] + [0 if section_light is None else 1 for section_light in self.sky_light] + [1])
        block_light_mask = light_mask_serializer.to_bitsets([1] + [0 if section_light is None else 1 for section_light in self.block_light] + [1])
        completely_dark_light = np.zeros(2048, dtype=np.int16)
        completely_bright_light = np.full(2048, 255, dtype=np.int16)
        sky_light_arrays = [completely_dark_light.tolist()] + [self.bitset_serializer.to_bitsets(section_light.flatten().tolist()) for section_light in self.sky_light if section_light is not None] + [completely_bright_light.tolist()]
        block_light_arrays = [completely_dark_light.tolist()] + [self.bitset_serializer.to_bitsets(section_light.flatten().tolist()) for section_light in self.block_light if section_light is not None] + [completely_bright_light.tolist()]
        empty_sky_light_mask = light_mask_serializer.to_bitsets([1] + [1 if not np.any(section_light) else 0 for section_light in self.sky_light] + [0])
        empty_block_light_mask = light_mask_serializer.to_bitsets([1] + [1 if not np.any(section_light) else 0 for section_light in self.block_light] + [0])
        # sky light mask
        packet_buffer.write_varint(len(sky_light_mask))
        for sky_light_mask_value in sky_light_mask:
            packet_buffer.write_int64(sky_light_mask_value)
        # block light mask
        packet_buffer.write_varint(len(block_light_mask))
        for block_light_mask_value in block_light_mask:
            packet_buffer.write_int64(block_light_mask_value)
        # empty sky light mask
        packet_buffer.write_varint(len(empty_sky_light_mask))
        for empty_sky_light_mask_value in empty_sky_light_mask:
            packet_buffer.write_int64(empty_sky_light_mask_value)
        # empty block light mask
        packet_buffer.write_varint(len(empty_block_light_mask))
        for empty_block_light_mask_value in empty_block_light_mask:
            packet_buffer.write_int64(empty_block_light_mask_value)
        # sky light array
        packet_buffer.write_varint(len(sky_light_arrays))
        for sky_light_array in sky_light_arrays:
            packet_buffer.write_varint(len(sky_light_array))
            for value in sky_light_array:
                packet_buffer.write_int8(value - 256 if value > 127 else value)
        # block light array
        packet_buffer.write_varint(len(block_light_arrays))
        for block_light_array in block_light_arrays:
            packet_buffer.write_varint(len(block_light_array))
            for value in block_light_array:
                packet_buffer.write_int8(value - 256 if value > 127 else value)

    def read_buffer(self, packet_buffer):
        pass
    
    def __str__(self):
        return f'LightData(block_light={self._block_light}, sky_light={self._sky_light})'
    
    def __repr__(self):
        return self.__str__()



class Heightmap(NBTSerializable):
    '''
    Heightmap class to represent heightmaps in chunks.
    Heightmaps are stored as a list of integers, where each integer represents a heightmap entry.
    Each entry is a 9-bit value, and the number of entries depends on the heightmap type.
    The heightmap type is defined by the HeightmapType enum.
    '''
    HEIGHTMAP_BPE = 9 
    '''
    Bit-per-entry size is fixed as of 1.21.8, but may change in future, who knows
    Technically this supports up to y level of 511 (0 - 511) but specification allows range of 0 - 384
    '''
    ENTRY_PER_BITSET = 64 // HEIGHTMAP_BPE
    '''
    Literally, defines how many entries are in a bitset.
    As of 1.21.8, bitset is 64 bits long
    '''
    VALUES_PER_HEIGHTMAP = Chunk.CHUNK_SIZE * Chunk.CHUNK_SIZE
    '''
    Number of values per heightmap, which is 16 x 16 = 256
    '''

    def __init__(self, heightmap_type: HeightmapType, bitset_list: list[int]):
        self._type = heightmap_type
        self._bitset_serializer = BitsetsSerializer(Heightmap.HEIGHTMAP_BPE, 64)
        map = self._bitset_serializer.from_bitsets(Heightmap.VALUES_PER_HEIGHTMAP, bitset_list)
        self._map: np.ndarray = np.array(map, dtype=np.int16).reshape(Chunk.CHUNK_SIZE, Chunk.CHUNK_SIZE)

    def to_nbt(self) -> nbtlib.Compound:
        nbt_data = nbtlib.Compound()
        nbt_data['type'] = str(self._type)
        nbt_data['data'] = nbtlib.LongArray(self._map.flatten().tolist())
        return nbt_data
    
    @classmethod
    def from_nbt(cls, heightmap_type: HeightmapType, nbt_heightmap: nbtlib.LongArray) -> 'Heightmap':
        return cls(heightmap_type, [int(i) for i in nbt_heightmap])

    @property
    def heightmap_type(self) -> HeightmapType:
        return self._type
    
    @property
    def map(self) -> np.ndarray:
        return self._map
    
    @property
    def heightmap_bitsets(self) -> list[int]:
        entries = self.map.ravel().tolist()
        return self._bitset_serializer.to_bitsets(entries)

    
    def __str__(self):
        return f'Heightmap(type={self._type}, map={self._map.tolist()})'
    
    def __repr__(self):
        return self.__str__()