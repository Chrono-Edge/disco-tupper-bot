from typing import Union

from tortoise import fields
from tortoise.models import Model


class User(Model):
    id = fields.IntField(pk=True)
    discord_id = fields.IntField()
    tuppers: fields.ManyToManyRelation["models.Tupper"] = fields.ManyToManyField(
        "models.Tupper", related_name="user", through="user_tuppers"
    )

    class Meta:
        table = "users"
