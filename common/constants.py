

class _errcode(int):
    def to_errmsg(self):
        return ErrMsg.get(self, 'unknown error code')


class ErrCode(int):
    UNKNOWN = _errcode(-1)
    SUCCESS = _errcode(0)
    DHT_SOCK_CLOSED = _errcode(1)
    TIMEOUT = _errcode(2)
    KRPC_SERVER_NOT_START = _errcode(3)
    BIT_TORRENT_SERVER_NOT_START = _errcode(4)
    SERVER_NOT_START = _errcode(5)
    SERVER_ERROR = _errcode(10)
    INVALID_PARAMETERS = _errcode(11)
    VALIDATION_FAILED = _errcode(12)

    @classmethod
    def to_errmsg(cls, code):
        return ErrMsg.get(code, 'unknown error code')


ErrMsg = {
    ErrCode.SUCCESS: 'success',
    ErrCode.UNKNOWN: 'unknown error',
    ErrCode.SERVER_ERROR: 'server error',
    ErrCode.DHT_SOCK_CLOSED: 'dht socket was closed',
    ErrCode.BIT_TORRENT_SERVER_NOT_START: 'bit torrent server not start',
    ErrCode.SERVER_NOT_START: 'server not start',
    ErrCode.TIMEOUT: 'timeout',
    ErrCode.KRPC_SERVER_NOT_START: 'krpc server not start',
    ErrCode.INVALID_PARAMETERS: 'invalid parameters',
    ErrCode.VALIDATION_FAILED: 'validation failed',
}

PYTHON_INTERPRETER_SHUTDOWN = (
    RuntimeError('cannot schedule new futures after shutdown'),
    RuntimeError('cannot schedule new futures after interpreter shutdown'),
)
PYTHON_INTERPRETER_SHUTDOWN = [repr(x) for x in PYTHON_INTERPRETER_SHUTDOWN]

