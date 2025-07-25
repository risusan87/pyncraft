
from networking.mcpacket import ServerboundPacket
from networking.enums import JEPacketConnectionState

@ServerboundPacket.register_packet(JEPacketConnectionState.CONFIGURATION, 0x00)
class SClientInformation(ServerboundPacket):
    def __init__(self, locale: str, view_distance: int, chat_mode: int, chat_colors: bool, displayed_skin_parts: int, main_hand: int):
        self.locale = locale
        self.view_distance = view_distance
        self.chat_mode = chat_mode
        self.chat_colors = chat_colors
        self.displayed_skin_parts = displayed_skin_parts
        self.main_hand = main_hand
    
    @property
    def packet_id(self):
        return self._packet_id
    
    def handle(self, con_state):
        # クライアント情報を受け取った際の処理
        with con_state.config_lock:
            con_state.client_info = self
        return None
    
    @classmethod
    def from_bytes(cls, packet_buffer):
        protocol_version = packet_buffer.read_varint()
        username = packet_buffer.read_utf8_string()
        entity_id = packet_buffer.read_varint()
        entity_uuid = packet_buffer.read_uuid()
        is_hardcore = packet_buffer.read_boolean()
        is_demo = packet_buffer.read_boolean()
        return cls(protocol_version, username, entity_id, entity_uuid, is_hardcore, is_demo)
    

@ServerboundPacket.register_packet(JEPacketConnectionState.CONFIGURATION, 0x02)
class SPluginMessage(ServerboundPacket):
    def __init__(self, channel: str, data: bytes):
        self.channel = channel
        self.data = data

    @property
    def packet_id(self):
        return self._packet_id
    
    def handle(self, con_state):
        # クライアントからのプラグインメッセージを処理する
        with con_state.config_lock:
            con_state.plugin_message = self
        pass

    @classmethod
    def from_bytes(cls, packet_buffer):
        channel = packet_buffer.read_utf8_string()
        data = packet_buffer.remaining_bytes()
        return cls(channel, data)
    
@ServerboundPacket.register_packet(JEPacketConnectionState.CONFIGURATION, 0x03)
class SFinishConfigurationAcknowledged(ServerboundPacket):
    def __init__(self):
        pass

    @property
    def packet_id(self):
        return self._packet_id

    def handle(self, con_state):
        # 設定完了の確認応答を処理する
        con_state._switch_state(JEPacketConnectionState.PLAY)
        return None

    @classmethod
    def from_bytes(cls, packet_buffer):
        return cls()