
import networking
from core.logger import logger
from core.pyncraftserver import PyncraftServer

_version = '0.0.4'

def start_server():
    try:
        logger.info("Pyncraft is running version " + _version)
        pyncraft_server = PyncraftServer()
        networking.start_server(pyncraft_server.server_config)
        pyncraft_server.init()
        pyncraft_server.start_loop()
    except KeyboardInterrupt:
        logger.info('Stopping Pyncraft server...')
        networking.stop_server()