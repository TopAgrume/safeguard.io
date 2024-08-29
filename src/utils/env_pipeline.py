import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from contextlib import contextmanager
from src.utils.init_database import init_database

init_database()
MAX_TIME_DIFF = 20

# Database connection parameters
DB_PARAMS = {
    "dbname": "postgres",
    "user": "postgres",
    "password": "postgres",
    "host": "localhost",
    "port": "5432"
}

@contextmanager
def get_db_connection():
    conn = psycopg2.connect(**DB_PARAMS)
    try:
        yield conn
    finally:
        conn.close()

def less_than_one_hour(time1: dict, time2: dict):
    # Convert time strings to datetime objects
    time1_obj = time1['time']
    time2_obj = datetime.strptime(time2['time'], '%H:%M').time()

    # Calculate the difference in minutes
    difference_in_minutes = abs(time1_obj.hour - time2_obj.hour) * 60 + abs(time1_obj.minute - time2_obj.minute)

    return abs(difference_in_minutes) < MAX_TIME_DIFF

# TODO
def add_user_and_link_request(user_id: int, username: str, current_dict: list, value: list):
    special_action = []
    related_user_id = RequestManager.on_get_user_usernames_id()

    for new_contact in value:
        if any(contact['tag'] == new_contact for contact in current_dict):
            continue

        if new_contact in list(related_user_id.keys()):
            new_contact_id = related_user_id[new_contact]
            current_dict.append({"id": int(new_contact_id), "tag": new_contact, "pair": False})

            # Write in destination contact_request
            request_dict = RequestManager.read_contact_requests_properties(int(new_contact_id))
            request_dict[str(user_id)] = username
            RequestManager.update_user_properties(int(new_contact_id), "contact_request", request_dict)

            # Actions to take
            pair_asking = {"id": int(new_contact_id), "tag": new_contact}
            special_action.append(pair_asking)
            continue

        current_dict.append({"id": None, "tag": new_contact, "pair": False})

        # Save the data
        pair_asking = {"tag": username, "dest_tags": [new_contact]}
        for origin_id, content in RequestManager.on_get_request_user("items"): #TODO
            if origin_id == str(user_id):
                content['dest_tags'].append(new_contact)
                RequestManager.on_write_request(origin_id, 'dest_tags', content['dest_tags'])
                break
        else:
            RequestManager.on_init_request(str(user_id), pair_asking)

    return current_dict, special_action

# TODO
def delete_user_and_request(user_id: int, current_dict: list, value: list):
    filtered_dict = []
    print(current_dict)
    for contact in current_dict:
        if contact['tag'] not in value:
            filtered_dict.append(contact)
            continue

        user_tag = contact['id']
        if user_tag is None:
            dest_tags = RequestManager.on_read_request(user_id, "dest_tags")
            dest_tags.remove(contact['tag'])
            if len(dest_tags) == 0:
                request_contacts: dict = RequestManager.on_get_request_user("dict") #TODO
                del request_contacts[str(user_id)]
                RequestManager.on_write_all_request(request_contacts)
            else:
                RequestManager.on_write_request(str(user_id), "dest_tags", dest_tags)
            continue

        contact_request = RequestManager.read_contact_requests_properties(user_tag)
        if str(user_id) in contact_request:
            del contact_request[str(user_id)]
            RequestManager.update_user_properties(user_tag, "contact_request", contact_request)
    print("test")
    return filtered_dict

        
