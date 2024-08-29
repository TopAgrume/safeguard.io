from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, Message
from telegram.ext import ContextTypes
from src.utils.env_pipeline import RequestManager
import telegram
from logzero import logger
from functools import wraps
from typing import Any, Callable

TOKEN, BOT_USERNAME = RequestManager.telegram_keys()
P_HTML = telegram.constants.ParseMode.HTML


def verify_condition(func: Callable) -> Callable: # VALID
    """
    Decorator to verify conditions before executing bot commands.

    This decorator checks if:
    1. The message is from a group (not supported)
    2. The user has a username (required)

    If conditions are not met, appropriate messages are sent to the user.

    Args:
        func (Callable): The function to be decorated.

    Returns:
        Callable: The wrapped function.
    """
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, **kwargs: Any) -> Any:
        logger.debug(f"{'API' if func.__name__ == 'handle_messages' else 'COMMAND'}: {func.__name__} call")

        message = update.message
        chat_type = message.chat.type

        if chat_type == 'group':
            if BOT_USERNAME.lower() in message.text.lower():
                await message.reply_text('This bot does not support groups for now. 🚫')
            return

        username = message.from_user.username
        if not username:
            await message.reply_text(
                "Please <b>create a username</b> in your Telegram profile to use my features. "
                "Then use <b>/start</b> if you are not already registered 📲✨.",
                parse_mode=P_HTML
            )
            return

        return await func(update, context, **kwargs)

    return wrapper


@verify_condition
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE, **kwargs) -> Message:
    """
    Handle the /start command for the Telegram bot.

    This function:
    1. Checks if the user is already registered
    2. Registers new users
    3. Processes any pending contact requests for the user
    4. Sends a welcome message

    Args:
        update (Update): The incoming update.
        context (ContextTypes.DEFAULT_TYPE): The context object for the update.
        **kwargs: Additional keyword arguments.

    Returns:
        Message: Response message from the bot.
    """
    user = update.message.from_user
    user_id, username = user.id, user.username

    if RequestManager.user_already_registered(user_id):
        logger.debug(f"└── User @{username} already registered")
        message = "Your profile is already linked with Safeguard.io!"
        return await update.message.reply_text(message)

    RequestManager.on_create_user(user_id, username)
    logger.debug(f"└── New user @{username} registered")

    message = f"Hello {user.first_name} 🌟! Thanks for chatting with me! I am Safeguard.io 😊."
    await update.message.reply_text(message)

    requester_keys = RequestManager.transfer_pending_requests(user_id, username)
    logger.debug(f"└── New user @{username} has {len(requester_keys)} pending contact requests")
    for contact_key in requester_keys:
        RequestManager.update_contacts_properties(contact_key, "contact_id", user_id)

    return await request_command(update, context, quiet=True)


@verify_condition # VALID
async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE, **kwargs) -> Message:
    """
    Handle the /info command, providing information about bot usage.

    Args:
        update (Update): The incoming update.
        context (ContextTypes.DEFAULT_TYPE): The context object for the update.
        **kwargs: Additional keyword arguments.

    Returns:
        Message: Response message from the bot.
    """
    message = ("Welcome! I'm here to ensure everything is smooth for you. Use these commands to interact with me:\n"
               "\n<b>Edit bot configuration</b>\n"
               "/start or /subscribe - Initiate a conversation with me.\n"
               "/stop or /unsubscribe - Delete personal related data.\n"
               "/info - Receive information on how to use the bot.\n"
               "\n<b>In case of emergency</b>\n"
               "/help - Request emergency assistance from your contacts.\n"
               "/undohelp - Disable emergency alerts.\n"
               "\n<b>Edit emergency contacts</b>\n"
               "/addcontact - Add new emergency contacts.\n"
               "/showcontacts - Display your list of emergency contacts.\n"
               "/delcontact - Delete specific emergency contacts.\n"
               "/request - View received association requests.\n"
               "\n<b>Edit daily messages</b>\n"
               "/addverif - Add a daily verification message.\n"
               "/showverifs - Display your list of daily verifications.\n"
               "/delverif - Delete specific daily verifications.\n"
               "/skip - Skip the next verification.\n"
               "/undoskip - Activate the previously skipped verification.\n"
               "/fastcheck - Perform a quick verification.\n"
               "\n<b>Miscellaneous</b>\n"
               "/bugreport - Report any bugs you encounter or suggest improvements!\n\n"
               "Feel free to ask for assistance or information anytime! 😊")

    return await update.message.reply_text(message, parse_mode=P_HTML)


