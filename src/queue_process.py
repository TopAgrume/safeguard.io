from datetime import datetime

from telegram import Bot, KeyboardButton
from telegram import ReplyKeyboardMarkup
from utils.env_pipeline import RequestManager
import random
import telegram
import asyncio

TOKEN, BOT_USERNAME = RequestManager.telegram_keys()
WAITING_TIME = 9
P_HTML = telegram.constants.ParseMode.HTML
bot = Bot(TOKEN)


async def send_reminder(user_id: str, user_data: dict):
    user_data["reminder_count"] += 1
    RequestManager.on_write_check_queue(user_id, "reminder_count", user_data["reminder_count"])

    # 5th reminder = set alert mode
    reminder_count = user_data["reminder_count"]
    if reminder_count == 5:
        return

    print('WORKING QUEUE:', f"Send {reminder_count=} to {user_id=}")

    messages = [
        f"<b>Reminder {reminder_count}</b>: Please respond to the verification message! 📬",
        f"<b>Reminder {reminder_count}:</b> Don't forget to reply to the verification message! 📬",
        f"<b>Reminder {reminder_count}:</b> Your prompt response to the verification message is appreciated! 📬",
        f"<b>Reminder {reminder_count}:</b> Kindly acknowledge the verification message. 📬",
        f"<b>Reminder {reminder_count}:</b> Ensure you respond to the verification message in a timely manner! 📬",
        f"<b>Reminder {reminder_count}:</b> Please take a moment to reply to the verification message! 📬",
        f"<b>Reminder {reminder_count}:</b> A quick response to the verification message is required! 📬"
    ]
    random_message = random.choice(messages)
    await bot.send_message(chat_id=user_id, text=random_message, parse_mode=P_HTML)


async def send_alert_message(user_id):
    print('WORKING QUEUE:', f"Send Alert Message to/from {user_id=}")
    username = RequestManager.username_from_user_id()[user_id]
    user_data = RequestManager.on_get_check_users("dict")[user_id]
    time = user_data['time']
    desc = user_data['desc']
    message = (f"🚨<b>ALERT</b>🚨. I haven't heard from @{username} for his/her {time} callback."
               "<b>Don't take this call lightly and make sure she/he is okay! It might be urgent!</b>\n"
               f"This could be important, here is the description that was given to this recall:\n\n {desc}")

    for contact in RequestManager.read_contacts_properties(user_id):
        if not contact["pair"]:
            continue

        await bot.send_message(chat_id=contact["id"], text=message, parse_mode=P_HTML)
    keyboard = [
        [KeyboardButton("I am back!")],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)

    message = '🚨 Alert sent to emergency contacts. <b>Please answer to disable it.</b>'
    return await bot.send_message(chat_id=user_id, text=message, reply_markup=reply_markup, parse_mode=P_HTML)


async def check_for_response():
    await asyncio.sleep(5)
    current_hour = -1
    while True:
        # Wait until the next hour
        if datetime.now().hour != current_hour:
            current_hour = datetime.now().hour
            print('WORKING QUEUE:', f"--- REFRESH {current_hour}h ---")

        for user_id, user_data in RequestManager.on_get_check_users("items"):
            # Check for response message
            if RequestManager.read_user_properties(user_id, "response_message"):
                RequestManager.on_kill_queue_data(user_id)
                continue

            # If there is no response
            if user_data['waiting_time'] == 0:
                user_data['waiting_time'] = WAITING_TIME
                await send_reminder(user_id, user_data)

            # Set alert mode to True
            if user_data["reminder_count"] >= 5:
                await send_alert_message(user_id)
                RequestManager.on_kill_queue_data(user_id)
                RequestManager.update_user_properties(user_id, "alert_mode", True)
                continue

            user_data['waiting_time'] -= 1
            RequestManager.on_write_check_queue(user_id, 'waiting_time', user_data['waiting_time'])

        current_minute = datetime.now().minute
        # Wait until the minute changes
        while datetime.now().minute == current_minute:
            await asyncio.sleep(1)
        await asyncio.sleep(5)


def run_queue_process():
    asyncio.run(check_for_response())
