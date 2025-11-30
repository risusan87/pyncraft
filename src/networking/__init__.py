from networking.connection import ConnectionListener

_listener = None

def get_listener():
    global _listener
    if _listener is None:
        raise RuntimeError("ConnectionListener is not initialized. Call start_server() first.")
    return _listener

def start_server(server_config):
    global _listener
    _listener = ConnectionListener(server_config)
    _listener.start_server()

def stop_server():
    global _listener
    _listener.stop_server()