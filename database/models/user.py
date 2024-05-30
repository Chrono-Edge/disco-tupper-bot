from typing import Union

from tortoise import fields
from tortoise.models import Model


class User(Model):
    id = fields.IntField(pk=True)
    actors: fields.ManyToManyRelation['models.Actor'] = fields.ManyToManyField('models.Actor', related_name='user',
                                                                               through='user_actors')

    class Meta:
        table = 'users'

    def set_discord_id(self, member_id: [Union[str, int]]):
        self.id = int(member_id)

    def get_discord_id(self) -> Union[str, int]:
        return self.id
