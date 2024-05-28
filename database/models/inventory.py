from tortoise import fields
from tortoise.models import Model
from database.validators.integers import not_negative


class Inventory(Model):
    id = fields.IntField(pk=True)
    tupper = fields.ForeignKeyField('models.Tuppers', related_name='inventory')
    items = fields.ForeignKeyField('models.Items', related_name='inventory')
    quantity = fields.IntField(default=1, validators=[not_negative])
    acquired_at = fields.DatetimeField(auto_now_add=True)
    
    class Meta:
        table = 'inventory'