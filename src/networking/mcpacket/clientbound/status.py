
import json

from networking.mcpacket import ClientboundPacket
from networking.mcpacket.io import JEPacketBuffer

class CStatusResponse(ClientboundPacket):
    def __init__(self, server_version: str, protocol_version: int, max_players: int, online_players: int, sample_players: list, description: str):
        # サーバーの状態をJSON形式で保持
        self.json_data = {
            'version': {
                'name': server_version,
                'protocol': protocol_version
            },
            'players': {
                'max': max_players,
                'online': online_players,
                'sample': sample_players
            },
            'description': {
                'text': description
            }
        }
    
    @property
    def packet_id(self):
        return 0x00
    
    def to_bytes(self, con_state):
        packet_buffer = JEPacketBuffer()
        # JSONデータをUTF-8文字列として書き込む
        packet_buffer.write_utf8_string(json.dumps(self.json_data), 32767)
        return packet_buffer

class CPongResponse(ClientboundPacket):
    def __init__(self, timestamp: int):
        self.timestamp = timestamp

    @property
    def packet_id(self):
        return 0x01
    
    def to_bytes(self, con_state):
        packet_buffer = JEPacketBuffer()
        packet_buffer.write_int64(self.timestamp)
        return packet_buffer