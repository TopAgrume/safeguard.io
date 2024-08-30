from src.database.operations import DatabaseOperations
from src.utils.logger import setup_logger

logger = setup_logger("user_service")
"""Logger for the user service module"""

class UserService:
    """
    A service class for managing user-related operations such as creating, deleting,
    and retrieving user data from the database. This class interacts with the database
    through the DatabaseOperations module and logs operations using the setup logger.
    """
    @staticmethod
    def create_user(user_id: int, username: str) -> None:
        """
        Create a new user in the 'users' table with default values.

        Args:
            user_id (int): The ID of the new user.
            username (str): The username of the new user.
        """
        try:
            DatabaseOperations.create_user(user_id, username)
            logger.info(f"User created successfully: user_id={user_id}, username={username}")
        except Exception as e:
            logger.error(f"Failed to create user: user_id={user_id}, username={username}. Error: {e}")
            raise

    @staticmethod
    def delete_user(user_id: int) -> None:
        """
        Delete a user from the 'users' table and all its relative data.

        Args:
            user_id (int): The ID of the user to delete.
        """
        try:
            DatabaseOperations.delete_user(user_id)
            logger.info(f"User deleted successfully: user_id={user_id}")
        except Exception as e:
            logger.error(f"Failed to delete user: user_id={user_id}. Error: {e}")
            raise

    @staticmethod
    def user_exists(user_id: int) -> bool:
        """
        Check if a user with the given ID exists in the 'users' table.

        Args:
            user_id (int): The ID of the user to check.

        Returns:
            bool: True if the user exists, False otherwise.
        """
        try:
            return DatabaseOperations.user_exists(user_id)
        except Exception as e:
            logger.error(f"Failed to check if user exists: user_id={user_id}. Error: {e}")
            raise

    @staticmethod
    def get_username(user_id: int) -> str:
        """
        Retrieve the username associated with a user ID.

        Args:
            user_id (int): The ID of the user to look up.

        Returns:
            str: The username associated with the given user ID, or None if no user is found.
        """
        try:
            username = DatabaseOperations.get_username(user_id)
            if username is None:
                logger.warning(f"No username found for user_id={user_id}")
            return username
        except Exception as e:
            logger.error(f"Failed to get username: user_id={user_id}. Error: {e}")
            raise

    @staticmethod
    def get_user_property(user_id: int, key: str) -> str | bool:
        """
        Read a specific property of a user from the 'users' table.

        Args:
            user_id (int): The ID of the user whose property is being read.
            key (str): The column name in the 'users' table to retrieve.

        Returns:
            str | bool: The value of the specified property for the user, or None if the user is not found.
        """
        try:
            value = DatabaseOperations.get_user_property(user_id, key)
            if value is None:
                logger.warning(f"No value found for property '{key}' of user_id={user_id}")
            return value
        except Exception as e:
            logger.error(f"Failed to get user property: user_id={user_id}, key={key}. Error: {e}")
            raise

    @staticmethod
    def update_user_property(user_id: int, key: str, value: str | bool) -> None:
        """
        Update a specific property of a user in the 'users' table.

        Args:
            user_id (int): The ID of the user whose property is to be updated.
            key (str): The column name in the 'users' table to update.
            value (str | bool): The new value for the property.
        """
        try:
            DatabaseOperations.update_user_property(user_id, key, value)
            logger.info(f"User property updated successfully: user_id={user_id}, key={key}, value={value}")
        except Exception as e:
            logger.error(f"Failed to update user property: user_id={user_id}, key={key}, value={value}. Error: {e}")
            raise

    @staticmethod
    def get_user_information(user_id: int) -> tuple[bool, bool]:
        """
        Retrieve specific information about a user.

        Args:
            user_id (int): The ID of the user whose information is being retrieved.

        Returns:
            tuple: A tuple containing the response message and alert mode for the user, or (None, None) if the user is not found.
        """
        try:
            user_info = DatabaseOperations.get_user_information(user_id)
            logger.info(f"Retrieved user information for user_id={user_id}")
            return user_info
        except Exception as e:
            logger.error(f"Failed to get user information for user_id={user_id}. Error: {e}")
            raise

    @staticmethod
    def user_already_registered(user_id: int) -> bool:
        """
        Check if a user is already registered in the 'users' table.

        Args:
            user_id (int): The ID of the user to check.

        Returns:
            bool: True if the user is registered, False otherwise.
        """
        try:
            is_registered = DatabaseOperations.user_already_registered(user_id)
            logger.info(f"Checked registration status for user_id={user_id}: {is_registered}")
            return is_registered
        except Exception as e:
            logger.error(f"Failed to check registration status for user_id={user_id}. Error: {e}")
            raise