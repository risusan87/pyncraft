
from core.logger import logger

from networking.mcpacket import ServerboundPacket
from networking.enum import JEPacketConnectionState

@ServerboundPacket.register_packet(JEPacketConnectionState.PLAY, 0x00)
class SConfirmTeleport(ServerboundPacket):
    def __init__(self, teleport_id: int):
        self.teleport_id = teleport_id

    @property
    def packet_id(self):
        return self._packet_id
    
    def handle(self, con_state) -> None:
        logger.debug(f"Confirming teleport with ID: {self.teleport_id}")
        return None
    
    @classmethod
    def from_bytes(cls, packet_buffer):
        teleport_id = packet_buffer.read_varint()
        return cls(teleport_id)
    
@ServerboundPacket.register_packet(JEPacketConnectionState.PLAY, 0x09)
class SPlayerSession(ServerboundPacket):
    def __init__(self, session_id: str, expiration: int, public_key: bytes, signature: bytes):
        self.session_id = session_id
        self.expiration = expiration
        self.public_key = public_key
        self.signature = signature

    @property
    def packet_id(self):
        return self._packet_id
    
    def handle(self, con_state) -> None:
        with con_state.userinfo_lock:
            con_state.session['uuid'] = self.session_id
            con_state.session['public_key'] = self.public_key
            con_state.session['signature'] = self.signature
            con_state.session['expiration'] = self.expiration
        return None
    
    @classmethod
    def from_bytes(cls, packet_buffer):
        session_id = packet_buffer.read_uuid()
        expiration = packet_buffer.read_int64()
        public_key_length = packet_buffer.read_varint() # must be exactly 512
        public_key = packet_buffer.read(public_key_length)
        signature_length = packet_buffer.read_varint() # must be exactly 4096
        signature = packet_buffer.read(signature_length)
        return cls(session_id, expiration, public_key, signature)
    
@ServerboundPacket.register_packet(JEPacketConnectionState.PLAY, 0x0C)
class SClientTickEnd(ServerboundPacket):
    '''
    Tick synchronization for entity rendering
    Introduced in 1.21.3 so relatively new
    '''
    def __init__(self):
        pass

    @property
    def packet_id(self):
        return self._packet_id
    
    def handle(self, con_state) -> None:
        # TODO: Notify server here
        return None
    
    @classmethod
    def from_bytes(cls, packet_buffer):
        return cls()

@ServerboundPacket.register_packet(JEPacketConnectionState.PLAY, 0x12)
class SCloseContainer(ServerboundPacket):
    '''
    "This packet is sent by the client when closing a window."
    "vanilla clients send a Close Window packet with Window ID 0 to close their inventory even though there is never an Open Screen packet for the inventory."
    '''
    def __init__(self, window_id: int):
        self.window_id = window_id

    @property
    def packet_id(self):
        return self._packet_id
    
    def handle(self, con_state) -> None:
        # TODO: Notify server here
        return None

    @classmethod
    def from_bytes(cls, packet_buffer):
        window_id = packet_buffer.read_varint()
        return cls(window_id)

@ServerboundPacket.register_packet(JEPacketConnectionState.PLAY, 0x1B)
class SKeepAlive(ServerboundPacket):
    def __init__(self, keep_alive_id: int):
        self.keep_alive_id = keep_alive_id

    @property
    def packet_id(self):
        return self._packet_id
    
    def handle(self, con_state) -> None:
        # Update the keep-alive ID in the connection state
        with con_state.userinfo_lock:
            if con_state.keep_alive_id == self.keep_alive_id:
                con_state.keep_alive_id = None
        return None
    
    @classmethod
    def from_bytes(cls, packet_buffer):
        keep_alive_id = packet_buffer.read_int64()
        return cls(keep_alive_id)


