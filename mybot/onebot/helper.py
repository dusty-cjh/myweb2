

_status_to_errmsg = {
    200: '',
    401: 'onebot access_token not provided',
    403: 'onebot access_token not matched',
    406: 'onebot content-type not allowed',
    400: 'onebot content-type invalid',
    404: 'onebot api not found',
}


def get_errmsg_from_status(status: int) -> str:
    return _status_to_errmsg.get(status, 'onebot unexpected status: %d' % status)
