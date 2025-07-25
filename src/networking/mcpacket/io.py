
from abc import ABC, abstractmethod
import zlib
import struct
import uuid 

from networking.mcpacket import jepacket_class_registry

class Buffer:
    def __init__(self, buffer: bytes | bytearray = None, read_only: bool = False):
        # バッファの初期化
        if read_only:
            self._buffer = bytes(buffer) if buffer is not None else bytes()
        else:
            self._buffer = bytearray(buffer) if buffer is not None else bytearray()
        self._read_only = read_only
        self._position = 0
        self._mark = -1
    
    def read(self, n: int, byte_order='big'):
        # バッファからnバイト読み取る
        if self._position + n > len(self._buffer):
            raise EOFError('Buffer underflow')
        data = self._buffer[self._position:self._position + n]
        self._position += n
        return bytes(data if byte_order == 'big' else data[::-1])
    
    def write(self, data, byte_order='big'):
        # バッファにデータを書き込む
        if self._read_only:
            raise TypeError('Buffer is read only')
        self._buffer[self._position:self._position] = data if byte_order == 'big' else data[::-1]
        self._position += len(data)

    def mark(self):
        # 現在の位置をマークする
        self._mark = self._position
    
    def rewind(self):
        # マークされた位置に戻る
        if self._mark < 0:
            raise BufferError('Mark not set, cannot rewind.')
        self._position = self._mark
    
    def seek(self, position: int):
        # バッファの位置を設定
        if position < 0 or position > len(self._buffer):
            raise BufferError('Position out of bounds')
        self._position = position
    
    def flip(self):
        # バッファの位置を先頭に戻す
        self._position = 0
    
    def clear(self):
        # バッファをクリアする
        if self._read_only:
            raise TypeError('Buffer is read only')
        self._buffer.clear()
        self._position = 0
        self._mark = -1
    
    def remaining_bytes(self):
        # 現在位置からバッファの終端までのデータを取得
        return bytes(self._buffer[self._position:])

    def get_value(self):
        # バッファの内容を取得
        return bytes(self._buffer)
    
    def size(self):
        # バッファのサイズを取得
        return len(self._buffer)

