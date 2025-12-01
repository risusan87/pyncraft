
import networking
from core.logger import logger
from core.pyncraftserver import PyncraftServer

_version = '0.6'
pynctaft_server = None

def start_server():
    global pyncraft_server
    logger.info("Pyncraft is running version " + _version)
    pyncraft_server = PyncraftServer()
    networking.start_server(pyncraft_server.server_config)
    pyncraft_server.init()
    try:
        pyncraft_server.start_loop()
    except KeyboardInterrupt:
        pass
    finally:
        networking.stop_server()
        logger.info('Pyncraft server stopped.')