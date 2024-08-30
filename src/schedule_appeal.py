from datetime import datetime
from telegram import Bot, KeyboardButton, Message
from telegram import ReplyKeyboardMarkup
from src.utils.env_pipeline import RequestManager
from logzero import logger
import asyncio
import time

TOKEN, BOT_USERNAME = RequestManager.telegram_keys()
WAITING_TIME = 9
bot = Bot(TOKEN)


async def send_daily_message(user_id: int, username: str, verif_time: datetime.time, description: str) -> Message:
    logger.debug(f"SCHEDULER: Send daily {verif_time} message to @{username}")

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
    current_hour = -1
    while True:
        if datetime.now().hour != current_hour:
            current_hour = datetime.now().hour
            logger.info(f"SCHEDULER: --- REFRESH {current_hour}h ---")

        for user_id, verif_time, verif_desc, verif_active in RequestManager.get_verifications_from_idle_users():
            if not time.localtime().tm_hour == verif_time.hour:
                continue
            if not time.localtime().tm_min == verif_time.minute:
                continue

            username = RequestManager.username_from_user_id(user_id)

            # In case of skip or fast-check
            if not verif_active:
                if isinstance(verif_active, bool):
                    RequestManager.undoskip_verifications(user_id, [verif_time])
                    logger.debug(f"SCHEDULER: undo skip for @{username} at {verif_time} {verif_active}")
                    continue

                # Fast-check -> delete the created check
                RequestManager.del_verifications(user_id, [verif_time])
                logger.debug(f"SCHEDULER: kill fast check for @{username} at {verif_time} {verif_active}")

            RequestManager.update_user_properties(user_id, "response_message", False)
            RequestManager.init_check_queue(user_id, verif_time, verif_desc, WAITING_TIME)
            await send_daily_message(user_id, username, verif_time, verif_desc)

        current_minute = datetime.now().minute
        # Wait until the minute changes
        while datetime.now().minute == current_minute:
            await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(run_schedule())
