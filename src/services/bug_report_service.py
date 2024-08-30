from src.database.operations import DatabaseOperations
from src.utils.logger import setup_logger

logger = setup_logger("bug_report_service")
"""Logger for the bug report service module"""

class BugReportService:
    """The `BugReportService` class provides static methods to handle bug reports submitted by users."""
    @staticmethod
    def add_bug_report(user_id: int, username: str, message: str) -> int:
        """
        Write a bug report for a user.

        Args:
            user_id (int): The ID of the user submitting the bug report.
            username (str): The username of the user submitting the bug report.
            message (str): The content of the bug report.

        Returns:
            int: The ID of the newly created bug report.
        """
        try:
            report_id = DatabaseOperations.add_bug_report(user_id, username, message)
            logger.info(f"Added bug report for user_id={user_id}, username={username}, report_id={report_id}")
            return report_id
        except Exception as e:
            logger.error(f"Failed to add bug report for user_id={user_id}, username={username}. Error: {e}")
            raise