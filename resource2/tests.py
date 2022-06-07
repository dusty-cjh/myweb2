import os
import time
import shutil
import hashlib
from django.conf import settings
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework.test import APITestCase

from .models import Resource, Material


class ResourceAPITests(APITestCase):
    def setUp(self):

        # 文件
        self.TMP_ROOT = os.path.join(settings.MEDIA_ROOT, 'temp')
        if not os.path.exists(self.TMP_ROOT):
            os.makedirs(self.TMP_ROOT)

        self.file1 = os.path.join(self.TMP_ROOT, 'file1')
        with open(self.file1, 'wb') as fp:
            fp.write(b'123' * 4096)

        self.file2 = os.path.join(self.TMP_ROOT, 'file2')
        with open(self.file2, 'wb') as fp:
            fp.write(b'456' * 1568)

        self.file3 = os.path.join(self.TMP_ROOT, 'file3')
        with open(self.file3, 'wb') as fp:
            fp.write(b'789' * 7775)

        # 用户
        self.u1 = User.objects.create_user('user1', password='123456', is_staff=True)
        self.u2 = User.objects.create_user('user2', password='789012', is_staff=True)

    def tearDown(self):
        try:
            shutil.rmtree(self.TMP_ROOT)
        except PermissionError:
            pass

    def test_create_without_hash_value(self):
        # login
        self.client.force_login(user=self.u1)

        #
        #
        #   上传文件

        # data
        data = {
            'stream': open(self.file1),
            'link_type': Resource.LINK_TYPE_FILE,
        }

        # client
        response = self.client.post(reverse('resource-list'), data)

        # check
        res = response.data
        m = hashlib.sha256(open(self.file1, 'rb').read(2**30))
        self.assertEqual(sha3 := m.hexdigest(), res['hash_val'])

    def test_create_with_hash_value(self):
        self.client.force_login(self.u1)
        hash = hashlib.sha256(open(self.file1, 'rb').read(2**30)).hexdigest()
        data = {
            'stream': open(self.file1),
            'link_type': Resource.LINK_TYPE_FILE,
            'hash_val': hash,
            'hash_type': 'sha256',
        }
        response = self.client.post(reverse('resource-list'), data)

        res = response.data
        self.assertEqual(hash, res['hash_val'])

    def test_create_twice(self):
        data = {
            'stream': open(self.file1),
            'link_type': Resource.LINK_TYPE_FILE,
            'hash_val': hashlib.sha256(open(self.file1, 'rb').read(2**30)).hexdigest(),
            'hash_type': 'sha256',
        }

        # user 1 uploaded
        self.client.force_login(self.u1)
        response = self.client.post(reverse('resource-list'), data)
        self.client.logout()
        res1 = response.data

        # user 2 uploaded
        self.client.force_login(self.u2)
        data['stream'] = open(self.file1)
        response = self.client.post(reverse('resource-list'), data)
        self.client.logout()
        res2 = response.data

        # check
        self.assertDictEqual(res1, res2, '多次上传相同资源时必须返回相同的资源数据')

    def test_list(self):
        uri = reverse('resource-list')
        # file1
        self.client.force_login(self.u1)
        self.client.post(uri, dict(stream=open(self.file1), link_type=Resource.LINK_TYPE_FILE))
        self.client.logout()
        # file2
        self.client.force_login(self.u2)
        self.client.post(uri, dict(stream=open(self.file2), link_type=Resource.LINK_TYPE_FILE))
        self.client.logout()
        # file3
        self.client.force_login(self.u1)
        self.client.post(uri, dict(stream=open(self.file3), link_type=Resource.LINK_TYPE_FILE))
        self.client.logout()
        # verify all files
        self.client.force_login(self.u2)
        Resource.objects.all().update(status=Resource.STATUS_NORMAL)

        # request
        response = self.client.get(uri)
        self.assertEqual(response.data['count'], 3)
        data = response.data['results']

    def test_retrieve(self):
        uri = reverse('resource-list')
        # file1
        self.client.force_login(self.u1)
        self.client.post(uri, dict(stream=open(self.file1), link_type=Resource.LINK_TYPE_FILE))
        self.client.logout()
        # file2
        self.client.force_login(self.u2)
        self.client.post(uri, dict(stream=open(self.file2), link_type=Resource.LINK_TYPE_FILE))
        self.client.logout()
        # file3
        self.client.force_login(self.u1)
        self.client.post(uri, dict(stream=open(self.file3), link_type=Resource.LINK_TYPE_FILE))
        self.client.logout()
        # verify all files
        self.client.force_login(self.u2)
        Resource.objects.all().update(status=Resource.STATUS_NORMAL)

        #
        self.client.force_login(self.u1)
        response = self.client.get('{}{}/'.format(uri, 2))
        self.client.logout()
        data = response.data
        self.assertEqual(data['id'], 2)
        #
        self.client.force_login(self.u2)
        response = self.client.get('{}{}/'.format(uri, 1))
        self.client.logout()
        data = response.data
        self.assertEqual(data['id'], 1)
        #
        self.client.force_login(self.u1)
        response = self.client.get('{}{}/'.format(uri, 3))
        self.client.logout()
        data = response.data
        self.assertEqual(data['id'], 3)

    def test_delete_without_privileges(self):
        uri = reverse('resource-list')
        # file1
        self.client.force_login(self.u1)
        self.client.post(uri, dict(stream=open(self.file1), link_type=Resource.LINK_TYPE_FILE))
        self.client.logout()
        # file2
        self.client.force_login(self.u2)
        self.client.post(uri, dict(stream=open(self.file2), link_type=Resource.LINK_TYPE_FILE))
        self.client.logout()
        # file3
        self.client.force_login(self.u1)
        self.client.post(uri, dict(stream=open(self.file3), link_type=Resource.LINK_TYPE_FILE))
        self.client.logout()
        # verify all files
        self.client.force_login(self.u2)
        Resource.objects.all().update(status=Resource.STATUS_NORMAL)

        #
        data = self.client.get('{}{}/'.format(uri, 2)).data
        response = self.client.delete('{}{}/'.format(uri, 2))
        self.assertEqual(response.status_code, 204, 'delete error')
        self.assertFalse(Resource.objects.filter(id=2).exists(), '数据库项未删除')
        self.assertFalse(os.path.exists(os.path.join(settings.RESOURCE_ROOT, data['name'])), '必须同步删除本地文件')


class MaterialAPITests(APITestCase):
    def setUp(self):
        # 用户
        self.u1 = User.objects.create_user('user1', password='123456', is_staff=True)
        self.u2 = User.objects.create_user('user2', password='789012', is_staff=True)
        pass

    def tearDown(self):

        pass

    def test_create(self):
        self.client.force_login(self.u1)
        
        pass

    def test_read(self):

        pass

    def test_permission(self):

        pass
