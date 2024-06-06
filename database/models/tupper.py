﻿from tortoise import fields, Model

from database.validators import url, integers


class Tupper(Model):
    id = fields.BigIntField(pk=True)
    name = fields.CharField(max_length=255)
    call_pattern = fields.TextField()
    image = fields.TextField(description="URL to avatar", validators=[url.valid_url])
    balance = fields.IntField(default=0, validators=[integers.not_negative])
    inventory_chat_id = fields.IntField(default=0)
    created_at = fields.DatetimeField(auto_now_add=True)

    owners: fields.ReverseRelation["Tupper"]
    items: fields.ReverseRelation["models.Item"]
    attrs: fields.ReverseRelation["models.Attribute"]

    class Meta:
        table = "tuppers"