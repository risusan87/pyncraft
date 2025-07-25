
import socket
import threading
from typing import List
import select

from core.logger import logger
from networking.mcpacket.io import JEPacketWrapper
from networking.enums import JEPacketConnectionState
from networking.mcrypto import gen_rsa_key_pair, encode_public_key_der

class ConnectionListener:
    def __init__(self):
        # サーバー停止イベントとスレッド管理用の変数
        self._server_stop_event = threading.Event()
        self._server_thread = None
        self._server = None

        # ConnectionProcessorのインスタンスを保持
        self._connection_processor = None

        # 暗号化情報
        key_pair = gen_rsa_key_pair()
        self.private = key_pair[0]
        self.public = key_pair[1]
        self.public_der = encode_public_key_der(self.public)
        self.server_id = ''

    def _listen_connection(self):
        logger.info('Listening for connections...')
        while not self._server_stop_event.is_set():
            try:
                # クライアントの接続を待機
                client, addr = self.server.accept()
            except socket.timeout:
                # タイムアウトでループ継続（_server_stop_eventフラグの検出用）
                continue
            # 新しいconnectionオブジェクトを作成してプロセッサーに委託
            con = Connection(client, addr, self)
            self._connection_processor.add_connection(con)

        # self.server_stop_eventがフラグを立てたらサーバーソケットを閉じる
        logger.info('Connection listener is shutting down...')
        
        self.server.close()
        logger.info('Terminating listener')

    def start_server(self):
        logger.info('Starting server...')
        address = '0.0.0.0'
        port = 25565
        
        # ConnectionProcessorのインスタンスを作成
        self._connection_processor = ConnectionProcessor()
        self._connection_processor.start_processor()

        # ソケットの作成とバインド
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((address, port))
        self.server.listen(1)
        self.server.settimeout(1.0)  # タイムアウトで停止フラグをチェックできるようにする

        # リスナースレッドを開始
        self.server_thread = threading.Thread(target=self._listen_connection, name='ConnectionListener')
        self.server_thread.start()
        logger.info('Server started!')
    
    def stop_server(self):
        if not self.server_thread:
            logger.warning(f'Connection listener not started.')
            return
        # 停止フラグを立ててスレッドを待機
        self._server_stop_event.set()
        self.server_thread.join()
        # 接続中のクライアントをシャットダウン
        self._connection_processor.stop_processor()
        logger.info('Server stopped!')

class ConnectionProcessor:
    def __init__(self):
        # 接続リストとロックの初期化
        self._connections: List[Connection] = []
        self._connection_list_lock = threading.Lock()

        # 接続処理の停止フラグとプロセススレッド
        self._processor_stop_event = threading.Event()
        self._processor_thread = None

    def _process_connections(self):
        # ここで接続に対する処理を行う
        while not self._processor_stop_event.is_set():
            # リスナークラスのレイテンシーを考慮してロックはなるべく短くする
            with self._connection_list_lock:
                current_connections = list(self._connections)

            # クライアントソケットの状態を確認
            read_ready, write_ready, exceptional = select.select(current_connections, current_connections, current_connections, 0)

            for connection in current_connections:
                # クライアントソケットが例外状態の場合は接続を閉じる
                if connection in exceptional:
                    logger.error(f'Connection {connection.fileno()} is in exceptional state, closing it.')
                    connection.con_state._switch_state(JEPacketConnectionState.CLOSED)
                    continue
                # クライアントソケットにデータがある場合は受信してバッファに追加
                if connection in read_ready:
                    decryptor = connection.con_state.cipher_pair[1] if connection.con_state.cipher_pair else None
                    if connection.packet_wrapper.recv_to_buffer(decryptor) == -1:
                        connection.con_state._switch_state(JEPacketConnectionState.CLOSED)
                try:
                    # ここでクライアントからのパケットがあれば処理する (C -> S)
                    outgoing_packets = []
                    with connection._awaiting_replies_lock:
                        awaiting_replies = connection._awaiting_replies
                    while (incoming_packet := connection.packet_wrapper.read_packet(connection.con_state)) is not None:
                        # サーバーが送ったパケットの返信であるか確認
                        logger.debug(f'Incoming packet: {incoming_packet}')
                        for reply in awaiting_replies:
                            if incoming_packet.__class__ in reply._repliable_packets:
                                # 返信可能なパケットがあれば待機フラグを立てる
                                if reply._timeout_flag.is_set():
                                    logger.warning(f'Timeout waiting for reply for packet {reply._packet_id}')
                                    with connection._awaiting_replies_lock:
                                        connection._awaiting_replies.remove(reply)
                                else:
                                    logger.debug(f'Packet reply arrived for {reply}')
                                    reply._reply = incoming_packet
                                    reply._reply_arrived_flag.set()
                                    with connection._awaiting_replies_lock:
                                        connection._awaiting_replies.remove(reply)
                        logger.debug(f'Handling incoming packet: {incoming_packet}')
                        outgoing_packet = incoming_packet.handle(connection.con_state)
                        if outgoing_packet is not None:
                            outgoing_packets.append(outgoing_packet)

                    # クライアント行きのパケットのキューを確認
                    with connection._outgoing_packets_lock:
                        con_packets = connection._outgoing_packets
                        connection._outgoing_packets = []
                    for outgoing_packet in con_packets:
                        outgoing_packets.append(outgoing_packet)

                    # ここでクライアントへ送信するパケットがあれば処理する (S -> C)
                    for outgoing_packet in outgoing_packets:
                        connection.packet_wrapper.write_packet(outgoing_packet, connection.con_state)
                        logger.debug(f'Outgoing packet: {outgoing_packet}')
                    
                    # クライアントソケットが書き込み可能な場合はパケットを送信
                    if connection in write_ready:
                        encryptor = connection.con_state.cipher_pair[0] if connection.con_state.cipher_pair else None
                        connection.packet_wrapper.flush(encryptor)
                except EOFError:
                    continue
                except Exception as e:
                    # バッファIO周りでエラーが発生した場合はログに記録して接続を閉じる
                    logger.exception(f'Error processing connection {connection.fileno()}: {e}')
                    connection.con_state._switch_state(JEPacketConnectionState.CLOSED)
                finally:
                    # 接続ステートがCLOSEDになった場合は接続を閉じる
                    if connection.con_state.get_state() == JEPacketConnectionState.CLOSED:
                        connection.close()
                        with self._connection_list_lock:
                            # 接続リストから削除
                            self._connections.remove(connection)
                
        # _server_stop_eventフラグが立てられたらループを抜ける
        # 接続中のクライアントをシャットダウン
        with self._connection_list_lock:
            active_connections = list(self._connections)
        for connection in active_connections:
            connection.close()
        
    def add_connection(self, connection: 'Connection'):
        # スレッドセーフなリスト改変
        with self._connection_list_lock:
            self._connections.append(connection)

    def all_connections(self):
        # 現在の接続リストを返す
        # 論理サーバー側でパケット送受信をするために使用
        with self._connection_list_lock:
            connections = list(self._connections)
        return connections

    def start_processor(self):
        # 接続処理を開始するための関数
        self._processor_thread = threading.Thread(target=self._process_connections, name='ConnectionProcessor')
        self._processor_thread.start()

    def stop_processor(self):
        # 接続処理を停止するための関数
        if not self._processor_thread:
            logger.warning(f'Connection processor not started.')
            return
        # 停止フラグを立ててスレッドを待機
        self._processor_stop_event.set()
        self._processor_thread.join()
        logger.info('Connection processor stopped!')
        pass

