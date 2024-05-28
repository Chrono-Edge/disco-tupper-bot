from tortoise import fields, Model
from database.validators.url import valid_url

class Tuppers(Model):
    id = fields.BigIntField(pk=True)
    owner = fields.ForeignKeyField('models.Users', related_name='tuppers', on_delete=fields.CASCADE)
    name = fields.CharField(max_length=255, unique=True)
    call_pattern = fields.TextField()
    image = fields.TextField(description="URL to avatar", validators=[valid_url])
    balance = fields.IntField(default=0)
    created_at = fields.DatetimeField(auto_now_add=True)
    
    class Meta:
        table = 'tuppers'