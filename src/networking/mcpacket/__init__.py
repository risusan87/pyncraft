
from abc import ABC, abstractmethod
import threading
import typing

from networking.enum import JEPacketConnectionState

JESERVERBOUND_PACKETS = {}

class Packet(ABC):
    @property
    @abstractmethod
    def packet_id(self) -> str:
        """
        SINCE v0.6: this now indicates string namespace IDs (NOT NUMERICAL IDs). Refer to "resource" namespace instead of numerical ones.
        """
        pass

class ServerboundPacket(Packet):
    """
    Base class for CLIENT initiated packets, bound to SERVER.
    """
    @staticmethod
    def register_packet(state: JEPacketConnectionState, packet_id: str):
        def wrapper(cls):
            JESERVERBOUND_PACKETS[(state, packet_id)] = cls
            cls._packet_id = packet_id
            cls._state = state
            return cls
        return wrapper
    
    def handle(self, con_state) -> 'ClientboundPacket':
        """
        Process the packet intent to digest and apply server logic, then return a reply if applicable.
        """
        pass
    
    @classmethod
    @abstractmethod
    def from_bytes(cls, packet_buffer) -> 'ServerboundPacket':
        pass
    
class ClientboundPacket(Packet):
    """
    Base class for SERVER initiated packets, bound to CLIENT.
    """
    # decorater
    @classmethod
    def repliable(*repliable_packet_types: typing.Type[ServerboundPacket]):
        """
        Indicates that this packet may expect a reply defined by its protocol.
        """
        def wrapper(cls):
            cls._repliable_packets = repliable_packet_types
            cls._reply_arrived_flag = threading.Event()
            cls._timeout_flag = threading.Event()
            cls._reply = None
            # async in future
            def wait_for_reply(self, timeout=5):
                if not self._reply_arrived_flag.wait(timeout):
                    self._timeout_flag.set()
                    None
                return self._reply
            cls.wait_for_reply = wait_for_reply
            return cls
        return wrapper

    def to_bytes(self, con_state):
        pass