import logging
import uuid


class Logger:
    def __init__(self, logger_name, *args, auto_trace_id=False, **kwargs):
        if auto_trace_id == True:
            args = list(args)
            args.append(uuid.uuid4().hex)

        self.log = logging.getLogger(logger_name)
        self._args = [str(x) for x in args]
        self._fields = kwargs

    def render_fields(self, msg):
        return '|'.join(self._args) + '|'+msg+'|'+'|'.join(['{}={}'.format(k, v) for k, v in self._fields.items()])

    def info(self, fmt: str, *args, **kwargs):
        data = fmt.format(*args, **kwargs)
        self.log.info(self.render_fields(data))

    def warning(self, fmt: str, *args, **kwargs):
        data = fmt.format(*args, **kwargs)
        self.log.warning(self.render_fields(data))

    def error(self, fmt: str, *args, **kwargs):
        data = fmt.format(*args, **kwargs)
        self.log.error(self.render_fields(data))

    def exception(self, fmt: str, *args, **kwargs):
        data = fmt.format(*args, **kwargs)
        self.log.exception(self.render_fields(data))

    def critical(self, fmt: str, *args, **kwargs):
        data = fmt.format(*args, **kwargs)
        self.log.critical(self.render_fields(data))

    def with_field(self, key, val):
        obj = self.__class__(self.log.name, *self._args, **self._fields.copy())
        obj._fields[key] = val
        return obj

    def with_fields(self, fields):
        obj = self.__class__(self.log.name, *self._args, **self._fields.copy())
        obj._fields.update(**fields)
        return obj

    def get_trace_id(self):
        if len(self._args) > 0:
            return self._args[-1]
