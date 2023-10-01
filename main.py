from twilio.rest import Client
from flask import Flask, request
import logging

import time
import asyncio
import threading

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger('SOS_ALERT')

account_sid = 'ACd82bc829c02333b6c5c9dac3eab546f1'
auth_token = '287440909711bad55b8e727c852336d0'
client = Client(account_sid, auth_token)

server_number = 'whatsapp:+14155238886'
client_number = 'whatsapp:+33647528686'
emergency_number = 'whatsapp:+33647528686'

if not account_sid or not auth_token or not server_number or not client_number or not emergency_number:
    raise ValueError("One or more required environment variables are missing.")

app = Flask(__name__)

response_message = False
alert_mode = False
reminder_count = 0


async def send_daily_message_10h():
    global response_message
    logger.info("Send daily 10h Message")
    client.messages.create(
        from_=server_number,
        body='Hey! This is your first daily message, please answer if you are fine! :)',
        to=client_number
    )

    response_message = False
    await check_for_response()


async def send_daily_message_21h():
    global response_message
    logger.info("Send daily 21h Message")
    client.messages.create(
        from_=server_number,
        body='Hey! This is your second daily message, please answer if you are fine! :)',
        to=client_number
    )

    response_message = False
    await check_for_response()


def send_reminder():
    global reminder_count
    reminder_count += 1

    # 5th reminder = set alert mode
    if reminder_count == 5:
        return

    logger.info(f"Send reminder {reminder_count}")
    client.messages.create(
        from_=server_number,
        body=f"Reminder {reminder_count}: Please respond to the verification message.",
        to=client_number
    )


async def check_for_response():
    global alert_mode
    global reminder_count
    global response_message
    time_amount = 12
    while not response_message:
        # Wait for 12 min (720 sec) before sending reminder
        logger.info(f"Wait {time_amount} secs")
        await asyncio.sleep(time_amount)
        send_reminder()

        # Set alert mode to True
        if reminder_count >= 5:
            send_alert_message()
            alert_mode = True
            break


def send_alert_message():
    logger.info('Send Alert Message')
    client.messages.create(
        from_=server_number,
        body='No response received from VAL. URGENT SYSTEM LAUNCHING',
        to=emergency_number
    )
    client.messages.create(
        from_=server_number,
        body='Alert sent to emergency contacts. Please answer to disable it',
        to=client_number
    )


def send_hope_message():
    logger.info('Send Hope Message')
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


async def run_timed_functions():
    while True:
        logger.info("Sending Daily Message")
        await send_daily_message_10h()
        # if not alert_mode:
        #    if time.localtime().tm_hour == 10:
        #        await send_daily_message_10h()
        #    elif time.localtime().tm_hour == 21:
        #        await send_daily_message_21h()
        # else:
        # message info on alert tu urgent contact
        await asyncio.sleep(120)


@app.route("/sms", methods=['GET', 'POST'])
def sms_reply():
    global response_message
    global alert_mode
    global reminder_count

    logger.info('Connection post')
    message_body = request.values.get('Body', '').strip().lower()

    if response_message:
        # Already answered / Random call
        logger.debug('Response out of context')
    elif not alert_mode:
        logger.info('Response to contact and confirmation demand')
        greeting = "Have a great day! :D" if time.localtime().tm_hour == 10 else "Have a wonderful night! ;)"
        response_message = 'Thank you for your response! '

        client.messages.create(
            from_=server_number,
            body=response_message + greeting,
            to=client_number
        )
        reminder_count = 0
        response_message = True
    else:
        logger.info('Response to unset the alert mode')
        alert_mode = False
        send_hope_message()

    return "test"


def run_async_function():
    asyncio.run(run_timed_functions())


if __name__ == "__main__":
    logger.info("Launching SCHEDULER")
    flask_thread = threading.Thread(target=run_async_function)
    flask_thread.start()

    logger.info("Launching ENDPOINT API")
    app.run(debug=True)
