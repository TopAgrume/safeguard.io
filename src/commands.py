from telegram import Update, Bot
from telegram.ext import ContextTypes
from utils.env_pipeline import AccessEnv

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_first_name: str = str(update.message.chat.first_name)
    # TODO Create new database user_id
    await update.message.reply_text(f"Hello {user_first_name}! Thanks for chatting with me! I am a Safeguard.io bot")


async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('I make sure everything is okay! ;)')


"""def extract_user_id(content: str):
    # Use regular expression to extract the username from the tag
    match_tag = re.match(r'@(\w+)', content)
    match_number = re.match(r'+(\d+)', content)

    if match_tag:
        username = match_tag.group(1)
        return username

    if match_number:
        username = match_number.group(1)
        return username

    return "Invalid tag format"
"""

async def addcontact_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = ("OK. Send me a list of contacts to add. Please use this format:\n\n"
               "@username1\n"
               "@username2\n\n"
               "Send /empty to keep the list empty.")

    user_id = update.message.from_user.id
    AccessEnv.on_write(user_id, "state", "addcontact")
    await update.message.reply_text(message)


async def showcontacts_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = ("OK. Here is you list of contacts:\n\n") # TODO list contacts, + show pairing
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
    message = ("OK. Here is you list of daily verifications:\n\n")  # TODO list verifs, + show description
    await update.message.reply_text(message)


async def delverif_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = ("OK. Send me a list of daily verifications to delete. Please use this format:\n\n"
               "8:20"
               "21:30"
               "Send /empty to keep the list empty.")

    user_id = update.message.from_user.id
    AccessEnv.on_write(user_id, "state", "delverif")
    await update.message.reply_text(message)


async def skip_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = ("OK. Next daily verification will be skipped ()") # TODO add time + description

    user_id = update.message.from_user.id
    AccessEnv.on_write(user_id, "state", "skip")
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
