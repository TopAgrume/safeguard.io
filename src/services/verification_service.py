from datetime import datetime
from src.database.operations import DatabaseOperations
from src.utils.logger import setup_logger

logger = setup_logger("verification_service")
"""Logger for the verification service module"""

class VerificationService:
    """A service class for managing verifications-related operations such as retrieving, adding,
    deleting, skipping, and updating verification records. It also manages check queue items
    for verification checks.
    """
    @staticmethod
    def get_user_verifications(user_id: int) -> list[tuple[datetime.time, str, bool]]:
        """
        Retrieve the verifications for a user.

        Args:
            user_id (int): The ID of the user whose verifications are being retrieved.

        Returns:
            list[tuple[datetime.time, str, bool]]: A list of tuples containing the time, description, and active status for each verification.
        """
        try:
            verifications = DatabaseOperations.get_user_verifications(user_id)
            logger.info(f"Retrieved {len(verifications)} verifications for user_id={user_id}")
            return verifications
        except Exception as e:
            logger.error(f"Failed to get verifications for user_id={user_id}. Error: {e}")
            raise

    @staticmethod
    def get_idle_users_verifications() -> list[tuple[int, datetime.time, str, bool]]:
        """
        Retrieves a list of verifications from users who have not responded.

        Returns:
            list[tuple[int, datetime.time, str, bool]]: A list of tuples, each containing:
                - user ID (int)
                - time of the message (datetime.time)
                - description of the message (str)
                - whether the message is active (bool)
        """
        try:
            idle_verifications = DatabaseOperations.get_idle_users_verifications()
            logger.info(f"Retrieved {len(idle_verifications)} idle user verifications")
            return idle_verifications
        except Exception as e:
            logger.error(f"Failed to get idle user verifications. Error: {e}")
            raise

    @staticmethod
    def add_verifications(user_id: int, new_verifications: list, skip_check: bool = False) -> list[str]:
        """
        Add new verifications for a user.

        Args:
            user_id (int): The ID of the user for whom verifications are being added.
            new_verifications (list): A list of new verification entries to add.
            skip_check (bool): Whether to skip validation checks for existing verifications.

        Returns:
            list[str]: A list of times for which verifications were not valid.
        """
        try:
            not_valid = DatabaseOperations.add_verifications(user_id, new_verifications, skip_check)
            logger.info(f"Added {len(new_verifications) - len(not_valid)} verifications for user_id={user_id}")
            return not_valid
        except Exception as e:
            logger.error(f"Failed to add verifications for user_id={user_id}. Error: {e}")
            raise

    @staticmethod
    def delete_verifications(user_id: int, times_to_delete: list) -> None:
        """
        Delete specific verifications for a user.

        Args:
            user_id (int): The ID of the user from whom verifications will be deleted.
            times_to_delete (list): A list of times specifying which verifications to delete.
        """
        try:
            DatabaseOperations.delete_verifications(user_id, times_to_delete)
            logger.info(f"Deleted {len(times_to_delete)} verifications for user_id={user_id}")
        except Exception as e:
            logger.error(f"Failed to delete verifications for user_id={user_id}. Error: {e}")
            raise

    @staticmethod
    def skip_verifications(user_id: int, times_to_skip: list) -> None:
        """
        Mark specific verifications as skipped (inactive).

        Args:
            user_id (int): The ID of the user whose verifications are being skipped.
            times_to_skip (list): A list of times specifying which verifications to skip.
        """
        try:
            DatabaseOperations.skip_verifications(user_id, times_to_skip)
            logger.info(f"Skipped {len(times_to_skip)} verifications for user_id={user_id}")
        except Exception as e:
            logger.error(f"Failed to skip verifications for user_id={user_id}. Error: {e}")
            raise

    @staticmethod
    def undoskip_verifications(user_id: int, times_to_undoskip: list) -> None:
        """
        Revert the status of specific verifications to active.

        Args:
            user_id (int): The ID of the user whose verifications are being reverted.
            times_to_undoskip (list): A list of times specifying which verifications to reactivate.
        """
        try:
            DatabaseOperations.undoskip_verifications(user_id, times_to_undoskip)
            logger.info(f"Undoskipped {len(times_to_undoskip)} verifications for user_id={user_id}")
        except Exception as e:
            logger.error(f"Failed to undoskip verifications for user_id={user_id}. Error: {e}")
            raise

    @staticmethod
    def get_check_queue_items() -> list[tuple[int, datetime.time, str, int, int]]:
        """
        Retrieves all checks from the check queue.

        Returns:
            list[tuple[int, datetime.time, str, int, int]]: A list of tuples, each containing:
                - user ID (int)
                - time of the check (datetime.time)
                - description of the check (str)
                - reminder count (int)
                - waiting time (int)
        """
        try:
            queue_items = DatabaseOperations.get_check_queue_items()
            logger.info(f"Retrieved {len(queue_items)} check queue items")
            return queue_items
        except Exception as e:
            logger.error(f"Failed to get check queue items. Error: {e}")
            raise

    @staticmethod
    def update_check_queue_property(user_id: int, key: str, value: int) -> None:
        """
        Updates a specific property of a user's check queue entry.

        Args:
            user_id (int): The ID of the user.
            key (str): The name of the field to be updated.
            value (int): The new value to be set for the specified field.
        """
        try:
            DatabaseOperations.update_check_queue_property(user_id, key, value)
            logger.info(f"Updated check queue property for user_id={user_id}: {key}={value}")
        except Exception as e:
            logger.error(f"Failed to update check queue property for user_id={user_id}: {key}={value}. Error: {e}")
            raise

    @staticmethod
    def add_check_queue_item(user_id: int, time: datetime.time, desc: str, waiting_time: int) -> None:
        """
        Initializes a check queue entry for a user.

        Args:
            user_id (int): The ID of the user.
            time (datetime.time): The time associated with the check.
            desc (str): The description of the check.
            waiting_time (int): The waiting time before the next reminder.
        """
        try:
            DatabaseOperations.add_check_queue_item(user_id, time, desc, waiting_time)
            logger.info(
                f"Added check queue item for user_id={user_id}: time={time}, desc={desc}, waiting_time={waiting_time}")
        except Exception as e:
            logger.error(f"Failed to add check queue item for user_id={user_id}. Error: {e}")
            raise

    @staticmethod
    def delete_check_queue_item(user_id: int) -> None:
        """
        Deletes a user's check queue entry.

        Args:
            user_id (int): The ID of the user whose check queue entry should be deleted.
        """
        try:
            DatabaseOperations.delete_check_queue_item(user_id)
            logger.info(f"Deleted check queue item for user_id={user_id}")
        except Exception as e:
            logger.error(f"Failed to delete check queue item for user_id={user_id}. Error: {e}")
            raise

    @staticmethod
    def update_verification_status(user_id: int, times_to_update: list, active: bool) -> None:
        """
        Update the status of specific verifications for a user.

        Args:
            user_id (int): The ID of the user whose verification statuses are being updated.
            times_to_update (list): A list of times specifying which verifications to update.
            active (bool): The new status for the verifications (active or inactive).
        """
        try:
            DatabaseOperations.update_verification_status(user_id, times_to_update, active)
            logger.info(f"Updated verification status for user_id={user_id}, active={active}, times={times_to_update}")
        except Exception as e:
            logger.error(f"Failed to update verification status for user_id={user_id}. Error: {e}")
            raise