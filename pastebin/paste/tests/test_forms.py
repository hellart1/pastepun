from django.test import TestCase
from paste.forms import TextForm


class TextFormTest(TestCase):
    def test_valid_form(self):
        form = TextForm({
            'paste_text': 'test_text',
            'expiration': 'test_expiration',
            'visibility': 'visibility'
        })

        self.assertTrue(form.is_valid())

    def test_invalid_form(self):
        form = TextForm({
            'paste_text': 'test_text'
        })

        self.assertFalse(form.is_valid())