class RequestManager(object):
    users: dict = {}

    @staticmethod # TODO only user attributes
    def update_user_properties(user_id: int, key: str, value: str | bool) -> None:
        """
        Update a specific property of a user in the 'users' table.

        Args:
            user_id (int): The ID of the user whose property is to be updated.
            key (str): The column name in the 'users' table to update.
            value (str | bool): The new value for the property.

        Returns:
            None
        """
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(f"UPDATE users SET {key} = %s WHERE id = %s", (value, user_id))
            conn.commit()

    @staticmethod  # VALID
    def update_contacts_properties(user_id: int, key: str, value: int | bool) -> None:
        """
        Update a specific property of a contact in the 'contacts' table.

        Args:
            user_id (int): The ID of the user who owns the contact.
            key (str): The column name in the 'contacts' table to update.
            value (int | bool): The new value for the property.

        Returns:
            None
        """
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(f"UPDATE contacts SET {key} = %s WHERE user_id = %s", (value, user_id))
            conn.commit()

    @staticmethod  # VALID
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
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                notifications = []
                for target_username in target_usernames:
                    cur.execute("SELECT id FROM users WHERE username = %s", (target_username,))
                    contact_user = cur.fetchone()

                    if contact_user:
                        # Check if contact already exists
                        cur.execute("SELECT * FROM contacts WHERE user_id = %s AND contact_id = %s", (user_id, contact_user['id']))
                        if not cur.fetchone():
                            # Add to contacts table
                            cur.execute("""
                                    INSERT INTO contacts (user_id, contact_id, tag, pair) 
                                    VALUES (%s, %s, %s, FALSE)
                                    ON CONFLICT (user_id, contact_id, tag) DO NOTHING
                                """, (user_id, contact_user['id'], target_username))

                            # Add to contact_requests table
                            cur.execute("""
                                    INSERT INTO contact_requests (user_id, requester_id, requester_tag) 
                                    VALUES (%s, %s, %s)
                                    ON CONFLICT (user_id, requester_id) DO NOTHING
                                """, (contact_user['id'], user_id, username))

                            notifications.append({"id": contact_user['id'], "tag": target_username})
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
                conn.commit()
                return notifications

    @staticmethod  # VALID
    def del_contacts(user_id: int, target_usernames: list[str]) -> None:
        """
        Delete contacts from the user's contact list.

        Args:
            user_id (int): The ID of the user from whom contacts will be deleted.
            target_usernames (list[str]): A list of usernames to delete from the contacts.

        Returns:
            None
        """
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                for contact_tag in target_usernames:
                    cur.execute("DELETE FROM contacts WHERE user_id = %s AND tag = %s", (user_id, contact_tag))
                conn.commit()

    @staticmethod  # VALID
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
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                not_valid = []
                for verification in new_verifications:
                    cur.execute("SELECT time, description, active FROM daily_messages WHERE user_id = %s",(user_id,))
                    current_verifications = cur.fetchall()

                    if any(v['time'] == verification['time'] for v in current_verifications):
                        continue
                    if not skip_check and any(less_than_one_hour(v, verification) for v in current_verifications):
                        not_valid.append(verification['time'])
                        continue
                    cur.execute(
                        "INSERT INTO daily_messages (user_id, time, description, active) VALUES (%s, %s, %s, %s)",
                        (user_id, verification['time'], verification['description'], verification['active']))

                conn.commit()
                return not_valid

    @staticmethod  # VALID
    def del_verifications(user_id: int, times_to_delete: list) -> None:
        """
        Delete specific verifications for a user.

        Args:
            user_id (int): The ID of the user from whom verifications will be deleted.
            times_to_delete (list): A list of times specifying which verifications to delete.

        Returns:
            None
        """
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM daily_messages WHERE user_id = %s AND time = ANY(%s::time[])",
                            (user_id, times_to_delete))
                conn.commit()

    @staticmethod #VALID
    def update_verification_status(user_id: int, times_to_update: list, active: bool) -> None:
        """
        Update the status of specific verifications for a user.

        Args:
            user_id (int): The ID of the user whose verification statuses are being updated.
            times_to_update (list): A list of times specifying which verifications to update.
            active (bool): The new status for the verifications (active or inactive).

        Returns:
            None
        """
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE daily_messages SET active = %s WHERE user_id = %s AND time = ANY(%s::time[])",
                            (active, user_id, times_to_update))
                conn.commit()

    @staticmethod #VALID
    def skip_verifications(user_id: int, times_to_skip: list) -> None:
        """
        Mark specific verifications as skipped (inactive).

        Args:
            user_id (int): The ID of the user whose verifications are being skipped.
            times_to_skip (list): A list of times specifying which verifications to skip.

        Returns:
            None
        """
        RequestManager.update_verification_status(user_id, times_to_skip, False)


    @staticmethod #VALID
    def undoskip_verifications(user_id: int, times_to_undoskip: list) -> None:
        """
        Revert the status of specific verifications to active.

        Args:
            user_id (int): The ID of the user whose verifications are being reverted.
            times_to_undoskip (list): A list of times specifying which verifications to reactivate.

        Returns:
            None
        """
        RequestManager.update_verification_status(user_id, times_to_undoskip, True)


    @staticmethod # VALID
    def user_information(user_id: int) -> tuple[bool, bool]:
        """
        Retrieve specific information about a user.

        Args:
            user_id (int): The ID of the user whose information is being retrieved.

        Returns:
            tuple: A tuple containing the response message and alert mode for the user, or (None, None) if the user is not found.
        """
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT response_message, alert_mode FROM users WHERE id = %s", (user_id,))
                user = cur.fetchone()
                return (user['response_message'], user['alert_mode']) if user else (None, None)


    @staticmethod # VALID
    def read_user_properties(user_id: int, key: str) -> str | bool:
        """
        Read a specific property of a user from the 'users' table.

        Args:
            user_id (int): The ID of the user whose property is being read.
            key (str): The column name in the 'users' table to retrieve.

        Returns:
            str | bool: The value of the specified property for the user, or None if the user is not found.
        """
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(f"SELECT {key} FROM users WHERE id = %s", (user_id,))
                user = cur.fetchone()
                return user[key] if user else None

    @staticmethod  # VALID
    def read_contact_requests_properties(user_id: int) -> list[tuple[int, str]]:
        """
        Retrieve the contact requests for a user.

        Args:
            user_id (int): The ID of the user whose contact requests are being retrieved.

        Returns:
            list[tuple[int, str]]: A list of tuples containing the requester ID and requester tag for each contact request.
        """
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(f"SELECT requester_id, requester_tag FROM contact_requests WHERE user_id = %s", (user_id,))
                requesters_info = cur.fetchone()
                return [(requester['requester_id'], requester['requester_tag']) for requester in requesters_info] if requesters_info else []

    @staticmethod  # VALID
    def read_contacts_properties(user_id: int) -> list[tuple[int, str, bool]]:
        """
        Retrieve the contact information for a user.

        Args:
            user_id (int): The ID of the user whose contacts are being retrieved.

        Returns:
            list[tuple[int, str, bool]]: A list of tuples containing the contact ID, tag, and pair status for each contact.
        """
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(f"SELECT contact_id, tag, pair FROM contacts WHERE user_id = %s", (user_id,))
                contacts = cur.fetchall()
                return [(contact['contact_id'], contact['tag'], contact['pair']) for contact in contacts] if contacts else []

    @staticmethod  # VALID
    def read_verifications_properties(user_id: int) -> list[tuple[str, str, bool]]:
        """
        Retrieve the verifications for a user.

        Args:
            user_id (int): The ID of the user whose verifications are being retrieved.

        Returns:
            list: A list of tuples containing the time, description, and active status for each verification.
        """
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(f"SELECT time, description, active FROM daily_messages WHERE user_id = %s", (user_id,))
                verifications = cur.fetchall()
                return [(verif['time'], verif['description'], verif['active']) for verif in verifications] if verifications else []

    @staticmethod # VALID
    def user_already_registered(user_id: int) -> bool:
        """
        Check if a user is already registered in the 'users' table.

        Args:
            user_id (int): The ID of the user to check.

        Returns:
            bool: True if the user is registered, False otherwise.
        """
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT id FROM users WHERE id = %s", (user_id,))
                users = cur.fetchall()
                return bool(users)

    @staticmethod # VALID
    def write_bug_report(user_id: int, username: str, message: str) -> int:
        """
        Write a bug report for a user.

        Args:
            user_id (int): The ID of the user submitting the bug report.
            username (str): The username of the user submitting the bug report.
            message (str): The content of the bug report.

        Returns:
            int: The ID of the newly created bug report.
        """
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("INSERT INTO bug_reports (user_id, username, content) VALUES (%s, %s, %s) RETURNING id",
                            (user_id, username, message))
                report_id = cur.fetchone()['id']
            conn.commit()
            return report_id






    @staticmethod
    def on_get_users():
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT id, username FROM users")
                users = cur.fetchall()
                return [(str(user['id']), user) for user in users]

    @staticmethod # TODO
    def username_from_user_id():
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT id, username FROM users")
                users = cur.fetchall()
                return {str(user['id']): user['username'] for user in users}

    @staticmethod # TODO
    def on_get_user_usernames_id():
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT id, username FROM users")
                users = cur.fetchall()
                return {user['username']: str(user['id']) for user in users}

    @staticmethod # VALID
    def on_kill_data(user_id: int, file_path: str = "data/data.json") -> None:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
            conn.commit()

    @staticmethod # VALID
    def on_create_user(user_id: int, username: str) -> None:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO users (id, username, alert_mode, response_message, state)
                    VALUES (%s, %s, %s, %s, %s)
                """, (user_id, username, False, True, ''))
            conn.commit()

    @staticmethod
    def telegram_keys() -> tuple[str, str]:
        API_TOKEN = os.getenv('TOKEN')
        BOT_USERNAME = os.getenv('BOT_USERNAME')
        if not API_TOKEN or not BOT_USERNAME:
            raise ValueError("One or more keys required environment variables are missing.")
        return API_TOKEN, BOT_USERNAME


    @staticmethod
    def on_init_check_queue(user_id: str, daily_check: dict, waiting_time: int):
        base_dict = RequestManager.on_update("data/queue.json")
        base_dict[user_id] = {
            "time": daily_check['time'],
            "desc": daily_check['desc'],
            'reminder_count': 0,
            'waiting_time': waiting_time
        }

        with open('data/queue.json', 'w') as json_file:
            json.dump(base_dict, json_file, indent=4)

    @staticmethod
    def on_write_check_queue(user_id: str, key: str = None, value=None) -> None:
        base_dict = RequestManager.on_update("data/queue.json")

        # Write contacts to a JSON file
        if key is not None:
            base_dict[str(user_id)][key] = value

        with open("data/queue.json", 'w') as json_file:
            json.dump(base_dict, json_file, indent=4)

    @staticmethod
    def on_read_check_queue(user_id: int, key: str = None):
        # Open and read a JSON file
        with open('data/queue.json', 'r') as json_file:
            data = json.load(json_file)[str(user_id)]

        return data[key]

    @staticmethod
    def on_get_check_users(method: str):
        # Open and read a JSON file
        with open('data/queue.json', 'r') as json_file:
            data: dict = json.load(json_file)

        if method == "keys":
            return list(data.keys())
        if method == "dict":
            return data
        return list(data.items())

    @staticmethod
    def on_kill_queue_data(user_id: int, file_path: str = "data/queue.json") -> None:
        RequestManager.on_kill_data(user_id, file_path)

    @staticmethod # TODO
    def on_get_request_user(method: str = "keys"):
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT id, contact_request FROM users WHERE contact_request != '{}'")
                users = cur.fetchall()
                if method == "keys":
                    return [str(user['id']) for user in users]
                elif method == "dict":
                    return {str(user['id']): user['contact_request'] for user in users}
                return [(str(user['id']), user['contact_request']) for user in users]

    @staticmethod # VALID
    def transfer_pending_requests(user_id: int, target_username: str):
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT requester_id, tag FROM pending_requests WHERE target_username = %s", (target_username,))
                pending_requests = cur.fetchall()
                for contact_request in pending_requests:
                    cur.execute("INSERT INTO contact_requests (user_id, requester_id, requester_tag) VALUES (%s, %s, %s)",
                                (user_id, contact_request['requester_id'], contact_request['tag']))
                if len(pending_requests) > 0:
                    cur.execute("DELETE FROM pending_requests WHERE target_username = %s", (target_username,))
            conn.commit()
            return [contact_request['requester_id'] for contact_request in pending_requests]

    @staticmethod
    def on_init_request(user_id: str, daily_check: dict):
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE users SET contact_request = %s WHERE id = %s", (json.dumps(daily_check), int(user_id)))
            conn.commit()

    @staticmethod
    def on_write_request(user_id: str, key: str = None, value=None) -> None:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT contact_request FROM users WHERE id = %s", (int(user_id),))
                user = cur.fetchone()
                if user:
                    contact_request = user['contact_request']
                    if key is not None:
                        contact_request[key] = value
                    else:
                        contact_request = value
                    cur.execute("UPDATE users SET contact_request = %s WHERE id = %s", (json.dumps(contact_request), int(user_id)))
            conn.commit()

    @staticmethod #TODO add pending requests to the user requests
    def on_write_all_request(all_data: dict) -> None:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                for user_id, request_data in all_data.items():
                    cur.execute("UPDATE users SET contact_request = %s WHERE id = %s", (json.dumps(request_data), int(user_id)))
            conn.commit()

    @staticmethod
    def on_read_request(user_id: int, key: str = None):
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT contact_request FROM users WHERE id = %s", (user_id,))
                user = cur.fetchone()
                if user and user['contact_request']:
                    return user['contact_request'].get(key)

    @staticmethod
    def on_kill_request(user_id: int, file_path: str = "data/request.json") -> None:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE users SET contact_request = '{}' WHERE id = %s", (user_id,))
            conn.commit()