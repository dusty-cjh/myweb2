import os
import shutil
import hashlib
from django.test import TestCase
from datetime import datetime, timedelta
from django.test import TestCase, override_settings
from django.utils import timezone
from django.contrib.auth.models import User
from django.conf import settings
from django.urls import reverse
from rest_framework.test import APITestCase, APIRequestFactory
from rest_framework import status

from .models import MATERIAL_ROOT, MATERIAL_URL


class MaterialAPITests(APITestCase):
    def setUp(self):

        # 文件
        self.TMP_ROOT = os.path.join(settings.MEDIA_ROOT, 'temp')
        if not os.path.exists(self.TMP_ROOT):
            os.makedirs(self.TMP_ROOT)

        self.file1 = os.path.join(self.TMP_ROOT, 'file1')
        with open(self.file1, 'wb') as fp:
            fp.write(b'123')

        self.file2 = os.path.join(self.TMP_ROOT, 'file2')
        with open(self.file2, 'wb') as fp:
            fp.write(b'456')

        self.file3 = os.path.join(self.TMP_ROOT, 'file3')
        with open(self.file3, 'wb') as fp:
            fp.write(b'789')

        # 用户
        self.u1 = User.objects.create_user('user1', password='123456', is_staff=True)

        # 物料
        m = hashlib.sha3_512()
        m.update(b'789')
        filename = os.path.join(MATERIAL_ROOT, '.'.join([sha3 := m.hexdigest(), 'file3']))
        with open(filename, 'wb') as fp:
            fp.write(b'789')
        self.m3 = sha3

    def tearDown(self):
        try:
            shutil.rmtree(self.TMP_ROOT)
        except PermissionError:
            pass

    def test_material_create(self):
        # login
        self.client.force_login(user=self.u1)

        #
        #
        #   上传文件

        # data
        data = {
            'file': open(self.file1),
        }

        # client
        response = self.client.post(reverse('material-list'), data)

        # check
        res = response.data
        m = hashlib.sha3_512()
        m.update(b'123')
        self.assertEqual(sha3 := m.hexdigest(), res['sha3'])
        url = res['url']

        #
        #
        # 重复上传同一文件

        # data
        data = {
            'sha3': sha3,
            'file': open(self.file1),
        }

        # client
        response = self.client.post(reverse('material-list'), data)

        # check
        res = response.data
        self.assertEqual(sha3, res['sha3'])
        self.assertEqual(url, res['url'])

        #
        #
        # 上传未知哈希值的同一文件

        # data
        data = {
            'file': open(self.file1),
        }

        # client
        response = self.client.post(reverse('material-list'), data)

        # check
        res = response.data
        self.assertEqual(sha3, res['sha3'])
        self.assertEqual(url, res['url'])

        #
        #
        #   URL正确

        # # get
        # response = self.client.get(url)
        # self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_material_list(self):
        # login
        self.client.force_login(user=self.u1)

        # client
        response = self.client.get('{}?limit=1&offset=0'.format(reverse('material-list')))

        # check
        self.assertEqual(len(response.data['results']), 1)
        for file in response.data['results']:
            sha3 = file['sha3']
            url = file['url']
            self.assertEqual(os.path.basename(os.path.dirname(url)).split('.')[0], sha3)

    def test_material_retrieve(self):
        # login
        self.client.force_login(user=self.u1)

        # get
        filename = '{}.file3'.format(self.m3)
        response = self.client.get(reverse('material-list') + filename + '/', format='json')

        # check
        data = response.data
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(data['filename'], filename)
        self.assertEqual(data['size'], 3)
        pass

    def test_material_destory(self):
        # login
        self.client.force_login(user=self.u1)

        # get
        response = self.client.delete(reverse('material-list') + '{}.file3/'.format(self.m3), format='json')

        # check
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(os.path.exists(os.path.join(MATERIAL_ROOT, '{}.file3'.format(self.m3))))
        pass

