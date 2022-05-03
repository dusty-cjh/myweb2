
class ErrCode:
    UNKNOWN = -1
    SUCCESS = 0
    DHT_SOCK_CLOSED = 1
    TIMEOUT = 2
    KRPC_SERVER_NOT_START = 3
    BIT_TORRENT_SERVER_NOT_START = 4
    SERVER_NOT_START = 5
    SERVER_ERROR = 10


ErrMsg = {
    ErrCode.SUCCESS: 'success',
    ErrCode.UNKNOWN: 'unknown error',
    ErrCode.SERVER_ERROR: 'server error',
    ErrCode.DHT_SOCK_CLOSED: 'dht socket was closed',
    ErrCode.BIT_TORRENT_SERVER_NOT_START: 'bit torrent server not start',
    ErrCode.SERVER_NOT_START: 'server not start',
    ErrCode.TIMEOUT: 'timeout',
    ErrCode.KRPC_SERVER_NOT_START: 'krpc server not start',
}
