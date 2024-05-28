from tortoise import fields
from tortoise.models import Model

class Users(Model):
    id = fields.BigIntField(pk=True)
    username = fields.CharField(unique=True, max_length=255)
    
    class Meta:
        table = 'users'