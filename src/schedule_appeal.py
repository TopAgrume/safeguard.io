from typing import Final

import telegram
from twilio.rest import Client
from utils.env_pipeline import AccessEnv

import asyncio
import time

# sos_logger = AccessEnv.logger('SOS_SCHEDULE')
TOKEN: Final = '6969147937:AAHy6mwcoATmDbajrmo8TTzDNxFDzq5_blo'
BOT_USERNAME: Final = '@Safeguard_io_bot'

bot = telegram.Bot(TOKEN)


async def send_daily_message_10h():
    print('SCHEDULER:', "Send daily 10h Message")
    await bot.send_message(chat_id=6577580728, text='Hey! This is your first daily message, please answer if you are fine! :)')

    AccessEnv.on_write("response_message", False)
    await check_for_response()


async def send_daily_message_21h():
    print('SCHEDULER:', "Send daily 21h Message")
    await bot.send_message(chat_id=6577580728, text='Hey! This is your second daily message, please answer if you are fine! :)')

    AccessEnv.on_write("response_message", False)
    await check_for_response()


async def send_reminder():
    reminder_count = AccessEnv.on_read("reminder_count")
    reminder_count += 1
    AccessEnv.on_write("reminder_count", reminder_count)

    # 5th reminder = set alert mode
    if reminder_count == 5:
        return

    print('SCHEDULER:', f"Send reminder {reminder_count}")
    await bot.send_message(chat_id=6577580728, text=f"Reminder {reminder_count}: Please respond to the verification message.")


async def send_alert_message():
    print('SCHEDULER:', 'Send Alert Message')
    await bot.send_message(chat_id=6577580728, text='No response received from VAL. URGENT SYSTEM LAUNCHING')
    await bot.send_message(chat_id=6577580728, text='Alert sent to emergency contacts. Please answer to disable it')


async def check_for_response():
    time_amount = 5
    while True:
        # Wait for 12 min (720 sec) before sending reminder
        print('SCHEDULER:', f"Wait {time_amount} secs")
        await asyncio.sleep(time_amount)

        # Check for response message
        if AccessEnv.on_read("response_message"):
            break

        # If there is no response
        await send_reminder()

        # Set alert mode to True
        reminder_count = AccessEnv.on_read("reminder_count")

        if reminder_count >= 5:
            await send_alert_message()
            AccessEnv.on_write("alert_mode", True)
            break


async def run_schedule():
    loop_count = 0
    while True:
        loop_count += 1
        print('SCHEDULER:', f"5 min check loop: {loop_count = }")

        # Send message
        if not AccessEnv.on_read("alert_mode"):
            if time.localtime().tm_hour == 10:
                await send_daily_message_10h()

            elif time.localtime().tm_hour == 20:
                await send_daily_message_21h()
            elif time.localtime().tm_hour == 21:
                await send_daily_message_21h()

        # Loop every five minutes
        await asyncio.sleep(300)


def run_schedule_process():
    asyncio.run(run_schedule())
