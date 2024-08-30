from datetime import datetime
from src.utils.logger import setup_logger
from src.database.connection import get_db_cursor

logger = setup_logger(__name__)
"""Logger for the database operations module"""
MAX_TIME_DIFF = 20
"""Maximum time difference in minutes"""

def less_than_one_hour(time1: datetime.time, time2: dict) -> bool:
    """
    Determines whether the time difference between two given time objects is less than one hour.

    Args:
        time1 (datetime.time): A `datetime.time` object.
        time2 (dict): A dictionary containing a 'time' key, which holds a time string in the format '%H:%M'.

    Returns:
        bool: `True` if the difference between the two times is less than one hour, `False` otherwise.
    """
    # Convert time strings to datetime.time objects
    time2_obj = datetime.strptime(time2['time'], '%H:%M').time()

    # Calculate the difference in minutes
    difference_in_minutes = abs(time1.hour - time2_obj.hour) * 60 + abs(time1.minute - time2_obj.minute)

    return abs(difference_in_minutes) < MAX_TIME_DIFF

class DatabaseOperations:
    # -- User-related methods -----------------------------------------------------
    @staticmethod
    def user_exists(user_id: int) -> bool:
        """
        Check if a user with the given ID exists in the 'users' table.

        Args:
            user_id (int): The ID of the user to check.

        Returns:
            bool: True if the user exists, False otherwise.
        """
        with get_db_cursor() as cur:
            cur.execute("SELECT 1 FROM users WHERE id = %s LIMIT 1", (user_id,))
            return cur.fetchone()[0] is not None

    @staticmethod
    def user_already_registered(user_id: int) -> bool:
        """
        Check if a user is already registered in the 'users' table.

        Args:
            user_id (int): The ID of the user to check.

        Returns:
            bool: True if the user is registered, False otherwise.
        """
        with get_db_cursor() as cur:
            cur.execute("SELECT id FROM users WHERE id = %s", (user_id,))
            users = cur.fetchall()
            return bool(users)

    @staticmethod
    def get_username(user_id: int) -> str:
        """
        Retrieve the username associated with a user ID.

        Args:
            user_id (int): The ID of the user to look up.

        Returns:
            str: The username associated with the given user ID, or None if no user
        """
        with get_db_cursor() as cur:
            cur.execute("SELECT username FROM users WHERE id = %s", (user_id,))
            user = cur.fetchone()
            return user[0] if user else None

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
        with get_db_cursor() as cur:
            cur.execute(f"SELECT {key} FROM users WHERE id = %s", (user_id,))
            user = cur.fetchone()
            return user[0] if user else None

    @staticmethod
    def get_user_information(user_id: int) -> tuple[bool, bool]:
        """
        Retrieve specific information about a user.

        Args:
            user_id (int): The ID of the user whose information is being retrieved.

        Returns:
            tuple: A tuple containing the response message and alert mode for the user, or (None, None) if the user is not found.
        """
        with get_db_cursor() as cur:
            cur.execute("SELECT response_message, alert_mode FROM users WHERE id = %s", (user_id,))
            user = cur.fetchone()
            return user if user else (None, None)

    @staticmethod
    def update_user_property(user_id: int, key: str, value: str | bool) -> None:
        """
        Update a specific property of a user in the 'users' table.

        Args:
            user_id (int): The ID of the user whose property is to be updated.
            key (str): The column name in the 'users' table to update.
            value (str | bool): The new value for the property.
        """
        with get_db_cursor(commit=True) as cur:
            cur.execute(f"UPDATE users SET {key} = %s WHERE id = %s", (value, user_id))

    @staticmethod
    def create_user(user_id: int, username: str) -> None:
        """
        Create a new user in the 'users' table with default values.

        Args:
            user_id (int): The ID of the new user.
            username (str): The username of the new user.
        """
        with get_db_cursor(commit=True) as cur:
            cur.execute("""
                    INSERT INTO users (id, username, alert_mode, response_message, state)
                    VALUES (%s, %s, %s, %s, %s)
                """, (user_id, username, False, True, ''))

    @staticmethod
    def delete_user(user_id: int) -> None:
        """
        Delete a user from the 'users' table and all its relative data.

        Args:
            user_id (int): The ID of the user to delete.
        """
        with get_db_cursor(commit=True) as cur:
            cur.execute("DELETE FROM users WHERE id = %s", (user_id,))


    # -- Contact-related methods -----------------------------------------------------
    @staticmethod
    def get_contacts(user_id: int) -> list[tuple[int, str, bool]]:
        """
        Retrieve the contact information for a user.

        Args:
            user_id (int): The ID of the user whose contacts are being retrieved.

        Returns:
            list[tuple[int, str, bool]]: A list of tuples containing the contact ID, tag, and pair status for each contact.
        """
        with get_db_cursor() as cur:
            cur.execute(f"SELECT contact_id, tag, pair FROM contacts WHERE user_id = %s", (user_id,))
            contacts = cur.fetchall()
            return contacts if contacts else []

    @staticmethod
    def get_paired_contacts(user_id: int) -> list[tuple[int, str]]:
        """
        Retrieve the paired contacts information for a user.

        Args:
            user_id (int): The ID of the user whose contacts are being retrieved.

        Returns:
            list[tuple[int, str, bool]]: A list of tuples containing the contact ID and tag for each contact.
        """
        with get_db_cursor() as cur:
            cur.execute(
                f"SELECT contact_id, tag FROM contacts WHERE user_id = %s AND pair = TRUE AND contact_id IS NOT NULL",
                (user_id,))
            contacts = cur.fetchall()
            return contacts if contacts else []

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
        with get_db_cursor(commit=True) as cur:
            notifications = []
            for target_username in target_usernames:
                cur.execute("SELECT id FROM users WHERE username = %s", (target_username,))
                contact_user = cur.fetchone()[0]

                if contact_user:
                    # Check if contact already exists
                    cur.execute("SELECT * FROM contacts WHERE user_id = %s AND contact_id = %s",
                                (user_id, contact_user))
                    if not cur.fetchone():
                        # Add to contacts table
                        cur.execute("""
                                    INSERT INTO contacts (user_id, contact_id, tag, pair) 
                                    VALUES (%s, %s, %s, FALSE)
                                    ON CONFLICT (user_id, contact_id, tag) DO NOTHING
                                """, (user_id, contact_user, target_username))

                        # Add to contact_requests table
                        cur.execute("""
                                    INSERT INTO contact_requests (user_id, requester_id, requester_tag) 
                                    VALUES (%s, %s, %s)
                                    ON CONFLICT (user_id, requester_id) DO NOTHING
                                """, (contact_user, user_id, username))

                        notifications.append({"id": contact_user, "tag": target_username})
                else:
                    # Check if pending contact already exists
                    cur.execute("""
                                SELECT * FROM contacts 
                                WHERE user_id = %s AND contact_id IS NULL AND tag = %s
                            """, (user_id, target_username))
                    if not cur.fetchone():
                        # Add to pending_requests table
                        cur.execute("""
                                    INSERT INTO pending_requests (requester_id, target_username, tag) 
                                    VALUES (%s, %s, %s)
                                    ON CONFLICT (requester_id, target_username, tag) DO NOTHING
                                """, (user_id, target_username, username))

                        # Add to contacts table with NULL contact_id
                        cur.execute("""
                                    INSERT INTO contacts (user_id, contact_id, tag, pair) 
                                    VALUES (%s, NULL, %s, FALSE)
                                """, (user_id, target_username))
            return notifications

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
        with get_db_cursor(commit=True) as cur:
            cur.execute(f"UPDATE contacts SET {key} = %s WHERE user_id = %s AND tag = %s",
                        (value, user_id, target_username))

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
        with get_db_cursor(commit=True) as cur:
            cur.execute(f"UPDATE contacts SET {key} = %s WHERE user_id = %s AND contact_id = %s ",
                        (value, user_id, contact_id))

    @staticmethod
    def update_contacts_reload(username: str, user_id: int) -> None:
        """
        Reload the contact_id property when a user reconnects.

        Args:
            username (str): The username of the user that just reconnected.
            user_id (int): The contact_id of the user that just reconnected.
        """
        with get_db_cursor(commit=True) as cur:
            cur.execute(f"UPDATE contacts SET contact_id = %s WHERE tag = %s AND contact_id IS NULL",
                        (user_id, username))

    @staticmethod
    def delete_contact(user_id: int, target_usernames: list[str]) -> None:
        """
        Delete contacts from the user's contact list.

        Args:
            user_id (int): The ID of the user from whom contacts will be deleted.
            target_usernames (list[str]): A list of usernames to delete from the contacts.
        """
        with get_db_cursor(commit=True) as cur:
            for contact_tag in target_usernames:
                cur.execute("DELETE FROM contacts WHERE user_id = %s AND tag = %s", (user_id, contact_tag))


    # -- Contact Request-related methods -----------------------------------------------------
    @staticmethod
    def get_contact_requests(user_id: int) -> list[tuple[int, str]]:
        """
        Retrieve the contact requests for a user.

        Args:
            user_id (int): The ID of the user whose contact requests are being retrieved.

        Returns:
            list[tuple[int, str]]: A list of tuples containing the requester ID and requester tag for each contact request.
        """
        with get_db_cursor() as cur:
            cur.execute(f"SELECT requester_id, requester_tag FROM contact_requests WHERE user_id = %s", (user_id,))
            requesters_info = cur.fetchall()
            return requesters_info if requesters_info else []

    @staticmethod
    def delete_contact_request(user_id: int, requester_user_id: int) -> None:
        """
        Delete contacts requests from the user's contact requests list.

        Args:
            user_id (int): The ID of the user from whom contact requests will be deleted.
            requester_user_id (int): The ID of the user whose will be deleted from the contact requests.
        """
        with get_db_cursor(commit=True) as cur:
            cur.execute("DELETE FROM contact_requests WHERE user_id = %s AND requester_id = %s", (user_id, requester_user_id))


    # -- Verification-related methods -----------------------------------------------------
    @staticmethod
    def get_user_verifications(user_id: int) -> list[tuple[datetime.time, str, bool]]:
        """
        Retrieve the verifications for a user.

        Args:
            user_id (int): The ID of the user whose verifications are being retrieved.

        Returns:
            list: A list of tuples containing the time, description, and active status for each verification.
        """
        with get_db_cursor() as cur:
            cur.execute(f"SELECT time, description, active FROM daily_messages WHERE user_id = %s", (user_id,))
            verifications = cur.fetchall()
            return verifications if verifications else []

    @staticmethod
    def get_idle_users_verifications() -> list[tuple[int, datetime.time, str, bool]]:
        """
        Retrieves a list of verifications from users who have not responded.

        The method queries the database for users with active daily messages
        but have a response_message flag set to True.

        Returns:
            list[tuple[int, datetime.time, str, bool]]: A list of tuples, each containing:
                - user ID (int)
                - time of the message (datetime.time)
                - description of the message (str)
                - whether the message is active (bool)
        """
        with get_db_cursor() as cur:
            cur.execute(
                "SELECT u.id, d.time, d.description, d.active FROM users u INNER JOIN daily_messages d ON d.user_id = u.id WHERE u.response_message = TRUE")
            users = cur.fetchall()
            return users if users else []

    @staticmethod
    def delete_verifications(user_id: int, times_to_delete: list) -> None:
        """
        Delete specific verifications for a user.

        Args:
            user_id (int): The ID of the user from whom verifications will be deleted.
            times_to_delete (list): A list of times specifying which verifications to delete.
        """
        with get_db_cursor(commit=True) as cur:
            cur.execute("DELETE FROM daily_messages WHERE user_id = %s AND time = ANY(%s::time[])",
                        (user_id, times_to_delete))

    @staticmethod
    def update_verification_status(user_id: int, times_to_update: list, active: bool) -> None:
        """
        Update the status of specific verifications for a user.

        Args:
            user_id (int): The ID of the user whose verification statuses are being updated.
            times_to_update (list): A list of times specifying which verifications to update.
            active (bool): The new status for the verifications (active or inactive).
        """
        with get_db_cursor(commit=True) as cur:
            cur.execute("UPDATE daily_messages SET active = %s WHERE user_id = %s AND time = ANY(%s::time[])",
                        (active, user_id, times_to_update))

    @staticmethod
    def skip_verifications(user_id: int, times_to_skip: list) -> None:
        """
        Mark specific verifications as skipped (inactive).

        Args:
            user_id (int): The ID of the user whose verifications are being skipped.
            times_to_skip (list): A list of times specifying which verifications to skip.
        """
        DatabaseOperations.update_verification_status(user_id, times_to_skip, False)

    @staticmethod
    def undoskip_verifications(user_id: int, times_to_undoskip: list) -> None:
        """
        Revert the status of specific verifications to active.

        Args:
            user_id (int): The ID of the user whose verifications are being reverted.
            times_to_undoskip (list): A list of times specifying which verifications to reactivate.
        """
        DatabaseOperations.update_verification_status(user_id, times_to_undoskip, True)


    @staticmethod
    def add_verifications(user_id: int, new_verifications: list, skip_check: bool = False) -> list[str]:
        """
        Add new verifications for a user.

        Args:
            user_id (int): The ID of the user for whom verifications are being added.
            new_verifications (list): A list of new verification entries to add.
            skip_check (bool): Whether to skip validation checks for existing verifications.

        Returns:
            list: A list of times for which verifications were not valid.
        """
        with get_db_cursor(commit=True) as cur:
            not_valid = []
            for verification in new_verifications:
                cur.execute("SELECT time, description, active FROM daily_messages WHERE user_id = %s", (user_id,))
                current_verifications = cur.fetchall()

                if any(verif_time == verification['time'] for verif_time, _, _ in current_verifications):
                    continue
                if not skip_check and any(less_than_one_hour(verif_time, verification) for verif_time, _, _ in current_verifications):
                    not_valid.append(verification['time'])
                    continue
                cur.execute(
                    "INSERT INTO daily_messages (user_id, time, description, active) VALUES (%s, %s, %s, %s)",
                    (user_id, verification['time'], verification['description'], verification['active']))

            return not_valid


    # -- Pending Requests-related methods -----------------------------------------------------
    @staticmethod
    def transfer_pending_requests(user_id: int, target_username: str) -> list[tuple[int, str]]:
        """
        Transfer pending requests to the 'contact_requests' table and delete them from the 'pending_requests' table.

        Args:
            user_id (int): The ID of the user receiving the pending requests.
            target_username (str): The username associated with the pending requests.

        Returns:
            list[int]: A list of requester IDs whose requests were transferred.
        """
        with get_db_cursor(commit=True) as cur:
            cur.execute("SELECT requester_id, tag FROM pending_requests WHERE target_username = %s",
                        (target_username,))
            pending_requests = cur.fetchall()
            for requester_id, tag in pending_requests:
                cur.execute(
                    "INSERT INTO contact_requests (user_id, requester_id, requester_tag) VALUES (%s, %s, %s)",
                    (user_id, requester_id, tag))
            if len(pending_requests) > 0:
                cur.execute("DELETE FROM pending_requests WHERE target_username = %s", (target_username,))
            return pending_requests if pending_requests else []

    # -- Bug Report-related methods -----------------------------------------------------
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
        with get_db_cursor(commit=True) as cur:
            cur.execute("INSERT INTO bug_reports (user_id, username, content) VALUES (%s, %s, %s) RETURNING id",
                        (user_id, username, message))
            report_id = cur.fetchone()[0]
            return report_id if report_id else 0


    # -- Check Queue-related methods -----------------------------------------------------
    @staticmethod
    def get_check_queue_items() -> list[tuple[int, datetime.time, str, int, int]]:
        """
        Retrieves all checks from the check queue.

        Queries the check_queue table to get all queued checks.

        Returns:
            list[tuple[int, datetime.time, str, int, int]]: A list of tuples, each containing:
                - user ID (int)
                - time of the check (datetime.time)
                - description of the check (str)
                - reminder count (int)
                - waiting time (int)
        """
        with get_db_cursor() as cur:
            cur.execute("""
                    SELECT user_id, time, description, reminder_count, waiting_time
                    FROM check_queue
                """)
            queue_items = cur.fetchall()
            return queue_items if queue_items else []

    @staticmethod
    def update_check_queue_property(user_id: int, key: str, value: int) -> None:
        """
        Updates a specific property of a user's check queue entry.

        Allows updating any integer field in the check_queue table
        for the given user based on the provided key.

        Parameters:
            user_id (int): The ID of the user.
            key (str): The name of the field to be updated.
            value (int): The new value to be set for the specified field.
        """
        with get_db_cursor(commit=True) as cur:
            cur.execute(f"UPDATE check_queue SET {key} = %s WHERE user_id = %s", (value, user_id))

    @staticmethod
    def add_check_queue_item(user_id: int, time: datetime.time, desc: str, waiting_time: int) -> None:
        """
        Initializes a check queue entry for a user.

        Inserts a new entry into the check_queue table with the given user ID,
        time, description, and waiting time. The reminder_count is set to 0 by default.

        Parameters:
            user_id (int): The ID of the user.
            time (datetime.time): The time associated with the check.
            desc (str): The description of the check.
            waiting_time (int): The waiting time before the next reminder.
        """
        with get_db_cursor(commit=True) as cur:
            cur.execute("""
                INSERT INTO check_queue (user_id, time, description, reminder_count, waiting_time)
                VALUES (%s, %s, %s, 0, %s)
            """, (user_id, time,desc, waiting_time))

    @staticmethod
    def delete_check_queue_item(user_id: int) -> None:
        """
        Deletes a user's check queue entry.

        Removes the entry from the check_queue table for the specified user.

        Parameters:
            user_id (int): The ID of the user whose check queue entry should be deleted.
        """
        with get_db_cursor(commit=True) as cur:
            cur.execute("DELETE FROM check_queue WHERE user_id = %s", (user_id,))