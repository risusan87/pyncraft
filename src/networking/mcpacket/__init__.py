
from abc import ABC, abstractmethod
import threading

from networking.enum import JEPacketConnectionState

jepacket_class_registry = {}

class Packet(ABC):
    @property
    @abstractmethod
    def packet_id(self):
        pass

class ServerboundPacket(Packet):
    # クライアントからサーバーへ送信されるパケットの基底クラス
    @staticmethod
    def register_packet(state: JEPacketConnectionState, packet_id: int):
        # サーバー行きパケットIDをクラスレジストリへ登録するデコレータ
        # ステート+IDでユニークなパケットを識別するために使用
        def wrapper(cls):
            jepacket_class_registry[(state, packet_id)] = cls
            cls._packet_id = packet_id
            cls._state = state
            return cls
        return wrapper
    
    def handle(self, con_state) -> 'ClientboundPacket':
        # パケットの処理を実装
        pass
    
    @classmethod
    @abstractmethod
    def from_bytes(cls, packet_buffer) -> 'ServerboundPacket':
        # バイト列からパケットを生成する抽象関数
        pass
    
class ClientboundPacket(Packet):
    # クライアント行きパケットを返信可能にするデコレータ
    @classmethod
    def repliable(*repliable_packet_types):
        def wrapper(cls):
            cls._repliable_packets = repliable_packet_types # 返信待ちをするパケットのクラス
            cls._reply_arrived_flag = threading.Event() # 返信が来たかどうかのフラグ
            cls._timeout_flag = threading.Event() # タイムアウトしたかどうかのフラグ
            cls._reply = None # 返信内容を格納する変数
            # 返信を待つための関数
            def wait_for_reply(self, timeout=5):
                if not self._reply_arrived_flag.wait(timeout):
                    self._timeout_flag.set()
                    None
                return self._reply
            cls.wait_for_reply = wait_for_reply
            return cls
        return wrapper
    # サーバーからクライアントへ送信されるパケットの基底クラス
    def to_bytes(self, con_state): # -> PacketBuffer:
        # パケットをバイト列に変換
        pass