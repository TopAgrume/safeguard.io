import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from contextlib import contextmanager
from utils.init_database import init_database

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
    time1_obj = datetime.strptime(time1['time'], '%H:%M')
    time2_obj = datetime.strptime(time2['time'], '%H:%M')

    # Calculate the difference in minutes
    difference_in_minutes = (time2_obj - time1_obj).total_seconds() / 60

    return abs(difference_in_minutes) < MAX_TIME_DIFF


def add_user_and_link_request(user_id: int, username: str, current_dict: list, value: list):
    special_action = []
    related_user_id = AccessEnv.on_get_user_usernames_id()

    for new_contact in value:
        if any(contact['tag'] == new_contact for contact in current_dict):
            continue

        if new_contact in list(related_user_id.keys()):
            new_contact_id = related_user_id[new_contact]
            current_dict.append({"id": int(new_contact_id), "tag": new_contact, "pair": False})

            # Write in destination contact_request
            request_dict = AccessEnv.read_user_properties(int(new_contact_id), "contact_request")
            request_dict[str(user_id)] = username
            AccessEnv.update_user_properties(int(new_contact_id), "contact_request", request_dict)

            # Actions to take
            pair_asking = {"id": int(new_contact_id), "tag": new_contact}
            special_action.append(pair_asking)
            continue

        current_dict.append({"id": None, "tag": new_contact, "pair": False})

        # Save the data
        pair_asking = {"tag": username, "dest_tags": [new_contact]}
        for origin_id, content in AccessEnv.on_get_request_user("items"):
            if origin_id == str(user_id):
                content['dest_tags'].append(new_contact)
                AccessEnv.on_write_request(origin_id, 'dest_tags', content['dest_tags'])
                break
        else:
            AccessEnv.on_init_request(str(user_id), pair_asking)

    return current_dict, special_action


def delete_user_and_request(user_id: int, current_dict: list, value: list):
    filtered_dict = []
    print(current_dict)
    for contact in current_dict:
        if contact['tag'] not in value:
            filtered_dict.append(contact)
            continue

        user_tag = contact['id']
        if user_tag is None:
            dest_tags = AccessEnv.on_read_request(user_id, "dest_tags")
            dest_tags.remove(contact['tag'])
            if len(dest_tags) == 0:
                request_contacts: dict = AccessEnv.on_get_request_user("dict")
                del request_contacts[str(user_id)]
                AccessEnv.on_write_all_request(request_contacts)
            else:
                AccessEnv.on_write_request(str(user_id), "dest_tags", dest_tags)
            continue

        contact_request = AccessEnv.read_user_properties(user_tag, "contact_request")
        if str(user_id) in contact_request:
            del contact_request[str(user_id)]
            AccessEnv.update_user_properties(user_tag, "contact_request", contact_request)
    print("test")
    return filtered_dict

        
class AccessEnv(object):
    users: dict = {}

    @staticmethod # VALID
    def update_user_properties(user_id: int, key: str = None, value=None) -> None:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(f"UPDATE users SET {key} = %s WHERE id = %s", (json.dumps(value) if isinstance(value, (dict, list)) else value, user_id))
            conn.commit()


    @staticmethod
    def on_write_contacts(user_id: int, username: str, method: str = None, value: list = None):
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT contacts FROM users WHERE id = %s", (user_id,))
                user = cur.fetchone()
                if user:
                    current_contacts = user['contacts'] or []
                    special_action = []

                    if method == 'add':
                        for new_contact in value:
                            if any(contact['tag'] == new_contact for contact in current_contacts):
                                continue
                            cur.execute("SELECT id FROM users WHERE username = %s", (new_contact,))
                            contact_user = cur.fetchone()
                            if contact_user:
                                current_contacts.append({"id": contact_user['id'], "tag": new_contact, "pair": False})
                                cur.execute("UPDATE users SET contact_request = contact_request || %s WHERE id = %s",
                                            (json.dumps({str(user_id): username}), contact_user['id']))
                                special_action.append({"id": contact_user['id'], "tag": new_contact})
                            else:
                                current_contacts.append({"id": None, "tag": new_contact, "pair": False})
                    elif method == 'del':
                        current_contacts = [contact for contact in current_contacts if contact['tag'] not in value]

                    cur.execute("UPDATE users SET contacts = %s WHERE id = %s", (json.dumps(current_contacts), user_id))
                conn.commit()
                return special_action

    @staticmethod
    def on_write_verifications(user_id: int, method: str = None, value: list = None, skip_check: bool = False):
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT daily_message FROM users WHERE id = %s", (user_id,))
                user = cur.fetchone()
                if user:
                    current_verifications = user['daily_message'] or []
                    not_valid = []

                    if method == 'add':
                        for new_check in value:
                            if any(daily_message['time'] == new_check['time'] for daily_message in current_verifications):
                                continue
                            if not skip_check and any(less_than_one_hour(daily_message, new_check) for daily_message in current_verifications):
                                not_valid.append(new_check['time'])
                                continue
                            current_verifications.append(new_check)
                    elif method == 'del':
                        current_verifications = [check for check in current_verifications if check["time"] not in value]
                    elif method in ('skip', 'undoskip'):
                        for check in current_verifications:
                            if check["active"] is None:
                                continue
                            if check["time"] in value:
                                check["active"] = (method == 'undoskip')

                    cur.execute("UPDATE users SET daily_message = %s WHERE id = %s", (json.dumps(current_verifications), user_id))
                conn.commit()
                return not_valid

    @staticmethod # VALID
    def user_information(user_id: int):
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT response_message, alert_mode FROM users WHERE id = %s", (user_id,))
                user = cur.fetchone()
                return user['response_message'], user['alert_mode'] if user else (None, None)


    @staticmethod # VALID
    def read_user_properties(user_id: int, key: str):
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(f"SELECT {key} FROM users WHERE id = %s", (user_id,))
                user = cur.fetchone()
                return user[key] if user else None

    @staticmethod # VALID
    def user_already_registered(user_id: int) -> bool:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT id FROM users WHERE id = %s", (user_id,))
                users = cur.fetchall()
                return bool(users)

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
                    INSERT INTO users (id, username, alert_mode, response_message, state, contacts, daily_message, contact_request)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (user_id, username, False, True, '', '[]', '[]', '{}'))
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
        base_dict = AccessEnv.on_update("data/queue.json")
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
        base_dict = AccessEnv.on_update("data/queue.json")

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
        AccessEnv.on_kill_data(user_id, file_path)

    @staticmethod
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

    @staticmethod
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