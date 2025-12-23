from unittest.mock import patch, PropertyMock

from django.test import SimpleTestCase, TestCase
from django.shortcuts import reverse

from paste.models import Paste


class TestHomePage(TestCase):
    def test_homepage_status_code(self):
        response = self.client.get(reverse('home'))

        self.assertEqual(response.status_code, 200)

    def test_homepage_correct_template(self):
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
    def setUp(self):
        self.paste = Paste.objects.create(hash='test_hash', expiration_type='10M')

        self.patcher_s3 = patch(
            'paste.views.S3UtilsMixin.get_text_from_object_in_s3',
            return_value='some_text'
        )
        self.mock_s3 = self.patcher_s3.start()

        self.patcher_cached = patch(
            'paste.views.S3UtilsMixin.get_or_set_paste_cached',
            return_value=self.paste
        )
        self.mock_get_cached = self.patcher_cached.start()

        self.addCleanup(self.patcher_s3.stop)
        self.addCleanup(self.patcher_cached.stop)

    def test_paste_detail_status_code(self):
        response = self.client.get(reverse('paste_detail', kwargs={'data': self.paste.hash}))

        self.assertEqual(response.status_code, 200)

    def test_paste_detail_correct_template(self):
        response = self.client.get(reverse('paste_detail', kwargs={'data': self.paste.hash}))

        self.assertTemplateUsed(response, 'paste/paste_detail.html')