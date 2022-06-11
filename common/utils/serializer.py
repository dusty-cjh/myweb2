import json, bencodepy, struct
import abc
import time
from datetime import datetime
from collections.abc import MutableSequence
from functools import wraps

import pytz


class AutoStorage:
    __counter = 0
    verbose_name = ""

    def __init__(self, field_name='', verbose_name="", null=False, default=None, django_form_field=None):
        cls = self.__class__
        name = cls.__name__
        index = cls.__counter
        self.storage_name = '_{}#{}'.format(name, index)
        self.verbose_name = verbose_name
        self.default_value = default
        self.allow_null = null
        self.field_name = field_name
        self.django_form_field = django_form_field
        cls.__counter += 1

    def __get__(self, instance, owner):
        if instance is None:
            return self
        else:
            if not hasattr(instance, self.storage_name):
                if self.default_value is not None:
                    return self.default_value
                if self.allow_null:
                    return None
            return getattr(instance, self.storage_name)

    def __set__(self, instance, value):
        setattr(instance, self.storage_name, value)


class Validated(AutoStorage):
    @abc.abstractmethod
    def validate(self, instance, value):
        """
        return validated value or raise ValueError
        """

    def __set__(self, instance, value):
        value = self.validate(instance, value)
        setattr(instance, self.storage_name, value)


