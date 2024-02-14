from typing import Tuple

from twilio.rest import Client
import logging
import os
import json


class AccessEnv(object):
    users: dict = {}

    @staticmethod
    def on_write(user_id: int, key: str = None, value=None) -> None:
        # Write contacts to a JSON file
        if key is not None:
            AccessEnv.users[str(user_id)][key] = value

        with open('data/data.json', 'w') as json_file:
            json.dump(AccessEnv.users, json_file, indent=4)

    @staticmethod
    def on_write_contacts(user_id: int, method: str = None, value: list = None) -> None:
        # Write contacts to a JSON file
        current_dict = AccessEnv.users[str(user_id)]['contacts']

        if method == 'add':
            current_dict.extend(value)
        if method == 'del':
            current_dict = [element for element in current_dict if element not in value]

        AccessEnv.users[str(user_id)]['contacts'] = current_dict
        with open('data/data.json', 'w') as json_file:
            json.dump(AccessEnv.users, json_file, indent=4)

    @staticmethod
    def on_write_verifications(user_id: int, method: str = None, value: list = None) -> None:
        # Write verifications to a JSON file
        current_dict = AccessEnv.users[str(user_id)]['daily_message']

        if method == 'add':
            current_dict.extend(value)
        if method == 'del':
            current_dict = [element for element in current_dict if element not in value]

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
    def on_reset() -> None:
        file_path = "data/data.json"

        # Check if the file exists
        if not os.path.exists(file_path):
            with open(file_path, 'w') as file:
                json.dump({}, file, indent=4)

        with open(file_path, 'r') as json_file:
            AccessEnv.users = json.load(json_file)

    @staticmethod
    def on_create_user(user_id: int) -> None:
        fresh_data: dict = {
            'alert_mode': False,
            'response_message': False,
            'reminder_count': 0,
            'skip': False,
            'state': '',
            'fast_check': (),
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
    def get_demo() -> str:
        my_id = os.getenv('me')
        if not my_id:
            raise ValueError("My telegram id is missing")
        return my_id

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
