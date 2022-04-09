import json, socket
import bencodepy

import pytest
import numpy as np
from . import constants, krpc
from .node import Node, distance, DHT
from . import krpc

_0001 = Node(b'\x01')
_0010 = Node(b'\x02')
_0011 = Node(b'\x03')
_0100 = Node(b'\x04')
_0101 = Node(b'\x05')
_0110 = Node(b'\x06')
_0111 = Node(b'\x07')
_1000 = Node(b'\x08')
_1001 = Node(b'\x09')
_1010 = Node(b'\x0a')
_1011 = Node(b'\x0b')
_1100 = Node(b'\x0c')
_1101 = Node(b'\x0d')
_1110 = Node(b'\x0e')
_1111 = Node(b'\x0f')
dht = DHT(_0100)
dht.puts([
    _0001, _0010, _0101, _1010, _1111, _0011,
])


class TestNode:
    def test_exception(self):
        n1, n2 = Node.create_random(), Node.create_random(3)
        with pytest.raises(AssertionError):
            var = n1 == n2
        with pytest.raises(AssertionError):
            distance(n1, n2)
        with pytest.raises(AssertionError):
            DHT(n1).put(n2)

    @pytest.mark.parametrize('node,expected', [
        (_0100, (r"Node(b'\x04')", '00000100', b'04')),
        (_1111, (r"Node(b'\x0f')", '00001111', b'0f')),
        (_1011, (r"Node(b'\x0b')", '00001011', b'0b'))
    ])
    def test_print(self, node, expected):
        assert node.created_info() == expected[0]
        assert node.base2 == expected[1]
        assert node.base16 == expected[2]

    @pytest.mark.parametrize('binary_string,expected', [
        ('01000100',) * 2,
        (b'0110010101100101', '0110010101100101'),
        ('011101000101011101000101',) * 2,
        ('01110110100101101111101010110101',) * 2,
    ])
    def test_from_binary_string(self, binary_string: str, expected):
        n = Node.from_binary_string(binary_string)
        assert n.base2 == expected


@pytest.mark.parametrize('a,b,expected', [
    (_0100, _1111, _1011),
    (_0100, _1010, _1110),
    (_0100, _1111, _1011),
    (_1010, _0101, _1111),
    (_0100, _1111, _1011),
])
def test_distance(a, b, expected):
    assert distance(a, b) == expected


class TestDistributedHashTable:
    @pytest.mark.parametrize('node,neighbor,expected', [
        (_0100, _1111, 3),
        (_0100, _1110, 3),
        (_0100, _1101, 3),
        (_0100, _1100, 3),
        (_0100, _1011, 3),
        (_0100, _1010, 3),
        (_0100, _1001, 3),
        (_0100, _1000, 3),
        (_0100, _0011, 2),
        (_0100, _0010, 2),
        (_0100, _0001, 2),
        (_0100, _0110, 1),
        (_0100, _0111, 1),
        (_0100, _0101, 0),

        (_1010, _1011, 0),
        (_1010, _1000, 1),
        (_1010, _1001, 1),
        (_1010, _1100, 2),
        (_1010, _1101, 2),
        (_1010, _1110, 2),
        (_1010, _1111, 2),
        (_1010, _0001, 3),
        (_1010, _0010, 3),
        (_1010, _0011, 3),
        (_1010, _0100, 3),
        (_1010, _0101, 3),
        (_1010, _0110, 3),
        (_1010, _0111, 3),
    ])
    def test_put_node(self, node: Node, neighbor: Node, expected: int):
        # create distributed hash table
        tab = DHT(node)
        assert len(tab.buckets) == 8
        # put neighbor to table
        tab.put(neighbor)
        assert neighbor in tab.buckets[expected]

    @pytest.mark.parametrize('dht,node,expected', [
        (dht, _1011, [_1010, _1111, _0011, ])
    ])
    def test_get_neighbors(self, dht, node, expected):
        ret = dht.get_neighbors(node, nums=3)
        for i in range(len(expected)):
            assert expected[i] == ret[i]


