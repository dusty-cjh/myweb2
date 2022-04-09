import logging
import socket
import struct
import numpy as np
import asyncio as aio
import bencodepy
import threading
from .node import Node
from .constants import DEFAULT_BIT_TORRENT_CONFIG

"""
refer: 
    http://bittorrent.org/beps/bep_0003.html
    http://bittorrent.org/beps/bep_0009.html
    http://bittorrent.org/beps/bep_0010.html
    https://wiki.wireshark.org/BitTorrent   # useful pcap file diving into BT
    https://www.zhihu.com/people/man-san-54/posts   # tcpdump brief explain
    http://dandylife.net/docs/BitTorrent-Protocol.pdf   # pay attention when read this
    https://docs.python.org/3/library/struct.html   # pack and unpack binary stream
"""

BITTORRENT_PROTOCOL = b'\x13BitTorrent protocol'
RESERVED_BYTES = np.zeros(8, dtype=np.uint8)


def SUPPORT_EXTENDED_PROTOCOL(reserved_bytes: np.ndarray) -> np.ndarray:
    assert len(reserved_bytes) == 8
    reserved_bytes[5] |= 0x10
    return reserved_bytes


# all message were big endian
MESSAGE_CHOKE = struct.pack('>IBB', 1, 0, 0)
MESSAGE_UNCHOKE = struct.pack('>IBB', 1, 1, 0)
MESSAGE_INTERESTED = struct.pack('>IBB', 1, 2, 0)
MESSAGE_NOT_INTERESTED = struct.pack('>IBB', 1, 3, 0)


def parse_handshake(data: bytes, info_hash: bytes = None, peer_id: bytes = None):
    # validate whether the connection is bit torrent protocol
    assert data[:len(BITTORRENT_PROTOCOL)] == BITTORRENT_PROTOCOL
    data = data[len(BITTORRENT_PROTOCOL):]
    assert len(data) == 48

    # validate whether the connection match the downloading we want
    reserved_bytes, ih, pi = data[:8], data[8:28], data[28:]
    if (info_hash and info_hash != ih) or (peer_id and peer_id != pi):
        raise ValueError('bittorrent.parse_handshake|info_hash or peer_id not match')

    return reserved_bytes, ih, pi


class MessageType:
    CHOKE = 0
    UNCHOKE = 1
    INTERESTED = 2
    NOT_INTERESTED = 3
    HAVE = 4
    BITFIELD = 5
    REQUEST = 6
    PIECE = 7
    CANCEL = 8
    EXTENDED = 0x14  # bep_0010


class BitTorrentSupportedFeatures:
    reserved_bytes: np.ndarray

    def __init__(self, support_extended_protocol=True):
        self.reserved_bytes = np.zeros(8, dtype=np.uint8)

        # open options
        if support_extended_protocol:
            self.reserved_bytes[5] |= 0x10

    def merge_with(self, reserved_bytes: bytes):
        assert len(reserved_bytes) == 8
        data = np.array([int(x) for x in reserved_bytes], dtype=np.uint8)
        self.reserved_bytes &= data

    def is_support_extended_protocol(self) -> bool:
        return self.reserved_bytes[5] & 0x10


class Message:
    features: BitTorrentSupportedFeatures
    peer_id: bytes
    info_hash: bytes

    def __init__(self, peer_id: bytes, info_hash: bytes = None):
        self.features = BitTorrentSupportedFeatures()
        self.peer_id = peer_id
        self.info_hash = info_hash

    def handshake(self, info_hash: bytes = None, peer_id: bytes = None):
        if not info_hash:
            info_hash = self.info_hash
        if not peer_id:
            peer_id = self.peer_id
        assert info_hash and peer_id and len(info_hash) == 20 and len(peer_id) == 20

        data = BITTORRENT_PROTOCOL + self.features.reserved_bytes.tobytes() + info_hash + peer_id
        return data

    def parse_handshake(self, data: bytes, update_features=True):
        # validate whether the connection is bit torrent protocol
        assert data[:len(BITTORRENT_PROTOCOL)] == BITTORRENT_PROTOCOL
        data = data[len(BITTORRENT_PROTOCOL):]
        assert len(data) == 48

        # validate whether the connection match the downloading we want
        reserved_bytes, ih, pi = data[:8], data[8:28], data[28:]
        if (self.info_hash and self.info_hash != ih) or (self.peer_id and self.peer_id != pi):
            raise ValueError('bittorrent.Message.parse_handshake|info_hash or peer_id not match')

        if update_features:
            self.features.merge_with(reserved_bytes)

        return reserved_bytes, ih, pi

    def extened_handshake(self):
        msg_id = 20

