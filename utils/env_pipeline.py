from twilio.rest import Client
from datetime import datetime

import logging
import os
import json

MAX_TIME_DIFF = 60


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
            request_dict = AccessEnv.on_read(int(new_contact_id), "contact_request")
            request_dict[str(user_id)] = username
            AccessEnv.on_write(int(new_contact_id), "contact_request", request_dict)

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

        contact_request = AccessEnv.on_read(user_tag, "contact_request")
        if str(user_id) in contact_request:
            del contact_request[str(user_id)]
            AccessEnv.on_write(user_tag, "contact_request", contact_request)
    print("test")
    return filtered_dict


class AccessEnv(object):
    users: dict = {}

    @staticmethod
    def on_write(user_id: int, key: str = None, value=None) -> None:
        base_dict = AccessEnv.on_update()

        # Write contacts to a JSON file
        if key is not None:
            base_dict[str(user_id)][key] = value

        with open('data/data.json', 'w') as json_file:
            json.dump(base_dict, json_file, indent=4)

    @staticmethod
    def on_write_contacts(user_id: int, username: str, method: str = None, value: list = None):
        base_dict = AccessEnv.on_update()
        special_action = []
        current_dict = base_dict[str(user_id)]['contacts']

        if method == 'add':
            current_dict, special_action = add_user_and_link_request(user_id, username, current_dict, value)
        elif method == 'del':
            current_dict = delete_user_and_request(user_id, current_dict, value)

        base_dict = AccessEnv.on_update()
        base_dict[str(user_id)]['contacts'] = current_dict
        with open('data/data.json', 'w') as json_file:
            json.dump(base_dict, json_file, indent=4)

        return special_action

    @staticmethod
    def on_write_verifications(user_id: int, method: str = None, value: list = None, skip_check: bool = False) -> None:
        base_dict = AccessEnv.on_update()

        # Write verifications to a JSON file
        current_dict = base_dict[str(user_id)]['daily_message']

        if method == 'add':
            for new_checks in value:
                if any(daily_message['time'] == new_checks['time'] for daily_message in current_dict):
                    continue

                if not skip_check:
                    if any(less_than_one_hour(daily_message, new_checks) for daily_message in current_dict):
                        continue

                current_dict.append(new_checks)
        elif method == 'del':
            current_dict = [dail_check for dail_check in current_dict if dail_check["time"] not in value]
        elif method in ('skip', 'undoskip'):
            for dail_check in current_dict:
                if dail_check["time"] in value:
                    dail_check["active"] = (method == 'undoskip')

        base_dict[str(user_id)]['daily_message'] = current_dict
        with open('data/data.json', 'w') as json_file:
            json.dump(base_dict, json_file, indent=4)

    @staticmethod
    def on_read(user_id: int, key: str = None):
        # Open and read a JSON file
        with open('data/data.json', 'r') as json_file:
            data = json.load(json_file)[str(user_id)]

        if key is None:
            return data["response_message"], data["alert_mode"]
        else:
            return data[key]

    @staticmethod
    def on_get_users(method: str = "keys"):
        # Open and read a JSON file
        with open('data/data.json', 'r') as json_file:
            data = json.load(json_file)

        if method == "keys":
            return list(data.keys())
        return list(data.items())

    @staticmethod
    def on_get_user_id_usernames():
        # Open and read a JSON file
        with open('data/data.json', 'r') as json_file:
            data = json.load(json_file)

        user_id_to_username = {}
        for user_id, data in data.items():
            username = data.get('username', '')
            user_id_to_username[user_id] = username

        return user_id_to_username

    @staticmethod
    def on_get_user_usernames_id():
        # Open and read a JSON file
        with open('data/data.json', 'r') as json_file:
            data = json.load(json_file)

        user_username_to_id = {}
        for user_id, data in data.items():
            username = data.get('username', '')
            user_username_to_id[username] = user_id

        return user_username_to_id

    @staticmethod
    def on_update(file_path: str = "data/data.json"):
        # Check if the file exists
        if not os.path.exists(file_path):
            with open(file_path, 'w') as file:
                json.dump({}, file, indent=4)

        with open(file_path, 'r') as json_file:
            return json.load(json_file)

    @staticmethod
    def on_kill_data(user_id: int, file_path: str = "data/data.json") -> None:
        with open(file_path, 'r') as json_file:
            dict_users: dict = json.load(json_file)

        del dict_users[str(user_id)]
        with open(file_path, 'w') as json_file:
            json.dump(dict_users, json_file, indent=4)

    @staticmethod
    def on_create_user(user_id: int, username: str) -> None:
        fresh_data: dict = {
            'alert_mode': False,
            'response_message': True,
            'state': '',
            'username': username,
            'contacts': [],
            'daily_message': [],
            'contact_request': {}
        }

        base_dict = AccessEnv.on_update()
        base_dict[str(user_id)] = fresh_data
        with open('data/data.json', 'w') as json_file:
            json.dump(base_dict, json_file, indent=4)

    @staticmethod
    def telegram_keys() -> tuple[str, str]:
        API_TOKEN = os.getenv('TOKEN')
        BOT_USERNAME = os.getenv('BOT_USERNAME')
        if not API_TOKEN or not BOT_USERNAME:
            raise ValueError("One or more keys required environment variables are missing.")
        return API_TOKEN, BOT_USERNAME

    @staticmethod
    def client() -> Client:
        account_sid = os.getenv('account_sid')
        auth_token = os.getenv('auth_token')
        if not account_sid or not auth_token:
            raise ValueError("One or more keys required environment variables are missing.")
        return Client(account_sid, auth_token)

    @staticmethod
    def contacts() -> tuple[str, str, str]:
        server_number = os.getenv('server_number')
        client_number = os.getenv('client_number')
        emergency_number = os.getenv('emergency_number')
        if not server_number or not client_number or not emergency_number:
            raise ValueError("One or more contacts required environment variables are missing.")
        return server_number, client_number, emergency_number

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
        return list(data.items())

    @staticmethod
    def on_kill_queue_data(user_id: int, file_path: str = "data/queue.json") -> None:
        AccessEnv.on_kill_data(user_id, file_path)

    @staticmethod
    def on_get_request_user(method: str = "keys"):
        with open('data/request.json', 'r') as json_file:
            data = json.load(json_file)

        if method == "keys":
            return list(data.keys)
        if method == "dict":
            return data
        return list(data.items())

    @staticmethod
    def on_init_request(user_id: str, daily_check: dict):
        base_dict = AccessEnv.on_update("data/request.json")
        base_dict[user_id] = daily_check

        with open('data/request.json', 'w') as json_file:
            json.dump(base_dict, json_file, indent=4)

    @staticmethod
    def on_write_request(user_id: str, key: str = None, value=None) -> None:
        base_dict = AccessEnv.on_update("data/request.json")

        # Write contacts to a JSON file
        if key is not None:
            base_dict[str(user_id)][key] = value
        else:
            base_dict[str(user_id)][key] = value

        with open("data/request.json", 'w') as json_file:
            json.dump(base_dict, json_file, indent=4)

    @staticmethod
    def on_write_all_request(all_data: dict) -> None:
        with open("data/request.json", 'w') as json_file:
            json.dump(all_data, json_file, indent=4)

    @staticmethod
    def on_read_request(user_id: int, key: str = None):
        # Open and read a JSON file
        with open('data/request.json', 'r') as json_file:
            data = json.load(json_file)[str(user_id)]

        return data[key]

    @staticmethod
    def on_kill_request(user_id: int, file_path: str = "data/request.json") -> None:
        AccessEnv.on_kill_data(user_id, file_path)

    @staticmethod
    def emergencies() -> str:
        emergency_number = os.getenv('emergency_number')
        if not emergency_number:
            raise ValueError("emergency numbers are missing.")
        return emergency_number

    @staticmethod
    def logger(logger_name: str):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        return logging.getLogger(logger_name)
