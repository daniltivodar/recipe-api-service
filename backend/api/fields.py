import base64

from django.core.files.base import ContentFile
from rest_framework.serializers import ImageField, ValidationError


class Base64ImageField(ImageField):
    """Декодирование изображений, переданных в формате Base64."""

    def to_internal_value(self, data):
        """Преобразует входные данные в объект изображения."""
        if isinstance(data, str) and data.startswith('data:image'):
            try:
                format, imgstr = data.split(';base64,')
                ext = format.split('/')[-1]
                data = ContentFile(
                    base64.b64decode(imgstr),
                    name=f'temp.{ext}',
                )
            except (ValueError, IndexError, base64.binascii.Error) as error:
                raise ValidationError(
                    'Неверный формат Base64 изображения!',
                ) from error
        return super().to_internal_value(data)
