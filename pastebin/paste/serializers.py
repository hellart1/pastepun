from rest_framework import serializers
from rest_framework.renderers import JSONRenderer

from .models import Paste

class SaveCurrentUserDefault(serializers.CurrentUserDefault):
    def __call__(self, serializer_field):
        user = super().__call__(serializer_field)

        return user if user and user.is_authenticated else None


class PasteSerializer(serializers.ModelSerializer):
    download_url = serializers.SerializerMethodField()
    user = serializers.HiddenField(default=SaveCurrentUserDefault())

    class Meta:
        model = Paste
        fields = ('hash', 'expiration_type', 'user', 'download_url')

    def get_download_url(self, obj):
        return self.context.get('download_url')
