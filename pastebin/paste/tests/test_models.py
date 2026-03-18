from django.test import TestCase
from paste.models import Paste


class PasteTestCase(TestCase):
    def setUp(self):
        self.paste = Paste.objects.create(hash='test_text', expiration_type='10M')

    def test_paste_is_created(self):
        self.assertEqual(str(self.paste), 'test_text')

    def test_property_is_expire(self):
        self.assertEqual(self.paste.is_expired, False)