import requests, json
from . import utils


class IpManager:
    _IPINFO_HOST = 'http://ipinfo.io/'
    _IPINFO_TOKEN = '0c3d02f1d561ab'

    ip, city, region, country, loc, timezone, postal, org, hostname, bogon = (None,) * 10

    def __init__(self, data: dict):
        utils.read_attr_from_dict(self, data)
        self.loc = [float(x) for x in self.loc.split(',')]

    @classmethod
    def create_by_ip(cls, ip):
        url = '{}{}'.format(cls._IPINFO_HOST, ip)
        params = {
            'token': cls._IPINFO_TOKEN,
        }
        resp = requests.get(url, params=params)
        data = resp.json()
        if 'error' in data or data.get('bogon', False) is True:
            raise ValueError(', '.join(data.values()))
        return cls(data=data)

    @classmethod
    def get_current_ip(cls):
        return cls.create_by_ip('')

    @property
    def longitude(self):
        return self.loc[0]

    @property
    def latitude(self):
        return self.loc[1]

    def __str__(self):
        return json.dumps(self._data, indent=4)

    def __repr__(self):
        return self.__str__()

