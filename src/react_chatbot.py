"""
This module implements a Telegram bot for managing user contacts, verifications, and alerts.
It provides various commands and message handlers to interact with users and manage their data.
"""

import re
import random
from datetime import datetime, timedelta

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot, Message
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from telegram.constants import ParseMode

from utils.env_pipeline import RequestManager
from src import commands

TOKEN, BOT_USERNAME = RequestManager.telegram_keys()
bot = Bot(TOKEN)

import functools
from logzero import logger

def debug_logger(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        logger.debug(f"API: {func.__name__} call")
        return await func(*args, **kwargs)
    return wrapper

def sub_debug_logger(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        logger.debug(f"    └── {func.__name__} call")
        return await func(*args, **kwargs)
    return wrapper

async def send_hope_message(update: Update) -> Message:
    """Send a message indicating that the alert status has been reset."""
    username = update.message.from_user.username
    logger.debug(f"└── User @{username} sent a hope message to reset the alert status")

    message = '<b>Alert status is reset</b>. Everything is back to normal. ✅'
    return await update.message.reply_text(text=message, parse_mode=ParseMode.HTML)


@sub_debug_logger
async def notif_pairing_invitation(update: Update, notif_details: list) -> None:
    """
    Send notification to users about a pairing invitation.

    Args:
        update (Update): The update object from Telegram.
        notif_details (list): List of notification details.
    """
    user_id = update.message.from_user.id
    username = update.message.from_user.username

    for notif in notif_details:
        logger.debug(f"Sending pairing invitation to {notif['id']} from @{username}")
        message = f"<b>Do you want to accept the pairing invitation from @{username}? 🤝</b>"
        keyboard = [
            [
                InlineKeyboardButton("Yes", callback_data=f"+{user_id}"),
                InlineKeyboardButton("No", callback_data=f"-{user_id}"),
            ],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await bot.send_message(chat_id=notif['id'], text=message, reply_markup=reply_markup, parse_mode=ParseMode.HTML)


@sub_debug_logger
async def process_contacts(update: Update, content: str, action: str) -> Message:
    """
    Process adding or deleting contacts.

    Args:
        update (Update): The update object from Telegram.
        content (str): The message content containing contact information.
        action (str): The action to perform ('add' or 'del').
    """
    user_id = update.message.from_user.id
    user_username = update.message.from_user.username
    valid_contacts, error_contacts = [], []

    for line in content.splitlines():
        if match := re.match(r'@(\w+)', line):
            valid_contacts.append(match.group(1))
        else:
            error_contacts.append(line)

    if action == 'add':
        notification = RequestManager.add_contacts(user_id, user_username, valid_contacts)
        await notif_pairing_invitation(update, notification)
        message = "Given contact(s) are now added to your account.\nThey received an association request.🎉\n"
    else:
        RequestManager.del_contacts(user_id, valid_contacts)
        message = "Given contact(s) are now deleted from your account.🚮\n"

    if error_contacts:
        message += "\nFollowing contact(s) weren't processed due to their unknown format:\n"
        message += "\n".join(f"❌ {contact}" for contact in error_contacts)

    return await update.message.reply_text(message)


@sub_debug_logger
async def process_verifications(update: Update, content: str, action: str) -> Message:
    """
    Process adding or deleting verifications.

    Args:
        update (Update): The update object from Telegram.
        content (str): The message content containing verification information.
        action (str): The action to perform ('add' or 'del').
    """
    user_id = update.message.from_user.id
    valid_verifs, error_verifs = [], []

    for line in content.splitlines():
        if action == 'add':
            if match := re.match(r'^(0[0-9]|1[0-9]|2[0-3]):([0-5][0-9]) *- *([\w ]+)', line):
                chosen_time, desc = f"{match.group(1)}:{match.group(2)}", match.group(3)
                valid_verifs.append({"time": chosen_time, "description": desc, "active": True})
            else:
                error_verifs.append(line)
        else:
            if match := re.match(r'^(0[0-9]|1[0-9]|2[0-3]):([0-5][0-9])$', line):
                valid_verifs.append(f"{match.group(1)}:{match.group(2)}")
            else:
                error_verifs.append(line)

    not_valid = []
    message, base_message = "", ""
    if len(valid_verifs) > 0:
        if action == 'add':
            not_valid = RequestManager.add_verifications(user_id, valid_verifs, skip_check=False)
            base_message = "Given daily verification(s) are now added to your account. 📅🔐\n"
            if not_valid:
                message += ("\nFollowing verification(s) weren't added. Make sure to "
                            "space daily messages at least 20 minutes apart:\n")
                message += "\n".join(f"❌ {verif}" for verif in not_valid)
        else:
            RequestManager.del_verifications(user_id, valid_verifs)
            base_message = "Given daily verification(s) are now deleted from your account.🚫📅\n"

    message = f"{base_message if len(not_valid) != len(valid_verifs) else ''}" + message
    if error_verifs:
        message += "\nFollowing verification(s) weren't processed due to their unknown format:\n"
        message += "\n".join(f"❌ {verif}" for verif in error_verifs)

    return await update.message.reply_text(message)


@sub_debug_logger
async def extract_bugreport(update: Update, content: str) -> Message:
    """
    Extract and save a bug report.

    Args:
        update (Update): The update object from Telegram.
        content (str): The bug report content.
    """
    user = update.effective_user
    user_id = user.id
    username = user.username or user.first_name

    report_id = RequestManager.write_bug_report(user_id, username, content)
    return await update.message.reply_text(f"Thank you for the report! Your report ID is: {report_id}")


@sub_debug_logger
async def process_alarm(update: Update, content: str, action: str) -> Message:
    """
    Process skipping or undoing skip for alarms.

    Args:
        update (Update): The update object from Telegram.
        content (str): The message content containing alarm information.
        action (str): The action to perform ('skip' or 'undoskip').
    """
    user_id = update.message.from_user.id
    valid_alarms, error_alarms = [], []

    for line in content.splitlines():
        if match := re.match(r'^(0[0-9]|1[0-9]|2[0-3]):([0-5][0-9])$', line):
            valid_alarms.append(f"{match.group(1)}:{match.group(2)}")
        else:
            error_alarms.append(line)

    if action == 'skip':
        RequestManager.skip_verifications(user_id, valid_alarms)
    elif action == 'undoskip':
        RequestManager.undoskip_verifications(user_id, valid_alarms)

    message = (f"Given daily verification(s) are now {'skipped for the next 24h' if action == 'skip' else 'activated'}."
               f"{'⏰✨' if action == 'skip' else '🔐🔄'}\n")

    if error_alarms:
        message += f"\nFollowing verification(s) weren't {action}ped due to their unknown format:\n"
        message += "\n".join(f"❌ {alarm}" for alarm in error_alarms)

    return await update.message.reply_text(message)


@sub_debug_logger
async def extract_fastcheck(update: Update, content: str) -> Message:
    """
    Extract and process a fast check request.

    Args:
        update (Update): The update object from Telegram.
        content (str): The message content containing fast check information.
    """
    user_id = update.message.from_user.id
    if not (match := re.match(r'(\d+) *mn', content)):
        return await update.message.reply_text(f"Unknown format: \"{content}\".")

    waiting_time = int(match.group(1))
    if waiting_time > 20:
        return await update.message.reply_text("Invalid time, 20mn max")

    check_time = datetime.now() + timedelta(minutes=waiting_time)
    time_to_display = check_time.strftime("%H:%M")

    new_alarm = {"time": time_to_display, "description": "Auto fast check", "active": None}
    RequestManager.add_verifications(user_id, [new_alarm], skip_check=True)

    message = f"Fast Check in {waiting_time}mn taken into account! ({time_to_display}) 🚀"
    return await update.message.reply_text(message)


async def state_dispatcher(update: Update, state: str, message_body: str) -> Message:
    """
    Dispatch the appropriate function based on the current state.

    Args:
        update (Update): The update object from Telegram.
        state (str): The current state of the conversation.
        message_body (str): The message content.
    """
    username = update.message.from_user.username
    switch_dict = {
        "addcontact": lambda: process_contacts(update, message_body, "add"),
        "delcontact": lambda: process_contacts(update, message_body, "del"),
        "addverif": lambda: process_verifications(update, message_body, "add"),
        "delverif": lambda: process_verifications(update, message_body, "del"),
        "bugreport": lambda: extract_bugreport(update, message_body),
        "skip": lambda: process_alarm(update, message_body, "skip"),
        "undoskip": lambda: process_alarm(update, message_body, "undoskip"),
        "fastcheck": lambda: extract_fastcheck(update, message_body),
    }

    logger.debug(f"└── User @{username} answered to call '{state or 'empty'}' with content: '{update.message.text}'")
    return await switch_dict.get(state, lambda: update.message.reply_text("Excuse me, I didn't quite understand your request. 🤔"))()


@commands.verify_condition
async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE, **kwargs) -> Message:
    """
    Handle incoming messages and route them to the appropriate function.

    Args:
        update (Update): The update object from Telegram.
        context (ContextTypes.DEFAULT_TYPE): The context object for the handler.
    """
    user_id = update.message.from_user.id
    response_message, alert_mode = RequestManager.user_information(user_id)

    if response_message:
        get_state = RequestManager.read_user_properties(user_id, "state")
        RequestManager.update_user_properties(user_id, "state", "")
        return await state_dispatcher(update, get_state, update.message.text)

    if not alert_mode:
        logger.debug('└── User response to verification demand')
        greeting = "Have a great day 🌞!" if datetime.now().hour < 16 else "Have a wonderful afternoon 🌅!"
        response = f"Thank you for your response! {greeting}"
        RequestManager.update_user_properties(user_id, "response_message", True)
        return await update.message.reply_text(response)

    logger.debug('└── User response to unset the alert mode')
    RequestManager.update_user_properties(user_id, "alert_mode", False)
    RequestManager.update_user_properties(user_id, "response_message", True)
    await manual_undohelp(user_id, update.message.from_user.username)
    return await send_hope_message(update)


async def error(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log errors caused by updates."""
    logger.error(f'/!\ Update {update} caused error {context.error}')


@debug_logger
async def manual_help(user_id: int, username: str) -> None:
    """
    Send a manual help alert to user's contacts.

    Args:
        user_id (int): The user's ID.
        username (str): The user's username.
    """
    message = (f"🚨<b>ALERT</b>🚨. @{username} has manually triggered the call for help."
               " <b>Please take this call seriously and ensure their well-being!</b>")

    for contact in RequestManager.read_contacts_properties(user_id):
        if contact["pair"]:
            await bot.send_message(chat_id=contact["id"], text=message, parse_mode=ParseMode.HTML)


@debug_logger
async def manual_undohelp(user_id: int, username: str) -> None:
    """
    Send a manual undo help alert to user's contacts.

    Args:
        user_id (int): The user's ID.
        username (str): The user's username.
    """
    message = (f"⚠️<b>Alert disabled</b>⚠️. @{username} manually disabled the alert."
               " <b>Please confirm it was intentional or check if it was a simple mistake.</b>")

    for contact in RequestManager.read_contacts_properties(user_id):
        if contact["pair"]:
            await bot.send_message(chat_id=contact["id"], text=message, parse_mode=ParseMode.HTML)


@debug_logger
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Message:
    """
    Handle button callback queries.

    Args:
        update (Update): The update object from Telegram.
        context (ContextTypes.DEFAULT_TYPE): The context object for the handler.
    """
    query = update.callback_query
    user_id = query.from_user.id

    await query.answer()

    if not query.data:
        return await query.edit_message_text(text=f"Unknown: Query data empty ({query.data})")

    if query.data == "1":
        RequestManager.update_user_properties(user_id, "alert_mode", True)
        message = ("OK. Emergency contacts have received your request for help! 🆘\n"
                   "Type /undohelp to cancel the alert.")
        await manual_help(user_id, query.from_user.username)
    elif query.data == "2":
        message = "OK 😅. Glad to hear it was a mistake!"
    elif query.data == "3":
        RequestManager.update_user_properties(user_id, "alert_mode", False)
        message = "OK. Your emergency contacts have received information that the alert has been disabled. 📢"
        await manual_undohelp(user_id, query.from_user.username)
    elif query.data == "4":
        message = "OK. Operation canceled."
    elif query.data[0] == "-":
        contact_request = RequestManager.read_contact_requests_properties(user_id)
        del contact_request[query.data[1:]]
        RequestManager.update_user_properties(user_id, "contact_request", contact_request)
        message = "<b>OK. Association request declined. ❌</b>"
    else:
        origin_id = int(query.data[1:])
        contacts_pairing = RequestManager.read_contacts_properties(origin_id)
        updated_pairing = [{"id": contact['id'], "pair": True if contact['id'] == user_id else contact['pair']}
                           for contact in contacts_pairing]

        RequestManager.update_user_properties(origin_id, "contacts", updated_pairing)
        users_data = RequestManager.username_from_user_id()

        contact_request = RequestManager.read_contact_requests_properties(user_id)
        del contact_request[query.data[1:]]
        RequestManager.update_user_properties(user_id, "contact_request", contact_request)

        logger.debug(f"API: Response message to association with {origin_id}")
        await bot.send_message(
            chat_id=origin_id,
            text=f"<b>@{query.from_user.username} has accepted your association "
                 f"request and will be contacted in the event of an emergency. 🤝</b>",
            parse_mode=ParseMode.HTML
        )

        message = (f"<b>Successful association @{users_data[query.data[1:]]} 🎉. "
                   f"You will now be informed if this person no longer gives any news.</b>")

    return await query.edit_message_text(text=message, parse_mode=ParseMode.HTML)


def run_api():
    """Initialize and run the Telegram bot."""
    logger.info('API: Starting bot...')

    app = Application.builder().token(TOKEN).build()

    # Commands
    command_handlers = [
        ('start', commands.start_command),
        ('subscribe', commands.start_command),
        ('info', commands.info_command),
        ('help', commands.help_command),
        ('undohelp', commands.undohelp_command),
        ('bugreport', commands.bugreport_command),
        ('addcontact', commands.addcontact_command),
        ('showcontacts', commands.showcontacts_command),
        ('delcontact', commands.delcontact_command),
        ('addverif', commands.addverif_command),
        ('showverifs', commands.showverifs_command),
        ('delverif', commands.delverif_command),
        ('skip', commands.skip_command),
        ('undoskip', commands.undoskip_command),
        ('fastcheck', commands.fastcheck_command),
        ('stop', commands.kill_user_data),
        ('unsubscribe', commands.kill_user_data),
        ('request', commands.request_command),
        ('empty', commands.empty_command),
    ]

    for command, handler in command_handlers:
        app.add_handler(CommandHandler(command, handler))

    # Buttons under text
    app.add_handler(CallbackQueryHandler(button))

    # Messages
    app.add_handler(MessageHandler(filters.TEXT, handle_messages))

    # Errors
    app.add_error_handler(error)

    # Polls the bot
    logger.info('API: Bot is running...')
    app.run_polling()

if __name__ == "__main__":
    run_api()