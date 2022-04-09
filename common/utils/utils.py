from common.constants import ErrCode, ErrMsg


def read_attr_from_dict(instance: object, data: dict):
    setattr(instance, '_data', data)
    for key, val in data.items():
        if key in instance.__class__.__dict__ and 'a' < key[0] < 'z':
            setattr(instance, key, val)


def error_response(errcode, errmsg='', status=200):
    return {
        'errcode': errcode,
        'errmsg': ErrMsg.get(errcode, ErrMsg[ErrCode.UNKNOWN]) + ('' if not errmsg else f'|{errmsg}')
    }