class TestKrpc:
    @pytest.mark.parametrize('serializer,expected', [
        (krpc.FindNodeResponse(
            response={
                'id': b'\x1c\x11\xe0\x1b\xe8\xe7\x8dvZ.c3\x9f\xc9\x9af2\r\xb7T',
                'nodes': b"\xb2c\x88#3\x1b\xeb\xaf{#&MDY\x8f\\l[\n\xcf\xdf\xb3\xe3\xc7b\xce\x1d\xcd\xa1m\xd8[\x97\xa4\x8e\xec\xfb \x18\xb0a\xd1\xa793\xf4f'\xc6w\xe2xb\x19B\x07.g\x1e\x81\xb0Mn\xd0G?\xaf\x02\x15\xe7\xb9<\xa8\xc2j\x01\xc6\xc6",
            },
            visible_ip=b'w\x81a\xbc9k',
            version=b'LT\x01\x02',
        ),
         ''),
        (krpc.PingRequest(arguments=dict(id=Node.create_random().data)), ''),
    ])
    def test_serializer(self, serializer, expected):
        obj = serializer.validate()  # check whether object is serializable

    @pytest.mark.parametrize('sender,receivers,expected', [
        (Node.create_random_with_prefix(b'-WW0001-'), constants.dht_bootstrap_address, 1),
    ])
    def test_ping(self, sender, receivers, expected):
        req = krpc.PingRequest(
            arguments=dict(id=sender.data)
        )
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
        sock.bind(('0.0.0.0', 6881))
        sock.settimeout(0.3)

        success = False
        for host, port in receivers:
            resp = None
            data = req.bencode()
            print(f'{data} | ping {host}:{port}', end='\t')
            for _ in range(3):  # retry 3 times
                sock.sendto(data, (host, port))
                try:
                    resp, addr = sock.recvfrom(8192)
                except socket.timeout:
                    pass
                else:
                    resp = krpc.parse_response(resp)
                    success = True
                    break
                print('.', end='')
            print(f'\tresponse: {resp}')
        sock.close()
        assert success

    @pytest.mark.parametrize('sender,receivers,expected', [
        (Node.create_random_with_prefix(b'-WW0001-'), constants.dht_bootstrap_address, 1),
    ])
    def test_find_node(self, sender, receivers, expected):
        req = krpc.FindNodeRequest(
            arguments=dict(id=sender.data, target=sender.data)
        )
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
        sock.bind(('0.0.0.0', 6881))
        sock.settimeout(0.3)

        success = False
        for host, port in receivers:
            data = req.bencode()
            print(f'{data} | find_node {host}:{port}', end='\t')
            for _ in range(3):  # retry 3 times
                sock.sendto(data, (host, port))
                try:
                    resp, addr = sock.recvfrom(8192)
                except socket.timeout:
                    pass
                else:
                    resp = krpc.parse_response(krpc.QueryType.get_response_class_by_request(req), resp)
                    print(f'\t {addr} response: {resp}')
                    success = True
                    break
                print('.', end='')
            print()
        sock.close()
        assert success

    @pytest.mark.parametrize('raw_data,expected', [
        # (b'd1:eli201e23:A Generic Error Ocurrede1:t2:aa1:y1:ee', {"t":"aa", "y":"e", "e":[201, "A Generic Error Ocurred"]}),
        (b'd1:ad2:id20:abcdefghij0123456789e1:q4:ping1:t2:aa1:y1:qe',
         {"t": b"aa", "y": "q", "q": "ping", "a": {"id": "abcdefghij0123456789"}}),
        (b'd1:ad2:id20:abcdefghij01234567896:target20:mnopqrstuvwxyz123456e1:q9:find_node1:t2:aa1:y1:qe',
         {"t": b"aa", "y": "q", "q": "find_node",
          "a": {"id": "abcdefghij0123456789", "target": "mnopqrstuvwxyz123456"}}),
        (b'd1:ad2:id20:abcdefghij01234567899:info_hash20:mnopqrstuvwxyz123456e1:q9:get_peers1:t2:aa1:y1:qe',
         {"t": b"aa", "y": "q", "q": "get_peers",
          "a": {"id": "abcdefghij0123456789", "info_hash": "mnopqrstuvwxyz123456"}}),
        (
                b'd1:ad2:id20:abcdefghij012345678912:implied_porti1e9:info_hash20:mnopqrstuvwxyz1234564:porti6881e5:token8:aoeusnthe1:q13:announce_peer1:t2:aa1:y1:qe',
                {"t": b"aa", "y": "q", "q": "announce_peer",
                 "a": {"id": "abcdefghij0123456789", "implied_port": 1, "info_hash": "mnopqrstuvwxyz123456",
                       "port": 6881,
                       "token": "aoeusnth"}}),
        (b'd1:ad2:id20:--WW0001--\x15F\xc4\xe0\x1b\xfd\x1a65\xdee1:y1:q1:q4:ping1:t2:\x04\x00e',
         {'a': {'id': b'--WW0001--\x15F\xc4\xe0\x1b\xfd\x1a65\xde'}, 'y': 'q', 'q': 'ping', 't': b'\x04\x00'}),
        (b'd1:q4:ping1:t2:\x01\x001:ad2:id20:--WW0001--\xbe\xb3dLG\x16m\xbd\xd2\xf1e1:y1:qe',
         {'y': 'q', 'a': {'id': b'--WW0001--\x03\xfe\xcaF\xbb\x02n|#*'}, 'q': 'ping', 't': b'\x01\x00'}),
    ])
    def test_parse_request(self, raw_data, expected: dict):
        req = krpc.parse_request(raw_data)
        assert req.transaction_id == expected['t']
        assert req.request_type == expected['y']
        assert req.query == expected['q']

    # @pytest.mark.parametrize('raw_data,expected', [
    #     (b'd2:ip6:;?\xcfK?\x831:rd2:id20:\x1c\x11\xe0\x1b\xe8\xe7\x8dvZ.c3\x9f\xc9\x9af2\r\xb7Te1:t2:\x05\x001:y1:r1:v4:LT\x01\x02e',
    #      {
    #
    #      })
    # ])
    # def test_parse_response(self, raw_data, expected: dict):
    #     req = krpc.parse_response(krpc.QueryType.PING, raw_data)
    #     assert req.transaction_id == expected['t']
    #     assert req.request_type == expected['y']
    #     assert req.query == expected['q']


