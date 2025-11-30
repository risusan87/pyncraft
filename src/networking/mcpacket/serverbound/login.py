
import os
import uuid

import requests

from core.logger import logger
from networking.mcpacket import ServerboundPacket
from networking.enum import JEPacketConnectionState
from networking.mcrypto import decrypt_rsa, gen_ciphers, auth_hash
import networking.mcpacket.clientbound.login as login

@ServerboundPacket.register_packet(JEPacketConnectionState.LOGIN, 0x00)
class SLoginStart(ServerboundPacket):
    def __init__(self, username: str, uuid: uuid.UUID):
        self.username = username
        self.uuid = uuid

    @property
    def packet_id(self):
        return self._packet_id
    
    def handle(self, con_state) -> login.CEncryptionRequest:
        # C -> S: Login Start
        # S -> C: LoginSuccess
        public_der = con_state.public_der
        con_state.username = self.username
        con_state.uuid = self.uuid
        verify_token = os.urandom(16)
        con_state.verify_token = verify_token
        return login.CEncryptionRequest(public_der, verify_token)

    @classmethod
    def from_bytes(cls, packet_buffer):
        username = packet_buffer.read_utf8_string(16)
        uuid = packet_buffer.read_uuid()
        return cls(username, uuid)

@ServerboundPacket.register_packet(JEPacketConnectionState.LOGIN, 0x01)
class SEncryptionResponse(ServerboundPacket):
    def __init__(self, shared_secret: bytes, verify_token: bytes):
        self._shared_secret = shared_secret
        self._verify_token = verify_token
        
    @property
    def packet_id(self):
        return self._packet_id
    
    def handle(self, con_state) -> login.CLoginSuccess | login.CDisconnect:
        # C -> S: Encryption Response
        # S -> C: Login Success
        rsa_private, _ = con_state.rsa_pair
        server_id = con_state.server_id
        public_der = con_state.public_der
        verify_token = decrypt_rsa(self._verify_token, rsa_private)
        if con_state.verify_token != verify_token:
            return login.CDisconnect("Encryption failed")
        shared_key = decrypt_rsa(self._shared_secret, rsa_private)
        con_state.cipher_pair = gen_ciphers(shared_key)
        # Client authentication
        hash = auth_hash(server_id, shared_key, public_der)
        params = {
            'username': con_state.username,
            'serverId': hash,
        }
        response = requests.get('https://sessionserver.mojang.com/session/minecraft/hasJoined', params=params)
        if response.status_code != 200:
            return login.CDisconnect(f"Authentication failed ({response.status_code}): Mojang API is down perhaps?")
        data = response.json()
        profile_id = uuid.UUID(data.get('id'))
        player_name = data.get('name')
        name = data.get('properties')[0].get('name')
        value = data.get('properties')[0].get('value')
        signature = data.get('properties')[0].get('signature')
        logger.info(f'Player {player_name} ({profile_id}) has been authorized', False)
        return login.CLoginSuccess(profile_id, player_name, name, value, signature)

    @classmethod
    def from_bytes(cls, packet_buffer):
        shared_secret_length = packet_buffer.read_varint()
        shared_secret = packet_buffer.read(shared_secret_length)
        verify_token_length = packet_buffer.read_varint()
        verify_token = packet_buffer.read(verify_token_length)
        return cls(shared_secret, verify_token)
    
@ServerboundPacket.register_packet(JEPacketConnectionState.LOGIN, 0x03)
class SLoginAcknowledged(ServerboundPacket):
    def __init__(self):
        pass

    @property
    def packet_id(self):
        return self._packet_id
    
    def handle(self, con_state):
        # S -> C: LoginSuccess 
        # C -> S: LoginAcknowledged
        con_state._switch_state(JEPacketConnectionState.CONFIGURATION)
        return None
    
    @classmethod
    def from_bytes(cls, packet_buffer):
        return cls()