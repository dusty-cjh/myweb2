import os
import hashlib
import glob
from django.db import models
from django.conf import settings


MATERIAL_ROOT = os.path.join(settings.MEDIA_ROOT, 'material')
MATERIAL_URL = os.path.join(settings.MEDIA_URL, 'material')


class Material:
    def __init__(self, filename):
        self.filename = filename
        if not self.exists:
            raise FileNotFoundError('文件{}不存在'.format(filename))

    @property
    def url(self):
        return '{}/{}/'.format(MATERIAL_URL, self.filename)

    @property
    def filepath(self):
        return os.path.join(MATERIAL_ROOT, self.filename)

    @property
    def sha3_extension(self):
        return self.filename.split('.')

    @property
    def exists(self):
        return os.path.exists(self.filepath)

    def open(self, mode='rb'):
        return open(self.filepath, mode)

    def delete(self):
        filepath = self.filepath
        if os.path.isfile(filepath):
            os.remove(filepath)

    @classmethod
    def create(cls, file, sha3=None):
        """
        创建文件
        :param file: 可读取文件
        :param sha3: 哈希值
        :return: Material对象实例
        """

        extension = file.name.split('.')[-1]

        # 文件已存在
        if sha3:
            path = os.path.join(MATERIAL_ROOT, filename := '.'.join([sha3, extension]))
            if os.path.isfile(path):
                return cls(filename)

        # 新文件

        # 计算哈希值
        tempfile = os.path.join(MATERIAL_ROOT, 'temp')
        with open(tempfile, 'wb') as fp:
            m = hashlib.sha3_512()
            for chunk in file.chunks(4096):
                m.update(chunk)
                fp.write(chunk)

        # 更新文件
        path = os.path.join(MATERIAL_ROOT, filename := '{}.{}'.format(sha3 := m.hexdigest(), extension))
        if os.path.exists(path):
            os.remove(path)
        os.rename(tempfile, path)

        # 返回实例
        return cls(filename)

    @classmethod
    def all(cls):
        return [cls(filename) for filename in os.listdir(MATERIAL_ROOT)]

    @property
    def data(self):
        """返回文件详细信息"""
        n = os.stat(os.path.join(MATERIAL_ROOT, self.filename))
        sha3, extension = self.sha3_extension
        data = {
            'url': self.url,
            'filename': self.filename,
            'sha3': sha3,
            'extension': extension,
            'size': n.st_size,
            'last_visit': n.st_atime,
            'last_modify': n.st_mtime,
            'created_time': n.st_ctime,
        }

        return data