from tortoise import fields
from tortoise.models import Model


class Item(Model):
    id = fields.BigIntField(pk=True)
    tupper_owner = fields.ForeignKeyField(
        "models.Tupper", related_name="items", to_field="id", on_delete=fields.CASCADE
    )
    item_message = fields.IntField(description="Message ID")
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "items"
