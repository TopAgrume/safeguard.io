import time
import re
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.ext import CallbackQueryHandler
from utils.env_pipeline import AccessEnv

from src.commands import start_command, info_command, bugreport_command
from src.commands import addcontact_command, showcontacts_command, delcontact_command
from src.commands import addverif_command, showverifs_command, delverif_command
from src.commands import skip_command, unskip_command, fastcheck_command, help_command, undohelp_command

TOKEN, BOT_USERNAME = AccessEnv.telegram_keys()


async def send_hope_message(update: Update):
    print('API:', 'Send Hope Message')
    await update.message.reply_text('Alert status is reset. Everything is back to normal.')


async def extract_user_id_add(update: Update, content: str):
    error_contact, new_contacts = [], []
    user_id = update.message.from_user.id

    # Use regular expression to extract the username from the tag
    for line in content.splitlines():
        match_tag = re.match(r'@(\w+)', line)

        if match_tag:
            new_contacts.append((match_tag.group(1), False))
        else:
            error_contact.append(line)

    AccessEnv.on_write_contacts(user_id, "add", new_contacts)

    message = "Given contacts are now added to your account."
    if len(error_contact) != 0:
        message += "\nFollowing contacts weren't added due to their unknown format:\n" + str(error_contact)

    return await update.message.reply_text(message)


async def extract_user_id_del(update: Update, content: str):
    error_contact, del_contacts = [], []
    user_id = update.message.from_user.id

    # Use regular expression to extract the username from the tag
    for line in content.splitlines():
        match_tag = re.match(r'@(\w+)', line)

        if match_tag:
            del_contacts.append(match_tag.group(1))
        else:
            error_contact.append(line)

    AccessEnv.on_write_contacts(user_id, "del", del_contacts)

    message = "Given contacts are now deleted from your account."
    if len(error_contact) != 0:
        message += "\nFollowing contacts weren't removed due to their unknown format:\n" + str(error_contact)

    return await update.message.reply_text(message)


async def extract_verif_add(update: Update, content: str):
    error_contact, new_verif = [], []
    user_id = update.message.from_user.id

    # Use regular expression to extract the username from the tag
    for line in content.splitlines():
        match_tag = re.match(r'(\d+):(\d{2}) *- *([\w ]+)', line)

        if match_tag:
            hour, min = int(match_tag.group(1)), int(match_tag.group(2))
            desc = match_tag.group(3)
            new_verif.append((hour, min, desc, True))
        else:
            error_contact.append(line)

    AccessEnv.on_write_verifications(user_id, "add", new_verif)

    message = "Given daily verifications are now added to your account."
    if len(error_contact) != 0:
        message += "\nFollowing verifications weren't added due to their unknown format:\n" + str(error_contact)

    return await update.message.reply_text(message)


async def extract_verif_del(update: Update, content: str):
    error_contact, del_verif = [], []
    user_id = update.message.from_user.id

    # Use regular expression to extract the username from the tag
    for line in content.splitlines():
        match_tag = re.match(r'(\d+):(\d{2})', line)

        if match_tag:
            hour, min = int(match_tag.group(1)), int(match_tag.group(2))
            del_verif.append((hour, min))
        else:
            error_contact.append(line)

    AccessEnv.on_write_verifications(user_id, "del", del_verif)

    message = "Given daily verifications are now deleted to your account."
    if len(error_contact) != 0:
        message += "\nFollowing verifications weren't removed due to their unknown format:\n" + str(error_contact)

    return await update.message.reply_text(message)


async def extract_bugreport(update: Update, content: str):  # TODO link
    print(content)
    message = "Thank you for the report!"
    return await update.message.reply_text(message)


async def skip_alarm(update: Update, content: str):
    error_contact, skip_verif = [], []
    user_id = update.message.from_user.id

    # Use regular expression to extract the username from the tag
    for line in content.splitlines():
        match_tag = re.match(r'(\d+):(\d{2})', line) #TODO verif format 23:59

        if match_tag:
            hour, min = int(match_tag.group(1)), int(match_tag.group(2))
            skip_verif.append((hour, min))
        else:
            error_contact.append(line)

    AccessEnv.on_write_verifications(user_id, "skip", skip_verif)

    message = "Given daily verification(s) is now skipped for the next 24h."
    if len(error_contact) != 0:
        message += "\nFollowing verification(s) weren't skipped due to their unknown format:\n" + str(error_contact)

    return await update.message.reply_text(message)


