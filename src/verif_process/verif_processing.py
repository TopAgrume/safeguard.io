import random
import telegram
import asyncio

from datetime import datetime
from telegram import Bot, KeyboardButton, Message
from telegram import ReplyKeyboardMarkup
from utils.config import Config
from utils.logger import setup_logger
from services.contact_service import ContactService
from services.user_service import UserService
from services.verification_service import VerificationService

try:
    Config.validate()
except ValueError as e:
    print(f"Configuration error: {e}")

# Initialization
logger = setup_logger("Queue Process", "queue_process.log")
"""Logger for the Queue Process service module"""
API_TOKEN = Config.TELEGRAM_API_TOKEN
"""The API token for the Telegram bot, retrieved from the configuration file."""
BOT_USERNAME = Config.TELEGRAM_BOT_USERNAME
"""The username of the Telegram bot, retrieved from the configuration file."""
P_HTML = telegram.constants.ParseMode.HTML
"""Parse mode set to HTML for formatting Telegram messages."""
WAITING_TIME = 9
"""The default waiting time (in minutes) before sending the next reminder."""
bot = Bot(API_TOKEN)
"""The Telegram bot object used to send messages and interact with users."""

async def send_reminder(user_id: int, username: str, reminder_count: int) -> Message:
    """
    Sends a reminder message to a user, prompting them to respond to a verification message.

    Args:
        user_id (int): The Telegram user ID to send the message to.
        username (str): The username of the user for logging purposes.
        reminder_count (int): The count of the reminder being sent.

    Returns:
        Message: The Telegram message object representing the sent reminder.
    """
    logger.debug(f"└── Reminder count set to {reminder_count} for @{username}")

    # Predefined reminder messages
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


async def send_alert_message(user_id: int, verif_time: datetime.time, desc: str) -> Message:
    """
    Sends an alert message to a user's emergency contacts if the user fails to respond.

    Args:
        user_id (int): The Telegram user ID to alert.
        verif_time (datetime.time): The time when the verification was supposed to occur.
        desc (str): Description provided for the callback.

    Returns:
        Message: The Telegram message object sent to the user after alerting their contacts.
    """
    username = UserService.get_username(user_id)
    logger.debug(f"└── @{username} is now in alert mode")

    contact_message = (f"🚨<b>ALERT</b>🚨.\nI haven't received any response from @{username} for the scheduled {verif_time.hour:02}:{verif_time.minute:02} callback.\n"
               "<b>Please don't take this lightly—ensure they are okay! This could be urgent.</b>\n"
               f"Here's the description provided for the callback:\n\n {desc}")

    # Notify emergency contacts
    for contact_id, contact_tag in ContactService.get_paired_contacts(user_id):
        await bot.send_message(chat_id=contact_id, text=contact_message, parse_mode=P_HTML)
        logger.debug(f"    └── Alert notification about @{username} sent to @{contact_tag}")

    # Provide the user with an option to disable the alert
    keyboard =[KeyboardButton("I am back!")]
    reply_markup = ReplyKeyboardMarkup([keyboard], one_time_keyboard=True)

    message = '🚨 Alert sent to emergency contacts. <b>Please answer to disable it.</b>'
    return await bot.send_message(chat_id=user_id, text=message, reply_markup=reply_markup, parse_mode=P_HTML)


async def check_for_response() -> None:
    """
    Continuously checks for user responses and manages the reminder and alert system.

    This function runs an infinite loop that checks for user responses to scheduled verification
    messages. If a response is not received within the set waiting time, it sends reminders.
    If the user fails to respond after several reminders, it sends alerts to emergency contacts.

    The function also manages the queue of users to be checked and updates their status accordingly.
    """
    await asyncio.sleep(5)
    current_hour = -1
    while True:
        # Refresh the queue logger every hour
        if datetime.now().hour != current_hour:
            current_hour = datetime.now().hour
            logger.info(f"--- REFRESH {current_hour}h ---")

        # Process the verification queue
        for user_id, verif_time, verif_desc, reminder_c, waiting_time in VerificationService.get_check_queue_items():
            username = UserService.get_username(user_id)
            logger.debug(f"{verif_time}'s verification processing for @{username}")

            # Check if the user has responded
            if UserService.get_user_property(user_id, "response_message"):
                logger.debug(f"└── User @{username} responded to the verification message")
                VerificationService.delete_check_queue_item(user_id)
                continue

            # If no response and the waiting time has expired, send a reminder
            if waiting_time == 0:
                waiting_time = WAITING_TIME
                reminder_c += 1
                VerificationService.update_check_queue_property(user_id, "reminder_count", reminder_c)
                await send_reminder(user_id, username, reminder_c)

            # If the maximum number of reminders has been reached, send an alert
            if reminder_c >= 5:
                await send_alert_message(user_id, verif_time, verif_desc)
                VerificationService.delete_check_queue_item(user_id)
                UserService.update_user_property(user_id, "alert_mode", True)
                continue

            # Update the waiting time for the next iteration
            VerificationService.update_check_queue_property(user_id, "waiting_time", waiting_time - 1)

        # Wait for the next minute before checking again
        current_minute = datetime.now().second
        while datetime.now().second == current_minute:
            await asyncio.sleep(1)
        await asyncio.sleep(5)


if __name__ == "__main__":
    # Start the asynchronous event loop
    logger.info('Starting Queue Process...')
    asyncio.run(check_for_response())
