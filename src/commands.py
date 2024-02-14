from telegram import Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from utils.env_pipeline import AccessEnv


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):  # TODO PAIRING
    user_id = update.message.from_user.id
    username = update.message.from_user.username
    if user_id not in AccessEnv.on_get_users():
        AccessEnv.on_create_user(user_id, username)

    user_first_name: str = str(update.message.chat.first_name)
    return await update.message.reply_text(f"Hello {user_first_name}! Thanks for chatting with me! I am a "
                                           f"Safeguard.io bot")


async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = ("I make sure everything is okay! ;). Here are commands to interact with me\n\n"
               "/start - start the conversation with the bot\n"
               "/info - get bot usage\n"
               "/help - ask for help to emergency contacts\n"
               "/undohelp - disable emergency alert\n"
               "/addcontact - add emergency contacts\n"
               "/showcontacts - show emergency contacts\n"
               "/delcontact - delete emergency contacts\n"
               "/addverif - add daily verification\n"
               "/showverifs - show daily verfications\n"
               "/delverif - delete daily verifications\n"
               "/skip - skip next verification\n"
               "/undoskip - activate back skipped verification\n"
               "/bugreport - report a bug\n"
               "/fastcheck - quick verification")

    return await update.message.reply_text(message)


async def addcontact_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = ("OK. Send me a list of contacts to add. Please use this format:\n\n"
               "@username1\n"
               "@username2\n\n"
               "Send /empty to keep the list empty.")

    user_id = update.message.from_user.id
    if len(AccessEnv.on_read(user_id, "contacts")) > 9:
        message = "You cannot add an additional contacts (10 max)."
        return await update.message.reply_text(message)

    AccessEnv.on_write(user_id, "state", "addcontact")

    return await update.message.reply_text(message)


async def showcontacts_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = "OK. Here is you list of contacts:\n\n"  # TODO list contacts, + show pairing

    user_id = update.message.from_user.id
    contact_list = AccessEnv.on_read(user_id, "contacts")

    if len(contact_list) == 0:
        return await update.message.reply_text("There is no emergency contact to display.")

    for contact, pairing in contact_list:
        if pairing:
            message += AccessEnv.on_read(int(contact), "username") + f" - OK\n"
            continue

        message += AccessEnv.on_read(int(contact), "username") + f" - waiting for pairing\n"

    return await update.message.reply_text(message)


async def delcontact_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = ("OK. Chose the contact to delete.\n"
               "Send /empty to empty the current list.") #TODO impossible de revenir en arrière

    user_id = update.message.from_user.id
    if len(AccessEnv.on_read(user_id, "contacts")) == 0:
        message = "No contact to delete."
        return await update.message.reply_text(message)

    get_contacts = AccessEnv.on_read(user_id, "contacts")
    display = [contact[0] for contact in get_contacts]

    reply_markup = ReplyKeyboardMarkup([display], resize_keyboard=True, one_time_keyboard=True)

    AccessEnv.on_write(user_id, "state", "delcontact")
    return await update.message.reply_text(message, reply_markup=reply_markup)


async def addverif_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = ("OK. Send me a list of daily verifications to add. Please use this format:\n\n"
               "08:05 - Awakening\n"
               "21:30 - End of the day\n\n"
               "Send /empty to keep the list empty.")

    user_id = update.message.from_user.id
    if len(AccessEnv.on_read(user_id, "daily_message")) > 5:
        message = "You cannot add an additional daily check."
        return await update.message.reply_text(message)

    AccessEnv.on_write(user_id, "state", "addverif")
    return await update.message.reply_text(message)


