
import os
import time
import threading
import configparser
import asyncio

from nbtlib import tag

from core.logger import logger
from core.registry import CORE_REGISTRY
from core.level import level

from networking.enum import JEPacketConnectionState
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

        self.region = level.Region(0, 0)

    def init(self):
        self._processor = get_listener()._connection_processor
        

    def start_loop(self):
        async def _run(self):
            await self.region.read()
            logger.debug(f'Chunks in region: {len(self.region.chunks)}')
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
                try:
                    await asyncio.sleep(0.05)  # 20 ticks per second
                    # logger.info('Nothing wrong.')
                except asyncio.CancelledError:
                    logger.error('Server loop interrupted')
        asyncio.run(_run(self))

    def configurations(self, connections: list[Connection]):
        for con in connections:
            con_state = con.con_state
            client_infos = con_state.configs()
            if client_infos is None:
                continue
            client_info, plugin_message = client_infos
            
            ### 
            # Registry Data (for clients 1.16.3+)
            # https://minecraft.wiki/w/Java_Edition_protocol/Registry_data
            # TODO: Of course, legacy notchian clients won't be able to handle this
            ###
            server_known_packs = configuration.CKnownPacks([])
            client_known_packs = con.queue_packet(server_known_packs, 1)
            if client_known_packs is None:
                logger.error(f'Failed to send CKnownPacks to {con._address}')
                continue
            logger.debug(f'Client\'s known packs: {client_known_packs.packs}')
            # Server computes the mutually supported data packs
            # Send registry data here
            for registry_id, entries in CORE_REGISTRY.core.items():
                logger.debug(f'Sending registry data for {registry_id} to {con._address}')
                con.queue_packet(configuration.CRegistryData(str(registry_id), dict(entries)))
            ### End of Registry Data ###

            # クライアントへPLAY状態へ移行するためのパケットを送信
            if con.queue_packet(configuration.CFinishConfiguration(), 1) is None:
                logger.error(f'Failed to send CFinishConfiguration to {con._address}')
                continue
            logger.info(f'Configuration setup for {con._address} completed. Switching to PLAY')
            con.queue_packet(play.CLogin(
                entity_id=1145,
                is_hardcore=False,
                dimension_names=list(CORE_REGISTRY.core['minecraft:dimension_type'].keys()),
                max_players=int(self.server_config.get('pyncraft', 'max_players')),
                view_distance=3,
                simulation_distance=3,
                reduced_debug_info=False,
                enable_respawn_screen=True,
                do_limited_crafting=False,
                dimension_type=1,
                dimension_name='minecraft:overworld',
                hashed_seed=0,
                gamemode=1,
                previous_gamemode=-1,
                is_debug=False,
                is_flat=False,
                has_death_location=False,
                death_dimension_name=None,
                death_location=None,
                portal_cooldown=100,
                sea_level=63,
                enforce_secure_chat=False
            ))
            spawn: level.Chunk = None
            for chunk_z in range(5):
                for chunk_x in range(5):
                    # Get the chunk from the region
                    chunk: level.Chunk = [chunk for chunk in self.region.chunks if chunk is not None and chunk.x == chunk_x and chunk.z == chunk_z][0]
                    if chunk is None:
                        logger.warning(f'Chunk ({chunk_x}, {chunk_z}) not found in region {self.region.region_x}, {self.region.region_z}')
                        continue
                    if chunk_x == 2 and chunk_z == 2:
                        spawn = chunk
                    logger.debug(f'Expected chunk coordinates: ({chunk_x}, {chunk_z}) Actual chunk coordinates: ({chunk.x}, {chunk.z})')
                    con.queue_packet(play.CChunkDataAndUpdateLight(chunk.x, chunk.z, chunk, chunk.light_data))
            surface_level = spawn.surface_level(8, 8)
            world_x = spawn.x * 16 + 8
            world_z = spawn.z * 16 + 8
            logger.debug(f'Spawn chunk at ({world_x}, {surface_level}, {world_z})')
            # Send CDefaultSpawnPosition and CSynchronizePlayerPosition packets
            logger.debug(f'Sending CDefaultSpawnPosition {(world_x, surface_level, world_z)} to {con._address}')
            con.queue_packet(play.CDefaultSpawnPosition(world_x, surface_level, world_z, 0.0))
            con.queue_packet(play.CSynchronizePlayerPosition(
                teleport_id=0,
                x=world_x,
                y=surface_level,
                z=world_z,
                velocity_x=0.0,
                velocity_y=0.0,
                velocity_z=0.0,
                yaw=0.0,
                pitch=0.0,
                flags=0
            ))
            con.queue_packet(play.CSetCenterChunk(spawn.x, spawn.z))
            logger.debug(f'Sent CChunkDataAndUpdateLight to {con._address}')
    
    def send_server_updates(self, connections: list[Connection]):
        for con in connections:
            con.queue_packet(play.CKeepAlive(199))  # Send a keep-alive packet to the client

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