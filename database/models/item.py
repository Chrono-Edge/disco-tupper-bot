from tortoise import fields
from tortoise.models import Model


class Item(Model):
    id = fields.BigIntField(pk=True)
    name = fields.TextField()
    quantity = fields.IntField()

    tupper_owner = fields.ForeignKeyField(
        "models.Tupper", related_name="items", to_field="id", on_delete=fields.CASCADE
    )

    class Meta:
        table = "items"
