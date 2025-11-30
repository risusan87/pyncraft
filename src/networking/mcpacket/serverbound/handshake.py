
from networking.mcpacket import ServerboundPacket
from networking.enum import JEPacketConnectionState

@ServerboundPacket.register_packet(JEPacketConnectionState.HANDSHAKING, 0x00)
class SHandshakePacket(ServerboundPacket):
    """
    https://minecraft.wiki/w/Java_Edition_protocol/Packets#Handshake
    """
    def __init__(self, protocol_version: int, server_address: str, server_port: int, intent: int):
        self.protocol_version = protocol_version
        self.server_address = server_address
        self.server_port = server_port
        self.intent = intent

    @property
    def packet_id(self):
        return self._packet_id

    def handle(self, con_state):
        # C -> S: Handshake
        if self.intent == 1:  # STATUS
            con_state._switch_state(JEPacketConnectionState.STATUS)
        elif self.intent == 2:  # LOGIN
            con_state._switch_state(JEPacketConnectionState.LOGIN)
        elif self.intent == 3:  # TRANSFER (for bungee?)
            con_state._switch_state(JEPacketConnectionState.TRANSFER)
        return None

    @classmethod
    def from_bytes(cls, packet_buffer):
        protocol_version = packet_buffer.read_varint() # Protocol Version
        server_address = packet_buffer.read_utf8_string(255) # Server Address 
        server_port = packet_buffer.read_uint16() # Server Port
        intent = packet_buffer.read_varint() # Intent (1: STATUS, 2: LOGIN, 3: TRANSFER)
        return cls(protocol_version, server_address, server_port, intent)
