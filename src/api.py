import time
import re
import random
import telegram
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ChatMemberHandler
from telegram.ext import CallbackQueryHandler
from datetime import datetime, timedelta
from utils.env_pipeline import AccessEnv

from src.commands import start_command, info_command, bugreport_command
from src.commands import addcontact_command, showcontacts_command, delcontact_command
from src.commands import addverif_command, showverifs_command, delverif_command, kill_user_data
from src.commands import skip_command, undoskip_command, fastcheck_command, help_command, undohelp_command

TOKEN, BOT_USERNAME = AccessEnv.telegram_keys()
P_HTML = telegram.constants.ParseMode.HTML

async def send_hope_message(update: Update):
    print('API:', 'Send Hope Message')
    message = '<b>Alert status is reset</b>. Everything is back to normal.'
    await update.message.reply_text(text=message, parse_mode=P_HTML)


async def extract_user_id_add(update: Update, content: str):
    error_contact, new_contacts = [], []
    user_id = update.message.from_user.id

    # Use regular expression to extract the username from the tag
    for line in content.splitlines():
        match_tag = re.match(r'@([\w\d_]+)', line)

        if match_tag:
            new_contacts.append(match_tag.group(1))
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
        match_tag = re.match(r'@([\w\d_]+)', line)

        if match_tag:
            del_contacts.append(match_tag.group(1))
        else:
            error_contact.append(line)

    AccessEnv.on_write_contacts(user_id, "del", del_contacts)

    message = "Given contacts are now deleted from your account."
    if len(error_contact) != 0:
        message += "\nFollowing contacts weren't removed due to their unknown format:\n" + str(error_contact)

    return await update.message.reply_text(message)


async def extract_verif_add(update: Update, content: str):  # TODO Check same date verif / not enough space between
    error_contact, new_verif = [], []
    user_id = update.message.from_user.id

    # Use regular expression to extract the username from the tag
    for line in content.splitlines():
        match_tag = re.match(r'^(0[0-9]|1[0-9]|2[0-3]):([0-5][0-9]) *- *([\w ]+)', line)

        if match_tag:
            chosen_time, desc = f"{match_tag.group(1)}:{match_tag.group(2)}", match_tag.group(3)
            new_verif.append({"time": chosen_time, "desc": desc, "active": True})
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
        match_tag = re.match(r'^(0[0-9]|1[0-9]|2[0-3]):([0-5][0-9])$', line)

        if match_tag:
            chosen_time = f"{match_tag.group(1)}:{match_tag.group(2)}"
            del_verif.append(chosen_time)
        else:
            error_contact.append(line)

    AccessEnv.on_write_verifications(user_id, "del", del_verif)

    message = "Given daily verifications are now deleted to your account."
    if len(error_contact) != 0:
        message += "\nFollowing verifications weren't removed due to their unknown format:\n" + str(error_contact)

    return await update.message.reply_text(message)


async def extract_bugreport(update: Update, content: str):
    filename = "bug_reports/report_" + str(random.randint(0, 999999))
    with open(filename, 'w') as file:
        file.write(content)
    message = "Thank you for the report!"
    return await update.message.reply_text(message)


async def skip_alarm(update: Update, content: str):
    error_contact, skip_verif = [], []
    user_id = update.message.from_user.id

    # Use regular expression to extract the username from the tag
    for line in content.splitlines():
        match_tag = re.match(r'^(0[0-9]|1[0-9]|2[0-3]):([0-5][0-9])$', line)

        if match_tag:
            chosen_time = f"{match_tag.group(1)}:{match_tag.group(2)}"
            skip_verif.append(chosen_time)
        else:
            error_contact.append(line)

    AccessEnv.on_write_verifications(user_id, "skip", skip_verif)

    message = "Given daily verification(s) is now skipped for the next 24h."
    if len(error_contact) != 0:
        message += "\nFollowing verification(s) weren't skipped due to their unknown format:\n" + str(error_contact)

    return await update.message.reply_text(message)


async def undoskip_alarm(update: Update, content: str):
    error_contact, skip_verif = [], []
    user_id = update.message.from_user.id

    # Use regular expression to extract the username from the tag
    for line in content.splitlines():
        match_tag = re.match(r'^(0[0-9]|1[0-9]|2[0-3]):([0-5][0-9])$', line)

        if match_tag:
            chosen_time = f"{match_tag.group(1)}:{match_tag.group(2)}"
            skip_verif.append(chosen_time)
        else:
            error_contact.append(line)

    AccessEnv.on_write_verifications(user_id, "undoskip", skip_verif)

    message = "Given daily verification(s) is now activated."
    if len(error_contact) != 0:
        message += "\nFollowing verification(s) weren't activated due to their unknown format:\n" + str(error_contact)

    return await update.message.reply_text(message)


async def extract_fastcheck(update: Update, content: str):
    user_id = update.message.from_user.id
    current_time = datetime.now()
    # Use regular expression to extract the username from the tag
    match_tag = re.match(r'(\d+) *mn', content)

    if not match_tag:
        return await update.message.reply_text(f"Unknown format: \"{content}\".")

    waiting_time = int(match_tag.group(1))
    if waiting_time > 20:
        return await update.message.reply_text("Invalid time, 20mn max")

    current_time += timedelta(minutes=waiting_time)
    time_to_display = current_time.strftime("%H:%M")

    new_alarm = {"time": time_to_display, "desc": "Auto fast check", "active": None}
    AccessEnv.on_write_verifications(user_id, "add", [new_alarm], True)

    message = f"Fast Check in {waiting_time}mn taken into account! ({time_to_display})"
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
        "undoskip": undoskip_alarm,
        "fastcheck": extract_fastcheck,
    }

    selected_case = switch_dict.get(state, default_case)

    user_id = update.message.from_user.id
    AccessEnv.on_write(user_id, "state", "")

    return await selected_case(update, message_body)


async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_type: str = update.message.chat.type
    message_body: str = update.message.text

    if message_type == 'group':
        message_body: str = message_body.lower()
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
        get_state = AccessEnv.on_read(user_id, "state")

        print('API:', f"Command call {get_state=}", f"Content: {message_body=}")
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
        message = ("OK. Emergency contacts have received your request for help!\n"
                   "Type /undohelp to cancel the alert")
        return await query.edit_message_text(text=message)
    if query.data == "2":
        message = "OK. Glad to hear it was a mistake!"
        return await query.edit_message_text(text=message)

    if query.data == "3":
        AccessEnv.on_write(user_id, "alert_mode", False)
        message = "OK. Your emergency contacts have received information that the alert has been disabled."
        return await query.edit_message_text(text=message)
    if query.data == "4":
        message = "OK. Operation canceled."
        return await query.edit_message_text(text=message)

    return await query.edit_message_text(text=f"Unknown: Query data ({query.data})")


def run_api():
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
    app.add_handler(CommandHandler('undoskip', undoskip_command))
    app.add_handler(CommandHandler('fastcheck', fastcheck_command))
    app.add_handler(CommandHandler('stop', kill_user_data))
    app.add_handler(CommandHandler('unsubscibe', kill_user_data))

    # Buttons under text
    app.add_handler(CallbackQueryHandler(button))

    # Messages
    app.add_handler(MessageHandler(filters.TEXT, handle_messages))

    # Errors
    app.add_error_handler(error)

    # Polls the bot
    app.run_polling()
