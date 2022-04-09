import asyncio as aio
import bencodepy
import logging
import socket
import struct
import threading
import time
from asyncio.transports import DatagramTransport
from functools import reduce
from hashlib import md5
from typing import Iterable, Sequence

from common.utils import serializer, ip_address
from .constants import ONE_WEEK, dht_bootstrap_address, DEFAULT_KRPC_CONFIG
from .node import Node, NodeInfo, DHT

"""
    refer: http://bittorrent.org/beps/bep_0005.html
"""


class QueryType:
    PING = 'ping'
    FIND_NODE = 'find_node'
    GET_PEERS = 'get_peers'
    ANNOUNCE_PEER = 'announce_peer'

    @classmethod
    def get_query_class(cls, name: str):
        return getattr(cls, name.upper() + "_CLASS", None)

    @classmethod
    def get_response_class_by_request(cls, req):
        return cls.get_response_class(getattr(req, '__query_type'))

    @classmethod
    def get_response_class(cls, name: str):
        return getattr(cls, name.upper() + '_RESP_CLASS', None)

    @classmethod
    def register_query(cls, name: str):
        def decorator(target):
            setattr(cls, name.upper()+'_CLASS', target)
            setattr(target, '__query_type', name)
            return target
        return decorator

    @classmethod
    def register_response(cls, name: str):
        def decorator(target):
            setattr(cls, name.upper()+'_RESP_CLASS', target)
            return target
        return decorator