class JEPacketBuffer(Buffer):
    def __init__(self, buffer: bytes | bytearray = None, read_only: bool = False):
        super().__init__(buffer, read_only=read_only)

    def read_boolean(self):
        # boolean値を読み取る
        return self.read(1)[0] == 1
    
    def write_boolean(self, value: bool):
        # boolean値を書き込む
        self.write(bytes([1 if value else 0]))

    def read_int8(self):
        # 符号付きbyteを読み取る (two's complement)
        value = self.read(1)[0]
        return value - 256 if value > 127 else value

    def write_int8(self, value: int):
        # 符号付きbyteを書き込む (two's complement)
        if not -128 <= value < 128:
            raise ValueError('Value must be between -128 and 127.')
        self.write(bytes([value & 0xFF]))
    
    def read_uint8(self):
        # 符号なしbyteを読み取る
        return self.read(1)[0]
    
    def write_uint8(self, value: int):
        # 符号なしbyteを書き込む
        if not 0 <= value < 256:
            raise ValueError('Value must be between 0 and 255.')
        self.write(bytes([value]))

    def read_int16(self, byte_order='big'):
        # 符号付きshortを読み取る (two's complement)
        value = struct.unpack(f'{">" if byte_order == "big" else "<"}h', self.read(2))[0]
        return value
    
    def write_int16(self, value: int, byte_order='big'):
        # 符号付きshortを書き込む (two's complement)
        if not -32768 <= value < 32768:
            raise ValueError('Value must be between -32768 and 32767.')
        self.write(struct.pack(f'{">" if byte_order == "big" else "<"}h', value))

    def read_uint16(self, byte_order='big'):
        # 符号なしshortを読み取る
        if len(self._buffer) < 2:
            return None
        value = struct.unpack(f'{">" if byte_order == "big" else "<"}H', self.read(2))[0]
        return value

    def write_uint16(self, value: int, byte_order='big'):
        # 符号なしshortを書き込む
        if not 0 <= value < 65536:
            raise ValueError('Value must be between 0 and 65535.')
        self.write(struct.pack(f'{">" if byte_order == "big" else "<"}H', value))

    def read_int32(self, byte_order='big'):
        # 符号付きintを読み取る (two's complement)
        if len(self._buffer) < 4:
            return None
        value = struct.unpack(f'{">" if byte_order == "big" else "<"}i', self.read(4))[0]
        return value

    def write_int32(self, value: int, byte_order='big'):
        # 符号付きintを書き込む (two's complement)
        if not -2147483648 <= value < 2147483648:
            raise ValueError('Value must be between -2147483648 and 2147483647.')
        self.write(struct.pack(f'{">" if byte_order == "big" else "<"}i', value))

    def read_int64(self, byte_order='big'):
        # 符号付きlongを読み取る (two's complement)
        if len(self._buffer) < 8:
            return None
        value = struct.unpack(f'{">" if byte_order == "big" else "<"}q', self.read(8))[0]
        return value

    def write_int64(self, value: int, byte_order='big'):
        # 符号付きlongを書き込む (two's complement)
        if not -9223372036854775808 <= value < 9223372036854775808:
            raise ValueError("Value must be between -9223372036854775808 and 9223372036854775807.")
        self.write(struct.pack(f'{">" if byte_order == "big" else "<"}q', value))

    def read_float(self, byte_order='big'):
        # floatを読み取る (IEEE 754)
        if len(self._buffer) < 4:
            return None
        value = struct.unpack(f'{">" if byte_order == "big" else "<"}f', self.read(4))[0]
        return value

    def write_float(self, value: float, byte_order='big'):
        # floatを書き込む (IEEE 754)
        self.write(struct.pack(f'{">" if byte_order == "big" else "<"}f', value))

    def read_double(self, byte_order='big'):
        # doubleを読み取る (IEEE 754)
        if len(self._buffer) < 8:
            return None
        value = struct.unpack(f'{">" if byte_order == "big" else "<"}d', self.read(8))[0]
        return value

    def write_double(self, value: float, byte_order='big'):
        # doubleを書き込む (IEEE 754)
        self.write(struct.pack(f'{">" if byte_order == "big" else "<"}d', value))

    def read_utf8_string(self, n: int=32767) -> str:
        # UTF-8文字列を読み取る
        if n > 32767:
            raise ValueError('Maximum n value is 32767.')

        byte_length = self.read_varint()
        if byte_length < 1 or byte_length > (n * 3) + 3:
            raise ValueError(f'Invalid encoded string size: {byte_length}. Must be between 1 and {(n * 3) + 3} bytes.')

        utf8_bytes = self.read(byte_length)
        string = utf8_bytes.decode('utf-8')

        # Validate the number of UTF-16 code units in the decoded string
        utf16_code_units = sum(1 + (ord(ch) > 0xFFFF) for ch in string)
        if utf16_code_units > n:
            raise ValueError(f'Decoded string exceeds maximum of {n} UTF-16 code units.')

        return string
    
    def write_utf8_string(self, string: str, n: int=32767):
        if n > 32767:
            raise ValueError('Maximum length is 32767')
        
        utf16_code_units = sum(1 + (ord(ch) > 0xFFFF) for ch in string)
        if utf16_code_units > n:
            raise ValueError(f"String exceeds maximum of {n} UTF-16 code units.")

        utf8_bytes = string.encode('utf-8')
        byte_length = len(utf8_bytes)

        if byte_length > n * 3:
            raise ValueError(f"Encoded UTF-8 string exceeds {n * 3} bytes.")

        self.write_varint(byte_length)
        self.write(utf8_bytes)


    def read_varint(self):
        # 可変長整数を読み取る
        value = 0
        position = 0

        while True:
            current_byte = self.read_uint8()
            value |= (current_byte & 0x7F) << position
            if (current_byte & 0x80) == 0:
                break
            position += 7
            if position >= 32:
                raise ValueError('Varint is too long')
        return value
    
    def write_varint(self, value: int):
        while True:
            if value & ~0x7F == 0:
                self.write_uint8(value)
                return
            self.write_uint8((value & 0x7F) | 0x80) 
            value >>= 7

    def read_uuid(self, byte_order='big') -> uuid.UUID:
        # UUIDを読み取る
        uuid_bytes = self.read(16)
        return uuid.UUID(bytes=uuid_bytes) if byte_order == 'big' else uuid.UUID(bytes_le=uuid_bytes)
    
    def write_uuid(self, uuid_value: uuid.UUID, byte_order='big'):
        # UUIDを書き込む
        if not isinstance(uuid_value, uuid.UUID):
            raise TypeError('Value must be a UUID instance.')
        self.write(uuid_value.bytes if byte_order == 'big' else uuid_value.bytes_le)