@ServerboundPacket.register_packet(JEPacketConnectionState.PLAY, 0x1D)
class SSetPlayerPosition(ServerboundPacket):
    def __init__(self, x: float, feet_y: float, z: float, flags: int):
        self.x = x
        self.feet_y = feet_y
        self.z = z
        self.flags = flags

    @property
    def packet_id(self):
        return self._packet_id
    
    def handle(self, con_state) -> None:
        return None
    
    @classmethod
    def from_bytes(cls, packet_buffer):
        x = packet_buffer.read_double()
        feet_y = packet_buffer.read_double()
        z = packet_buffer.read_double()
        flags = packet_buffer.read_int8()
        return cls(x, feet_y, z, flags)

@ServerboundPacket.register_packet(JEPacketConnectionState.PLAY, 0x1E)
class SSetPlayerPositionAndRotation(ServerboundPacket):
    def __init__(self, x: float, feet_y: float, z: float, yaw: float, pitch: float, flags: int):
        self.x = x
        self.feet_y = feet_y
        self.z = z
        self.yaw = yaw
        self.pitch = pitch
        self.flags = flags
    
    @property
    def packet_id(self):
        return self._packet_id
    
    def handle(self, con_state) -> None:
        return None
    
    @classmethod
    def from_bytes(cls, packet_buffer):
        x = packet_buffer.read_double()
        feet_y = packet_buffer.read_double()
        z = packet_buffer.read_double()
        yaw = packet_buffer.read_float()
        pitch = packet_buffer.read_float()
        flags = packet_buffer.read_int8()
        return cls(x, feet_y, z, yaw, pitch, flags)
    
@ServerboundPacket.register_packet(JEPacketConnectionState.PLAY, 0x1F)
class SSetPlayerRotation(ServerboundPacket):
    def __init__(self, yaw: float, pitch: float, flags: int):
        self.yaw = yaw
        self.pitch = pitch
        self.flags = flags

    @property
    def packet_id(self):
        return self._packet_id
    
    def handle(self, con_state) -> None:
        # TODO: Notify server here
        return None

    @classmethod
    def from_bytes(cls, packet_buffer):
        yaw = packet_buffer.read_float()
        pitch = packet_buffer.read_float()
        flags = packet_buffer.read_int8()
        return cls(yaw, pitch, flags)
    
@ServerboundPacket.register_packet(JEPacketConnectionState.PLAY, 0x20)
class SSetPlayerMovementFlags(ServerboundPacket):
    def __init__(self, flags: int):
        self.flags = flags

    @property
    def packet_id(self):
        return self._packet_id
    
    def handle(self, con_state) -> None:
        return None
    
    @classmethod
    def from_bytes(cls, packet_buffer):
        flags = packet_buffer.read_int8()
        return cls(flags)

@ServerboundPacket.register_packet(JEPacketConnectionState.PLAY, 0x27)
class SPlayerAbility(ServerboundPacket):
    def __init__(self, flags: int):
        self._flags = flags

    @property
    def packet_id(self):
        return self._packet_id
    
    def handle(self, con_state) -> None:
        return None
    
    @classmethod
    def from_bytes(cls, packet_buffer):
        flags = packet_buffer.read_int8()
        return cls(flags)

@ServerboundPacket.register_packet(JEPacketConnectionState.PLAY, 0x29)
class SPlayerCommand(ServerboundPacket):
    def __init__(self, entity_id: int, action_id: int, jump_boost: int):
        self._entity_id = entity_id
        self._action_id = action_id
        self._jump_boost = jump_boost
    
    @property
    def packet_id(self):
        return self._packet_id
    
    def handle(self, con_state) -> None:
        return None
    
    @classmethod
    def from_bytes(cls, packet_buffer):
        entity_id = packet_buffer.read_varint()
        action_id = packet_buffer.read_varint()
        jump_boost = packet_buffer.read_varint()
        return cls(entity_id, action_id, jump_boost)
    
@ServerboundPacket.register_packet(JEPacketConnectionState.PLAY, 0x2A)
class SPlayerInput(ServerboundPacket):
    def __init__(self, flags: int):
        self._flags = flags
    
    @property
    def packet_id(self):
        return self._packet_id
    
    def handle(self, con_state) -> None:
        return None
    
    @classmethod
    def from_bytes(cls, packet_buffer):
        flags = packet_buffer.read_uint8()
        return cls(flags)
    