class CommonMessage(serializer.Serializer):
    __query_type = ''
    __transaction_id = 52000
    transaction_id = serializer.BytesField(field_name='t', default=b'')
    request_type = serializer.CharField(field_name='y', choices='q r e'.split(), encode='ascii')
    version = serializer.BytesField(field_name='v', null=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.transaction_id == b'':
            self.transaction_id = self.__get_transaction_id()

    @classmethod
    def __get_transaction_id(cls):
        cls.__transaction_id += 1
        if cls.__transaction_id >= 65536:
            cls.transaction_id = 0
        return struct.pack('H', cls.__transaction_id)

    @classmethod
    def get_query_type(cls):
        query_type = getattr(cls, '__query_type', None)
        return query_type


class Request(CommonMessage):
    raw: dict   # using parse_request
    query = serializer.CharField(field_name='q', encode='ascii')
    arguments = serializer.DictField(field_name='a')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request_type = 'q'

    def validate(self):
        id = self.arguments.get(b'id') or self.arguments.get('id')
        if id is None:
            raise ValueError(f'{self.__class__.__name__} validate error: arguments.id not exists')
        if not isinstance(id, bytes) or len(id) != 20:
            raise ValueError(f'{self.__class__.__name__} validate error: arguments.id should be a 20 lengths bytes, actual: {len(id)}')
        return super().validate()

    def get_querying_id(self):
        return self.arguments[b'id']


class Response(CommonMessage):
    raw: dict   # using parse_response
    remote: (str, int)
    response = serializer.DictField(field_name='r')
    visible_addr = serializer.BytesField(field_name='ip',
                                         null=True,
                                         max_length=6,
                                         min_length=6,
                                         verbose_name='IP address which remote saw',
                                         )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request_type = 'r'

    def validate(self):
        id = self.response.get('id', None) or self.response.get(b'id', None)
        if not isinstance(id, bytes) or len(id) != 20:
            raise ValueError(f'{self.__class__.__name__} validate error: response.id={id} should be a 20 lengths bytes')
        return super().validate()

    def __repr__(self):
        return f'{self.__class__.__name__}(ip={self.visible_addr}, response={self.response}'

    def get_queried_id(self) -> bytes:
        return self.response[b'id']

    def get_queried_node(self):
        info = NodeInfo(
        )
        if self.visible_addr is not None:
            info.visible_addr = self.visible_addr
        if hasattr(self, 'remote'):
            info.addr = getattr(self, 'remote')

        n = Node(self.get_queried_id(), info=info)
        return n

    def has_visible_addr(self):
        return self.visible_addr is not None

    def get_visible_addr(self):
        return decompress_ip_port(self.visible_addr)


class ErrorResponse(CommonMessage):
    error = serializer.ListField(field_name='e')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request_type = 'e'


@QueryType.register_query(QueryType.PING)
class PingRequest(Request):
    query = serializer.CharField(field_name='q', default=QueryType.PING, encode='ascii')


@QueryType.register_response(QueryType.PING)
class PingResponse(Response):
    pass


@QueryType.register_query(QueryType.FIND_NODE)
class FindNodeRequest(Request):
    query = serializer.CharField(field_name='q', default=QueryType.FIND_NODE, encode='ascii')

    def get_target(self) -> bytes:
        return self.arguments[b'target']


@QueryType.register_response(QueryType.FIND_NODE)
class FindNodeResponse(Response):
    def get_nodes(self, fetch_detail=False):
        nodes = self.response.get(b'nodes')
        if not nodes:
            return []
        return decompress_node_info(nodes, fetch_detail=fetch_detail)


@QueryType.register_query(QueryType.GET_PEERS)
class GetPeersRequest(Request):
    query = serializer.CharField(field_name='q', default=QueryType.GET_PEERS, encode='ascii')

    def get_info_hash(self) -> bytes:
        return self.arguments[b'info_hash']


@QueryType.register_response(QueryType.GET_PEERS)
class GetPeersResponse(Response):
    def validate(self):
        # token = self.response.get('token', None)
        # if token is None:
        #     raise ValueError(f'{self.__class__.__name__} validate error: response.token is required')
        return super().validate()

    def get_token(self):
        token = self.response.get(b'token', None)
        return token

    def has_token(self):
        return b'token' in self.response

    def has_values(self):
        return b'values' in self.response

    def get_values(self):
        values = self.response.get(b'values', [])
        return decompress_ip_port(values)

    def get_nodes(self, fetch_detail=False):
        nodes = self.response.get(b'nodes')
        if not nodes:
            return []
        return decompress_node_info(self.response.get(b'nodes'), fetch_detail=fetch_detail)

    def get_queried_node(self):
        n = super().get_queried_node()
        if self.has_token():
            n.information['token'] = self.get_token()
        return n


@QueryType.register_query(QueryType.ANNOUNCE_PEER)
class AnnouncePeerRequest(Request):
    query = serializer.CharField(field_name='q', default=QueryType.ANNOUNCE_PEER, encode='ascii')

    def validate(self):
        if 'info_hash' not in self.arguments:
            raise ValueError(f'{self.__class__.__name__} validate error: arguments.info_hash is required')
        if 'port' not in self.arguments:
            raise ValueError(f'{self.__class__.__name__} validate error: arguments.port is required')
        if 'token' not in self.arguments:
            raise ValueError(f'{self.__class__.__name__} validate error: arguments.token is required')

        return super().validate()

    def get_implied_port(self) -> bool:
        return self.arguments.get(b'implied_port', 1)

    def get_info_hash(self) -> bytes:
        return self.arguments[b'info_hash']

    def get_port(self) -> int:
        return self.arguments[b'port']

    def get_token(self) -> bytes:
        return self.arguments[b'token']


@QueryType.register_response(QueryType.ANNOUNCE_PEER)
class AnnouncePeerResponse(Response):
    pass


def parse_request(data: bytes = None, obj: dict = None) -> Request:
    if obj:
        data = obj
    else:
        data = bencodepy.decode(data)
    query = data.get(b'q', b'').decode('utf8')
    if not query:
        raise ValueError(f'invalid request params: {data}')

    cls = QueryType.get_query_class(query)
    if cls is None:
        raise ValueError('request query-type:%s not found' % query)

    obj = dict()
    for key in getattr(cls, '_fields'):
        field_name = getattr(cls, key).field_name
        field_name = field_name.encode('utf8')
        if field_name in data:
            obj[key] = data[field_name]
    ret = cls(**obj)
    setattr(ret, 'raw', data)
    return ret


def parse_response(name: str, data: bytes = None, obj: dict = None):
    # parse bencode
    if obj:
        data = obj
    else:
        data = bencodepy.decode(data)

    #  get response class:
    if data[b'y'] == b'e':
        cls = ErrorResponse
    else:
        cls = QueryType.get_response_class(name)
    if cls is None:
        raise ValueError('response type:%s not found' % name)

    #   parse response
    obj = dict()
    for key in getattr(cls, '_fields'):
        field_name = getattr(cls, key).field_name
        field_name = field_name.encode('utf8')
        if field_name in data:
            obj[key] = data[field_name]
    ret = cls(**obj)
    setattr(ret, 'raw', data)

    # return
    return ret


def compact_ip_port(ip: str, port: int) -> bytes:
    try:
        fragment = [int(x) for x in ip.split('.')]
        if len(fragment) != 4:
            raise ValueError(f'ip {ip} format not valid')
    except Exception as e:
        raise ValueError(f'parse ip failed: {e}')
    data = struct.pack('BBBBH', *fragment, port)
    return data


def compact_node_info(n: bytes, ip: str, port: int) -> bytes:
    return n + compact_ip_port(ip, port)


def decompress_ip_port(values: list[bytes]) -> list[tuple[str, int]]:
    ret = []
    for value in values:
        if len(value) != 6:
            raise ValueError(f'kademlia.decompress_ip_port validation error:{value} is not the compacted ip-port data')
        args = struct.unpack('4BH', value)
        ip = '.'.join(map(lambda x: str(x), args[:4]))
        port = args[-1]
        ret.append((ip, port))
    return ret


def decompress_node_info(nodes: bytes, fetch_detail=False) -> list[Node]:
    nodes_len = len(nodes)
    if len(nodes) % 26 != 0:
        # TODO: log bad response
        return []

    # parse nodes
    ret = []
    for i in range(nodes_len // 26):
        node_info = NodeInfo()

        # parse bytes
        args = struct.unpack('20s4BH', nodes[i * 26:(i + 1) * 26])
        node_info.update({
            'id': args[0],
            'ip': '.'.join(map(lambda x: str(x), args[1:5])),
            'port': args[-1],
        })
        node_info['addr'] = (node_info.pop('ip'), node_info.pop('port'))

        # fetch ip detail info from https://ipinfo.io/, which may be too heavy
        if fetch_detail:
            node_info['ip_info'] = ip_address.IpManager.create_by_ip(node_info['ip'])
        node = Node(data=node_info['id'], info=NodeInfo(node_info))
        ret.append(node)

    return ret


class Token:
    token_seed = 'gjh4802343q'

    @classmethod
    def create(cls, addr: tuple[str, int]):
        """ generate krpc token """
        h = md5(addr[0] + cls.token_seed)
        return h.digest()

    @classmethod
    def is_valid(cls, token: bytes, addr: tuple[str, int]):
        t = cls.create(addr)
        return t == token


class KrpcProtocol(aio.DatagramProtocol):
    _krpc_session = dict()

    def __init__(
            self,
            root,
            dht: DHT,
            logger: logging.Logger,
            bootstrap_addrs: list[tuple[str, int]],
    ):
        self.logger = logger
        self.node = root
        self.dht = dht # decentralization hash table
        self.peers = dict()
        self.bootstrap_addrs = bootstrap_addrs
        self._krpc_session = dict()
        super().__init__()

    def connection_made(self, transport: DatagramTransport) -> None:
        self.logger.info(f'KrpcProtocol.connection_made|krpc listen on {self.node.base16}')
        self.transport = transport
        loop = aio.get_running_loop()
        self._krpc_session['bootstrap'] = {
            'future': loop.create_task(self.bootstrap()),
        }

    def connection_lost(self, exc) -> None:
        if not exc:
            self.logger.warning('KrpcProtocol.connection_lost|connection normal quit')
        else:
            self.logger.error('KrpcProtocol.connection_lost|error=%s', exc)
        for session_key, val in self._krpc_session.items():
            future = val['future']
            future.cancel('KrpcProtocol.connection_lost')

    def error_received(self, exc: Exception) -> None:
        self.logger.error('KrpcProtocol.error_received|error=%s', exc)
        raise exc

    def datagram_received(self, data: bytes, addr) -> None:
        #   parse message
        try:
            obj = bencodepy.decode(data)
        except Exception as e:
            self.logger.warning('KrpcProtocol.datagram_received|BencodeDecodeError|error=%s|data=%s', e, data)
            return
        t = obj[b't'].hex()
        y = obj[b'y']

        # print access log
        self.logger.info('access_log|KrpcProtocol.datagram_received|from=%s|message=%s', addr, dict(obj))

        #   handle response
        if y in [b'r', b'e']:
            if t in self._krpc_session:
                self._krpc_session[t]['future'].set_result((obj, addr))
            else:
                # handle drifting packet
                pass

        #   handle request
        elif y == b'q':
            # parse request
            req = parse_request(obj=obj)
            data = req.validate()
            # self.logger.info('access_log|KrpcProtocol.datagram_received|from={}|request={}'.format(addr, data))

            # add middleware, like logger / trace-id or etc.
            setattr(req, 'logger', self.logger)

            # handle request
            loop = aio.get_running_loop()
            if hasattr(self, req.query):
                name = 'handle_' + req.query
                handle = getattr(self, name, None)
                loop.create_task(handle(req, addr), name=name + '.' + req.transaction_id.hex())
                if req.query != QueryType.PING:
                    loop.create_task(self.try_record_requesting_node(req, addr))

            # handle not inherited query method
            else:
                self.logger.info('KrpcProtocol.datagram_received|unrecognized krpc request: %s', repr(obj))

        # handle unrecognized krpc packet
        elif y == b'echo':
            self.transport.sendto(data, addr)
        else:
            self.logger.info('KrpcProtocol.datagram_received|unrecognized krpc packet:%s', repr(obj))

    # client

    async def do_request(self, req: Request, addr, *, retry=3, timeout=0.2):
        def _timeout_handle(coro, transaction_id):
            del self._krpc_session[transaction_id]
            if not coro.done():
                coro.set_exception(aio.exceptions.TimeoutError())

        # insert coroutine to event loop
        loop = aio.get_running_loop()
        coro = loop.create_future()
        transaction_id = req.transaction_id.hex()
        self._krpc_session[transaction_id] = {
            'future': coro,
            'ctime': time.time(),
        }

        # send request
        self.transport.sendto(req.bencode(), addr)

        # set timeout
        loop.call_later(timeout, _timeout_handle, coro, transaction_id)

        # await response
        try:
            obj, received_addr = await coro
        except aio.exceptions.TimeoutError as e:
            retry -= 1
            if retry:
                return await self.do_request(req, addr, retry=retry, timeout=timeout*2)
            raise e
        except aio.CancelledError as e:
            raise e

        # parse response
        resp = parse_response(req.get_query_type(), obj=obj)

        # validate packet
        if received_addr != addr:
            raise AssertionError('KrpcProtocol.do_request|{}.{} requested addr={}, but received response from {}'.format(
                req.get_query_type(),
                transaction_id,
                addr,
                received_addr,
            ))
        if resp.transaction_id != req.transaction_id:
            raise AssertionError('KrpcProtocol.do_request|response={}|transaction id is different', resp.validate())

        # return
        setattr(resp, 'remote', addr)
        return resp

    async def batch_request(self, coro_list: Iterable) -> list[Response]:
        results = []
        loop = aio.get_running_loop()
        for task in aio.as_completed([loop.create_task(coro) for coro in coro_list]):
            try:
                resp = await task
            except aio.TimeoutError:
                pass
            else:
                results.append(resp)
        return results

    async def ping(self, addr: (str, int)) -> PingResponse:
        req = PingRequest(
            arguments=dict(id=self.node.data),
        )
        resp = await self.do_request(req, addr)
        return resp

    async def find_node(self, target: Node, addr: (str, int)) -> FindNodeResponse:
        req = FindNodeRequest(arguments=dict(
            id=self.node.data,
            target=target.data,
        ))
        return await self.do_request(req, addr)

    async def get_peers(self, info_hash: bytes, addr: (str, int)) -> GetPeersResponse:
        req = GetPeersRequest(arguments=dict(
            id=self.node.data,
            info_hash=info_hash,
        ))
        return await self.do_request(req, addr)

    async def announce_peer(self, addr: (str, int), info_hash, port, token,
                            implied_port=True) -> AnnouncePeerResponse:
        req = AnnouncePeerRequest(arguments=dict(
            id=self.node.data,
            implied_port=int(implied_port),
            info_hash=info_hash,
            port=port,
            token=token,
        ))
        return await self.do_request(req, addr)

    # request handler

    async def try_record_requesting_node(self, request: Request, addr):
        resp = await self.ping(addr)
        if not isinstance(resp, ErrorResponse):
            info = NodeInfo(addr=addr)
            if resp.visible_addr is not None:
                info.visible_addr = resp.visible_addr
            n = Node(request.get_querying_id(), info=info)
            self.dht.put(n)

    async def handle_ping(self, request: PingRequest, addr):
        # response
        resp = PingResponse(
            transaction_id=request.transaction_id,
            visible_addr=compact_ip_port(*addr),
            response=dict(id=self.node.data),
        )
        self.transport.sendto(resp.bencode(), addr)

    async def handle_find_node(self, request: FindNodeRequest, addr):
        # response
        target = Node(request.get_target())
        nodes = self.dht.get_neighbors(target, 16)
        info = reduce(
            lambda x, y: x + y,
            (compact_node_info(x.data, *x.information.addr) for x in nodes if x.information.addr is not None),
        )
        resp = FindNodeResponse(
            transaction_id=request.transaction_id,
            visible_addr=compact_ip_port(*addr),
            response=dict(
                id=self.node.data,
                nodes=info,
            )
        )
        self.transport.sendto(resp.bencode(), addr)

    async def handle_get_peers(self, request: GetPeersRequest, addr):
        # response
        info_hash = request.get_info_hash()
        token = Token.create(addr)
        if info_hash in self.peers:
            peers = self.peers.setdefault(info_hash, [])
            now = time.time()
            peers = [x[0] for x in peers if x[1] + ONE_WEEK > now],
            self.peers[info_hash] = peers
            args = dict(
                id=self.node.data,
                token=token,
                values=peers,
            )
        else:
            nodes = self.dht.get_neighbors(Node(info_hash), 16)
            info = reduce(
                lambda x, y: x + y,
                (compact_node_info(x.data, *x.information.addr) for x in nodes if x.information.addr is not None),
            )
            args = dict(
                id=self.node.data,
                nodes=info,
                token=token,
            )
        resp = GetPeersResponse(
            transaction_id=request.transaction_id,
            visible_addr=compact_ip_port(*addr),
            response=args,
        )
        self.transport.sendto(resp.bencode(), addr)

    async def handle_announce_peer(self, request: AnnouncePeerRequest, addr):
        # validate
        token = request.get_token()
        if not Token.is_valid(token, addr):
            return

        # save peer
        if request.get_implied_port():
            port = addr[1]
        else:
            port = request.get_port()
        peer = compact_ip_port(addr[0], port)
        self.peers.setdefault(request.get_info_hash(), []).append((peer, time.time()))

        # return response
        resp = AnnouncePeerResponse(
            transaction_id=request.transaction_id,
            visible_addr=compact_ip_port(*addr),
            response=dict(id=self.node.data),
        )
        self.transport.sendto(resp.bencode(), addr)

    async def bootstrap_by_ping(self, addrs) -> Sequence[Node]:
        ret = []
        loop = aio.get_running_loop()
        for task in aio.as_completed([loop.create_task(self.ping(x)) for x in addrs]):
            try:
                resp = await task
            except aio.TimeoutError:
                pass
            else:
                info = NodeInfo(
                    addr=resp.remote,
                    visible_addr=resp.visible_addr,
                )
                ret.append(Node(data=resp.get_queried_id(), info=info))

        return ret

    async def batch_find_node(self, target: Node, addrs: []) -> tuple[set[Node], set[Node]]:
        """
        return responses responded request, nodes indicating k nearest
        """
        responses = set()
        nodes = set()
        loop = aio.get_running_loop()
        for task in aio.as_completed(
                [loop.create_task(self.find_node(target, x)) for x in addrs]
        ):
            try:
                resp = await task
            except aio.TimeoutError:
                pass
            else:
                info = NodeInfo(
                    addr=resp.remote,
                    visible_addr=resp.visible_addr,
                )
                responses.add(Node(data=resp.get_queried_id(), info=info))
                nodes.update(resp.get_nodes())
        return responses, nodes

    async def bootstrap_by_find_node(self, addrs, timeout=3) -> set[Node]:
        # get booming nodes
        ret = set()
        if addrs is None:
            addrs = set()
        addrs = set(addrs)

        last_length = -1
        start_time = time.time()
        while len(ret) != last_length or time.time() - start_time < timeout:
            responses, nodes = await self.batch_find_node(self.node, addrs)
            ret |= nodes
            addrs ^= {x.information.addr for x in responses}
            addrs |= {x.information.addr for x in nodes}
            self.logger.info(
                'KrpcProtocol.bootstrap_by_find_node|querying_nodes=%d|found_counts=%d|differential=%d',
                len(addrs),
                len(ret),
                len(ret) - last_length,
            )
            last_length = len(ret)

        self.logger.info('KrpcProtocol.bootstrap_by_find_node|results={}'.format([dict(x.information) for x in ret]))
        return ret

    async def bootstrap_by_get_peers(self, info_hash: bytes, addrs, timeout: int = 10) -> tuple[set[Node], set]:
        addrs = set(addrs)
        nodes = set()
        peers = set()
        start_time = time.time()
        while len(addrs) > 0 and len(peers) == 0 and time.time() - start_time < timeout:
            results = await self.batch_request((self.get_peers(info_hash, x) for x in addrs))
            ns, vals = set(), set()
            for resp in results:
                ns = resp.get_nodes()
                vals = resp.get_values()
                addrs.remove(resp.remote)
            addrs |= {x.information.addr for x in ns}
            nodes |= set(ns)
            peers |= set(vals)
            self.logger.info(
                'KrpcProtocol.bootstrap_by_get_peers|responded_nodes=%d|found_nodes=%d|found_peers=%d|addrs=%s',
                len(results),
                len(nodes),
                len(peers),
                addrs,
            )

        return nodes, peers

    async def bootstrap(self):
        addrs = set(self.bootstrap_addrs)
        try:
            while True:
                nodes = await self.bootstrap_by_find_node(addrs, timeout=2)
                if len(nodes):
                    addrs |= nodes
                await aio.sleep(10)
        except Exception as e:
            self.logger.error('KrpcProtocol.bootstrap|error while bootstrap|error=%s', e)


# sync apis


class Krpc:
    loop: aio.AbstractEventLoop
    logger: logging.Logger
    dht: DHT
    thread: threading.Thread
    root: Node
    address: tuple[str, int]
    sock: socket.socket
    core: KrpcProtocol
    protocol_class = KrpcProtocol
    bootstrap_addrs = dht_bootstrap_address

    def __init__(
            self, root=None, loop=None, max_kbucket_length=16, address=None, logger=None,
            protocol_class=None, bootstrap_addrs=None,
    ):
        # set default value
        if not root:
            root = DEFAULT_KRPC_CONFIG['root_node'] or Node.create_random()
        if not loop:
            loop = aio.new_event_loop()
        if not protocol_class:
            protocol_class = KrpcProtocol
        if not bootstrap_addrs:
            bootstrap_addrs = []
        if not address:
            address = DEFAULT_KRPC_CONFIG['address']
        if not logger:
            logger = logging.getLogger(DEFAULT_KRPC_CONFIG['logger'])

        self.loop = loop
        self.dht = DHT(root, max_kbucket_length)
        self.root = root
        self.address = address
        self.thread = None
        self.logger = logger
        self.protocol_class = protocol_class
        self.bootstrap_addrs.extend(bootstrap_addrs)

    def start(self):
        if self.is_running():
            raise RuntimeError('Krpc is running, do not start again')
        th = threading.Thread(target=self.run)
        th.start()
        self.thread = th

    def stop(self):
        if self.thread is None:
            raise RuntimeError('Krpc is not running, can not stop')
        self.loop.stop()
        self.thread.join()
        self.sock.close()

    def run(self):
        task = self.loop.create_task(self.loop.create_datagram_endpoint(
            self.get_protocol,
            sock=self.create_socket(),
        ))
        self.logger.warning('[Krpc.run]starting krpc server!')
        trans, self.core = self.loop.run_until_complete(task)
        self.logger.warning('[Krpc.run]started krpc server!')
        self.loop.run_forever()
        trans.close()   # close transport
        self.logger.warning('[Krpc.run]krpc server has quit!')

    def is_running(self):
        return self.thread and self.thread.is_alive()

    def create_socket(self):
        if hasattr(self, 'sock') and isinstance(self.sock, socket.socket):
            try:
                self.sock.close()
            except Exception:
                pass

        # open a new DHT_SOCK
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
        sock.bind(self.address)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, True)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1 << 14)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 1 << 14)
        self.sock = sock
        self.logger.warning('Krpc.create_socket|fileno=%d|address=%s', sock.fileno(), self.address)
        return sock

    def get_protocol_class(self):
        return self.protocol_class

    def get_protocol(self) -> KrpcProtocol:
        cls = self.get_protocol_class()
        obj = cls(
            root=self.root,
            dht=self.dht,
            logger=self.logger,
            bootstrap_addrs=self.bootstrap_addrs,
        )
        return obj


_default_krpc = None


def get_default():
    global _default_krpc

    if not _default_krpc:
        _default_krpc = Krpc()

    return _default_krpc