class PacketWrapper(ABC):
    def __init__(self, client_socket, byte_order='big'):
        self._client_socket = client_socket
        self._byte_order = byte_order
        self._input_buffer = bytearray()
        self._output_buffer = None

    @abstractmethod
    def read_packet(self):
        pass

    @abstractmethod
    def write_packet(self, packet):
        pass
    
    def recv_to_buffer(self, decryptor):
        # この時点でクライアントソケットにデータが存在していることを前提とする
        data = self._client_socket.recv(4096)
        if data == b'':
            return -1  # ソケットが閉じられた場合は-1を返す
        if decryptor:
            # データを復号化する
            data = decryptor.update(data)
        self._input_buffer.extend(data)
        return 0
    
    def clear_input_buffer(self):
        # 入力バッファをクリアする
        del self._input_buffer[:]
    
    def flush(self, encryptor):
        if self._output_buffer is None:
            raise ValueError("Output buffer is not initialized.")
        packet_content = self._output_buffer.get_value()
        if packet_content == b'':
            return
        if encryptor:
            # データを暗号化する
            packet_content = encryptor.update(packet_content)
        self._output_buffer.clear()
        self._client_socket.send(packet_content)

    def fileno(self):
        return self._client_socket.fileno()
    
    def close(self):
        self._client_socket.close()


class JEPacketWrapper(PacketWrapper):
    def __init__(self, client_socket, byte_order='big'):
        super().__init__(client_socket, byte_order)
        self._output_buffer = JEPacketBuffer()

    def read_packet(self, con_state):
        # 最低パケットサイズに満たない場合はNoneを返す
        if len(self._input_buffer) < 1:
            return None
        packet_buffer = JEPacketBuffer(self._input_buffer, read_only=True)
        length = packet_buffer.read_varint() # パケット長を取得
        expected_length = packet_buffer._position + length
        # バッファの長さを確認
        if expected_length > len(self._input_buffer):
            return None
        # input_bufferからパケット長に応じたデータを削除 (データ同期)
        del self._input_buffer[:expected_length]
        if con_state.compression_threshold < 0:
            ### 圧縮プロトコル無効 ###
            packet_payload = packet_buffer.read(length) # パケットのペイロードを取得 (パケットID + データ)
            # パケットクラスに渡すバッファを再構築
            packet_buffer = JEPacketBuffer(packet_payload, read_only=True)
        else:
            ### 圧縮プロトコル有効 ###
            packet_buffer.mark() # マーク位置を設定 (packet_length=パケット全体の長さ=サイズ+パケットID+データの為)
            data_length = packet_buffer.read_varint() # パケットの長さを取得 (非圧縮の場合は0)
            packet_buffer.rewind() # マーク位置に戻る
            payload_buffer = packet_buffer.read(length) # パケット全体を取得 (サイズ+パケットID+データ)
            # バッファを再構築 + ポインタ調整
            packet_buffer = JEPacketBuffer(payload_buffer, read_only=True)
            packet_buffer.read_varint() # サイズ(data_length)を読み飛ばす
            if data_length > 0: # 非圧縮(data_length == 0)の場合は解凍しない
                # 圧縮されたデータを読み取る
                compressed_data = packet_buffer.remaining_bytes()
                # 圧縮されたデータを解凍してパケットデータを取得
                uncompressed_data = zlib.decompress(compressed_data)
                # 解凍されたデータをパケットバッファとして再構築
                packet_buffer = JEPacketBuffer(uncompressed_data, read_only=True)
        packet_id = packet_buffer.read_varint() # パケットIDを取得
        ServerboundPacket = jepacket_class_registry.get((con_state.get_state(), packet_id)) # 接続ステート+パケットIDを参照にパケットクラスを取得
        if not ServerboundPacket:
            # サーバーが無効なパケットを受信した場合はプロトコルエラー
            raise ValueError(f'Invalid packet: {(con_state.get_state(), packet_id)}')
        return ServerboundPacket.from_bytes(packet_buffer) # パケットクラスのインスタンスを生成して返却

    def write_packet(self, client_bound_packet, con_state):
        # パケットクラスからバッファを取得 (パケットID + データ)
        packet_buffer = client_bound_packet.to_bytes(con_state) 
        packet_buffer.flip()
        packet_buffer.write_varint(client_bound_packet.packet_id) # パケットIDを書き込む
        # 圧縮プロトコルのしきい値を取得
        compression_threshold = con_state.compression_threshold
        if compression_threshold >= 0: # 圧縮プロトコルが有効な場合
            if packet_buffer.size() >= compression_threshold: # パケットがしきい値を超える場合は圧縮する
                # 非圧縮のパケット長を取得
                uncompressed_length = packet_buffer.size() 
                # zlibで圧縮する
                compressed = zlib.compress(packet_buffer.get_value())
                # 圧縮されたデータでバッファを再構築
                packet_buffer = JEPacketBuffer(compressed) 
                # 圧縮前のパケット長を先頭に書き込む
                packet_buffer.flip()
                packet_buffer.write_varint(uncompressed_length) 
            else: 
                # 圧縮しない場合はパケット長を0に設定 
                packet_buffer.flip()
                packet_buffer.write_varint(0) 
        # パケット全体の長さを取得
        length = packet_buffer.size() 
        # パケットデータを書き込む
        self._output_buffer.write_varint(length)
        self._output_buffer.write(packet_buffer.get_value()) 
