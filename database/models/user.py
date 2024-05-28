from tortoise import fields
from tortoise.models import Model

class User(Model):
    id = fields.IntField(pk=True)
    discord_id = fields.IntField()
    username = fields.CharField(unique=True, max_length=255)
    
    class Meta:
        table_name = 'users'