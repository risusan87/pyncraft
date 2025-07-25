
from networking.mcpacket import ServerboundPacket
from networking.enums import JEPacketConnectionState

@ServerboundPacket.register_packet(JEPacketConnectionState.HANDSHAKING, 0x00)
class SHandshakePacket(ServerboundPacket):

    def __init__(self, protocol_version: int, server_address: str, server_port: int, intent: int):
        self.protocol_version = protocol_version
        self.server_address = server_address
        self.server_port = server_port
        self.intent = intent

    @property
    def packet_id(self):
        return self._packet_id

    def handle(self, con_state):
        # C -> S: Handshakeパケット
        # リスポンスはなし
        if self.intent == 1:  # 接続ステートをSTATUSに切り変える
            con_state._switch_state(JEPacketConnectionState.STATUS)
        elif self.intent == 2:  # 接続ステートをLOGINに切り変える
            con_state._switch_state(JEPacketConnectionState.LOGIN)
        elif self.intent == 3:  # 接続ステートをTRANSFERに切り変える
            con_state._switch_state(JEPacketConnectionState.TRANSFER)
        return None

    @classmethod
    def from_bytes(cls, packet_buffer):
        # バイト列からHandshakeパケットを生成
        protocol_version = packet_buffer.read_varint() # varintでプロトコルバージョンを読み取る
        server_address = packet_buffer.read_utf8_string(255) # stringでサーバーアドレスを読み取る
        server_port = packet_buffer.read_uint16() # unsigned shortでサーバーポートを読み取る
        intent = packet_buffer.read_varint() # varintで次のステートを読み取る
        return cls(protocol_version, server_address, server_port, intent)
