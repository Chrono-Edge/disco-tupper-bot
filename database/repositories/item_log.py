from typing import List, Optional

from database.models.item_log import ItemLog


class ItemLogRepository:
    @staticmethod
    async def create_item_log(item_id: int, chat_id: int, message_id: int, quantity_income: int = 0) -> ItemLog:
        """
        Create a new item log.

        Args:
            item_id (int): The ID of the item associated with the log.
            chat_id (int): The ID of the chat associated with the log.
            message_id (int): The ID of the message associated with the log.
            quantity_income (int, optional): The quantity income for the item log. Defaults to 0.

        Returns:
            ItemLog: The newly created item log.
        """
        item_log = await ItemLog.create(item_id=item_id, chat_id=chat_id, message_id=message_id,
                                        quantity_income=quantity_income)
        return item_log

    @staticmethod
    async def get_item_log_by_id(log_id: int) -> Optional[ItemLog]:
        """
        Retrieve an item log by its ID.

        Args:
            log_id (int): The ID of the item log.

        Returns:
            Optional[ItemLog]: The item log if found, else None.
        """
        item_log = await ItemLog.filter(id=log_id).first()
        return item_log

    @staticmethod
    async def get_item_logs_by_item(item_id: int) -> List[ItemLog]:
        """
        Retrieve all item logs associated with a specific item.

        Args:
            item_id (int): The ID of the item.

        Returns:
            List[ItemLog]: A list of item logs associated with the item.
        """
        item_logs = await ItemLog.filter(item_id=item_id).all()
        return item_logs

    @staticmethod
    async def update_item_log_quantity_income(log_id: int, new_quantity_income: int) -> int:
        """
        Update the quantity income of an item log.

        Args:
            log_id (int): The ID of the item log to update.
            new_quantity_income (int): The new quantity income for the item log.

        Returns:
            int: The number of updated rows (1 if successful, 0 if item log not found).
        """
        updated_rows = await ItemLog.filter(id=log_id).update(quantity_income=new_quantity_income)
        return updated_rows

    @staticmethod
    async def delete_item_log(log_id: int):
        """
        Delete an item log by its ID.

        Args:
            log_id (int): The ID of the item log to delete.
        """
        await ItemLog.filter(id=log_id).delete()

    # Add more methods as needed...
