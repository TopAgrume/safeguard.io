from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from utils.env_pipeline import AccessEnv
import telegram

P_HTML = telegram.constants.ParseMode.HTML


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):  # TODO PAIRING
    user_id = update.message.from_user.id
    username = update.message.from_user.username

    print("COMMAND:", f"Start {username}")
    if str(user_id) not in AccessEnv.on_get_users():
        AccessEnv.on_create_user(user_id, username)
    else:
        print("COMMAND:", "Already inside")

    user_first_name: str = str(update.message.chat.first_name)
    message = f"Hello {user_first_name}! Thanks for chatting with me! I am a Safeguard.io bot"
    return await update.message.reply_text(message)


async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = ("I make sure everything is okay! Here are commands to interact with me ;).\n"
               "\n<b>Edit bot configuration</b>\n"
               "/start - start the conversation with the bot\n"
               "/info - get bot usage\n"
               "/stop or /unsubscribe - delete personal data\n"
               "\n<b>In case of emergency</b>\n"
               "/help - ask for help to emergency contacts\n"
               "/undohelp - disable emergency alert\n"
               "\n<b>Edit emergency contacts</b>\n"
               "/addcontact - add emergency contacts\n"
               "/showcontacts - show emergency contacts\n"
               "/delcontact - delete emergency contacts\n"
               "\n<b>Edit daily messages</b>\n"
               "/addverif - add daily verification\n"
               "/showverifs - show daily verfications\n"
               "/delverif - delete daily verifications\n"
               "/skip - skip next verification\n"
               "/undoskip - activate back skipped verification\n"
               "/fastcheck - quick verification\n"
               "\n<b>Miscellaneous</b>\n"
               "/bugreport - report a bug")

    print("COMMAND:", f"Info")
    return await update.message.reply_text(message, parse_mode=P_HTML)


async def addcontact_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("COMMAND:", f"AddContact")
    message = ("OK. Send me a list of contacts to add.\n"
               "<b>Please use this format:</b>\n\n"
               "<b>@username1</b>\n"
               "<b>@username2</b>\n\n"
               "Send /empty to keep the list empty.")

    user_id = update.message.from_user.id
    if len(AccessEnv.on_read(user_id, "contacts")) > 9:
        message = "You cannot add an additional contacts (10 max)."
        return await update.message.reply_text(message)

    AccessEnv.on_write(user_id, "state", "addcontact")

    return await update.message.reply_text(message, parse_mode=P_HTML)


async def showcontacts_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("COMMAND:", f"ShowContacts")
    message = "OK. Here is you list of contacts:\n\n"  # TODO list contacts, + show pairing

    user_id = update.message.from_user.id
    contact_list = AccessEnv.on_read(user_id, "contacts")

    if len(contact_list) == 0:
        return await update.message.reply_text("There is no emergency contact to display.")

    for contact in contact_list:
        if contact['pair']:
            message += f"<b>@{contact['tag']}</b> - <b>OK</b>\n"
            continue

        message += f"<b>@{contact['tag']}</b> - waiting for pairing\n"

    return await update.message.reply_text(message, parse_mode=P_HTML)


async def delcontact_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("COMMAND:", f"DeleteContact")
    message = ("OK. Chose the contact to delete.\n"
               "Send /empty to empty the current list.")  # TODO impossible de revenir en arrière

    user_id = update.message.from_user.id
    if len(AccessEnv.on_read(user_id, "contacts")) == 0:
        message = "<b>No contact to delete.</b>"
        return await update.message.reply_text(message)

    get_contacts = AccessEnv.on_read(user_id, "contacts")
    display = ['@' + contact['tag'] for contact in get_contacts]

    reply_markup = ReplyKeyboardMarkup([display], resize_keyboard=True, one_time_keyboard=True)

    AccessEnv.on_write(user_id, "state", "delcontact")
    return await update.message.reply_text(message, reply_markup=reply_markup, parse_mode=P_HTML)


async def addverif_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("COMMAND:", f"AddDailyCheck")
    message = ("OK. Send me a list of daily verifications to add. <b>Please use this format</b>:\n\n"
               "08:05 - Awakening\n"
               "21:30 - End of the day\n\n"
               "Send /empty to keep the list empty.")

    user_id = update.message.from_user.id
    if len(AccessEnv.on_read(user_id, "daily_message")) > 5:
        message = "<b>You cannot add an additional daily check.</b>"
        return await update.message.reply_text(message, parse_mode=P_HTML)

    AccessEnv.on_write(user_id, "state", "addverif")
    return await update.message.reply_text(message, parse_mode=P_HTML)


async def showverifs_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("COMMAND:", f"ShowDailyChecks")
    message = "OK. Here is you list of daily verifications:\n"
    user_id = update.message.from_user.id
    verif_list = AccessEnv.on_read(user_id, "daily_message")

    if len(verif_list) == 0:
        message = "<b>There is no daily check to display.</b>"
        return await update.message.reply_text(message, parse_mode=P_HTML)

    sorted_list = sorted(verif_list, key=lambda x: x["time"])

    skipped_verif = "\n<b>Skipped today:</b>\n"
    skip_bool, active = False, True
    for verif in sorted_list:
        if verif["active"] or verif["active"] is None:
            message += f"\n<b>{verif['time']}</b> - {verif['desc']}"
            active = False
            continue

        skipped_verif += f"\n<b>{verif['time']}</b> - {verif['desc']}"
        skip_bool = True

    message += "<b>No daily check for the next 24 hours.</b>\n" if active else ""
    message += skipped_verif if skip_bool else ""
    return await update.message.reply_text(message, parse_mode=P_HTML)


