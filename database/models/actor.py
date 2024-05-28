from tortoise import fields, Model
from database.validators import url, integers

class Actor(Model):
    id = fields.BigIntField(pk=True)
    owner_id = fields.ForeignKeyField('models.User', related_name='actors', on_delete=fields.CASCADE)
    name = fields.CharField(max_length=255, unique=True)
    call_pattern = fields.TextField()
    image = fields.TextField(description="URL to avatar", validators=[url.valid_url])
    balance = fields.IntField(default=0, description="Balance", validators=[integers.not_negative])
    inventory_chat_id = fields.IntField()
    created_at = fields.DatetimeField(auto_now_add=True)
    
    class Meta:
        table_name = 'actors'