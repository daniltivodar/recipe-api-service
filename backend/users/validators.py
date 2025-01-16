from django.core.exceptions import ValidationError


def ban_name_me(username):
    """Не позволяет установить пользователю имя - me."""
    if username.lower() == 'me':
        raise ValidationError('Вы не можете установить такое имя!')
    return username
