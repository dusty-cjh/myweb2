import time
from collections import abc
import codecs
import numpy as np
from collections import deque, namedtuple
from functools import lru_cache
from abc import abstractmethod, ABCMeta

from common.utils import serializer


class NodeInfo(dict):
    ctime = serializer.DateTimeField(now=True)
    addr: (str, int)
    visible_addr: (str, int)

    def __init__(self, seq=None, **kwargs):
        if seq is None:
            super().__init__(**kwargs)
        else:
            super().__init__(seq, **kwargs)

    @property
    def addr(self):
        return self.get('addr')

    @addr.setter
    def addr(self, value):
        self['addr'] = value

    @property
    def visible_addr(self):
        return self.get('visible_addr')

    @visible_addr.setter
    def visible_addr(self, value):
        self['visible_addr'] = value


class Node(metaclass=ABCMeta):
    """
    Exapmles:
    >>> a, b = Node.create_random(1), Node.create_random(1)
    >>> a
    (160 bits: b'dc398ad728ef7627cc4eaff611eb0483a85a30c7')
    >>> print(a.base2, b.base2, distance(a, b).base2)
    1101110000111001100010101101011100101000111011110111011000100111110011000100111010101111111101100001000111101011000001001000001110101000010110100011000011000111
    0001110000011001010111000101100010110010011010110011100001011000101100111101011111011000100010100011011000000111001001101101010001110011101010111101100011111010
    1100000000100000110101101000111110011010100001000100111001111111011111111001100101110111011111000010011111101100001000100101011111011011111100011110100000111101
    >>> a.base16
    b'708f97b22cc8e827a26e1211155490ba6b0a3b73'
    >>> a.base64
    b'cI+XsizI6CeibhIRFVSQumsKO3M=\n'
    >>> a.bits
    160
    """

    def __init__(self, data: bytes = None, base16=None, base64=None, ndarray: np.ndarray = None, info: NodeInfo = None):
        if base16:
            dec = codecs.getdecoder('hex')
            data, _ = dec(base16)
        elif base64:
            dec = codecs.getdecoder('base64')
            data, _ = dec(base64)
        elif ndarray is not None:
            data = ndarray.tobytes()
        elif data is None:
            raise ValueError("Node uninitialized cause no valid input")

        self.data = data

        #   init information
        if info is None:
            info = dict()
        info['id'] = self.base16
        self.information = info

    def __bytes__(self):
        return self.data

    def __repr__(self):
        data = self.base2 if self.bits <= 32 else self.base2[:32] + '...'
        return '({} bits: {})'.format(self.bits, data)

    def __eq__(self, other):
        return self.data == other.data

    def __lt__(self, other):
        return bytes(self) < bytes(other)

    def __hash__(self):
        return hash(self.data)

    @classmethod
    def create_random(cls, bytes=20):
        data = np.random.randint(0, 1 << 8, size=bytes, dtype=np.uint8)
        return cls(data.tobytes())

    @classmethod
    def create_random_with_prefix(cls, prefix: bytes, bytes=20):
        data = np.random.randint(0, 1 << 8, size=bytes - len(prefix), dtype=np.uint8)
        return cls(prefix + data.tobytes())

    @classmethod
    def from_binary_string(cls, binary_str: str):
        if len(binary_str) % 8 != 0:
            raise ValueError('length of `binary_str`, now it is {}, must be divisible with 8'.format(len(binary_str)))
        ar = []
        for i in range(0, len(binary_str), 8):
            ar.append(int(binary_str[i:i + 8], 2))
        ar = np.array(ar, dtype=np.uint8)
        return Node(ndarray=ar)

    @classmethod
    def from_array(cls, ar):
        if isinstance(ar, (list, tuple)):
            ar = np.array(ar, dtype=np.uint8)
        return Node(ndarray=ar)

    @property
    def base2(self):
        """ this mostly used when debug """
        return ''.join(['{:>08b}'.format(x) for x in self.data])

    @property
    def base16(self):
        return self.data.hex()

    @property
    def base64(self):
        enc = codecs.getencoder('base64')
        return enc(self.data)[0]

    @property
    def bits(self):
        return len(self.data) << 3

    def distance(self, node):
        return distance(self, node)

    def created_info(self):
        return 'Node({})'.format(bytes(self))

    @property
    def information(self) -> NodeInfo:
        return getattr(self, '__node_info')

    @information.setter
    def information(self, value):
        setattr(self, '__node_info', NodeInfo(value if value else dict()))

    def is_alive(self):
        return False


