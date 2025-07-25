import logging
import threading
import os

class Logger(logging.Logger):

    def __init__(self):
        # ログ保存先ディレクトリを作成（既に存在していてもOK）
        os.makedirs('resources/logs', exist_ok=True)

        # 名前付きloggerを取得（または新規作成）
        self.logger = logging.getLogger('file_and_console')
        self.logger.setLevel(logging.DEBUG)  # ログレベルをDEBUGに設定

        # コンソール出力用のハンドラを作成
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)

        # ファイル出力用のハンドラを作成
        file_handler = logging.FileHandler('resources/logs/app.log')
        file_handler.setLevel(logging.DEBUG)

        # ログのフォーマットを定義
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)

        # コンソールとファイルの両方にハンドラを追加
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)

    def info(self, msg, log_thread=True):
        # スレッド名を付けて info ログを出力（オプションで付加）
        self.logger.info(f'{"[" + threading.current_thread().name + "] " if log_thread else ""}{msg}')

    def debug(self, msg):
        # スレッド名付きの debug ログを出力
        self.logger.debug(f'[{threading.current_thread().name}] {msg}')

    def error(self, msg):
        # スレッド名付きの error ログを出力
        self.logger.error(f'[{threading.current_thread().name}] {msg}')

    def warning(self, msg):
        # スレッド名付きの warning ログを出力
        self.logger.warning(f'[{threading.current_thread().name}] {msg}')

    def critical(self, msg):
        # スレッド名付きの critical ログを出力
        self.logger.critical(f'[{threading.current_thread().name}] {msg}')

    def exception(self, msg):
        # スレッド名付きの例外ログ（スタックトレース付き）を出力
        self.logger.exception(f'[{threading.current_thread().name}] {msg}')

# グローバルで使える logger インスタンスを作成
logger = Logger()