@verify_condition # VALID
async def addcontact_command(update: Update, context: ContextTypes.DEFAULT_TYPE, **kwargs) -> Message:
    """
    Handle the /addcontact command, allowing users to add emergency contacts.

    Args:
        update (Update): The incoming update.
        context (ContextTypes.DEFAULT_TYPE): The context object for the update.
        **kwargs: Additional keyword arguments.

    Returns:
        Message: Response message from the bot.
    """
    user_id = update.message.from_user.id
    username = update.message.from_user.username

    if len(RequestManager.read_contacts_properties(user_id)) > 9:
        logger.debug(f"└── User @{username} already have 10 contacts")
        message = "You cannot add an additional contacts (10 max). 🛑"
        return await update.message.reply_text(message)

    RequestManager.update_user_properties(user_id, "state", "addcontact")

    message = ("Sure thing! Please provide me with a list of contacts you'd like to add. 📋\n"
               "<b>Make sure to use the following format:</b>\n\n"
               "<b>@username1</b>\n"
               "<b>@username2</b>\n\n"
               "Send /empty to keep the list empty.")
    return await update.message.reply_text(message, parse_mode=P_HTML)


@verify_condition # VALID
async def showcontacts_command(update: Update, context: ContextTypes.DEFAULT_TYPE, **kwargs) -> Message:
    """
    Handle the /showcontacts command, displaying the user's emergency contacts.

    Args:
        update (Update): The incoming update.
        context (ContextTypes.DEFAULT_TYPE): The context object for the update.
        **kwargs: Additional keyword arguments.

    Returns:
        Message: Response message from the bot.
    """
    user_id = update.message.from_user.id
    contact_list = RequestManager.read_contacts_properties(user_id)
    username = update.message.from_user.username

    if len(contact_list) == 0:
        logger.debug(f"└── User @{username} does not have any contact")
        message = "<b>There is no emergency contact to display. 🆘</b>"
        return await update.message.reply_text(message, parse_mode=P_HTML)

    message = "Sure thing! Here is your list of contacts:\n\n"

    for contact_id, tag, pair in contact_list:
        status = "👤" if contact_id else "🚫"
        pair_status = "" if pair else " - Waiting for pairing."
        message += f"{status} <b>@{tag}</b>{pair_status}\n"

    return await update.message.reply_text(message, parse_mode=P_HTML)


@verify_condition # VALID
async def delcontact_command(update: Update, context: ContextTypes.DEFAULT_TYPE, **kwargs) -> Message:
    """
    Handle the /delcontact command, allowing users to delete emergency contacts.

    Args:
        update (Update): The incoming update.
        context (ContextTypes.DEFAULT_TYPE): The context object for the update.
        **kwargs: Additional keyword arguments.

    Returns:
        Message: Response message from the bot.
    """
    user_id = update.message.from_user.id
    user_contacts = RequestManager.read_contacts_properties(user_id)
    username = update.message.from_user.username

    if len(user_contacts) == 0:
        logger.debug(f"└── User @{username} does not have any contact to delete")
        message = "<b>No contact to delete. 📭</b>"
        return await update.message.reply_text(message, parse_mode=P_HTML)

    display = ['@' + tag for _, tag, _ in user_contacts]
    reply_markup = ReplyKeyboardMarkup([display], resize_keyboard=True, one_time_keyboard=True)

    RequestManager.update_user_properties(user_id, "state", "delcontact")

    message = "Sure! Chose the contact to delete.🗑️\n"
    return await update.message.reply_text(message, reply_markup=reply_markup, parse_mode=P_HTML)


@verify_condition # VALID
async def addverif_command(update: Update, context: ContextTypes.DEFAULT_TYPE, **kwargs) -> Message:
    """
    Handle the /addverif command, allowing users to add daily verification messages.

    Args:
        update (Update): The incoming update.
        context (ContextTypes.DEFAULT_TYPE): The context object for the update.
        **kwargs: Additional keyword arguments.

    Returns:
        Message: Response message from the bot.
    """
    user_id = update.message.from_user.id
    username = update.message.from_user.username

    if len(RequestManager.read_verifications_properties(user_id)) > 5:
        logger.debug(f"└── User @{username} already have 6 verifications")
        message = "<b>You cannot add an additional daily check (6 max). 🛑</b>"
        return await update.message.reply_text(message, parse_mode=P_HTML)

    RequestManager.update_user_properties(user_id, "state", "addverif")

    message = ("OK. Send me a list of daily verifications to add. 📅⏰\n"
               "<b>Please use this format</b>:\n\n"
               "08:05 - Awakening\n"
               "21:30 - End of the day\n\n"
               "Click /empty to cancel the operation.")
    return await update.message.reply_text(message, parse_mode=P_HTML)


