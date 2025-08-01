
from networking.mcpacket import ServerboundPacket
from networking.enum import JEPacketConnectionState

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
    
    def handle(self, con_state):
        # Handle player session data
        # This is a placeholder for actual session handling logic
        con_state.session_id = self.session_id
        con_state.expiration = self.expiration
        con_state.public_key = self.public_key
        con_state.signature = self.signature
        return None
    
    @classmethod
    def from_bytes(cls, packet_buffer):
        session_id = packet_buffer.read_utf8_string(36)
        expiration = packet_buffer.read_varint()
        public_key_length = packet_buffer.read_varint()
        public_key = packet_buffer.read_bytes(public_key_length)
        signature_length = packet_buffer.read_varint()
        signature = packet_buffer.read_bytes(signature_length)
        return cls(session_id, expiration, public_key, signature)
