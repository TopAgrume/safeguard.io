import time
import asyncio

from datetime import datetime
from telegram import Bot, KeyboardButton, Message
from telegram import ReplyKeyboardMarkup
from utils.logger import setup_logger
from utils.config import Config
from services.user_service import UserService
from services.verification_service import VerificationService

# Initialization
logger = setup_logger("Scheduler", "scheduler.log")
"""Logger for the scheduler service module"""
API_TOKEN = Config.TELEGRAM_API_TOKEN
"""The API token for the Telegram bot, retrieved from the configuration file."""
BOT_USERNAME = Config.TELEGRAM_BOT_USERNAME
"""The username of the Telegram bot, retrieved from the configuration file."""
WAITING_TIME = 8
"""The default waiting time (in minutes) before sending the next reminder."""
bot = Bot(API_TOKEN)
"""The Telegram bot object used to send messages and interact with users."""

async def send_daily_message(user_id: int, username: str, verif_time: datetime.time, description: str) -> Message:
    """
    Sends a daily scheduled message to the user, prompting them to confirm their status.

    Args:
        user_id (int): The Telegram user ID to send the message to.
        username (str): The username of the user for logging purposes.
        verif_time (datetime.time): The scheduled time for the verification message.
        description (str): A description associated with the daily message.

    Returns:
        Message: The Telegram message object representing the sent daily message.
    """
    logger.debug(f"Send daily {verif_time} message to @{username}")

    # Construct the reply keyboard with predefined options
    keyboard = [
        [
            KeyboardButton("I am fine!"),
            KeyboardButton("/help"),
        ],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    message = f"Hey 🙂🌟! This is your daily message ({description}), please answer if you are fine!"
    return await bot.send_message(chat_id=user_id, text=message, reply_markup=reply_markup)


async def run_schedule() -> None:
    """
    Runs the main scheduling loop, sending daily messages at the specified time for each user.

    This function checks the current time every minute and sends messages to users
    when their scheduled verification time matches the current time. If the verification
    is skipped or marked as a fast-check, it updates the user's status accordingly.
    """
    current_hour = -1
    while True:
        # Refresh the logger every hour
        if datetime.now().hour != current_hour:
            current_hour = datetime.now().hour
            logger.info(f"--- REFRESH {current_hour}h ---")

        # Iterate over users and their scheduled verifications
        for user_id, verif_time, verif_desc, verif_active in VerificationService.get_idle_users_verifications():
            # Ensure the current time matches the scheduled verification time
            if not time.localtime().tm_hour == verif_time.hour:
                continue
            if not time.localtime().tm_min == verif_time.minute:
                continue

            username = UserService.get_username(user_id)

            # Handle skipped or fast-check verifications
            if not verif_active:
                if isinstance(verif_active, bool):
                    # Undo the skip and prepare the user for the next verification
                    VerificationService.undoskip_verifications(user_id, [verif_time])
                    logger.debug(f"Undo skip for @{username} at {verif_time} {verif_active}")
                    continue

                # Fast-check scenario: delete the created check
                VerificationService.delete_verifications(user_id, [verif_time])
                logger.debug(f"Kill fast check for @{username} at {verif_time} {verif_active}")

            # Update user properties and initialize the verification process
            UserService.update_user_property(user_id, "response_message", False)
            VerificationService.add_check_queue_item(user_id, verif_time, verif_desc, WAITING_TIME)
            await send_daily_message(user_id, username, verif_time, verif_desc)

        # Wait until the minute changes before checking again
        current_minute = datetime.now().minute
        while datetime.now().minute == current_minute:
            await asyncio.sleep(1)


if __name__ == "__main__":
    # Start the asynchronous event loop
    logger.info('Starting Scheduler...')
    asyncio.run(run_schedule())