# # since the existence of GIL lock, lock may have no means in python
# class BitTorrentProtocolStatus:
#     STATUS_CONNECTING = 0
#     STATUS_HANDSHAKING = 1
#     STATUS_NORMAL = 2
#     STATUS_DISCONNECTED = 3
#
#     def __init__(self):
#         self.lock = threading.RLock
#         self.status = self.STATUS_CONNECTING
#
#     def handshake(self):


class BitTorrentProtocol(aio.Protocol):
    info_hash: bytes
    peer_id: bytes
    transport: aio.Transport
    status: int
    buffer: bytes
    supported_features: BitTorrentSupportedFeatures

    STATUS_CONNECTING = 0
    STATUS_HANDSHAKING = 1
    STATUS_NORMAL = 2
    STATUS_DISCONNECTED = 3
    STATUS = {
        STATUS_CONNECTING: 'connecting',
        STATUS_HANDSHAKING: 'handshaking',
        STATUS_NORMAL: 'normal',
        STATUS_DISCONNECTED: 'disconnected',
    }

    def __init__(
            self,
            peer_id: bytes,
            loop: aio.AbstractEventLoop,
            logger: logging.Logger,
            info_hash: bytes = None,
            supported_features: BitTorrentSupportedFeatures = None,
    ):
        #   validate arguments and assign default value
        if info_hash:
            assert len(info_hash) == 20
        assert len(peer_id) == 20
        if not supported_features:
            supported_features = BitTorrentSupportedFeatures()

        self.info_hash = info_hash
        self.peer_id = peer_id
        self.logger = logger
        self.status = self.STATUS_CONNECTING
        self.buffer = b''
        self.loop = loop
        self.message = Message(self.peer_id, self.info_hash)

    def connection_made(self, transport: aio.Transport):
        self.transport = transport
        self.logger.info('BitTorrentProtocol.connection_made|tcp connection has built')

    def connection_lost(self, exc: Exception) -> None:
        self.status = self.STATUS_DISCONNECTED
        pass

    def data_received(self, data: bytes):
        # parse handshake message
        if self.status == self.STATUS_CONNECTING:
            try:
                _, self.info_hash, _ = self.message.parse_handshake(data)
            except Exception as e:
                self.logger.warning(
                    f'{self.__class__.__name__}.data_received|error while parse handshake message|error=%s',
                    e,
                )
                return self.disconnect()
            self.transport.write(self.message.handshake(self.info_hash))
            self.status = self.STATUS_NORMAL

        # parse handshake message
        elif self.status == self.STATUS_HANDSHAKING:
            # should never be used in server side
            return self.disconnect()

        # parse normal message
        elif self.status == self.STATUS_NORMAL:
            data_length, msg_identifier = struct.unpack('>IB', data[:5])
            print(data_length, msg_identifier)

        elif self.status == self.STATUS_DISCONNECTED:
            # do nothing
            return self.disconnect()

    def disconnect(self):
        self.status = self.STATUS_DISCONNECTED
        self.transport.close()