async def showverifs_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = "OK. Here is you list of daily verifications:\n"
    user_id = update.message.from_user.id
    verif_list = AccessEnv.on_read(user_id, "daily_message")

    if len(verif_list) == 0:
        return await update.message.reply_text("There is no daily check to display.")

    sorted_list = sorted(verif_list, key=lambda x: (x[0], x[1]))

    skipped_verif = "\nSkipped today:\n"
    skip_bool, active = False, True
    for verif in sorted_list:
        if verif[3] or verif[3] is None:
            message += f"\n{verif[0]}:{verif[1]} - {verif[2]}\n"
            active = False
            continue

        skipped_verif += f"\n{verif[0]}:{verif[1]} - {verif[2]}"
        skip_bool = True

    message += "No daily check for the next 24 hours.\n" if active else ""
    message += skipped_verif if skip_bool else ""
    return await update.message.reply_text(message)


async def delverif_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = ("OK. Chose the daily verifications to delete.\n"
               "Send /empty to empty the current list.")

    user_id = update.message.from_user.id
    verif_list = AccessEnv.on_read(user_id, "daily_message")

    if len(AccessEnv.on_read(user_id, "daily_message")) == 0:
        message = "No daily message to delete."
        return await update.message.reply_text(message)

    sorted_list = sorted(verif_list, key=lambda x: (x[0], x[1]))

    keyboard = [
        [f"{elt[0]}:{elt[1]}" for elt in sorted_list],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

    AccessEnv.on_write(user_id, "state", "delverif")
    return await update.message.reply_text(message, reply_markup=reply_markup)


async def skip_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = "OK. Chose the daily verifications to skip."

    user_id = update.message.from_user.id
    verif_list = AccessEnv.on_read(user_id, "daily_message")
    verif_list = list(filter(lambda x: x[3], verif_list))
    sorted_list = sorted(verif_list, key=lambda x: (x[0], x[1]))

    keyboard = [
        [f"{elt[0]}:{elt[1]}" for elt in sorted_list],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

    AccessEnv.on_write(user_id, "state", "skip")
    return await update.message.reply_text(message, reply_markup=reply_markup)


async def undoskip_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = "OK. Chose the daily verifications to skip."

    user_id = update.message.from_user.id
    verif_list = AccessEnv.on_read(user_id, "daily_message")
    verif_list = list(filter(lambda x: not x[3], verif_list))
    sorted_list = sorted(verif_list, key=lambda x: (x[0], x[1]))

    keyboard = [
        [f"{elt[0]}:{elt[1]}" for elt in sorted_list],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

    AccessEnv.on_write(user_id, "state", "undoskip")
    return await update.message.reply_text(message, reply_markup=reply_markup)


async def bugreport_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = ("OK. Please describe the bug and what you did to see it")

    user_id = update.message.from_user.id
    AccessEnv.on_write(user_id, "state", "bugreport")
    return await update.message.reply_text(message)


async def fastcheck_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = ("OK. How soon do you want to have the quick check? (< 20 mn).")  # TODO add time + description

    keyboard = [
        ["5 mn", "10 mn", "15 mn", "20 mn"],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

    user_id = update.message.from_user.id
    AccessEnv.on_write(user_id, "state", "fastcheck")

    return await update.message.reply_text(message, reply_markup=reply_markup)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    alert_mode = AccessEnv.on_read(user_id, "alert_mode")
    if alert_mode:
        return await update.message.reply_text("You are already in alert mode!")

    AccessEnv.on_write(user_id, "reminder_count", 0)
    if not AccessEnv.on_read(user_id, "response_message"):
        AccessEnv.on_write(user_id, "response_message", True)
        await update.message.reply_text("Answer received, daily verification disabled...")

    message = "Do you want to notify emergency contacts?"  # TODO add time + description
    keyboard = [
        [
            InlineKeyboardButton("Yes", callback_data="1"),
            InlineKeyboardButton("No", callback_data="2"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    return await update.message.reply_text(message, reply_markup=reply_markup)


async def undohelp_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if not AccessEnv.on_read(user_id, "alert_mode"):
        return await update.message.reply_text("This operation can only be used in alert state!")

    response = "Do you want to cancel the alert?"  # TODO add time + description
    keyboard = [
        [
            InlineKeyboardButton("Yes", callback_data="3"),
            InlineKeyboardButton("No", callback_data="4"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    return await update.message.reply_text(response, reply_markup=reply_markup)
