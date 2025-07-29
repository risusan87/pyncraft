
from abc import ABC, abstractmethod

from networking.enum import JEProtocolVersion

blocks = {}

class Block(ABC):
    def __init__(self):
        self.block_state: dict = {}

    @staticmethod
    def register_block(block_identifier: str):
        def wrapper(cls):
            cls.identifier = block_identifier
            blocks[block_identifier] = cls
            return cls
        return wrapper

@Block.register_block('air')
class BlockAir(Block):
    pass

@Block.register_block('cave_air')
class BlockCaveAir(Block):
    pass

@Block.register_block('void_air')
class BlockVoidAir(Block):
    pass

@Block.register_block('stone')
class BlockStone(Block):
    pass

