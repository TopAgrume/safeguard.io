from telegram import Update, Bot
from telegram.ext import ContextTypes
from utils.env_pipeline import AccessEnv


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE): #TODO PAIRING
    user_id = update.message.from_user.id
    username = update.message.from_user.username
    if user_id not in AccessEnv.on_get_users():
        AccessEnv.on_create_user(user_id, username)

    user_first_name: str = str(update.message.chat.first_name)
    await update.message.reply_text(f"Hello {user_first_name}! Thanks for chatting with me! I am a Safeguard.io bot")


async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = ("I make sure everything is okay! ;). Here are commands to interact with me\n\n"
               "/start - start the conversation with the bot\n"
               "/info - get bot usage\n"
               "/help - ask for help to emergency contacts\n"
               "/addcontact - add emergency contacts\n"
               "/showcontacts - show emergency contacts\n"
               "/delcontact - delete emergency contacts\n"
               "/addverif - add daily verification\n"
               "/showverifs - show daily verfications\n"
               "/delverif - delete daily verifications\n"
               "/skip - skip next verification\n"
               "/bugreport - report a bug\n"
               "/fastcheck - quick verification")
    await update.message.reply_text(message)


async def addcontact_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = ("OK. Send me a list of contacts to add. Please use this format:\n\n"
               "@username1\n"
               "@username2\n\n"
               "Send /empty to keep the list empty.")

    user_id = update.message.from_user.id
    AccessEnv.on_write(user_id, "state", "addcontact")

    await update.message.reply_text(message)


async def showcontacts_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = "OK. Here is you list of contacts:\n\n"  # TODO list contacts, + show pairing
    user_id = update.message.from_user.id
    contact_list = AccessEnv.on_read(user_id, "contacts")

    for contact, pairing in contact_list:
        if pairing:
            message += AccessEnv.on_read(int(contact), "username") + f" - OK\n"
            continue

        message += AccessEnv.on_read(int(contact), "username") + f" - waiting for pairing\n"

    await update.message.reply_text(message)


async def delcontact_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = ("OK. Send me a list of contacts to delete. Please use this format:\n\n"
               "@username1\n"
               "@username2\n\n"
               "Send /empty to keep the current list.")

    user_id = update.message.from_user.id
    AccessEnv.on_write(user_id, "state", "delcontact")

    await update.message.reply_text(message)


async def addverif_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = ("OK. Send me a list of daily verifications to add. Please use this format:\n\n"
               "8:20 - Awakening\n"
               "21:30 - End of the day\n\n"
               "Send /empty to keep the list empty.")

    user_id = update.message.from_user.id
    AccessEnv.on_write(user_id, "state", "addverif")
    await update.message.reply_text(message)


async def showverifs_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = "OK. Here is you list of daily verifications:\n\n"
    user_id = update.message.from_user.id
    verif_list = AccessEnv.on_read(user_id, "daily_message")
    sorted_list = sorted(verif_list, key=lambda x: (int(x[0]), int(x[1])))

    for verif in sorted_list:
        message += f"{verif[0]}:{verif[1]} - {verif[2]}\n"

    await update.message.reply_text(message)


async def delverif_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = ("OK. Send me a list of daily verifications to delete. Please use this format:\n\n"
               "8:20\n"
               "21:30\n\n"
               "Send /empty to keep the list empty.")

    user_id = update.message.from_user.id
    AccessEnv.on_write(user_id, "state", "delverif")
    await update.message.reply_text(message)


async def skip_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = ("OK. Next daily verification will be skipped ()")  # TODO add time + description

    user_id = update.message.from_user.id
    AccessEnv.on_write(user_id, "skip", True)
    await update.message.reply_text(message)


async def bugreport_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = ("OK. Please describe the bug and what you did to see it")  # TODO add time + description

    user_id = update.message.from_user.id
    AccessEnv.on_write(user_id, "state", "bugreport")
    await update.message.reply_text(message)


async def fastcheck_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = ("OK. Tell your problem to emergency conctacts")  # TODO add time + description

    user_id = update.message.from_user.id
    AccessEnv.on_write(user_id, "state", "fastcheck")
    await update.message.reply_text(message)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = ("OK. Describe your problem")  # TODO add time + description
    await update.message.reply_text(message)