@lru_cache(maxsize=1 << 12)
def distance(n1: Node, n2: Node) -> Node:
    assert n1.bits == n2.bits
    return Node(bytes([x ^ y for x, y in zip(n1.data, n2.data)]))


def first_different_bit_position(n1: Node, n2: Node) -> int:
    assert n1.bits == n2.bits

    xor = 0
    for i in range(len(n1.data)):
        xor = n1.data[i] ^ n2.data[i]
        if xor:
            break
    if not xor:
        raise LookupError('kademlia.node.first_different_bit_position error: n1 and n2 is identical')

    for n in range(7, -1, -1):
        if xor & (1 << n) != 0:
            break

    return i * 8 + 7 - n


def sort(n: Node, ar: list[Node]):
    return sorted(ar, key=lambda x: distance(x, n))


def create_node(data: bytes = None, base16=None, base64=None, ndarray: np.ndarray = None):
    kwargs = locals()
    return Node(**kwargs)


class Bucket:
    @abstractmethod
    def put(self):
        pass

    @abstractmethod
    def __len__(self):
        pass


class DecentralizedHashTable:
    @abstractmethod
    def put(self, node: Node):
        pass

    @abstractmethod
    def nearby(self, node: Node, nums=8):
        pass


# ------------------------------------------------------------------------------


class NetNode(NodeInfo):
    host = serializer.CharField()
    port = serializer.IntField(min_val=0, max_val=65535)
    protocol = serializer.CharField()


class KBucket(deque):
    parent = None
    index = None
    distance_sort = []

    def __init__(self, parent, index, maxlen=None):
        super().__init__(maxlen=maxlen)
        self.parent = parent
        self.index = index

    def __repr__(self):
        data = self.parent.base_node.base2
        idx = len(data) - self.index
        data = data[:-idx] + '-' * (idx)
        return '(index={:<5d}, {}, {})'.format(self.index, data, super().__repr__())

    def sort_elements(self):
        self.distance_sort = np.argsort([distance(self.parent.base_node, x) for x in self], kind='quicksort')

    @property
    def base2(self):
        data = '-' * self.maxlen
        data[self.maxlen - 1 - self.index] = 'X'
        return data

    def put_new_node(self, node: Node):
        # check
        if node in self:
            return

        # kademlia strategy
        if len(self) == self.maxlen and not self[0].is_alive():
            self[0] = node
        else:
            self.appendleft(node)


class DHT:
    """
    Examples:
    >>> a, b, k = Node.create_random(2), Node.create_random(2), DHT(Node.create_random(2))
    >>>
    """
    buckets = []

    def __init__(self, node: Node, k=8):
        bkt = []
        for i in range(node.bits):
            bkt.append(KBucket(parent=self, index=i, maxlen=k))

        self.buckets = bkt
        self._node = node

    def __repr__(self):
        return repr(self.base_node)

    def __eq__(self, other):
        return self.base_node == other.base_node

    @property
    def base_node(self):
        if self._node is None:
            self._node = Node.create_random()
        return self._node

    @base_node.setter
    def base_node(self, node: Node):
        self._node = node

    def put(self, node: Node):
        idx = first_different_bit_position(self._node, node)
        bk = self.buckets[idx]
        bk.put_new_node(node)

    def puts(self, ar):
        for n in ar:
            self.put(n)

    def get_neighbors(self, node: Node, nums=8) -> list[Node]:
        assert self.base_node.bits == node.bits
        idx = first_different_bit_position(self.base_node, node)
        return list(self.buckets[idx])[:nums]


if __name__ == '__main__':
    k = DHT(Node.create_random(1), 16)
    for i in range(1 << 14):
        n = Node.create_random(1)
        if n != k.base_node:
            k.put(n)
    print(k)
    for b in k.buckets:
        print(b)

    for i in range(10):
        n = Node.create_random(1)
        nodes = k.get_neighbors(n)
        print('get negihbors:', '\t', n, '\t', nodes)
        time.sleep(0.2)
