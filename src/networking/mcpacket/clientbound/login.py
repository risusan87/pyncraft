
import uuid
import io

import nbtlib

from networking.mcpacket import ClientboundPacket
from networking.mcpacket.io import JEPacketBuffer

class CDisconnect(ClientboundPacket):
    def __init__(self, reason: str):
        self.reason = reason

    @property
    def packet_id(self):
        return 0x00
    
    def to_bytes(self, con_state):
        packet_buffer = JEPacketBuffer()
        disconnect_message = nbtlib.String(self.reason)
        buffer = io.BytesIO()
        nbtlib.File({'': disconnect_message}).save(buffer)
        packet_buffer.write(buffer.getvalue())
        return packet_buffer
    
class CEncryptionRequest(ClientboundPacket):
    def __init__(self, public_der: bytes, verify_token: bytes, should_authenticate: bool = True, server_id: str = None):
        self._public_der = public_der
        self._verify_token = verify_token
        self.should_authenticate = should_authenticate
        self.server_id = '' if not server_id else server_id

    @property
    def packet_id(self):
        return 0x01

    def to_bytes(self, con_state):
        packet_buffer = JEPacketBuffer()
        # Server ID (バニラは未使用)
        packet_buffer.write_utf8_string(self.server_id, 20)
        # 公開鍵
        packet_buffer.write_varint(len(self._public_der))
        packet_buffer.write(self._public_der)
        # 認証トークン
        packet_buffer.write_varint(len(self._verify_token))
        packet_buffer.write(self._verify_token)
        # クライアントがアカウント認証するかどうか (con_stateの値に依存)
        packet_buffer.write_boolean(self.should_authenticate)
        return packet_buffer

class CLoginSuccess(ClientboundPacket):
    def __init__(self, profile_id: uuid.UUID, player_name: str, property_name: str, value: str, signature: str):
        self.uuid = profile_id
        self.username = player_name
        self.property_name = property_name
        self.value = value
        self.signature = signature
        
    @property
    def packet_id(self):
        return 0x02
    
    def to_bytes(self, con_state):
        packet_buffer = JEPacketBuffer()
        packet_buffer.write_uuid(self.uuid)
        packet_buffer.write_utf8_string(self.username, 16)
        # プロパティ
        packet_buffer.write_varint(1)
        packet_buffer.write_utf8_string(self.property_name, 64)
        packet_buffer.write_utf8_string(self.value, 32767)
        packet_buffer.write_boolean(self.signature is not None)
        if self.signature:
            # 署名がある場合は書き込む
            packet_buffer.write_utf8_string(self.signature, 1024)
        return packet_buffer