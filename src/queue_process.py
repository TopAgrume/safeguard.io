from telegram import Bot, KeyboardButton
from telegram import ReplyKeyboardMarkup
from utils.env_pipeline import AccessEnv

import telegram
import asyncio

TOKEN, BOT_USERNAME = AccessEnv.telegram_keys()
LOOP_QUEUE_TIME, WAITING_TIME = 1, 10
P_HTML = telegram.constants.ParseMode.HTML
bot = Bot(TOKEN)


async def send_reminder(user_id: str, user_data: dict):
    user_data["reminder_count"] += 1
    AccessEnv.on_write_check_queue(user_id, "reminder_count", user_data["reminder_count"])

    # 5th reminder = set alert mode
    reminder_count = user_data["reminder_count"]
    if reminder_count == 5:
        return

    print('WORKING QUEUE:', f"Send {reminder_count=} to {user_id=}")

    message = f"<b>Reminder {reminder_count}</b>: Please respond to the verification message."
    await bot.send_message(chat_id=user_id, text=message, parse_mode=P_HTML)


async def send_alert_message(user_id):
    print('WORKING QUEUE:', f"Send Alert Message to/from {user_id=}")
    # await bot.send_message(chat_id=user_id, text='No response received from VAL. URGENT SYSTEM LAUNCHING')
    # TODO contact emergencies
    keyboard = [
        [KeyboardButton("I am back!")],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)

    message = 'Alert sent to emergency contacts. Please answer to disable it'
    return await bot.send_message(chat_id=user_id, text=message, reply_markup=reply_markup)


async def check_for_response():  # TODO verification queue
    while True:
        print('WORKING QUEUE:', '--- REFRESH ---')

        for user_id, user_data in AccessEnv.on_get_check_users("items"):
            # Check for response message
            if AccessEnv.on_read(user_id, "response_message"):
                AccessEnv.on_kill_queue_data(user_id)
                continue

            # If there is no response
            if user_data['waiting_time'] == 0:
                user_data['waiting_time'] = WAITING_TIME
                await send_reminder(user_id, user_data)

            # Set alert mode to True
            if user_data["reminder_count"] >= 5:
                await send_alert_message(user_id)
                AccessEnv.on_kill_queue_data(user_id)
                AccessEnv.on_write(user_id, "alert_mode", True)
                continue

            user_data['waiting_time'] -= 1
            AccessEnv.on_write_check_queue(user_id, 'waiting_time', user_data['waiting_time'])

        await asyncio.sleep(LOOP_QUEUE_TIME)


def run_queue_process():
    asyncio.run(check_for_response())