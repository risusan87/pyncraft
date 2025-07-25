
import networking
from core.logger import logger
from core.pyncraftserver import PyncraftServer

_version = '0.0.3'

def start_server():
    try:
        logger.info("Pyncraft is running version " + _version)
        networking.start_server()
        pyncraft_server = PyncraftServer()
        pyncraft_server.start_loop()
    except KeyboardInterrupt:
        logger.info('Stopping Pyncraft server...')
        networking.stop_server()