async def unskip_alarm(update: Update, content: str):
    error_contact, skip_verif = [], []
    user_id = update.message.from_user.id

    # Use regular expression to extract the username from the tag
    for line in content.splitlines():
        match_tag = re.match(r'(\d+):(\d{2})', line) #TODO verif format 23:59

        if match_tag:
            hour, min = int(match_tag.group(1)), int(match_tag.group(2))
            skip_verif.append((hour, min))
        else:
            error_contact.append(line)

    AccessEnv.on_write_verifications(user_id, "unskip", skip_verif)

    message = "Given daily verification(s) is now activated."
    if len(error_contact) != 0:
        message += "\nFollowing verification(s) weren't activated due to their unknown format:\n" + str(error_contact)

    return await update.message.reply_text(message)


async def extract_fastcheck(update: Update, content: str):  # TODO link
    print(content)
    message = "Fast Check taken into account!"
    return await update.message.reply_text(message)


async def default_case(update: Update, content: str):
    return await update.message.reply_text(f"Response out of context -> Unknown command ({content})")


async def state_dispatcher(update: Update, state: str, message_body: str):
    switch_dict = {
        "addcontact": extract_user_id_add,
        "delcontact": extract_user_id_del,
        "addverif": extract_verif_add,
        "delverif": extract_verif_del,
        "bugreport": extract_bugreport,
        "skip": skip_alarm,
        "unskip": unskip_alarm,
        "fastcheck": extract_fastcheck,
    }

    selected_case = switch_dict.get(state, default_case)

    user_id = update.message.from_user.id
    AccessEnv.on_write(user_id, "state", "")

    return await selected_case(update, message_body)


async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_type: str = update.message.chat.type
    message_body: str = update.message.text.lower()

    if message_type == 'group':
        if BOT_USERNAME in message_body:
            # new_text: str = message_body.replace(BOT_USERNAME, '').strip()
            response = 'This bot does not support groups for now'
            await update.message.reply_text(response)
        else:
            return

    user_id = update.message.from_user.id
    response_message, alert_mode, _ = AccessEnv.on_read(user_id)

    if response_message:
        # Already answered / Random call
        print('API:', 'Response out of context')
        get_state = AccessEnv.on_read(user_id, "state")
        return await state_dispatcher(update, get_state, message_body)

    if not alert_mode:
        print('API:', 'Response to contact and confirmation demand')
        greeting = "Have a great day! :D" if time.localtime().tm_hour == 10 else "Have a wonderful night! ;)"
        response = 'Thank you for your response! ' + greeting

        AccessEnv.on_write(user_id, "reminder_count", 0)
        AccessEnv.on_write(user_id, "response_message", True)
        return await update.message.reply_text(response)

    print('API:', 'Response to unset the alert mode')
    AccessEnv.on_write(user_id, "alert_mode", False)
    AccessEnv.on_write(user_id, "reminder_count", 0)
    AccessEnv.on_write(user_id, "response_message", True)
    return await send_hope_message(update)


async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print('API ERROR:', f'Update {update} caused error {context}')


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    # 'button' will be called for each button the user clicks
    await query.answer()

    if query.data == "1":  # TODO contact emergencies
        AccessEnv.on_write(user_id, "alert_mode", True)
        return await query.edit_message_text(text="OK. Emergency contacts have received your request for help!")
    if query.data == "2":
        return await query.edit_message_text(text="OK. Glad to hear it was a mistake!")

    if query.data == "3":
        AccessEnv.on_write(user_id, "alert_mode", False)
        return await query.edit_message_text(
            text="OK. Your emergency contacts have received information that the alert has been disabled")
    if query.data == "4":
        return await query.edit_message_text(text="OK. Operation canceled.")

    return await query.edit_message_text(text=f"Unknown: Query data ({query.data})")


def run_api():
    AccessEnv.on_reset()
    print('API:', 'Starting bot...')

    app = Application.builder().token(TOKEN).build()

    # Commands
    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('info', info_command))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CommandHandler('undohelp', undohelp_command))
    app.add_handler(CommandHandler('bugreport', bugreport_command))
    app.add_handler(CommandHandler('addcontact', addcontact_command))
    app.add_handler(CommandHandler('showcontacts', showcontacts_command))
    app.add_handler(CommandHandler('delcontact', delcontact_command))
    app.add_handler(CommandHandler('addverif', addverif_command))
    app.add_handler(CommandHandler('showverifs', showverifs_command))
    app.add_handler(CommandHandler('delverif', delverif_command))
    app.add_handler(CommandHandler('skip', skip_command))
    app.add_handler(CommandHandler('unskip', unskip_command))
    app.add_handler(CommandHandler('fastcheck', fastcheck_command))
    app.add_handler(CallbackQueryHandler(button))

    # Messages
    app.add_handler(MessageHandler(filters.TEXT, handle_messages))

    # Errors
    app.add_error_handler(error)

    # Polls the bot
    print('API:', 'Polling...')
    app.run_polling(poll_interval=0.5)
