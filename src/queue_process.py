from datetime import datetime

from telegram import Bot, KeyboardButton, Message
from telegram import ReplyKeyboardMarkup
from src.utils.env_pipeline import RequestManager
import random
import telegram
import asyncio
from logzero import logger

TOKEN, BOT_USERNAME = RequestManager.telegram_keys()
WAITING_TIME = 9
P_HTML = telegram.constants.ParseMode.HTML
bot = Bot(TOKEN)


async def send_reminder(user_id: int, username: str, reminder_count: int) -> Message:
    logger.debug(f"└── Reminder count set to {reminder_count} for @{username}")

    messages = [
        f"<b>Reminder {reminder_count}:</b> Please respond to the verification message! 📬",
        f"<b>Reminder {reminder_count}:</b> Don't forget to reply to the verification message! 📬",
        f"<b>Reminder {reminder_count}:</b> Your prompt response to the verification message is appreciated! 📬",
        f"<b>Reminder {reminder_count}:</b> Kindly acknowledge the verification message. 📬",
        f"<b>Reminder {reminder_count}:</b> Ensure you respond to the verification message in a timely manner! 📬",
        f"<b>Reminder {reminder_count}:</b> Please take a moment to reply to the verification message! 📬",
        f"<b>Reminder {reminder_count}:</b> A quick response to the verification message is required! 📬"
    ]
    random_message = random.choice(messages)
    return await bot.send_message(chat_id=user_id, text=random_message, parse_mode=P_HTML)


async def send_alert_message(user_id: int, time: str, desc: str) -> Message:
    username = RequestManager.username_from_user_id(user_id)
    logger.debug(f"└── @{username} is now in alert mode")

    contact_message = (f"🚨<b>ALERT</b>🚨. I haven't heard from @{username} for his/her {time} callback."
               "<b>Don't take this call lightly and make sure she/he is okay! It might be urgent!</b>\n"
               f"This could be important, here is the description that was given to this recall:\n\n {desc}")

    for contact_id, contact_tag in RequestManager.read_paired_contacts_properties(user_id):
        await bot.send_message(chat_id=contact_id, text=contact_message, parse_mode=P_HTML)
        logger.debug(f"    └── Alert notification about @{username} sent to @{contact_tag}")

    keyboard =[KeyboardButton("I am back!")]
    reply_markup = ReplyKeyboardMarkup([keyboard], one_time_keyboard=True)

    message = '🚨 Alert sent to emergency contacts. <b>Please answer to disable it.</b>'
    return await bot.send_message(chat_id=user_id, text=message, reply_markup=reply_markup, parse_mode=P_HTML)


async def check_for_response():
    await asyncio.sleep(5)
    current_hour = -1
    while True:
        # Wait until the next hour
        if datetime.now().hour != current_hour:
            current_hour = datetime.now().hour
            logger.info(f"WORKING QUEUE: --- REFRESH {current_hour}h ---")

        for user_id, verif_time, verif_desc, reminder_c, waiting_time in RequestManager.retrieve_checks_from_queue():
            username = RequestManager.username_from_user_id(user_id)
            logger.debug(f"WORKING QUEUE: {verif_time}'s verification processing for @{username}")

            # Check for response message
            if RequestManager.read_user_properties(user_id, "response_message"):
                logger.debug(f"└── User @{username} responded to the verification message")
                RequestManager.on_kill_queue_data(user_id)
                continue

            # If there is no response
            if waiting_time == 0:
                waiting_time = WAITING_TIME
                await send_reminder(user_id, username, reminder_c)

            # Set alert mode to True
            if reminder_c >= 5:
                await send_alert_message(user_id, verif_time, verif_desc)
                RequestManager.on_kill_queue_data(user_id)
                RequestManager.update_user_properties(user_id, "alert_mode", True)
                continue

            RequestManager.update_check_queue_properties(user_id, "waiting_time", waiting_time - 1)

        current_minute = datetime.now().minute
        # Wait until the minute changes
        while datetime.now().minute == current_minute:
            await asyncio.sleep(1)
        await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(check_for_response())
