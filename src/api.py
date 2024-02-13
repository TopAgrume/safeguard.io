from typing import Final
import time

import telegram
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from utils.env_pipeline import AccessEnv

TOKEN: Final = '6969147937:AAHy6mwcoATmDbajrmo8TTzDNxFDzq5_blo'
BOT_USERNAME: Final = '@Safeguard_io_bot'

bot = telegram.Bot(TOKEN)

"""async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Hello! Thanks for chatting with me! I am a Safeguard.io bot')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('I make sure everything is okay! ;)')


async def custom_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('This is a custom command')"""

async def send_hope_message(update: Update):
    print('API:', 'Send Hope Message')
    # await bot.send_message(chat_id=6577580728, text='Alert status is reset. Everything is back to normal.')
    # await bot.send_message(chat_id=6577580728, text='Alert status is reset. Everything is back to normal.')
    await update.message.reply_text('Alert status is reset. Everything is back to normal.')


async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    response: str = ""
    message_type: str = update.message.chat.type
    message_body: str = update.message.text.lower()

    if message_type == 'group':
        if BOT_USERNAME in message_body:
            # new_text: str = message_body.replace(BOT_USERNAME, '').strip()
            response = 'This bot does not support groups for now'
        else:
            return

    response_message, alert_mode, _ = AccessEnv.on_read()

    if response_message:
        # Already answered / Random call
        print('API:', 'Response out of context')
        await update.message.reply_text("Already answered / Random call")

    elif not alert_mode:
        print('API:', 'Response to contact and confirmation demand')
        greeting = "Have a great day! :D" if time.localtime().tm_hour == 10 else "Have a wonderful night! ;)"
        response = 'Thank you for your response! ' + greeting
        await update.message.reply_text(response)

        AccessEnv.on_write("reminder_count", 0)
        AccessEnv.on_write("response_message", True)
    else:
        print('API:', 'Response to unset the alert mode')
        AccessEnv.on_write("alert_mode", False)
        AccessEnv.on_write("response_message", True)
        await send_hope_message(update)

    print('Bot:', response)
    return


async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'Update {update} caused error {context}')


def run_api():
    print('Starting bot...')
    app = Application.builder().token(TOKEN).build()

    # Commands
    """app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CommandHandler('custom', custom_command))"""

    # Messages
    app.add_handler(MessageHandler(filters.TEXT, handle_messages))

    # Errors
    app.add_error_handler(error)

    # Polls the bot
    print('Polling...')
    app.run_polling(poll_interval=1)
