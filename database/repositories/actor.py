from typing import List, Optional

from database.models.actor import Actor


class ActorRepository:
    
    @staticmethod
    async def create_actor(owner_id: int, name: str, call_pattern: str, image: str,
                           balance: int = 0, inventory_chat_id: Optional[int] = None) -> Actor:
        """
        Create a new actor.

        Args:
            owner_id (int): The ID of the owner (user) of the actor.
            name (str): The name of the actor.
            call_pattern (str): The call pattern for the actor.
            image (str): The URL to the actor's avatar.
            balance (int, optional): The initial balance of the actor. Defaults to 0.
            inventory_chat_id (int, optional): The ID of the inventory chat for the actor. Defaults to None.

        Returns:
            Actor: The newly created actor.
        """
        actor = await Actor.create(owner_id=owner_id, name=name, call_pattern=call_pattern,
                                   image=image, balance=balance, inventory_chat_id=inventory_chat_id)
        return actor

    @staticmethod
    async def get_actor_by_id(actor_id: int) -> Optional[Actor]:
        """
        Retrieve an actor by their ID.

        Args:
            actor_id (int): The ID of the actor.

        Returns:
            Optional[Actor]: The actor if found, else None.
        """
        actor = await Actor.filter(id=actor_id).first()
        return actor

    @staticmethod
    async def get_actors_by_owner(owner_id: int) -> List[Actor]:
        """
        Retrieve all actors belonging to a specific owner.

        Args:
            owner_id (int): The ID of the owner (user) of the actors.

        Returns:
            List[Actor]: A list of actors belonging to the owner.
        """
        actors = await Actor.filter(owner_id=owner_id).all()
        return actors

    @staticmethod
    async def update_actor_balance(actor_id: int, new_balance: int) -> int:
        """
        Update the balance of an actor.

        Args:
            actor_id (int): The ID of the actor to update.
            new_balance (int): The new balance for the actor.

        Returns:
            int: The number of updated rows (1 if successful, 0 if actor not found).
        """
        updated_rows = await Actor.filter(id=actor_id).update(balance=new_balance)
        return updated_rows

    @staticmethod
    async def delete_actor(actor_id: int):
        """
        Delete an actor by their ID.

        Args:
            actor_id (int): The ID of the actor to delete.
        """
        await Actor.filter(id=actor_id).delete()

    # Add more methods as needed...
