from twilio.rest import Client
from flask import Flask, request
from utils import AccessEnv

import time

# sos_logger = AccessEnv.logger('SOS_API')
client: Client = AccessEnv.client()
server_number, client_number, emergency_number = AccessEnv.contacts()

app = Flask(__name__)


def send_hope_message():
    print('API:', 'Send Hope Message')
    client.messages.create(
        from_=server_number,
        body='Alert status is reset. Everything is back to normal.',
        to=emergency_number
    )
    client.messages.create(
        from_=server_number,
        body='Alert status is reset. Everything is back to normal.',
        to=client_number
    )


@app.route("/sms", methods=['GET', 'POST'])
def sms_reply():
    response_message, alert_mode, _ = AccessEnv.on_read()

    print('API:', 'Connection post')
    message_body = request.values.get('Body', '').strip().lower()

    if response_message:
        # Already answered / Random call
        print('API:', 'Response out of context')
    elif not alert_mode:
        print('API:', 'Response to contact and confirmation demand')
        greeting = "Have a great day! :D" if time.localtime().tm_hour == 10 else "Have a wonderful night! ;)"
        response_message = 'Thank you for your response! '

        client.messages.create(
            from_=server_number,
            body=response_message + greeting,
            to=client_number
        )
        AccessEnv.on_write("reminder_count", 0)
        AccessEnv.on_write("response_message", True)
    else:
        print('API:', 'Response to unset the alert mode')
        AccessEnv.on_write("alert_mode", False)
        send_hope_message()

    return f"API ok, status actuel:\nreminder_count = {AccessEnv.on_read('reminder_count')}\nalert_mode = {AccessEnv.on_read('alert_mode')}\nresponse_message = {AccessEnv.on_read('response_message')}"


def run_api():
    app.run(debug=False, use_reloader=False)
