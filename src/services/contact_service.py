from database.operations import DatabaseOperations
from utils.logger import setup_logger

logger = setup_logger("contact_service")
"""Logger for the contact service module"""

class ContactService:
    """A service class for managing user-related operations such as adding, retrieving, updating,
    and deleting contacts, as well as handling contact requests.
    """
    @staticmethod
    def get_contacts(user_id: int) -> list[tuple[int, str, bool]]:
        """
        Retrieve the contact information for a user.

        Args:
            user_id (int): The ID of the user whose contacts are being retrieved.

        Returns:
            list[tuple[int, str, bool]]: A list of tuples containing the contact ID, tag, and pair status for each contact.
        """
        try:
            contacts = DatabaseOperations.get_contacts(user_id)
            logger.info(f"Retrieved {len(contacts)} contacts for user_id={user_id}")
            return contacts
        except Exception as e:
            logger.error(f"Failed to get contacts for user_id={user_id}. Error: {e}")
            raise

    @staticmethod
    def add_contacts(user_id: int, username: str, target_usernames: list[str]) -> list[dict]:
        """
        Add new contacts for a user and handle contact requests.

        Args:
            user_id (int): The ID of the user adding contacts.
            username (str): The username of the user adding contacts.
            target_usernames (list[str]): A list of usernames to add as contacts.

        Returns:
            list[dict]: A list of notifications with contact IDs and tags for successfully added contacts.
        """
        try:
            notifications = DatabaseOperations.add_contacts(user_id, username, target_usernames)
            logger.info(f"Added {len(notifications)} contacts for user_id={user_id}")
            return notifications
        except Exception as e:
            logger.error(f"Failed to add contacts for user_id={user_id}. Error: {e}")
            raise

    @staticmethod
    def delete_contact(user_id: int, target_usernames: list[str]) -> None:
        """
        Delete contacts from the user's contact list.

        Args:
            user_id (int): The ID of the user from whom contacts will be deleted.
            target_usernames (list[str]): A list of usernames to delete from the contacts.
        """
        try:
            DatabaseOperations.delete_contact(user_id, target_usernames)
            logger.info(f"Deleted {len(target_usernames)} contacts for user_id={user_id}")
        except Exception as e:
            logger.error(f"Failed to delete contacts for user_id={user_id}. Error: {e}")
            raise

    @staticmethod
    def get_contact_requests(user_id: int) -> list[tuple[int, str]]:
        """
        Retrieve the contact requests for a user.

        Args:
            user_id (int): The ID of the user whose contact requests are being retrieved.

        Returns:
            list[tuple[int, str]]: A list of tuples containing the requester ID and requester tag for each contact request.
        """
        try:
            requests = DatabaseOperations.get_contact_requests(user_id)
            logger.info(f"Retrieved {len(requests)} contact requests for user_id={user_id}")
            return requests
        except Exception as e:
            logger.error(f"Failed to get contact requests for user_id={user_id}. Error: {e}")
            raise

    @staticmethod
    def delete_contact_request(user_id: int, requester_user_id: int) -> None:
        """
        Delete contact request from the user's contact requests list.

        Args:
            user_id (int): The ID of the user from whom contact request will be deleted.
            requester_user_id (int): The ID of the user whose will be deleted from the contact requests.
        """
        try:
            DatabaseOperations.delete_contact_request(user_id, requester_user_id)
            logger.info(f"Deleted contact request from user_id={requester_user_id} for user_id={user_id}")
        except Exception as e:
            logger.error(f"Failed to delete contact request for user_id={user_id}, requester_user_id={requester_user_id}. Error: {e}")
            raise

    @staticmethod
    def update_contacts_property(user_id: int, target_username: str, key: str, value: int | bool) -> None:
        """
        Update a specific property of a contact in the 'contacts' table.

        Args:
            user_id (int): The ID of the user who owns the contact.
            target_username (str): The username of the contact.
            key (str): The column name in the 'contacts' table to update.
            value (int | bool): The new value for the property.
        """
        try:
            DatabaseOperations.update_contacts_property(user_id, target_username, key, value)
            logger.info(
                f"Updated contact property for user_id={user_id}, target_username={target_username}: {key}={value}")
        except Exception as e:
            logger.error(
                f"Failed to update contact property for user_id={user_id}, target_username={target_username}: {key}={value}. Error: {e}")
            raise

    @staticmethod
    def update_contact_pairing(user_id: int, contact_id: int, key: str, value: int | bool) -> None:
        """
        Update a specific property of a contact in the 'contacts' table.

        Args:
            user_id (int): The ID of the user who owns the contact.
            contact_id (int): The ID of the contact.
            key (str): The column name in the 'contacts' table to update.
            value (int | bool): The new value for the property.
        """
        try:
            DatabaseOperations.update_contact_pairing(user_id, contact_id, key, value)
            logger.info(f"Updated contact pairing for user_id={user_id}, contact_id={contact_id}: {key}={value}")
        except Exception as e:
            logger.error(
                f"Failed to update contact pairing for user_id={user_id}, contact_id={contact_id}: {key}={value}. Error: {e}")
            raise

    @staticmethod
    def update_contacts_reload(username: str, user_id: int) -> None:
        """
        Reload the contact_id property when a user reconnects.

        Args:
            username (str): The username of the user that just reconnected.
            user_id (int): The contact_id of the user that just reconnected.
        """
        try:
            DatabaseOperations.update_contacts_reload(username, user_id)
            logger.info(f"Reloaded contacts for username={username}, user_id={user_id}")
        except Exception as e:
            logger.error(f"Failed to reload contacts for username={username}, user_id={user_id}. Error: {e}")
            raise

    @staticmethod
    def get_paired_contacts(user_id: int) -> list[tuple[int, str]]:
        """
        Retrieve the paired contacts information for a user.

        Args:
            user_id (int): The ID of the user whose contacts are being retrieved.

        Returns:
            list[tuple[int, str]]: A list of tuples containing the contact ID and tag for each paired contact.
        """
        try:
            paired_contacts = DatabaseOperations.get_paired_contacts(user_id)
            logger.info(f"Retrieved {len(paired_contacts)} paired contacts for user_id={user_id}")
            return paired_contacts
        except Exception as e:
            logger.error(f"Failed to get paired contacts for user_id={user_id}. Error: {e}")
            raise

    @staticmethod
    def transfer_pending_requests(user_id: int, target_username: str) -> list[tuple[int, str]]:
        """
        Transfer pending requests to the 'contact_requests' table and delete them from the 'pending_requests' table.

        Args:
            user_id (int): The ID of the user receiving the pending requests.
            target_username (str): The username associated with the pending requests.

        Returns:
            list[tuple[int, str]]: A list of tuples containing requester IDs and tags whose requests were transferred.
        """
        try:
            transferred_requests = DatabaseOperations.transfer_pending_requests(user_id, target_username)
            logger.info(f"Transferred {len(transferred_requests)} pending requests for user_id={user_id}, target_username={target_username}")
            return transferred_requests
        except Exception as e:
            logger.error(f"Failed to transfer pending requests for user_id={user_id}, target_username={target_username}. Error: {e}")
            raise