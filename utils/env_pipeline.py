from twilio.rest import Client
import logging
import os
import json
from datetime import datetime


class AccessEnv(object):
    users: dict = {}

    @staticmethod
    def on_write(user_id: int, key: str = None, value=None) -> None:
        AccessEnv.on_reset()

        # Write contacts to a JSON file
        if key is not None:
            AccessEnv.users[str(user_id)][key] = value

        with open('data/data.json', 'w') as json_file:
            json.dump(AccessEnv.users, json_file, indent=4)

    @staticmethod
    def on_write_contacts(user_id: int, method: str = None, value: list = None) -> None:
        AccessEnv.on_reset()

        # Write contacts to a JSON file
        current_dict = AccessEnv.users[str(user_id)]['contacts']
        related_user_id = AccessEnv.on_get_user_usernames_id()
        if method == 'add':
            for new_contact in value:
                if any(contact['tag'] == new_contact for contact in current_dict):
                    continue

                if new_contact in related_user_id:
                    current_dict.append({"id": int(related_user_id[new_contact]), "tag": new_contact, "pair": False})
                    # TODO ask for pairing
                    continue

                current_dict.append({"id": None, "tag": new_contact, "pair": False})
                # TODO save for future pairing

        elif method == 'del':
            current_dict = [contact for contact in current_dict if contact['tag'] not in value]

        AccessEnv.users[str(user_id)]['contacts'] = current_dict
        with open('data/data.json', 'w') as json_file:
            json.dump(AccessEnv.users, json_file, indent=4)

    @staticmethod
    def less_than_one_hour(time1: dict, time2: dict): # TODO move into utils function
        # Convert time strings to datetime objects
        format_str = '%H:%M'
        time1_obj = datetime.strptime(time1['time'], format_str)
        time2_obj = datetime.strptime(time2['time'], format_str)

        # Calculate the difference in minutes
        difference_in_minutes = (time2_obj - time1_obj).total_seconds() / 60

        # Check if the difference is less than one hour (60 minutes)
        return abs(difference_in_minutes) < 60

    @staticmethod
    def on_write_verifications(user_id: int, method: str = None, value: list = None, skip_check: bool = False) -> None:
        AccessEnv.on_reset()

        # Write verifications to a JSON file
        current_dict = AccessEnv.users[str(user_id)]['daily_message']

        if method == 'add': #TODO check  compatibility between times
            for new_checks in value:
                if any(daily_message['time'] == new_checks['time'] for daily_message in current_dict):
                    continue

                if not skip_check:
                    if any(AccessEnv.less_than_one_hour(daily_message, new_checks) for daily_message in current_dict):
                        continue

                current_dict.append(new_checks)
        elif method == 'del':
            current_dict = [dail_check for dail_check in current_dict if dail_check["time"] not in value]
        elif method in ('skip', 'undoskip'):
            for dail_check in current_dict:
                if dail_check["time"] in value:
                    dail_check["active"] = (method == 'undoskip')

        AccessEnv.users[str(user_id)]['daily_message'] = current_dict
        with open('data/data.json', 'w') as json_file:
            json.dump(AccessEnv.users, json_file, indent=4)

    @staticmethod
    def on_read(user_id: int, key: str = None):
        # Open and read a JSON file
        with open('data/data.json', 'r') as json_file:
            data = json.load(json_file)[str(user_id)]

        if key is None:
            return data["response_message"], data["alert_mode"], data["reminder_count"]
        else:
            return data[key]

    @staticmethod
    def on_get_users():
        # Open and read a JSON file
        with open('data/data.json', 'r') as json_file:
            data = json.load(json_file)

        return list(data.keys())

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
    def on_reset() -> None:
        file_path = "data/data.json"

        # Check if the file exists
        if not os.path.exists(file_path):
            with open(file_path, 'w') as file:
                json.dump({}, file, indent=4)

        with open(file_path, 'r') as json_file:
            AccessEnv.users = json.load(json_file)

    @staticmethod
    def on_create_user(user_id: int, username: str) -> None:
        fresh_data: dict = {
            'alert_mode': False,
            'response_message': False,
            'reminder_count': 0,
            'state': '',
            'username': username,
            'contacts': [],
            'daily_message': [],
        }

        AccessEnv.users[str(user_id)] = fresh_data
        with open('data/data.json', 'w') as json_file:
            json.dump(AccessEnv.users, json_file, indent=4)

    @staticmethod
    def telegram_keys() -> tuple[str, str]:
        API_TOKEN = os.getenv('TOKEN')
        BOT_USERNAME = os.getenv('BOT_USERNAME')
        if not API_TOKEN or not BOT_USERNAME:
            raise ValueError("One or more keys required environment variables are missing.")
        return API_TOKEN, BOT_USERNAME

    @staticmethod
    def get_demo() -> int:
        my_id = os.getenv('me')
        if not my_id:
            raise ValueError("My telegram id is missing")
        return int(my_id)

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