@verify_condition # VALID
async def showverifs_command(update: Update, context: ContextTypes.DEFAULT_TYPE, **kwargs) -> Message:
    """
    Handle the /showverifs command, displaying the user's daily verification messages.

    Args:
        update (Update): The incoming update.
        context (ContextTypes.DEFAULT_TYPE): The context object for the update.
        **kwargs: Additional keyword arguments.

    Returns:
        Message: Response message from the bot.
    """
    user_id = update.message.from_user.id
    verif_list = RequestManager.read_verifications_properties(user_id)
    username = update.message.from_user.username

    if len(verif_list) == 0:
        logger.debug(f"└── User @{username} does not have any verification")
        message = "<b>There is no daily check to display. 📅</b>"
        return await update.message.reply_text(message, parse_mode=P_HTML)

    sorted_list = sorted(verif_list, key=lambda x: x[0])

    message = "OK. Here is your list of daily verifications:\n\n"
    skipped_verif = "\n\n<b>Skipped today:</b>\n\n"
    active_verifs = []
    skipped_verifs = []

    for time, desc, active in sorted_list:
        if active:
            active_verifs.append(f"🕗 <b>{time.hour:02}:{time.minute:02}</b> - {desc}")
        elif active is None:
            active_verifs.append(f"⏭️ <b>{time.hour:02}:{time.minute:02}</b> - {desc}")
        else:
            skipped_verifs.append(f"🚫 <b>{time.hour:02}:{time.minute:02}</b> - {desc}")

    message += "\n".join(active_verifs)
    message += "<b>No daily checks for the next 24 hours.</b> 📅" if not active_verifs else ""
    message += skipped_verif + "\n".join(skipped_verifs) if skipped_verifs else ""

    await update.message.reply_text(message, parse_mode=P_HTML)


@verify_condition # VALID
async def delverif_command(update: Update, context: ContextTypes.DEFAULT_TYPE, **kwargs) -> Message:
    """
    Handle the /delverif command, allowing users to delete daily verification messages.

    Args:
        update (Update): The incoming update.
        context (ContextTypes.DEFAULT_TYPE): The context object for the update.
        **kwargs: Additional keyword arguments.

    Returns:
        Message: Response message from the bot.
    """
    user_id = update.message.from_user.id
    username = update.message.from_user.username
    verif_list = RequestManager.read_verifications_properties(user_id)

    if len(verif_list) == 0:
        logger.debug(f"└── User @{username} does not have any verification to delete")
        message = "<b>No daily message to delete. 📅</b>"
        return await update.message.reply_text(message, parse_mode=P_HTML)

    sorted_list = sorted(verif_list, key=lambda x: x[0])

    keyboard =[f"{time.hour:02}:{time.minute:02}" for time, _, _ in sorted_list]
    reply_markup = ReplyKeyboardMarkup([keyboard], resize_keyboard=True, one_time_keyboard=True)

    RequestManager.update_user_properties(user_id, "state", "delverif")

    message = ("Alright! Please choose the daily verifications you'd like to delete. ❌🕒\n"
               "Click /empty to cancel the operation.")
    return await update.message.reply_text(message, reply_markup=reply_markup)


