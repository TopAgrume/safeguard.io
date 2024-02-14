from typing import Final

from telegram import Bot
from utils.env_pipeline import AccessEnv

import asyncio
import time

TOKEN, BOT_USERNAME = AccessEnv.telegram_keys()
bot = Bot(TOKEN)


async def send_daily_message_10h(user_id):
    print('SCHEDULER', f"Send daily 10h Message to {user_id}")
    await bot.send_message(chat_id=user_id,
                           text='Hey! This is your first daily message, please answer if you are fine! :)')

    AccessEnv.on_write(user_id, "response_message", False)
    await check_for_response(user_id)


async def send_reminder(user_id):
    reminder_count = AccessEnv.on_read(user_id, "reminder_count")
    reminder_count += 1
    AccessEnv.on_write(user_id, "reminder_count", reminder_count)

    # 5th reminder = set alert mode
    if reminder_count == 5:
        return

    print('SCHEDULER', f"Send reminder {reminder_count} to {user_id}")
    await bot.send_message(chat_id=user_id,
                           text=f"Reminder {reminder_count}: Please respond to the verification message.")


async def send_alert_message(user_id):
    print('SCHEDULER', f"Send Alert Message from {user_id}")
    await bot.send_message(chat_id=user_id, text='No response received from VAL. URGENT SYSTEM LAUNCHING')
    await bot.send_message(chat_id=user_id, text='Alert sent to emergency contacts. Please answer to disable it')


async def check_for_response(user_id):
    time_amount = 5
    while True:
        # Wait for 12 min (720 sec) before sending reminder
        print('SCHEDULER', f"Wait {time_amount} secs for {user_id}")
        await asyncio.sleep(time_amount)

        # Check for response message
        if AccessEnv.on_read(user_id, "response_message"):
            break

        # If there is no response
        await send_reminder(user_id)

        # Set alert mode to True
        reminder_count = AccessEnv.on_read(user_id, "reminder_count")

        if reminder_count >= 5:
            await send_alert_message(user_id)
            AccessEnv.on_write(user_id, "alert_mode", True)
            break


async def run_schedule(user_id: int = int(AccessEnv.get_demo())):
    AccessEnv.on_reset()
    loop_count = 0

    while True:
        loop_count += 1
        print('SCHEDULER', f"5 min check loop: {loop_count = } for {user_id}")

        # Send message
        if not AccessEnv.on_read(user_id, "alert_mode"):
            print(AccessEnv.users)
            if time.localtime().tm_hour == 1:
                await send_daily_message_10h(user_id)

        # Loop every five minutes
        await asyncio.sleep(300)


def run_schedule_process():
    asyncio.run(run_schedule())
