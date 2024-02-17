from datetime import datetime

from telegram import Bot, KeyboardButton
from telegram import ReplyKeyboardMarkup
from utils.env_pipeline import AccessEnv

import asyncio
import time

TOKEN, BOT_USERNAME = AccessEnv.telegram_keys()
WAITING_TIME = 9
bot = Bot(TOKEN)


async def send_daily_message(user_id: int, description: str):
    print('SCHEDULER:', f"Send daily 10h Message to {user_id = }")

    keyboard = [
        [
            KeyboardButton("I am fine!"),
            KeyboardButton("/help"),
        ],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    message = f"Hey 🙂🌟! This is your daily message ({description}), please answer if you are fine!"
    return await bot.send_message(chat_id=user_id, text=message, reply_markup=reply_markup)


async def run_schedule():
    while True:
        print('SCHEDULER:', "--- REFRESH ---")

        for user_id, user_data in AccessEnv.on_get_users("items"):
            # If alert mode, do nothing
            if not user_data["response_message"]:
                continue

            get_daily_messages = user_data["daily_message"]
            for unique_check in get_daily_messages:
                if not time.localtime().tm_hour == int(unique_check["time"][:2]):
                    continue
                if not time.localtime().tm_min == int(unique_check["time"][3:5]):
                    continue

                # In case of skip or fast-check
                state = unique_check["active"]
                if not state:
                    if isinstance(state, bool):
                        AccessEnv.on_write_verifications(user_id, "undoskip", [unique_check["time"]])
                        print('SCHEDULER:', f"undo skip for: {state}")
                        continue

                    # Fast-check -> delete the created check
                    AccessEnv.on_write_verifications(user_id, "del", [unique_check["time"]])
                    print('SCHEDULER:', f"kill fast check: {state}")

                AccessEnv.on_write(user_id, "response_message", False)
                AccessEnv.on_init_check_queue(str(user_id), unique_check, WAITING_TIME)
                await send_daily_message(user_id, unique_check["desc"])

        current_minute = datetime.now().minute
        # Wait until the minute changes
        while datetime.now().minute == current_minute:
            await asyncio.sleep(1)


def run_schedule_process():
    asyncio.run(run_schedule())
