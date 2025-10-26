
from abc import ABC, abstractmethod

from networking.mcpacket.io import JEPacketBuffer

class NBTSerializable(ABC):
    @abstractmethod
    def to_nbt(self):
        """
        Convert the object to an NBT format.
        """
        pass
    
    @classmethod
    @abstractmethod
    def from_nbt(cls, nbt_data):
        """
        Load the object from an NBT format.
        """
        pass

class NetworkSerializable(ABC):
    @abstractmethod
    def write_buffer(self, packet_buffer: JEPacketBuffer) -> None:
        """
        Convert the object to a network format.
        """
        pass

    @abstractmethod
    def read_buffer(cls, packet_buffer: JEPacketBuffer):
        """
        Load the object from a network format.
        """
        pass