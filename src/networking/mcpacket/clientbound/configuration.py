
import io
import json

import nbtlib

from core.logger import logger

from networking.mcpacket import ClientboundPacket
from networking.mcpacket.io import JEPacketBuffer
from networking.enum import JEPacketConnectionState
import networking.mcpacket.serverbound.configuration as config

class CDisconnect(ClientboundPacket):
    def __init__(self, reason: str):
        self.reason = reason

    @property
    def packet_id(self):
        return 0x02
    
    def to_bytes(self, con_state):
        con_state.state = JEPacketConnectionState.CLOSED
        packet_buffer = JEPacketBuffer()
        disconnect_message = nbtlib.String(self.reason)
        nbt_bytes = io.BytesIO()
        disconnect_message.write(nbt_bytes)
        # insert 0x08 (string type)
        packet_buffer.write_int8(0x08)
        packet_buffer.write(nbt_bytes.getvalue())
        return packet_buffer

@ClientboundPacket.repliable(config.SFinishConfigurationAcknowledged)
class CFinishConfiguration(ClientboundPacket):
    def __init__(self):
        pass

    @property
    def packet_id(self):
        return 0x03
    
    def to_bytes(self, con_state):
        packet_buffer = JEPacketBuffer()
        return packet_buffer
    
class CRegistryData(ClientboundPacket):
    def __init__(self, registry_id: str, entry: dict):
        '''
        Entry is a dictionary entry identifier as key and its data as value. The value is in NBT format. 
        For detailed registry id and entry structure, refer to:
        https://minecraft.wiki/w/Java_Edition_protocol/Registry_data
        '''
        self.registry_id = registry_id
        self.registry_data = entry

    @property
    def packet_id(self):
        return 0x07

    def to_bytes(self, con_state):
        packet_buffer = JEPacketBuffer()
        # Registry ID
        packet_buffer.write_utf8_string(self.registry_id)
        # Entries
        packet_buffer.write_varint(len(self.registry_data))
        for key, value in self.registry_data.items():
            # identifier
            packet_buffer.write_utf8_string(key)
            # data
            packet_buffer.write_boolean(value is not None)
            if value is not None:
                data = io.BytesIO()
                value.write(data)
                logger.debug(f'Sending: {data.getvalue().hex()}')
                packet_buffer.write_uint8(0x0a)
                packet_buffer.write(data.getvalue())
        return packet_buffer

@ClientboundPacket.repliable(config.SKnownPacks)
class CKnownPacks(ClientboundPacket):
    def __init__(self, packs: list[list[str]]):
        '''
        Packs is a list of dictionaries with keys 'pack_namespace', 'pack_id', and 'pack_version'.
        For example, a pack can be:
        a_pack = ['pack namespace', 'pack id', 'pack version']
        '''
        self.packs = packs
    
    @property
    def packet_id(self):
        return 0x0E
    
    def to_bytes(self, con_state):
        packet_buffer = JEPacketBuffer()
        # Number of packs
        packet_buffer.write_varint(len(self.packs))
        for pack in self.packs:
            # Pack namespace
            packet_buffer.write_utf8_string(pack[0])
            # Pack ID
            packet_buffer.write_utf8_string(pack[1])
            # Pack version
            packet_buffer.write_utf8_string(pack[2])
        return packet_buffer