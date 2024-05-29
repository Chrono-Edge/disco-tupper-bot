from tortoise import fields
from tortoise.models import Model

class Item(Model):
    id = fields.BigIntField(pk=True)
    actor_owner = fields.ForeignKeyField('models.Actor', related_name='items', to_field='id', on_delete=fields.CASCADE)
    item_message = fields.IntField(description='Message ID')
    created_at = fields.DatetimeField(auto_now_add=True)
    
    logs: fields.ReverseRelation['models.ItemLog']
    
    class Meta:
        table = 'items'