class TestLibTorrent:
    @pytest.mark.parametrize('input,expected', [
        ('', ''),
    ])
    def test_libtorrent(self, input, expected):
        pass


if __name__ == '__main__':
    from collections import OrderedDict
    d = {b'r': OrderedDict([(b'id', b'88888888\rKX\xe7*6\x1c\xd0f\xb4\xb5\xc1'), (b'nodes',
                                                                                  b'888888880b}\xe6\x91;\x07\x1c\x8e\xa4\r\x1e\xb2HM)\r\xa7888888880b}\xe6\x91;\x07\x1c\x8e\xa4\r\x1e\xb2HM)\r\xa7888888880b}\xe6\x91;\x07\x1c\x8e\xa4\r\x1e\xb2HM)\r\xa7888888880b}\xe6\x91;\x07\x1c\x8e\xa4\r\x1e\xb2HM)\r\xa7888888880b}\xe6\x91;\x07\x1c\x8e\xa4\r\x1e\xb2HM)\r\xa7888888880b}\xe6\x91;\x07\x1c\x8e\xa4\r\x1e\xb2HM)\r\xa7888888880b}\xe6\x91;\x07\x1c\x8e\xa4\r\x1e\xb2HM)\r\xa7888888880b}\xe6\x91;\x07\x1c\x8e\xa4\r\x1e\xb2HM)\r\xa7')]),
         b't': b"'\xcb", b'v': b'\xed\xb4\x91S', b'y': b'r'}

    print('hello')
