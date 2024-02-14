import time
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from utils.env_pipeline import AccessEnv
from src.commands import start_command, info_command, bugreport_command
from src.commands import addcontact_command, showcontacts_command, delcontact_command
from src.commands import addverif_command, showverifs_command, delverif_command
from src.commands import skip_command, fastcheck_command, help_command

TOKEN, BOT_USERNAME = AccessEnv.telegram_keys()


async def send_hope_message(update: Update):
    print('API:', 'Send Hope Message')
    #await update.message.reply_text('Alert status is reset. Everything is back to normal.')


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

    user_id = update.message.from_user.id
    response_message, alert_mode, _ = AccessEnv.on_read(user_id)

    if response_message:
        # Already answered / Random call
        print('API:', 'Response out of context')
        #await update.message.reply_text("Already answered / Random call")

    elif not alert_mode:
        print('API:', 'Response to contact and confirmation demand')
        greeting = "Have a great day! :D" if time.localtime().tm_hour == 10 else "Have a wonderful night! ;)"
        response = 'Thank you for your response! ' + greeting
        #await update.message.reply_text(response)

        AccessEnv.on_write(user_id, "reminder_count", 0)
        AccessEnv.on_write(user_id, "response_message", True)
    else:
        print('API:', 'Response to unset the alert mode')
        AccessEnv.on_write(user_id, "alert_mode", False)
        AccessEnv.on_write(user_id, "response_message", True)
        #await send_hope_message(update)

    print('API:', 'Bot response:', response)


async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print('API ERROR:', f'Update {update} caused error {context}')


def run_api():
    print('API:', 'Starting bot...')
    app = Application.builder().token(TOKEN).build()

    # Commands
    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('info', info_command))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CommandHandler('bugreport', bugreport_command))
    app.add_handler(CommandHandler('addcontact', addcontact_command))
    app.add_handler(CommandHandler('showcontacts', showcontacts_command))
    app.add_handler(CommandHandler('delcontact', delcontact_command))
    app.add_handler(CommandHandler('addverif', addverif_command))
    app.add_handler(CommandHandler('showverifs', showverifs_command))
    app.add_handler(CommandHandler('delverif', delverif_command))
    app.add_handler(CommandHandler('skip', skip_command))
    app.add_handler(CommandHandler('fastcheck', fastcheck_command))

    # Messages
    app.add_handler(MessageHandler(filters.TEXT, handle_messages))

    # Errors
    app.add_error_handler(error)

    # Polls the bot
    print('API:', 'Polling...')
    app.run_polling(poll_interval=0.5)
