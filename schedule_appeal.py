from twilio.rest import Client
from utils import AccessEnv

import asyncio
import time

logger = AccessEnv.logger('SOS_SCHEDULE')
client: Client = AccessEnv.client()
server_number, client_number, emergency_number = AccessEnv.contacts()


async def send_daily_message_10h():
    logger.info("Send daily 10h Message")
    client.messages.create(
        from_=server_number,
        body='Hey! This is your first daily message, please answer if you are fine! :)',
        to=client_number
    )

    AccessEnv.on_write("response_message", False)
    await check_for_response()


async def send_daily_message_21h():
    logger.info("Send daily 21h Message")
    client.messages.create(
        from_=server_number,
        body='Hey! This is your second daily message, please answer if you are fine! :)',
        to=client_number
    )

    AccessEnv.on_write("response_message", False)
    await check_for_response()


def send_reminder():
    reminder_count = AccessEnv.on_write("reminder_count")
    reminder_count += 1
    AccessEnv.on_write("response_message", reminder_count)

    # 5th reminder = set alert mode
    if reminder_count == 5:
        return

    logger.info(f"Send reminder {reminder_count}")
    client.messages.create(
        from_=server_number,
        body=f"Reminder {reminder_count}: Please respond to the verification message.",
        to=client_number
    )


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


async def check_for_response():
    response_message, alert_mode, reminder_count = AccessEnv.on_read()

    time_amount = 12
    while not response_message:
        # Wait for 12 min (720 sec) before sending reminder
        logger.info(f"Wait {time_amount} secs")
        await asyncio.sleep(time_amount)
        send_reminder()

        # Set alert mode to True
        if reminder_count >= 5:
            send_alert_message()
            AccessEnv.on_write("alert_mode", True)
            break


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


async def run_schedule():
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


asyncio.run(run_schedule())