@verify_condition # VALID
async def skip_command(update: Update, context: ContextTypes.DEFAULT_TYPE, **kwargs) -> Message:
    """
    Handle the /skip command, allowing users to skip the next daily verification.

    Args:
        update (Update): The incoming update.
        context (ContextTypes.DEFAULT_TYPE): The context object for the update.
        **kwargs: Additional keyword arguments.

    Returns:
        Message: Response message from the bot.
    """
    user_id = update.message.from_user.id
    username = update.message.from_user.username

    verif_list = RequestManager.read_verifications_properties(user_id)
    verif_list = list(filter(lambda x: x[2], verif_list))

    if len(verif_list) == 0:
        logger.debug(f"└── User @{username} does not have daily message to skip")
        message = "<b>No daily message to skip. 📅</b>"
        return await update.message.reply_text(message, parse_mode=P_HTML)

    sorted_list = sorted(verif_list, key=lambda x: x[0])

    keyboard = [f"{time.hour:02}:{time.minute:02}" for time, _, _ in sorted_list]
    reply_markup = ReplyKeyboardMarkup([keyboard], resize_keyboard=True, one_time_keyboard=True)

    RequestManager.update_user_properties(user_id, "state", "skip")

    message = ("Sure! Please choose the daily verifications you'd like to skip. 🚫🕒\n"
               "Click /empty to cancel the operation.")
    return await update.message.reply_text(message, reply_markup=reply_markup)


@verify_condition # VALID
async def undoskip_command(update: Update, context: ContextTypes.DEFAULT_TYPE, **kwargs) -> Message:
    """
    Handle the /undoskip command, allowing users to undo skipped daily verifications.

    Args:
        update (Update): The incoming update.
        context (ContextTypes.DEFAULT_TYPE): The context object for the update.
        **kwargs: Additional keyword arguments.

    Returns:
        Message: Response message from the bot.
    """
    user_id = update.message.from_user.id
    username = update.message.from_user.username
    verif_list = RequestManager.read_verifications_properties(user_id)
    verif_list = list(filter(lambda x: not x[2], verif_list))

    if len(verif_list) == 0:
        logger.debug(f"└── User @{username} does not have daily message skip to undo")
        message = "<b>No daily message skip to undo. 📅</b>"
        return await update.message.reply_text(message, parse_mode=P_HTML)

    sorted_list = sorted(verif_list, key=lambda x: x[0])

    keyboard =[f"{time.hour:02}:{time.minute:02}" for time, _, active in sorted_list if active is not None]
    reply_markup = ReplyKeyboardMarkup([keyboard], resize_keyboard=True, one_time_keyboard=True)

    RequestManager.update_user_properties(user_id, "state", "undoskip")

    message = ("OK. Please choose the daily verifications you'd like to undo skip for. 🔄🕒\n"
               "Click /empty to cancel the operation.")
    return await update.message.reply_text(message, reply_markup=reply_markup)


@verify_condition # VALID
async def bugreport_command(update: Update, context: ContextTypes.DEFAULT_TYPE, **kwargs) -> Message:
    """
    Handle the /bugreport command, allowing users to report bugs or suggest improvements.

    Args:
        update (Update): The incoming update.
        context (ContextTypes.DEFAULT_TYPE): The context object for the update.
        **kwargs: Additional keyword arguments.

    Returns:
        Message: Response message from the bot.
    """
    user_id = update.message.from_user.id
    RequestManager.update_user_properties(user_id, "state", "bugreport")

    message = ("Sure! Please describe the bug and the steps you took to encounter it. 🐞📝\n"
               "Click /empty to cancel the operation.")
    return await update.message.reply_text(message)


@verify_condition # VALID
async def request_command(update: Update, context: ContextTypes.DEFAULT_TYPE, quiet: bool = False, **kwargs) -> Message:
    """
    Handle the /request command, showing and processing association requests.

    Args:
        update (Update): The incoming update.
        context (ContextTypes.DEFAULT_TYPE): The context object for the update.
        quiet (bool): If True, don't send a message if there are no requests.
        **kwargs: Additional keyword arguments.

    Returns:
        Message: Response message from the bot.
    """
    user_id = update.message.from_user.id
    username = update.message.from_user.username
    contact_request = RequestManager.read_contact_requests_properties(user_id)

    if len(contact_request) == 0 and not quiet:
        logger.debug(f"└── User @{username} does not have any association request")
        message = "<b>There is no association request. 🤷‍♂️</b>"
        return await update.message.reply_text(message, parse_mode=P_HTML)

    for id, username in contact_request:
        message = f"<b>Do you want to accept the pairing invitation from @{username} 🤝?</b>"

        keyboard = [
            [
                InlineKeyboardButton("Yes", callback_data=f"+{id}"),
                InlineKeyboardButton("No", callback_data=f"-{id}"),
            ],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode=P_HTML)


