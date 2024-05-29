from typing import Union

from tortoise import fields
from tortoise.models import Model


class User(Model):
    id = fields.IntField(pk=True)
    discord_id = fields.CharField(max_length=255, unique=True)
    username = fields.CharField(unique=True, max_length=255)

    class Meta:
        table = 'users'

    def set_discord_id(self, member_id: [Union[str, int]]):
        self.discord_id = str(member_id)

    def get_discord_id(self) -> Union[str, int]:
        return self.discord_id
