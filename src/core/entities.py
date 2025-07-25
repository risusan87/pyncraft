
class Entity:
    pass

class LivingEntity(Entity):
    pass

class BlockEntity(Entity):
    def __init__(self, x: int, y: int, z: int):
        self.x = x
        self.y = y
        self.z = z

class Player(LivingEntity):
    def __init__(self, username: str, uuid: str):
        super().__init__()
        self.username = username
        self.uuid = uuid
        self.inventory = []
        self.health = 20