class BitTorrent:
    loop: aio.AbstractEventLoop
    logger: logging.Logger
    thread: threading.Thread
    peer_id: Node
    address: tuple[str, int]
    sock: socket.socket
    core: BitTorrentProtocol
    protocol_class = BitTorrentProtocol
    is_client: bool
    info_hash: bytes
    transport: aio.Transport

    def __init__(
            self, peer_id=None, loop=None, address=None, logger=None, protocol_class=None, is_client=True,
            info_hash=None
    ):
        # set default value
        if not peer_id:
            peer_id = DEFAULT_BIT_TORRENT_CONFIG['root_node'] or Node.create_random()
        if not loop:
            loop = aio.new_event_loop()
        if not protocol_class:
            protocol_class = BitTorrentProtocol
        if not address and not is_client:
            address = DEFAULT_BIT_TORRENT_CONFIG['address']
        if is_client:
            assert address is not None, f'{self.__class__.__name__}|client address should not be none'
            assert info_hash is not None, f'{self.__class__.__name__}|client info_hash should not be none'
        if not logger:
            logger = logging.getLogger(DEFAULT_BIT_TORRENT_CONFIG['logger'])
        if info_hash:
            assert len(info_hash) == 20, f'{self.__class__.__name__}|length of info_hash is restricted to 20'

        self.loop = loop
        self.peer_id = peer_id
        self.address = address
        self.thread = None
        self.logger = logger
        self.protocol_class = protocol_class
        self.is_client = is_client
        self.info_hash = info_hash
        self.task = None
        self.transport = None

    def start(self):
        if self.is_running():
            raise RuntimeError(f'{self.__class__.__name__}.{self.peer_id.data.hex()} is running, do not start again')
        th = threading.Thread(target=self.run)
        th.start()
        self.thread = th

    def stop(self):
        if self.thread is None:
            raise RuntimeError(f'{self.__class__.__name__}.{self.peer_id.data} is not running, can not stop')
        self.transport.close()
        self.loop.stop()
        print('join')
        self.thread.join()
        print('joined')
        self.sock.close()

    def run(self):
        if self.is_client:
            task = self.loop.create_task(self.loop.create_connection(
                self.get_protocol,
                sock=self.create_socket(),
            ))
        else:
            task = self.loop.create_task(self.loop.create_server(
                self.get_protocol,
                sock=self.create_socket(),
            ))
        self.task = task

        name = 'client' if self.is_client else 'server'
        self.logger.warning(f'[{self.__class__.__name__}.run]starting bt {name}! peer_id={self.peer_id.data.hex()}')
        if self.is_client:
            self.transport, self.core = self.loop.run_until_complete(task)
        else:
            self.core = self.loop.run_until_complete(task)
        self.logger.warning(f'[{self.__class__.__name__}.run]started bt {name}! peer_id={self.peer_id.data.hex()}')
        self.loop.run_forever()
        if self.is_client:
            self.close()   # close transport
        self.logger.warning(f'[{self.__class__.__name__}.run]bt {name} has quit! peer_id={self.peer_id.data.hex()}')

    def is_running(self):
        return self.thread and self.thread.is_alive()

    def create_socket(self):
        if hasattr(self, 'sock') and isinstance(self.sock, socket.socket):
            try:
                self.sock.close()
            except Exception:
                pass

        # open a new socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, True)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1 << 14)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 1 << 14)
        if self.is_client:
            sock.connect(self.address)
        else:
            sock.bind(self.address)
        self.sock = sock
        self.logger.warning(f'{self.__class__.__name__}.create_socket|fileno={sock.fileno()}|address={self.address}')
        return sock

    def get_protocol_class(self):
        return self.protocol_class

    def get_protocol(self) -> BitTorrentProtocol:
        cls = self.get_protocol_class()
        obj = cls(
            peer_id=self.peer_id.data,
            loop=self.loop,
            logger=self.logger,
            info_hash=self.info_hash,
        )
        return obj


async def handshake_with_remote(peer_id):
    info_hash = Node.create_random().data
    host, port = ('127.0.0.1', 6882)
    r, w = await aio.open_connection(host, port)
    msg_manager = Message(peer_id, info_hash)
    data = msg_manager.handshake()
    w.write(data)
    msg_manager.parse_handshake(await r.read(len(data)))
    w.close()

_default_bt = None


def get_default():
    global _default_bt

    if not _default_bt:
        _default_bt = BitTorrent(is_client=False)

    return _default_bt
