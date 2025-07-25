
import os
import time
import threading
import configparser

from core.logger import logger

from networking.enums import JEPacketConnectionState
import networking.mcpacket.clientbound.configuration as configuration
import networking.mcpacket.clientbound.play as play
from networking.connection import Connection
from networking import get_listener

class PyncraftServer:
    def __init__(self):
        # クライアント接続
        self._processor = None
        self._connected_clients = []
        self._connected_clients_lock = threading.Lock()
        # Server config
        self.server_config = PyncraftConfig()
        self.server_config.load_config()
        # Live server information
        self.online_players = 0

    def init(self):
        self._processor = get_listener()._connection_processor

    def start_loop(self):
        while True:
            # サーバーに接続するすべてのクライアントを取得
            all_connections = self._processor.all_connections()
            # 接続したクライアントがコンフィグ状態ならサーバーコンフィグを設定
            config_connections = [c for c in all_connections if c.con_state.get_state() == JEPacketConnectionState.CONFIGURATION]
            self.configurations(config_connections)
            # 接続したクライアントがPLAY状態なら最後のtickで更新されたサーバー状態のパケットを送信
            play_connections = [c for c in all_connections if c.con_state.get_state() == JEPacketConnectionState.PLAY]
            self.send_server_updates(play_connections)
            # ここでサーバーtick処理
            time.sleep(0.2)

    def configurations(self, connections: list[Connection]):
        for con in connections:
            con_state = con.con_state
            client_infos = con_state.configs()
            if client_infos is None:
                continue
            client_info, plugin_message = client_infos
            # ここでコンフィグ設定
            # クライアントへPLAY状態へ移行するためのパケットを送信
            if con.queue_packet(configuration.CFinishConfiguration(), 1) is None:
                logger.error(f'Failed to send CFinishConfiguration to {con._address}')
                continue
            logger.info(f'Configuration setup for {con._address} completed. Switching to PLAY')
    
    def send_server_updates(self, connections: list[Connection]):
        for con in connections:
            con.queue_packet(play.CDisconnect('ユーザー認証、通信暗号化、コンフィグ設定が完了しました'))

class PyncraftConfig:
    def __init__(self, config_name='server.ini'):
        self.config_name = config_name
        self._config = configparser.ConfigParser()
        self._config['pyncraft'] = {
            'max_players': 20,
            'motd': 'Pyncraft Server',
            'server_port': 25565,
            'server_ip': '',
        }

    def load_config(self):
        logger.info(f'Loading server configuration...')
        if not os.path.exists('resources/' + self.config_name):
            os.makedirs('resources', exist_ok=True)
            with open('resources/' + self.config_name, 'w') as f:
                self._config.write(f)
        else:
            self._config.read('resources/' + self.config_name)
        return self._config
    
    def get(self, section: str, option: str):
        if section in self._config and option in self._config[section]:
            return self._config[section][option]
        else:
            logger.error(f'Config option {section}.{option} not found')
            return None