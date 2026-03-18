from http.client import responses
from unittest.mock import patch, PropertyMock

from django.db.models.fields import return_None
from django.http import Http404
from django.test import SimpleTestCase, TestCase, RequestFactory
from django.shortcuts import reverse
from django.contrib.auth import get_user_model
from rest_framework.exceptions import PermissionDenied

from paste.models import Paste
from paste.views import PasteDetail


class TestHomePage(TestCase):
    def test_status_code(self):
        response = self.client.get(reverse('home'))

        self.assertEqual(response.status_code, 200)

    def test_correct_template(self):
        response = self.client.get(reverse('home'))

        self.assertTemplateUsed(response, 'paste/home.html')

    def test_create_paste_and_validate_processing(self):
        # создается обьект в хранилище (-)
        response = self.client.post(reverse('home'), data={
            'paste_text': 'test_text',
            'expiration': 'N',
            'visibility': 'public'
        })
        self.assertEqual(response.status_code, 302)

class TestPasteDetailPage(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()

        cls.owner = User.objects.create_user(
            username='owner',
            password='pass'
        )

        cls.other = User.objects.create_user(
            username='other',
            password='pass'
        )

        cls.paste = Paste.objects.create(
            hash='test_hash',
            expiration_type='N',
            owner=cls.owner
        )

        cls.patcher_s3 = patch(
            'paste.utils.S3UtilsMixin.get_text_from_object_in_s3',
            return_value='some_text'
        )
        cls.mock_s3 = cls.patcher_s3.start()

        cls.patcher_cached = patch(
            'paste.utils.S3UtilsMixin.get_or_set_cached_paste',
            return_value=cls.paste
        )
        cls.mock_get_cached = cls.patcher_cached.start()

        cls.addClassCleanup(cls.patcher_s3.stop)
        cls.addClassCleanup(cls.patcher_cached.stop)

    def test_status_code(self):
        response = self.client.get(reverse('paste_detail', kwargs={'data': self.paste.hash}))

        self.assertEqual(response.status_code, 200)

    def test_correct_template(self):
        response = self.client.get(reverse('paste_detail', kwargs={'data': self.paste.hash}))

        self.assertTemplateUsed(response, 'paste/paste_detail.html')

    def test_valid_get_object(self):
        response = self.client.get(reverse('paste_detail', kwargs={'data': self.paste.hash}))

        self.assertContains(response, 'some_text')
        self.assertEqual(response.context['paste'], self.paste)

    def test_pass_valid_context(self):
        response = self.client.get(reverse('paste_detail', kwargs={'data': self.paste.hash}))

        self.assertEqual(response.context['hash'], self.paste.hash)

    def test_paste_can_edit_owner(self):
        self.client.login(username='owner', password='pass')

        response = self.client.get(
            reverse('paste_detail', kwargs={'data': self.paste.hash})
        )

        self.assertTrue(response.context['can_edit'])

    def test_paste_can_edit_other(self):
        self.client.login(username='other', password='pass')

        response = self.client.get(
            reverse('paste_detail', kwargs={'data': self.paste.hash})
        )

        self.assertFalse(response.context['can_edit'])

    def test_paste_can_edit_guest(self):
        response = self.client.get(
            reverse('paste_detail', kwargs={'data': self.paste.hash})
        )

        self.assertFalse(response.context['can_edit'])

    def test_cannot_get_paste_object(self):
        with patch('paste.utils.S3UtilsMixin.get_or_set_cached_paste', side_effect=Paste.DoesNotExist):
            response = self.client.get(
                reverse('paste_detail', kwargs={'data': 'nonexisted_hash'})
            )

            self.assertEqual(response.status_code, 404)

    def test_private_paste_access(self):
        private_paste = Paste.objects.create(
            hash='secret',
            expiration_type='N',
            is_private='private',
            owner=self.owner
        )
        self.client.login(username='owner', password='pass')
        response = self.client.get(reverse('paste_detail', kwargs={'data': private_paste.hash}))

        self.assertEqual(response.status_code, 200)

    def test_private_paste_guest_access(self):
        private_paste = Paste.objects.create(
            hash='secret',
            expiration_type='N',
            is_private='private',
            owner=self.owner
        )

        with patch('paste.utils.S3UtilsMixin.get_or_set_cached_paste', return_value=private_paste):
            self.client.force_login(self.other)
            response = self.client.get(reverse('paste_detail', kwargs={'data': private_paste.hash}))

            self.assertEqual(response.status_code, 403)


