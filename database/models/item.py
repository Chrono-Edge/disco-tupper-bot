from tortoise import fields
from tortoise.models import Model

from database.validators.integers import not_negative

class Item(Model):
    id = fields.BigIntField(pk=True)
    actor_owner = fields.ForeignKeyField('models.Actor', related_name='items', on_delete=fields.CASCADE)
    item_message = fields.IntField(description='Message ID')
    created_at = fields.DatetimeField(auto_now_add=True)
    
    class Meta:
        table_name = 'items'