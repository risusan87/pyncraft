from networking.connection import ConnectionListener

# シングルトンの定義
_listener = None

def get_listener():
    global _listener
    if _listener is None:
        raise RuntimeError("ConnectionListener is not initialized. Call start_server() first.")
    return _listener

def start_server():
    global _listener
    _listener = ConnectionListener()
    # サーバーソケットを開く
    _listener.start_server()

def stop_server():
    global _listener
    # サーバーソケットを閉じる
    _listener.stop_server()