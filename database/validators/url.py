from tortoise.exceptions import ValidationError

def valid_url(url):
    if not url.startswith('http://') or not url.startswith('https://'):
        raise ValidationError('URL must start with http:// or https://')