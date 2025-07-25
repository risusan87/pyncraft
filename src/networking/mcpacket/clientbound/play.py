
import io

import nbtlib

from networking.mcpacket import ClientboundPacket
from networking.mcpacket.io import JEPacketBuffer
from networking.enums import JEPacketConnectionState

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