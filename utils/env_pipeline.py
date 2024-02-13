from twilio.rest import Client
import logging
import yaml
import os
import json


class AccessEnv(object):
    # Static data
    client_contact = os.getenv('client_number')
    server_sid = os.getenv('server_number')
    data: dict = {
        'response_message': False,
        'alert_mode': False,
        'reminder_count': 0
    }

    @staticmethod
    def on_write(key: str = None, value=None) -> None:
        # Write data to a YAML file
        if key is not None:
            AccessEnv.data[key] = value

        with open('../data_pipe.yaml', 'w') as yaml_file:
            yaml.dump(AccessEnv.data, yaml_file, default_flow_style=False)

    @staticmethod
    def on_read(key: str = None):
        # Open and read a YAML file
        with open('../data_pipe.yaml', 'r') as yaml_file:
            AccessEnv.data = yaml.safe_load(yaml_file)

        if key is None:
            return AccessEnv.data["response_message"], AccessEnv.data["alert_mode"], AccessEnv.data["reminder_count"]
        else:
            return AccessEnv.data[key]

    @staticmethod
    def on_reset() -> None:
        AccessEnv.on_write()

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
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        return logging.getLogger(logger_name)


class Messaging(object):
    @staticmethod
    def send(template_id: str, content_variable: dict):
        client = AccessEnv.client()
        client.messages.create(
            content_sid=template_id,
            from_=AccessEnv.server_sid,
            content_variables=json.dumps(content_variable),
            to=AccessEnv.client_contact
        )
