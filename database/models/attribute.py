from tortoise import fields
from tortoise.models import Model


class Attribute(Model):
    id = fields.BigIntField(pk=True)
    owner = fields.ForeignKeyField(
        'models.Actor', related_name='attrs', to_field='id', on_delete=fields.CASCADE)

    name = fields.CharField(max_length=3)
    value = fields.IntField()