async def delverif_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("COMMAND:", f"DeleteDailyChecks")
    message = ("OK. Chose the daily verifications to delete.\n"
               "Send /empty to empty the current list.")

    user_id = update.message.from_user.id
    verif_list = AccessEnv.on_read(user_id, "daily_message")

    if len(AccessEnv.on_read(user_id, "daily_message")) == 0:
        message = "<b>No daily message to delete.</b>"
        return await update.message.reply_text(message, parse_mode=P_HTML)

    sorted_list = sorted(verif_list, key=lambda x: x["time"])

    keyboard = [
        [f"{elt['time']}" for elt in sorted_list],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

    AccessEnv.on_write(user_id, "state", "delverif")
    return await update.message.reply_text(message, reply_markup=reply_markup)


async def skip_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("COMMAND:", f"SkipDailyCheck")
    message = "OK. Chose the daily verifications to skip."

    user_id = update.message.from_user.id
    verif_list = AccessEnv.on_read(user_id, "daily_message")
    verif_list = list(filter(lambda x: x["active"], verif_list))

    if len(verif_list) == 0:
        message = "<b>No daily message to skip.</b>"
        return await update.message.reply_text(message, parse_mode=P_HTML)

    sorted_list = sorted(verif_list, key=lambda x: x['time'])

    keyboard = [
        [f"{elt['time']}" for elt in sorted_list],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

    AccessEnv.on_write(user_id, "state", "skip")
    return await update.message.reply_text(message, reply_markup=reply_markup)


async def undoskip_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("COMMAND:", f"Undo SkipDailyCheck")
    message = "OK. Chose the daily verifications to skip."

    user_id = update.message.from_user.id
    verif_list = AccessEnv.on_read(user_id, "daily_message")
    verif_list = list(filter(lambda x: not x['active'], verif_list))

    if len(verif_list) == 0:
        message = "<b>No daily message skip to undo.</b>"
        return await update.message.reply_text(message, parse_mode=P_HTML)

    sorted_list = sorted(verif_list, key=lambda x: x['time'])

    keyboard = [
        [f"{elt['time']}" for elt in sorted_list],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

    AccessEnv.on_write(user_id, "state", "undoskip")
    return await update.message.reply_text(message, reply_markup=reply_markup)


async def bugreport_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("COMMAND:", f"Bug Report")
    message = "OK. Please describe the bug and what you did to see it"

    user_id = update.message.from_user.id
    AccessEnv.on_write(user_id, "state", "bugreport")
    return await update.message.reply_text(message)


async def fastcheck_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("COMMAND:", f"Fast Check")
    message = "OK. How soon do you want to have the quick check? <b>(less than 20mn)</b>"  # TODO add time + description

    keyboard = [
        ["5 mn", "10 mn", "15 mn", "20 mn"],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

    user_id = update.message.from_user.id
    AccessEnv.on_write(user_id, "state", "fastcheck")

    return await update.message.reply_text(message, reply_markup=reply_markup, parse_mode=P_HTML)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("COMMAND:", f"Help")
    user_id = update.message.from_user.id
    alert_mode = AccessEnv.on_read(user_id, "alert_mode")
    if alert_mode:
        message = "<b>You are already in alert mode!</b>"
        return await update.message.reply_text(message, parse_mode=P_HTML)

    AccessEnv.on_write(user_id, "reminder_count", 0)
    if not AccessEnv.on_read(user_id, "response_message"):
        AccessEnv.on_write(user_id, "response_message", True)
        await update.message.reply_text("Answer received, daily verification off...")

    message = "<b>Do you want to notify emergency contacts?</b>"  # TODO add time + description
    keyboard = [
        [
            InlineKeyboardButton("Yes", callback_data="1"),
            InlineKeyboardButton("No", callback_data="2"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    return await update.message.reply_text(message, reply_markup=reply_markup, parse_mode=P_HTML)


async def undohelp_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("COMMAND:", f"Undo help")
    user_id = update.message.from_user.id
    if not AccessEnv.on_read(user_id, "alert_mode"):
        message = "<b>This operation can only be used in alert state!</b>"
        return await update.message.reply_text(message, parse_mode=P_HTML)

    response = "<b>Do you want to cancel the alert?</b>"  # TODO add time + description
    keyboard = [
        [
            InlineKeyboardButton("Yes", callback_data="3"),
            InlineKeyboardButton("No", callback_data="4"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    return await update.message.reply_text(response, reply_markup=reply_markup, parse_mode=P_HTML)


async def kill_user_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("COMMAND:", f"Kill user data")
    user_id = update.message.from_user.id
    AccessEnv.on_kill_data(user_id)
    message = "<b>Your personal data has been deleted</b>"
    return await update.message.reply_text(message, parse_mode=P_HTML)