class DateTimeField(AutoStorage):
    __set = False

    def __init__(self, now=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if now:
            self.now = time.time()
        else:
            self.now = 0

    def __get__(self, instance, owner):
        if instance is None:
            return self
        elif self.now and not self.__set:
            super().__set__(instance, datetime.now(tz=pytz.UTC))
        return super().__get__(instance, owner)


class _string(Validated):
    def __init__(self, max_length=None, min_length=None, choices=None, *args, **kwargs):
        self.max_length = max_length
        self.min_length = min_length
        self.choices = choices
        super().__init__(*args, **kwargs)

    def validate(self, instance, value):
        if self.min_length and len(value) < self.min_length:
            raise ValueError('min_length:{}'.format(self.min_length))
        if self.max_length and len(value) > self.max_length:
            raise ValueError('max_length:{}'.format(self.max_length))
        if self.choices is not None and value not in self.choices:
            raise ValueError('choices:{}'.format(self.choices))
        return value


class CharField(_string):
    def __init__(self, *args, encode=None, **kwargs):
        self.encode = encode
        super().__init__(*args, **kwargs)

    def validate(self, instance, value):
        if isinstance(value, bytes) and self.encode:
            value = value.decode(self.encode)
        if not isinstance(value, str):
            raise ValueError('value {} is not str'.format(value))
        return super().validate(instance, value)


class BytesField(_string):
    def validate(self, instance, value):
        if not isinstance(value, bytes):
            raise ValueError('value {} is not bytes'.format(value))
        return super().validate(instance, value)


class IntField(Validated):
    def __init__(self, max_val=None, min_val=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_val, self.min_val = max_val, min_val

    def validate(self, instance, value):
        if self.min_val is not None and len(value) < self.min_val:
            raise ValueError('min_val:{}'.format(self.min_val))
        if self.max_val is not None and len(value) > self.max_val:
            raise ValueError('max_val:{}'.format(self.max_val))
        return value


class BooleanField(Validated):
    def validate(self, instance, value):
        assert isinstance(value, bool)
        return value


class DictField(Validated):
    def validate(self, instance, value):
        if not isinstance(value, dict):
            raise TypeError(
                '%s only accepts list, but received %s' % (self.__class__.__name__, value.__class__.__name__),
            )
        return value


class ListField(Validated):
    def validate(self, instance, value):
        if not isinstance(value, list):
            raise TypeError(
                '%s only accepts list, but received %s' % (self.__class__.__name__, value.__class__.__name__),
            )
        return value


class SetField(Validated):
    def validate(self, instance, value):
        if not isinstance(value, set):
            raise TypeError(
                '%s only accepts set, but received %s' % (self.__class__.__name__, value.__class__.__name__),
            )
        return value


class SerializerMeta(type):
    fields = dict()

    def __init__(cls, name, bases, attr_dict):
        # get field names
        fields = set()
        if len(bases) > 0:
            fields |= getattr(bases[0], '_fields', [])

        super().__init__(name, bases, attr_dict)
        for key, attr in attr_dict.items():
            if isinstance(attr, AutoStorage):
                fields.add(key)
                type_name = type(attr).__name__
                attr.storage_name = '_{}#{}'.format(type_name, key)
                if not attr.verbose_name:   attr.verbose_name = key
                if not attr.field_name:     attr.field_name = key
        setattr(cls, '_fields', fields)


# ---------------------------- user interface -----------------------------
class Serializer(metaclass=SerializerMeta):
    """带有验证字段的业务实体"""

    def __init__(self, *args, **kwargs):
        # global var
        fields = getattr(self, '_fields', [])

        # assign value by kwargs
        for key in fields:
            if key in kwargs:
                setattr(self, key, kwargs.pop(key))
        if kwargs:
            raise ValueError(f'{self.__class__.__name__} unrecognized fields: {list(kwargs.keys())}')

    def validate(self):
        ret = dict()
        for key in getattr(self, '_fields'):
            if not hasattr(self, key):
                raise AssertionError('{} have not assign value for field:{}'.format(self.__class__.__name__, key))
            val = getattr(self, key)
            if val is not None:
                ret[getattr(self.__class__, key).field_name] = val
        return ret

    def bencode(self):
        obj = self.validate()
        data = bencodepy.encode(obj)
        return data

    @classmethod
    def bdecode(cls, data: bytes):
        obj = dict()
        data = bencodepy.decode(data)
        for key in getattr(cls, '_fields'):
            field_name = getattr(cls, key).field_name
            field_name = field_name.encode('utf8')
            if field_name in data:
                obj[key] = data[field_name]
        return cls(**obj)


class FrozenJson(dict):
    # base field
    errcode: int
    errmsg: str

    # wechat common field
    url: str
    media_id: str
    appid: str
    nonce_str: str
    sign: str
    mch_id: str

    # wechat pay
    return_code: str    # 'SUCCESS',
    return_msg: str
    result_code: str
    total_fee: int
    cash_fee: int
    cash_refund_fee: int
    refund_fee: int

    def __init__(self, arg=None, name='FrozenJson', ):
        if arg is None:
            arg = dict()
        for key, val in arg.items():
            arg[key] = self._wrap_element(val)

        super().__init__(arg)
        self.__name = name

    def __missing__(self, key):
        return None

    def __getattr__(self, item):
        return super().__getitem__(item)

    def __setattr__(self, key, value):
        return super().__setattr__(key, self._wrap_element(value))

    def __repr__(self):
        return '{}({})'.format(self.__name, ', '.join(['{}={}'.format(key, val) for key, val in self.items()]))

    @classmethod
    def _wrap_element(cls, obj):
        if obj.__class__ == dict:
            return cls(obj)
        elif isinstance(obj, MutableSequence):
            for i, val in enumerate(obj):
                obj[i] = cls._wrap_element(val)
            return obj
        else:
            return obj


def dict_to_namedtuple(name='dict_to_namedtuple'):
    def decorator(func):
        @wraps(func)
        def inner(*args, **kwargs):
            resp = {}
            try:
                resp = func(*args, **kwargs)
                resp['errcode'] = 0
                resp['errmsg'] = 'success'
            except Exception as e:
                resp['errcode'] = getattr(e, 'errcode', -1)
                resp['errmsg'] = repr(e)
            return FrozenJson(resp, name)
        return inner
    return decorator


def async_dict_to_namedtuple(name='dict_to_namedtuple', cls=FrozenJson):
    def decorator(func):
        @wraps(func)
        async def inner(*args, **kwargs) -> cls:
            resp = {}
            try:
                resp = await func(*args, **kwargs)
                resp['errcode'] = 0
                resp['errmsg'] = 'success'
            except Exception as e:
                resp['errcode'] = getattr(e, 'errcode', -1)
                resp['errmsg'] = repr(e)
            return cls(resp, name)
        return inner
    return decorator