class Connection:
    def __init__(self, client: socket.socket, address, listener: ConnectionListener):
        self.packet_wrapper = JEPacketWrapper(client)
        self._address = address

        # クライアント行きパケットのキュー
        self._outgoing_packets = []
        self._outgoing_packets_lock = threading.Lock()

        # 返信を待つパケットのキュー
        self._awaiting_replies = []
        self._awaiting_replies_lock = threading.Lock()

        # 各クライアントの接続状態を管理するためのオブジェクト
        self.con_state = JEConnectionState(listener)

    def fileno(self):
        return self.packet_wrapper.fileno()
    
    def queue_packet(self, packet, timeout=0):
        # パケットがrepliableか確認
        # 返信待ちをするのパケットであれば
        if hasattr(packet, '_repliable_packets'):
            with self._awaiting_replies_lock:
                logger.debug(f'Adding packet {packet} to awaiting replies')
                self._awaiting_replies.append(packet)
        with self._outgoing_packets_lock:
            self._outgoing_packets.append(packet)
        # タイムアウトが設定されていない場合は返信を待たない
        if hasattr(packet, '_repliable_packets') and timeout > 0:
            reply = packet.wait_for_reply(timeout=timeout)
            return reply
        
    def close(self):
        # クライアントソケットを閉じる
        self.packet_wrapper.close()
        logger.debug(f'Connection closed: {self._address}')

class JEConnectionState:
    def __init__(self, listener: ConnectionListener):
        self._state_lock = threading.Lock()
        self._state = JEPacketConnectionState.HANDSHAKING # 接続状態を管理するための変数
        self.compression_threshold = -1 # 圧縮プロトコルのしきい値 (-1は圧縮なし)

        # クライアント情報パケット
        self.config_lock = threading.Lock()
        self.client_info = None
        self.plugin_message = None

        # 暗号化
        self.rsa_pair = (listener.private, listener.public)
        self.public_der = listener.public_der
        self.server_id = listener.server_id
        self.verify_token = None
        self.cipher_pair = None

        # ユーザー情報
        self.username = None
        self.uuid = None

    def _switch_state(self, new_state: JEPacketConnectionState):
        with self._state_lock:
            self._state = new_state
    
    def get_state(self):
        with self._state_lock:
            return self._state
    
    def configs(self):
        with self.config_lock:
            if self.client_info is None or self.plugin_message is None:
                return self.client_info, self.plugin_message
            return None