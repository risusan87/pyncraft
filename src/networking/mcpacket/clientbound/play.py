
import io

import nbtlib

from core.util.io import NetworkSerializable

from networking.mcpacket import ClientboundPacket
from networking.mcpacket.io import JEPacketBuffer
from networking.enum import JEPacketConnectionState

class CDisconnect(ClientboundPacket):
    def __init__(self, reason: str):
        self.reason = reason

    @property
    def packet_id(self):
        return 0x1C
    
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

class CKeepAlive(ClientboundPacket):
    def __init__(self, keep_alive_id: int):
        self.keep_alive_id = keep_alive_id
    
    @property
    def packet_id(self):
        return 0x26

    def to_bytes(self, con_state):
        packet_buffer = JEPacketBuffer()
        packet_buffer.write_int64(self.keep_alive_id)
        with con_state.userinfo_lock:
            con_state.keep_alive_id = self.keep_alive_id
        return packet_buffer
    
class CChunkDataAndUpdateLight(ClientboundPacket):
    def __init__(self, chunk_x: int, chunk_z: int, chunk: NetworkSerializable, light_data: NetworkSerializable):
        self._chunk_x = chunk_x
        self._chunk_z = chunk_z
        self._chunk = chunk
        self._light_data = light_data
    
    @property
    def packet_id(self):
        return 0x27

    def to_bytes(self, con_state):
        packet_buffer = JEPacketBuffer()
        # Chunk X
        packet_buffer.write_int32(self._chunk_x)
        # Chunk Z
        packet_buffer.write_int32(self._chunk_z)
        # Chunk Data
        self._chunk.write_buffer(packet_buffer)
        # Light Data
        self._light_data.write_buffer(packet_buffer)
        return packet_buffer


class CLogin(ClientboundPacket):
    def __init__(self, 
        entity_id: int, 
        is_hardcore: bool, 
        dimension_names: list,
        max_players: int,
        view_distance: int,
        simulation_distance: int,
        reduced_debug_info: bool,
        enable_respawn_screen: bool,
        do_limited_crafting: bool,
        dimension_type: int,
        dimension_name: str,
        hashed_seed: int,
        gamemode: int,
        previous_gamemode: int,
        is_debug: bool,
        is_flat: bool,
        has_death_location: bool,
        death_dimension_name: str,
        death_location: tuple,
        portal_cooldown: int,
        sea_level: int,
        enforce_secure_chat: bool
    ):
        self.entity_id = entity_id
        self.is_hardcore = is_hardcore
        self.dimension_names = dimension_names
        self.max_players = max_players
        self.view_distance = view_distance
        self.simulation_distance = simulation_distance
        self.reduced_debug_info = reduced_debug_info
        self.enable_respawn_screen = enable_respawn_screen
        self.do_limited_crafting = do_limited_crafting
        self.dimension_type = dimension_type
        self.dimension_name = dimension_name
        self.hashed_seed = hashed_seed
        self.gamemode = gamemode
        self.previous_gamemode = previous_gamemode
        self.is_debug = is_debug
        self.is_flat = is_flat
        self.has_death_location = has_death_location
        self.death_dimension_name = death_dimension_name
        self.death_location = death_location
        self.portal_cooldown = portal_cooldown
        self.sea_level = sea_level
        self.enforce_secure_chat = enforce_secure_chat
    
    @property
    def packet_id(self):
        return 0x2B
    
    def to_bytes(self, con_state):
        packet_buffer = JEPacketBuffer()
        # Entity ID
        packet_buffer.write_int32(self.entity_id)
        # Hardcore mode
        packet_buffer.write_boolean(self.is_hardcore)
        # Dimension names
        packet_buffer.write_varint(len(self.dimension_names))
        for name in self.dimension_names:
            packet_buffer.write_utf8_string(name)
        # Max players
        packet_buffer.write_varint(self.max_players)
        # View distance
        packet_buffer.write_varint(self.view_distance)
        # Simulation distance
        packet_buffer.write_varint(self.simulation_distance)
        # Reduced debug info
        packet_buffer.write_boolean(self.reduced_debug_info)
        # Enable respawn screen
        packet_buffer.write_boolean(self.enable_respawn_screen)
        # Do limited crafting
        packet_buffer.write_boolean(self.do_limited_crafting)
        # Dimension type
        packet_buffer.write_varint(self.dimension_type)
        # Dimension name
        packet_buffer.write_utf8_string(self.dimension_name)
        # Hashed seed
        packet_buffer.write_int64(self.hashed_seed)
        # Gamemode
        packet_buffer.write_uint8(self.gamemode)
        # Previous gamemode
        packet_buffer.write_int8(self.previous_gamemode)
        # Is debug world
        packet_buffer.write_boolean(self.is_debug)
        # Is flat world
        packet_buffer.write_boolean(self.is_flat)
        # Has death location
        packet_buffer.write_boolean(self.has_death_location)
        # Death dimension name
        if self.has_death_location:
            packet_buffer.write_utf8_string(self.death_dimension_name)
        # Death location
        if self.has_death_location:
            packet_buffer.write_position(self.death_location)
        # Portal cooldown
        packet_buffer.write_varint(self.portal_cooldown)
        # Sea level
        packet_buffer.write_varint(self.sea_level)
        # Enforce secure chat
        packet_buffer.write_boolean(self.enforce_secure_chat)
        return packet_buffer