@verify_condition # VALID
async def fastcheck_command(update: Update, context: ContextTypes.DEFAULT_TYPE, **kwargs) -> Message:
    """
    Handle the /fastcheck command, allowing users to set up a quick verification.

    Args:
        update (Update): The incoming update.
        context (ContextTypes.DEFAULT_TYPE): The context object for the update.
        **kwargs: Additional keyword arguments.

    Returns:
        Message: Response message from the bot.
    """
    keyboard = ["5 mn", "10 mn", "15 mn", "20 mn"]
    reply_markup = ReplyKeyboardMarkup([keyboard], resize_keyboard=True, one_time_keyboard=True)

    user_id = update.message.from_user.id
    RequestManager.update_user_properties(user_id, "state", "fastcheck")

    message = ("Alright! When would you like to have the quick check? 🕒🚀 "
               "<b>(less than 20 minutes)</b>\n"
               "Click /empty to cancel the operation.")
    return await update.message.reply_text(message, reply_markup=reply_markup, parse_mode=P_HTML)


@verify_condition # VALID
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE, **kwargs) -> Message:
    """
    Handle the /help command, allowing users to notify emergency contacts.

    Args:
        update (Update): The incoming update.
        context (ContextTypes.DEFAULT_TYPE): The context object for the update.
        **kwargs: Additional keyword arguments.

    Returns:
        Message: Response message from the bot.
    """
    user_id = update.message.from_user.id
    username = update.message.from_user.username
    alert_mode = RequestManager.read_user_properties(user_id, "alert_mode")

    if alert_mode:
        logger.debug(f"└── User @{username} already in alert mode")
        message = "<b>You are already in alert mode! 🚨</b>"
        return await update.message.reply_text(message, parse_mode=P_HTML)

    if not RequestManager.read_user_properties(user_id, "response_message"):
        RequestManager.update_user_properties(user_id, "response_message", True)
        await update.message.reply_text("Answer received, daily verification has been turned off.")

    message = "<b>Do you want to notify emergency contacts? 🚨</b>"
    keyboard = [
        [
            InlineKeyboardButton("Yes", callback_data="1"),
            InlineKeyboardButton("No", callback_data="2"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    return await update.message.reply_text(message, reply_markup=reply_markup, parse_mode=P_HTML)


@verify_condition # VALID
async def undohelp_command(update: Update, context: ContextTypes.DEFAULT_TYPE, **kwargs) -> Message:
    """
    Handle the /undohelp command, allowing users to cancel the alert state.

    Args:
        update (Update): The incoming update.
        context (ContextTypes.DEFAULT_TYPE): The context object for the update.
        **kwargs: Additional keyword arguments.

    Returns:
        Message: Response message from the bot.
    """
    user_id = update.message.from_user.id
    username = update.message.from_user.username

    if not RequestManager.read_user_properties(user_id, "alert_mode"):
        logger.debug(f"└── User @{username} already in safe mode")
        message = "<b>This operation can only be used in alert state! ⚠️</b>"
        return await update.message.reply_text(message, parse_mode=P_HTML)

    response = "<b>Do you want to cancel the alert? 🤔</b>"
    keyboard = [
        [
            InlineKeyboardButton("Yes", callback_data="3"),
            InlineKeyboardButton("No", callback_data="4"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    return await update.message.reply_text(response, reply_markup=reply_markup, parse_mode=P_HTML)


@verify_condition # VALID
async def empty_command(update: Update, context: ContextTypes.DEFAULT_TYPE, **kwargs) -> Message:
    """
    Handle the /empty command, canceling the current operation.

    Args:
        update (Update): The incoming update.
        context (ContextTypes.DEFAULT_TYPE): The context object for the update.
        **kwargs: Additional keyword arguments.

    Returns:
        Message: Response message from the bot.
    """
    user_id = update.message.from_user.id
    RequestManager.update_user_properties(user_id, "state", "")
    message = "Sure thing! Operation canceled. ✅"
    return await update.message.reply_text(message)


@verify_condition # VALID
async def kill_user_data(update: Update, context: ContextTypes.DEFAULT_TYPE, **kwargs) -> Message:
    """
    Handle the command to delete all user data.

    Args:
        update (Update): The incoming update.
        context (ContextTypes.DEFAULT_TYPE): The context object for the update.
        **kwargs: Additional keyword arguments.

    Returns:
        Message: Response message from the bot.
    """
    user_id = update.message.from_user.id
    RequestManager.on_kill_data(user_id)
    message = "<b>Your personal data has been deleted.🗑️</b>"
    return await update.message.reply_text(message, parse_mode=P_HTML)
