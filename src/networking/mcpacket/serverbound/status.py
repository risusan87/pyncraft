
from networking.mcpacket import ServerboundPacket
from networking.enums import JEPacketConnectionState
import networking.mcpacket.clientbound.status as status

@ServerboundPacket.register_packet(JEPacketConnectionState.STATUS, 0x00)
class SStatusRequest(ServerboundPacket):
    @property
    def packet_id(self):
        return 0x00

    def handle(self, con_state) -> status.CStatusResponse:
        # C -> S: Statusリクエスト
        # S -> C: Statusリスポンス (サーバーの状態をJSON形式で返す)

        # 将来的にはcon_stateからサーバーの状態を取得する
        mc_version = 'Pythonでマイクラサーバー書き直してみるよ' # protocol versionがマッチしない場合に表示
        protocol_version = 772 # クライアントのバージョンと照合するのに使用
        max_players = 99999 # 最大同時接続可能人数
        online_players = 9999 # 現在オンラインの人数
        # オンライン人数にホバーした時に表示するオンラインプレイヤー情報
        sample_players = [
            {'name':'ダミープレイヤー１','id':'2de4870c-deb6-42b2-8f34-36f9d2496142'},
            {'name':'ダミープレイヤー２','id':'2de4870c-deb6-42b2-8f34-36f9d2496142'},
             {'name':'ダミープレイヤー３','id':'2de4870c-deb6-42b2-8f34-36f9d2496142'}
        ] 
        description = 'Pythonでマイクラサーバー書き直してみるよ' # サーバー情報文字列

        return status.CStatusResponse(mc_version, protocol_version, max_players, online_players, sample_players, description)

    @classmethod
    def from_bytes(cls, packet_buffer):
        return cls()

@ServerboundPacket.register_packet(JEPacketConnectionState.STATUS, 0x01)
class SPingRequest(ServerboundPacket):

    def __init__(self, timestamp: int):
        self.timestamp = timestamp

    @property
    def packet_id(self):
        return self._packet_id
    
    def handle(self, con_state):
        # C -> S: Pingリクエスト
        # S -> C: Pongリスポンス (リクエストで受け取ったタイムスタンプをそのまま返す)
        return status.CPongResponse(self.timestamp)

    @classmethod
    def from_bytes(cls, packet_buffer):
        timestamp = packet_buffer.read_int64()
        return cls(timestamp)