class CSynchronizePlayerPosition(ClientboundPacket):
    def __init__(self, 
            teleport_id: int, 
            x: float, 
            y: float, 
            z: float, 
            velocity_x: float,
            velocity_y: float,
            velocity_z: float,
            yaw: float, 
            pitch: float, 
            flags: int
        ):
        self.teleport_id = teleport_id
        self.x = x
        self.y = y
        self.z = z
        self.velocity_x = velocity_x
        self.velocity_y = velocity_y
        self.velocity_z = velocity_z
        self.yaw = yaw
        self.pitch = pitch
        self.flags = flags

    @property
    def packet_id(self):
        return 0x41

    def to_bytes(self, con_state):
        packet_buffer = JEPacketBuffer()
        packet_buffer.write_varint(self.teleport_id)
        packet_buffer.write_double(self.x)
        packet_buffer.write_double(self.y)
        packet_buffer.write_double(self.z)
        packet_buffer.write_double(self.velocity_x)
        packet_buffer.write_double(self.velocity_y)
        packet_buffer.write_double(self.velocity_z)
        packet_buffer.write_float(self.yaw)
        packet_buffer.write_float(self.pitch)
        packet_buffer.write_int32(self.flags)
        return packet_buffer
    
class CPlayerRotation(ClientboundPacket):
    def __init__(self, yaw: float, pitch: float):
        self.yaw = yaw
        self.pitch = pitch

    @property
    def packet_id(self):
        return 0x42
    
    def to_bytes(self, con_state):
        packet_buffer = JEPacketBuffer()
        packet_buffer.write_float(self.yaw)
        packet_buffer.write_float(self.pitch)
        return packet_buffer
    
class CSetCenterChunk(ClientboundPacket):
    def __init__(self, chunk_x: int, chunk_z: int):
        self.chunk_x = chunk_x
        self.chunk_z = chunk_z

    @property
    def packet_id(self):
        return 0x57
    
    def to_bytes(self, con_state):
        packet_buffer = JEPacketBuffer()
        packet_buffer.write_varint(self.chunk_x)
        packet_buffer.write_varint(self.chunk_z)
        return packet_buffer
    
class CDefaultSpawnPosition(ClientboundPacket):
    def __init__(self, x: float, y: float, z: float, angle: float):
        self.x = x
        self.y = y
        self.z = z
        self.angle = angle

    @property
    def packet_id(self):
        return 0x5A
    
    def to_bytes(self, con_state):
        packet_buffer = JEPacketBuffer()
        packet_buffer.write_position((self.x, self.y, self.z))
        packet_buffer.write_float(self.angle)
        return packet_buffer