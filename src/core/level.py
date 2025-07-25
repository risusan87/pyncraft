
class Level:
    def __init__(self, name: str):
        self.name = name

class Chunk:
    def __init__(self, x: int, z: int):
        self.x = x
        self.z = z
        self.blocks = {}
    
    def tick(self):
        # チャンクのtick処理
        pass

class Region:
    def __init__(self, x: int, z: int):
        self.x = x
        self.z = z
        self.chunks = {}