﻿from tortoise import Model, fields

from database.validators import integers

class ItemLog(Model):
    id = fields.IntField(pk=True)
    item_id = fields.ForeignKeyField('models.Item', related_name='item_log', on_delete=fields.CASCADE)
    chat_id = fields.IntField()
    message_id = fields.IntField()
    quantity_income = fields.IntField(default=0, validators=[integers.not_negative])
    
    class Meta:
        table_name = 'item_logs'