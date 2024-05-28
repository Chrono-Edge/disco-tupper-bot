from tortoise import fields
from tortoise.models import Model

from database.validators.integers import not_negative

class Items(Model):
    id = fields.BigIntField(pk=True)
    name = fields.CharField(max_length=100)
    price = fields.IntField(default=0, validators=[not_negative])
    description = fields.TextField(null=True)
    acquired_at = fields.DatetimeField(auto_now_add=True)
    
    class Meta:
        table = 'items'