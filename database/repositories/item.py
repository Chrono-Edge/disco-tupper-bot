from typing import List, Optional
from database.models.item import Item

class ItemRepository:
    @staticmethod
    async def create_item(actor_owner_id: int, item_message: int) -> Item:
        """
        Create a new item.

        Args:
            actor_owner_id (int): The ID of the actor who owns the item.
            item_message (int): The message ID associated with the item.

        Returns:
            Item: The newly created item.
        """
        item = await Item.create(actor_owner_id=actor_owner_id, item_message=item_message)
        return item

    @staticmethod
    async def get_item_by_id(item_id: int) -> Optional[Item]:
        """
        Retrieve an item by its ID.

        Args:
            item_id (int): The ID of the item.

        Returns:
            Optional[Item]: The item if found, else None.
        """
        item = await Item.filter(id=item_id).first()
        return item

    @staticmethod
    async def get_items_by_owner(actor_owner_id: int) -> List[Item]:
        """
        Retrieve all items owned by a specific actor.

        Args:
            actor_owner_id (int): The ID of the actor who owns the items.

        Returns:
            List[Item]: A list of items owned by the actor.
        """
        items = await Item.filter(actor_owner_id=actor_owner_id).all()
        return items

    @staticmethod
    async def update_item_message(item_id: int, new_item_message: int) -> int:
        """
        Update the message ID associated with an item.

        Args:
            item_id (int): The ID of the item to update.
            new_item_message (int): The new message ID for the item.

        Returns:
            int: The number of updated rows (1 if successful, 0 if item not found).
        """
        updated_rows = await Item.filter(id=item_id).update(item_message=new_item_message)
        return updated_rows

    @staticmethod
    async def delete_item(item_id: int):
        """
        Delete an item by its ID.

        Args:
            item_id (int): The ID of the item to delete.
        """
        await Item.filter(id=item_id).delete()

    # Add more methods as needed...
