
import os
import json

from nbtlib import tag

from core.logger import logger

block_state_ids = {}

def register_block_states():
    '''
	Registers block states from a JSON file to the block_state_ids dictionary.
	Mapping information is provided by notchian server jar's Data Generator:
    https://minecraft.wiki/w/Minecraft_Wiki:Projects/wiki.vg_merge/Data_Generators
	'''
    global block_state_ids
    logger.info('Registering block states...')
    with open('src/core/registry/data/blocks.json', 'r') as f:
        ids = json.load(f)
    for block_state in ids:
        block_state_ids[block_state] = ids[block_state]
    logger.info(f'Registered {len(block_state_ids)} block states')

class DataPackRegistry:
    '''
    Modern way to register Minecraft data.
    This is done by reading data packs, which was introduced in Minecraft 1.16.
    Specifically, notchian clients 1.16.3+ supports this method.
    For registry, you can refer to wiki: https://minecraft.wiki/w/Java_Edition_protocol/Registry_data
    However, the wiki is INCORRECT that there is only 9 registries that are supported by notchian clients.
    You can basically send any registry data with valid registry ID and structure.
    For this, refer to the Minecraft Data reverse engineering repository at: https://github.com/PrismarineJS/minecraft-data
    '''
    def __init__(self, registry_path: str, registry_name: str):
        self._registry_path = registry_path
        self._registry_name = registry_name
        self.registry_data = {}
    
    def register_all(self):
        for registry_file in os.listdir(self._registry_path):
            if registry_file.endswith('.json'):
                registry_id = self._registry_name + ':' + registry_file.removesuffix('.json').replace('.', '/')
                with open(os.path.join(self._registry_path, registry_file), 'r') as f:
                    data = json.load(f)
                def _parse_json(value):
                    if isinstance(value, str):
                        return tag.String(value)
                    elif isinstance(value, bool):
                        return tag.Byte(1 if value else 0)
                    elif isinstance(value, int):
                        return tag.Int(value)
                    elif isinstance(value, float):
                        return tag.Float(value)
                    elif isinstance(value, list):
                        return tag.List([_parse_json(item) for item in value])
                    elif isinstance(value, dict):
                        return tag.Compound({k: _parse_json(v) for k, v in value.items()})
                    else:
                        raise ValueError(f'Unsupported type: {type(value)}')
                self.registry_data[registry_id] = {self._registry_name + ':' + k: _parse_json(v) for k, v in data.items()}
                logger.debug(f'self.registry_data[{registry_id}] = {self.registry_data[registry_id]}')
                logger.info(f'Registered {len(self.registry_data[registry_id])} entries in {registry_id}')



